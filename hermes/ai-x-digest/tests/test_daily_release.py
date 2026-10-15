from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import functools
import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
import xml.sax.saxutils

ROOT = Path(__file__).resolve().parents[3]
RELEASE = ROOT / 'scripts/daily-release.py'

class ReleaseTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
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
        self.artifact = self.home / 'artifact'
        self.live = self.home / 'live'
        for folder in (self.artifact, self.live):
            folder.mkdir()
            manifest = {'sourceRevision': self.new, 'editions': [{'date': '2026-10-16', 'sourcePath': 'content/digests/x-ai-2026-10-16.md', 'sourceSha256': 'a' * 64, 'path': '/editions/2026-10-16/', 'readPath': '/editions/2026-10-16/read/', 'stories': ['/editions/2026-10-16/stories/stable-id/']}]}
            (folder / 'deployment.json').write_text(json.dumps(manifest))
            body = '<main><article><h1>A full story</h1><p>The full opening and complete body remain visible.</p><a href="https://example.com/source">Original source</a></article></main>'
            for route in ['/editions/2026-10-16/', '/editions/2026-10-16/read/', '/editions/2026-10-16/stories/stable-id/']:
                path = folder / route.lstrip('/') / 'index.html'
                path.parent.mkdir(parents=True)
                path.write_text(body)
            (folder / 'index.html').write_text(body)
            for route in ('archive', 'search'):
                (folder / route).mkdir()
                (folder / route / 'index.html').write_text(body)
            (folder / 'sitemap.xml').write_text('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://daily.example/editions/2026-10-16/</loc></url></urlset>')
            (folder / 'rss.xml').write_text('<rss version="2.0"><channel><item><guid>https://daily.example/editions/2026-10-16/</guid><description>' + xml.sax.saxutils.escape(body) + '</description></item></channel></rss>')
        class Handler(SimpleHTTPRequestHandler):
            extensions_map = {**SimpleHTTPRequestHandler.extensions_map, '.xml': 'application/rss+xml; charset=utf-8'}
            def log_message(self, *args):
                pass
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Handler, directory=str(self.live)))
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.origin = f'http://127.0.0.1:{self.server.server_port}'
        self.env = dict(os.environ, PUBLISH_STATE_DIR=str(self.home / 'state'), PUBLISH_REPO=str(self.repo), PUBLISH_VAULT_PUBLIC=str(self.home / 'vault'))

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.repo), *args], check=True, capture_output=True, text=True).stdout.strip()

    def cli(self, *args):
        return subprocess.run([sys.executable, str(RELEASE), *args], env=self.env, capture_output=True, text=True)

    def verify(self):
        return self.cli('verify', '--artifact', str(self.artifact), '--origin', self.origin)

    def test_verified_day_extends_exact_redirects_and_failed_new_day_adds_none(self):
        result = self.verify()
        self.assertEqual(result.returncode, 0, result.stderr)
        mapping = self.home / 'state/verified-redirects.json'
        mappings = json.loads(mapping.read_text())['redirects']
        self.assertEqual(mappings['/digests/x-ai-2026-10-16']['destination'], self.origin + '/editions/2026-10-16/')
        self.assertEqual(len(mappings), 1)
        before = mapping.read_bytes()
        (self.live / 'editions/2026-10-16/read/index.html').write_text('<main><p>Truncated</p></main>')
        self.assertNotEqual(self.verify().returncode, 0)
        self.assertEqual(mapping.read_bytes(), before)

    def test_manifest_and_http200_cannot_cover_truncated_body(self):
        (self.live / 'editions/2026-10-16/stories/stable-id/index.html').write_text('<main>A full story</main>')
        self.assertNotEqual(self.verify().returncode, 0)
        self.assertFalse((self.home / 'state/verified-redirects.json').exists())

    def test_reverse_finish_blocks_older_build(self):
        result = self.cli('guard', '--candidate', self.old, '--origin', self.origin)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.cli('guard', '--candidate', self.new, '--origin', self.origin).returncode, 0)

    def test_bootstrap_does_not_treat_http_failure_as_absent_deployment(self):
        (self.live / 'deployment.json').unlink()
        self.assertNotEqual(self.cli('guard', '--candidate', self.new, '--origin', self.origin).returncode, 0)
        self.assertEqual(self.cli('guard', '--candidate', self.new, '--origin', self.origin, '--bootstrap').returncode, 0)
        (self.live / 'deployment.json').write_text('invalid JSON')
        self.assertNotEqual(self.cli('guard', '--candidate', self.new, '--origin', self.origin, '--bootstrap').returncode, 0)

    def test_failed_verification_preserves_last_verified_release(self):
        self.assertEqual(self.verify().returncode, 0)
        prior = (self.home / 'state/reader-release.json').read_bytes()
        (self.live / 'rss.xml').write_text('<rss><channel/></rss>')
        self.assertNotEqual(self.verify().returncode, 0)
        self.assertEqual((self.home / 'state/reader-release.json').read_bytes(), prior)

    def test_failed_deployment_preserves_previous_artifact_mapping_and_pending_delivery(self):
        self.assertEqual(self.verify().returncode, 0)
        state = self.home / 'state'
        before_map = (state / 'verified-redirects.json').read_bytes()
        before_release = (state / 'reader-release.json').read_bytes()
        before_body = (self.live / 'editions/2026-10-16/read/index.html').read_bytes()
        result = self.cli('deploy', '--artifact', str(self.artifact), '--origin', self.origin, '--', sys.executable, '-c', 'raise SystemExit(7)')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((state / 'verified-redirects.json').read_bytes(), before_map)
        self.assertEqual((state / 'reader-release.json').read_bytes(), before_release)
        self.assertEqual((self.live / 'editions/2026-10-16/read/index.html').read_bytes(), before_body)
        self.assertTrue((state / 'reader-failure.json').exists())

    def test_older_reverse_finish_never_reaches_deployment_command(self):
        manifest = json.loads((self.artifact / 'deployment.json').read_text())
        manifest['sourceRevision'] = self.old
        (self.artifact / 'deployment.json').write_text(json.dumps(manifest))
        marker = self.home / 'deployed'
        result = self.cli('deploy', '--artifact', str(self.artifact), '--origin', self.origin, '--', sys.executable, '-c', 'from pathlib import Path; import sys; Path(sys.argv[1]).write_text("deployed")', str(marker))
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(marker.exists())

    def test_descendant_can_verify_only_the_same_accepted_date_hash(self):
        import hashlib
        relative = 'digests/x-ai-2026-10-16.md'
        request = {'date': '2026-10-16', 'expected_head': self.old, 'files': {relative: {'staged': str(self.home / 'accepted.md'), 'before_sha256': None, 'staged_sha256': 'a' * 64}}}
        request_file = self.home / 'accepted.json'
        request_file.write_text(json.dumps(request))
        key = hashlib.sha256(json.dumps(request, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        receipt_file = self.home / 'state/receipts' / (key + '.json')
        receipt_file.parent.mkdir(parents=True)
        receipt = {'phase': 'readerpending', 'commit': self.old, 'files': {relative: 'a' * 64}}
        receipt_file.write_text(json.dumps(receipt))
        manifest = json.loads((self.artifact / 'deployment.json').read_text())
        manifest['sourceRevision'] = self.old
        (self.artifact / 'deployment.json').write_text(json.dumps(manifest))
        result = self.cli('verify', '--artifact', str(self.artifact), '--origin', self.origin, '--request', str(request_file))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(receipt_file.read_text())['phase'], 'readerverified')
        receipt_file.write_text(json.dumps(receipt))
        manifest['editions'][0]['sourceSha256'] = 'b' * 64
        (self.artifact / 'deployment.json').write_text(json.dumps(manifest))
        manifest['sourceRevision'] = self.new
        (self.live / 'deployment.json').write_text(json.dumps(manifest))
        self.assertNotEqual(self.cli('verify', '--artifact', str(self.artifact), '--origin', self.origin, '--request', str(request_file)).returncode, 0)
        self.assertEqual(json.loads(receipt_file.read_text())['phase'], 'readerpending')

    def test_failed_new_build_preserves_prior_complete_artifact(self):
        artifacts = self.home / 'state/artifacts'
        prior = artifacts / self.old
        prior.mkdir(parents=True)
        (prior / 'deployment.json').write_text(json.dumps({'sourceRevision': self.old}))
        (prior / 'index.html').write_text('previous complete artifact')
        result = self.cli('build', '--commit', self.new)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((prior / 'index.html').read_text(), 'previous complete artifact')
        self.assertFalse((artifacts / self.new).exists())

    def test_cloudflare_version_is_recorded_separately(self):
        deployments = self.home / 'deployments.json'
        deployments.write_text(json.dumps([{'created_on': '2026-10-15T00:00:00Z', 'versions': [{'version_id': 'first-real-version', 'percentage': 100}]}, {'created_on': '2026-10-16T00:00:00Z', 'versions': [{'version_id': 'second-real-version', 'percentage': 100}]}]))
        result = self.cli('version', '--deployments', str(deployments))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), 'second-real-version')

    def test_historical_route_deletion_is_rejected_before_deploy(self):
        manifest = json.loads((self.live / 'deployment.json').read_text())
        historical = dict(manifest['editions'][0], date='2026-10-15', path='/editions/2026-10-15/', readPath='/editions/2026-10-15/read/', stories=[])
        manifest['editions'].append(historical)
        (self.live / 'deployment.json').write_text(json.dumps(manifest))
        marker = self.home / 'deployed'
        result = self.cli('deploy', '--artifact', str(self.artifact), '--origin', self.origin, '--', sys.executable, '-c', 'from pathlib import Path; import sys; Path(sys.argv[1]).write_text("deployed")', str(marker))
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(marker.exists())

    def test_code_rollback_cannot_remove_a_declared_article_file(self):
        (self.artifact / 'editions/2026-10-16/stories/stable-id/index.html').unlink()
        marker = self.home / 'deployed'
        result = self.cli('deploy', '--artifact', str(self.artifact), '--origin', self.origin, '--', sys.executable, '-c', 'from pathlib import Path; import sys; Path(sys.argv[1]).write_text("deployed")', str(marker))
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(marker.exists())

    def test_cloudflare_bootstrap_distinguishes_missing_deployment_from_bad_response(self):
        metadata = self.live / ('accounts/' + '0' * 32 + '/workers/scripts/pawhouse-daily/deployments')
        code = '''
import importlib.util
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(sys.argv[1]).parent))
spec = importlib.util.spec_from_file_location('release', sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.CLOUDFLARE_API = sys.argv[2]
print(json.dumps(module.cloudflare_deployments(sys.argv[3] == 'yes')))
'''
        env = dict(self.env, CLOUDFLARE_ACCOUNT_ID='0' * 32, CLOUDFLARE_API_TOKEN='fixture-token')
        def lookup(bootstrap):
            return subprocess.run([sys.executable, '-c', code, str(RELEASE), self.origin, 'yes' if bootstrap else 'no'], env=env, capture_output=True, text=True)
        self.assertNotEqual(lookup(False).returncode, 0)
        self.assertEqual(json.loads(lookup(True).stdout), [])
        metadata.parent.mkdir(parents=True)
        metadata.write_text('not JSON')
        self.assertNotEqual(lookup(True).returncode, 0)
        metadata.write_text(json.dumps({'success': False, 'errors': [{'message': 'unauthorized'}]}))
        self.assertNotEqual(lookup(True).returncode, 0)
        metadata.write_text(json.dumps({'success': True, 'result': {'deployments': [{'created_on': '2026-10-15T00:00:00Z', 'versions': [{'version_id': 'fixture-version', 'percentage': 100}]}]}}))
        self.assertEqual(json.loads(lookup(False).stdout)[0]['versions'][0]['version_id'], 'fixture-version')

    def test_verified_later_day_extends_mapping_and_failed_day_adds_none(self):
        import shutil
        self.assertEqual(self.verify().returncode, 0)
        mapping_file = self.home / 'state/verified-redirects.json'
        for folder in (self.artifact, self.live):
            manifest = json.loads((folder / 'deployment.json').read_text())
            manifest = json.loads(json.dumps(manifest).replace('2026-10-16', '2026-10-17'))
            (folder / 'deployment.json').write_text(json.dumps(manifest))
            shutil.copytree(folder / 'editions/2026-10-16', folder / 'editions/2026-10-17')
            (folder / 'rss.xml').write_text((folder / 'rss.xml').read_text().replace('2026-10-16', '2026-10-17'))
            (folder / 'sitemap.xml').write_text((folder / 'sitemap.xml').read_text().replace('2026-10-16', '2026-10-17'))
        before = mapping_file.read_bytes()
        path = self.live / 'editions/2026-10-17/read/index.html'
        complete = path.read_text()
        path.write_text('<main>truncated new day</main>')
        self.assertNotEqual(self.verify().returncode, 0)
        self.assertEqual(mapping_file.read_bytes(), before)
        path.write_text(complete)
        self.assertEqual(self.verify().returncode, 0)
        self.assertEqual(set(json.loads(mapping_file.read_text())['redirects']), {'/digests/x-ai-2026-10-16', '/digests/x-ai-2026-10-17'})

    def test_stale_home_fails_even_when_dated_pages_and_manifest_match(self):
        (self.live / 'index.html').write_text('<main>Stale home</main>')
        self.assertNotEqual(self.verify().returncode, 0)
        self.assertFalse((self.home / 'state/verified-redirects.json').exists())

    def test_missing_discovery_route_fails_release(self):
        (self.live / 'search/index.html').unlink()
        self.assertNotEqual(self.verify().returncode, 0)
        self.assertFalse((self.home / 'state/verified-redirects.json').exists())

    def test_descendant_home_can_show_a_newer_day_while_accepting_an_older_edition(self):
        import hashlib
        relative = 'digests/x-ai-2026-10-16.md'
        request = {'date': '2026-10-16', 'expected_head': self.old, 'files': {relative: {'staged': str(self.home / 'accepted.md'), 'before_sha256': None, 'staged_sha256': 'a' * 64}}}
        request_file = self.home / 'accepted.json'
        request_file.write_text(json.dumps(request))
        key = hashlib.sha256(json.dumps(request, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        receipt_file = self.home / 'state/receipts' / (key + '.json')
        receipt_file.parent.mkdir(parents=True)
        receipt_file.write_text(json.dumps({'phase': 'readerpending', 'commit': self.old, 'files': {relative: 'a' * 64}}))
        accepted = json.loads((self.artifact / 'deployment.json').read_text())
        accepted['sourceRevision'] = self.old
        (self.artifact / 'deployment.json').write_text(json.dumps(accepted))
        live = json.loads((self.live / 'deployment.json').read_text())
        latest = dict(live['editions'][0], date='2026-10-17', path='/editions/2026-10-17/', readPath='/editions/2026-10-17/read/', stories=[])
        live['editions'].append(latest)
        (self.live / 'deployment.json').write_text(json.dumps(live))
        latest_front = self.live / 'editions/2026-10-17/index.html'
        latest_front.parent.mkdir(parents=True)
        latest_front.write_text('<main>The actual newer October 17 edition</main>')
        (self.live / 'index.html').write_bytes(latest_front.read_bytes())
        result = self.cli('verify', '--artifact', str(self.artifact), '--origin', self.origin, '--request', str(request_file))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(receipt_file.read_text())['phase'], 'readerverified')
        (self.live / 'index.html').write_bytes((self.artifact / 'index.html').read_bytes())
        self.assertNotEqual(self.cli('verify', '--artifact', str(self.artifact), '--origin', self.origin, '--request', str(request_file)).returncode, 0)

if __name__ == '__main__':
    unittest.main()
