"""Accepted fixture bytes served by the actual SSR build, then copied for negative HTTP tests."""
import functools
import hashlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import json
import os
from pathlib import Path
import select
import shutil
import subprocess
import sys
import tempfile
import threading
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[3]
RELEASE = ROOT / 'scripts/daily-release.py'
MISE = shutil.which('mise') or '/opt/homebrew/bin/mise'
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('daily_release_fixture_module', RELEASE)
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


def run(args, cwd=None, env=None):
    return subprocess.run([str(arg) for arg in args], cwd=cwd, env=env, check=True, capture_output=True, text=True).stdout.strip()


def start_runtime(owner, artifact, bundle, app=ROOT / 'apps/daily'):
    process = subprocess.Popen([MISE, 'exec', 'node@22.23.3', '--', 'node',
                                str(Path(__file__).with_name('daily_release_fixture.mjs')),
                                str(app), str(artifact), str(bundle)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    def stop():
        process.terminate()
        try:
            process.communicate(timeout=20)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()
    owner.addCleanup(stop)
    if not select.select([process.stdout], [], [], 45)[0]:
        stop()
        raise AssertionError('local SSR fixture did not start')
    origin = process.stdout.readline().strip()
    if not origin.startswith('http://127.0.0.1:'):
        stop()
        raise AssertionError('local SSR fixture failed: ' + origin)
    return origin


class Fixture:
    @classmethod
    def setUpClass(cls):
        cls.shared_tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.shared_tmp.cleanup)
        cls.shared = Path(cls.shared_tmp.name)
        sources = cls.shared / 'sources'
        sources.mkdir()
        fixtures = ROOT / 'apps/daily/tests/fixtures'
        for name, source in [('2026-05-10', 'legacy-unversioned.md'), ('2026-10-15', 'editorial-v2-four-stories.md'), ('2026-10-16', 'editorial-v2-brief-archive.md')]:
            text = (fixtures / source).read_text()
            if name == '2026-10-15':
                text = text.replace('digest_format: editorial-v2\n', '''digest_format: editorial-v2
story_metadata:
  anthropic-monorepo:
    section: Developer tools
    visual:
      kind: bar
      title: Reported daily merges
      unit: merges per day
      caption: Reported by the company.
      source_url: https://x.com/AnthropicAI/status/2110047081414987957
      points:
        - {label: May, value: 2500, qualifier: approximate}
        - {label: September, value: 30000, qualifier: greater-than}
  gloss-x-import:
    section: Reading
    visual:
      kind: image
      src: https://media.example/original.jpg
      width: 1200
      height: 675
      alt: The launch screen
      caption: A source image.
      credit: Author
      source_url: https://x.com/nutlope/status/2110385721391366263
''')
            (sources / f'x-ai-{name}.md').write_text(text)
        cls.bundle_source = cls.shared / 'bundle'
        metadata = json.loads(run([MISE, 'exec', 'node@22.23.3', '--', 'node', '--import', 'tsx', 'cli.ts',
                                   '--input-dir', sources, '--output-dir', cls.bundle_source, '--compiler-revision', 'c' * 40], ROOT / 'hermes/ai-x-digest/content'))
        (cls.bundle_source / 'bundle.json').write_text(json.dumps(metadata))
        # Each suite uses the real SSR output once. Negative tests mutate copies of those HTTP bodies.
        # The normal focused check order builds the app before these Python tests.
        # Copy its complete SSR output so runtime fixtures never mutate canonical build files.
        artifact = cls.shared / 'artifact'
        shutil.copytree(ROOT / 'apps/daily/dist', artifact)
        class Cleanup:
            def addCleanup(self, function):
                cls.addClassCleanup(function)
        cls.runtime_origin = start_runtime(Cleanup(), artifact, cls.bundle_source)
        cls.pages = cls.shared / 'pages'
        cls.pages.mkdir()
        manifest, _ = release.fetch(cls.runtime_origin, '/deployment.json')
        provenance = json.loads(manifest)
        cls.actual_code = provenance['codeRevision']
        for route in provenance['routes']:
            body, _ = release.fetch(cls.runtime_origin, route)
            filename = cls.pages / ('index.html' if route == '/' else route.lstrip('/') + ('index.html' if route.endswith('/') else ''))
            filename.parent.mkdir(parents=True, exist_ok=True)
            filename.write_text(body)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name).resolve()
        self.repo = self.home / 'repo'
        self.repo.mkdir()
        self.git('init', '-b', 'main')
        self.git('config', 'user.email', 'fixture@example.com')
        self.git('config', 'user.name', 'Fixture')
        (self.repo / 'note').write_text('one')
        self.git('add', '.')
        self.git('commit', '-m', 'one')
        self.old = self.git('rev-parse', 'HEAD')
        (self.repo / 'note').write_text('two')
        self.git('commit', '-am', 'two')
        self.new = self.git('rev-parse', 'HEAD')
        # This private synthetic Git repository has code identities only, never digest commits.
        (self.repo / 'scripts').symlink_to(ROOT / 'scripts', target_is_directory=True)
        (self.repo / 'hermes').symlink_to(ROOT / 'hermes', target_is_directory=True)
        self.state = self.home / 'state'
        self.state.mkdir()
        self.bundle = self.home / 'bundle'
        shutil.copytree(self.bundle_source, self.bundle)
        self.live = self.home / 'live'
        shutil.copytree(self.pages, self.live)
        provenance = json.loads((self.live / 'deployment.json').read_text())
        provenance['codeRevision'] = self.new
        (self.live / 'deployment.json').write_text(json.dumps(provenance))
        self.artifact = self.home / 'artifact'
        (self.artifact / 'server').mkdir(parents=True)
        (self.artifact / 'client').mkdir()
        (self.artifact / 'server/entry.mjs').write_text('export default {}')
        (self.artifact / 'server/wrangler.json').write_text(json.dumps({'main': 'entry.mjs', 'no_bundle': True, 'assets': {'directory': '../client'}}))
        (self.artifact / 'code.json').write_text(json.dumps({'codeRevision': self.new}))
        class Handler(SimpleHTTPRequestHandler):
            extensions_map = {**SimpleHTTPRequestHandler.extensions_map, '.xml': 'application/rss+xml; charset=utf-8'}
            def log_message(self, *args):
                pass
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Handler, directory=str(self.live)))
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.origin = f'http://127.0.0.1:{self.server.server_port}'
        self.env = dict(os.environ, PUBLISH_STATE_DIR=str(self.state), PUBLISH_REPO=str(self.repo), PUBLISH_VAULT_PUBLIC=str(self.home / 'vault'))

    def git(self, *args):
        return run(['git', '-C', self.repo, *args])

    def cli(self, *args):
        return subprocess.run([sys.executable, str(RELEASE), *map(str, args)], env=self.env, capture_output=True, text=True)

    def verify(self, *extra):
        return self.cli('verify', '--bundle', self.bundle, '--origin', self.origin, '--code-revision', self.new, *extra)

    def pending_request(self, phase='published'):
        metadata = json.loads((self.bundle / 'bundle.json').read_text())
        entry = next(entry for entry in metadata['manifest']['editions'] if entry['date'] == '2026-10-16')
        accepted = {'schemaVersion': 2, 'backend': 'r2', 'kind': 'scheduled', 'date': '2026-10-16', 'compilerRevision': 'c' * 40,
                    'expected': {'manifestSha256': 'a' * 64, 'etag': 'prior-etag'},
                    'files': {'x-ai-2026-10-16.md': {'staged': str(self.home / 'accepted.md'), 'beforeSha256': None, 'stagedSha256': entry['sourceSha256']}}}
        request = self.home / 'accepted.json'
        request.write_text(json.dumps(accepted))
        key = hashlib.sha256(json.dumps(accepted, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        frozen = self.state / 'bundles' / key
        frozen.parent.mkdir(exist_ok=True)
        if self.bundle != frozen:
            shutil.copytree(self.bundle, frozen, dirs_exist_ok=True)
        self.bundle = frozen
        receipt = self.state / 'receipts' / (key + '.json')
        receipt.parent.mkdir(exist_ok=True)
        value = {'schemaVersion': 2, 'backend': 'r2', 'requestHash': key, 'phase': phase, 'head': metadata['head'], 'manifest': metadata['manifest'],
                 'publicationId': metadata['head']['manifest']['sha256'], 'bundle': str(frozen), 'date': '2026-10-16', 'kind': 'scheduled'}
        receipt.write_text(json.dumps(value))
        (frozen / 'acceptance.json').write_text(json.dumps(value))
        (self.state / 'backend.json').write_text(json.dumps({'schemaVersion': 1, 'backend': 'r2', 'vaultRoot': str(self.home / 'private-vault'), 'configPath': str(self.home / 'r2.json')}))
        return request, receipt

    def deploy(self, candidate=None):
        if candidate:
            (self.artifact / 'code.json').write_text(json.dumps({'codeRevision': candidate}))
        marker = self.home / 'deployed'
        result = self.cli('deploy', '--artifact', self.artifact, '--bundle', self.bundle, '--origin', self.origin, '--',
                          sys.executable, '-c', 'from pathlib import Path; import sys; Path(sys.argv[1]).write_text("deployed")', marker,
                          '--config', self.artifact / 'server/wrangler.json')
        return result, marker
