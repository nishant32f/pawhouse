"""Local protocol proof. This fixture is not a Cloudflare preview bucket."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import unittest
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[3]
PUBLISH = ROOT / 'scripts/publication.py'
PACKAGE = ROOT / 'hermes/ai-x-digest/content'


class CliPublicationTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name).resolve()
        self.repo = self.home / 'repo'
        self.package = self.repo / 'hermes/ai-x-digest/content'
        self.package.mkdir(parents=True)
        for path in PACKAGE.glob('*.ts'):
            shutil.copyfile(path, self.package / path.name)
        shutil.copyfile(PACKAGE / 'package.json', self.package / 'package.json')
        (self.package / 'node_modules').symlink_to(PACKAGE / 'node_modules', target_is_directory=True)
        checker = Path('hermes/ai-x-digest/runtime/skills/note-taking/obsidian/scripts/verify-x-ai-digest-format.py')
        (self.repo / checker).parent.mkdir(parents=True)
        shutil.copyfile(ROOT / checker, self.repo / checker)
        shutil.copyfile(ROOT / 'hermes/ai-x-digest/story_identity.py', self.repo / 'hermes/ai-x-digest/story_identity.py')
        (self.repo / '.gitignore').write_text('node_modules\n__pycache__\n')
        self.git('init', '-b', 'fixture')
        self.git('config', 'user.name', 'Fixture')
        self.git('config', 'user.email', 'fixture@example.com')
        self.git('add', '.')
        self.git('commit', '-m', 'Pin fixture compiler')
        self.head = self.git('rev-parse', 'HEAD')
        self.state = self.home / 'state'
        self.state.mkdir()
        self.vault = self.home / 'private-vault'
        self.public = self.home / 'public'
        self.public.mkdir()
        (self.public / 'unrelated.md').write_text('unrelated public note may differ from Git\n')
        self.objects = {}
        self.mutex = threading.Lock()
        self.block = False
        self.upload_blocked = threading.Event()
        self.release_upload = threading.Event()
        outer = self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass
            def do_GET(self):
                key = unquote(urlsplit(self.path).path.removeprefix('/fixture/'))
                with outer.mutex:
                    item = outer.objects.get(key)
                if item is None:
                    self.send_response(404)
                    self.send_header('Content-Type', 'application/xml')
                    self.end_headers()
                    self.wfile.write(b'<Error><Code>NoSuchKey</Code></Error>')
                    return
                self.send_response(200)
                self.send_header('ETag', item['etag'])
                self.end_headers()
                self.wfile.write(item['bytes'])
            def do_PUT(self):
                key = unquote(urlsplit(self.path).path.removeprefix('/fixture/'))
                data = self.rfile.read(int(self.headers['Content-Length']))
                with outer.mutex:
                    old = outer.objects.get(key)
                    conflict = ((self.headers.get('If-None-Match') == '*' and old is not None) or
                                (self.headers.get('If-Match') is not None and (old is None or old['etag'] != self.headers['If-Match'])))
                    if not conflict:
                        item = {'bytes': data, 'etag': f'"opaque-{len(outer.objects) + 1}"'}
                        outer.objects[key] = item
                if conflict:
                    self.send_response(412)
                    self.send_header('Content-Type', 'application/xml')
                    self.end_headers()
                    self.wfile.write(b'<Error><Code>PreconditionFailed</Code></Error>')
                    return
                if outer.block and key != 'v1/head.json':
                    outer.block = False
                    outer.upload_blocked.set()
                    outer.release_upload.wait(timeout=20)
                try:
                    self.send_response(200)
                    self.send_header('ETag', item['etag'])
                    self.end_headers()
                except (BrokenPipeError, ConnectionResetError):
                    pass
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.server.daemon_threads = True
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop_server)
        config = self.home / 's3.json'
        config.write_text(json.dumps({'accountId': '1688bfec49a43a217df10ed33b86e300', 'bucket': 'fixture',
                                     'accessKeyId': 'fixture', 'secretAccessKey': 'fixture',
                                     'endpoint': f'http://127.0.0.1:{self.server.server_port}'}))
        config.chmod(0o600)
        (self.state / 'backend.json').write_text(json.dumps({'schemaVersion': 1, 'backend': 'r2', 'vaultRoot': str(self.vault), 'configPath': str(config)}))
        self.env = dict(os.environ, PUBLISH_REPO=str(self.repo), PUBLISH_STATE_DIR=str(self.state), PUBLISH_VAULT_PUBLIC=str(self.public))
        self.fixture = (ROOT / 'apps/daily/tests/fixtures/editorial-v2-four-stories.md').read_bytes()
        self.request_path = self.home / 'accepted.json'
        self.write_request('backfill', '2026-10-15', {'manifestSha256': None, 'etag': None}, self.fixture)

    def stop_server(self):
        self.release_upload.set()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.repo), *args], text=True, capture_output=True, check=True).stdout.strip()

    def write_request(self, kind, day, expected, data):
        name = f'x-ai-{day}.md'
        staged = self.home / ('staged-' + day + '.md')
        staged.write_bytes(data)
        target = self.vault / 'digests' / name
        self.request_path.write_text(json.dumps({'schemaVersion': 2, 'backend': 'r2', 'kind': kind, 'date': day, 'compilerRevision': self.head, 'expected': expected,
            'files': {name: {'staged': str(staged), 'stagedSha256': hashlib.sha256(data).hexdigest(), 'beforeSha256': hashlib.sha256(target.read_bytes()).hexdigest() if target.exists() else None}}}))

    def cli(self, *args):
        return subprocess.run([sys.executable, str(PUBLISH), *args], env=self.env, text=True, capture_output=True, timeout=30)

    def publish(self):
        result = self.cli('digest', '--request', str(self.request_path))
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def assert_git_unchanged(self):
        self.assertEqual(self.git('rev-parse', 'HEAD'), self.head)
        self.assertEqual(self.git('status', '--porcelain', '--untracked-files=all'), '')
        self.assertEqual(self.git('diff', '--cached', '--name-only'), '')

    def test_uncommitted_shared_formatter_rejects_the_claimed_compiler_revision(self):
        formatter = self.package / 'format.ts'
        formatter.write_text(formatter.read_text().replace('return "&lt;"', 'return "CHANGED"', 1))
        result = self.cli('digest', '--request', str(self.request_path))
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.objects, {})
        self.assertFalse((self.vault / 'digests').exists())
        self.assertEqual(self.git('rev-parse', 'HEAD'), self.head)

    def test_actual_cli_bootstrap_new_day_and_delivery_controls_without_git_writes(self):
        first = self.publish()
        self.assertEqual(first['phase'], 'published')
        self.assert_git_unchanged()
        self.assertEqual((self.vault / 'digests/x-ai-2026-10-15.md').read_bytes(), self.fixture)
        self.assertNotEqual(self.cli('delivery-begin', '--request', str(self.request_path)).returncode, 0)
        # An operator backfill cannot start delivery even after real reader proof is supplied by U4.
        receipt_file = self.state / 'receipts' / (first['requestHash'] + '.json')
        first['phase'] = 'readerverified'
        receipt_file.write_text(json.dumps(first))
        self.assertNotEqual(self.cli('delivery-begin', '--request', str(self.request_path)).returncode, 0)
        self.request_path = self.home / 'new-day.json'
        self.write_request('scheduled', '2026-10-16', {'manifestSha256': first['publicationId'], 'etag': first['etag']}, self.fixture.replace(b'2026-10-15', b'2026-10-16'))
        second = self.publish()
        self.assertEqual(second['phase'], 'published')
        self.assertNotEqual(second['publicationId'], first['publicationId'])
        self.assertEqual(len(second['manifest']['editions']), 2)
        self.assert_git_unchanged()
        self.assertNotEqual(self.cli('delivery-begin', '--request', str(self.request_path)).returncode, 0)
        receipt_file = self.state / 'receipts' / (second['requestHash'] + '.json')
        second['phase'] = 'readerverified'
        receipt_file.write_text(json.dumps(second))
        self.assertEqual(self.cli('delivery-begin', '--request', str(self.request_path)).returncode, 0)
        self.assertNotEqual(self.cli('resume', '--request', str(self.request_path)).returncode, 0)
        self.assertNotEqual(self.cli('delivery-begin', '--request', str(self.request_path)).returncode, 0)
        self.assertEqual(self.cli('delivery-complete', '--request', str(self.request_path), '--reference', 'fixture-proof').returncode, 0)
        self.assertEqual(self.publish()['phase'], 'complete')
        self.assert_git_unchanged()

    def test_sigkill_during_upload_recovers_same_frozen_publication(self):
        self.block = True
        process = subprocess.Popen([sys.executable, str(PUBLISH), 'digest', '--request', str(self.request_path)], env=self.env,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
        try:
            self.assertTrue(self.upload_blocked.wait(timeout=15), 'publisher never reached the upload')
            self.assertFalse('v1/head.json' in self.objects)
            receipt_file = next((self.state / 'receipts').glob('*.json'))
            before = json.loads(receipt_file.read_text())
            self.assertEqual(before['phase'], 'source-promoted')
            self.assertEqual((self.vault / 'digests/x-ai-2026-10-15.md').read_bytes(), self.fixture)
            os.killpg(process.pid, signal.SIGKILL)
            process.communicate(timeout=10)
            self.assertEqual(process.returncode, -signal.SIGKILL)
        finally:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL)
                process.communicate(timeout=10)
            self.release_upload.set()
        Path(json.loads(self.request_path.read_text())['files']['x-ai-2026-10-15.md']['staged']).write_text('draft changed after interruption')
        result = self.cli('recover')
        self.assertEqual(result.returncode, 0, result.stderr)
        after = json.loads(receipt_file.read_text())
        self.assertEqual(after['publicationId'], before['publicationId'])
        self.assertEqual(after['phase'], 'published')
        self.assertEqual(json.loads(self.objects['v1/head.json']['bytes'])['manifest']['sha256'], before['publicationId'])
        self.assertFalse((self.state / 'r2-promotion.json').exists())
        self.assert_git_unchanged()

if __name__ == '__main__':
    unittest.main()
