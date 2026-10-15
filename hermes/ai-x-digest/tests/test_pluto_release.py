"""Pluto releases keep credentials private and only accept verified readers."""
from contextlib import redirect_stderr, redirect_stdout
import fcntl
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
from unittest.mock import patch

import test_daily_release as fixtures
import test_release_contract as contracts

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / 'scripts/release-daily-from-pluto.py'


class PlutoReleaseTest(unittest.TestCase):
    git = fixtures.ReleaseTest.git
    pending_request = contracts.ReleaseContractTest.pending_request

    def setUp(self):
        contracts.ReleaseContractTest.setUp(self)
        self.home = self.home.resolve()
        self.repo = self.repo.resolve()
        sys.path.insert(0, str(ROOT / 'scripts'))
        self.addCleanup(sys.path.remove, str(ROOT / 'scripts'))
        spec = importlib.util.spec_from_file_location('pluto_release', SCRIPT)
        self.command = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.command)
        self.assertEqual(self.command.ORIGIN, 'https://daily.nishantkhurana.me')
        self.credentials = self.home / 'cloudflare.json'
        self.token = 'private-fixture-token'
        self.credentials.write_text(json.dumps({'account_id': '1688bfec49a43a217df10ed33b86e300', 'api_token': self.token}))
        self.credentials.chmod(0o600)
        self.state = self.home / 'state'
        self.cached = self.state / 'artifacts' / self.new
        self.cached.parent.mkdir(parents=True)
        shutil.copytree(self.artifact, self.cached)
        self.request_file, self.receipt = self.pending_request()
        self.events = []
        self.deployed = False
        self.deploy_error = None
        self.no_deployment = False
        self.no_deployment_after_deploy = False
        release = self.command.release
        original_run = release.run
        original_fetch = release.fetch

        def locked():
            with (self.state / 'host.lock').open('a') as lock:
                with self.assertRaises(BlockingIOError):
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)

        def deployments():
            locked()
            self.events.append('deployment lookup')
            self.assertEqual(os.environ['CLOUDFLARE_API_TOKEN'], self.token)
            self.assertEqual(os.environ['CLOUDFLARE_ACCOUNT_ID'], '1688bfec49a43a217df10ed33b86e300')
            if self.no_deployment or self.deployed and self.no_deployment_after_deploy:
                raise ValueError('Cloudflare has no deployment; explicit bootstrap is required')
            return [{'created_on': '2026-10-15T00:00:00Z', 'versions': [{'version_id': 'actual-version' if self.deployed else 'previous-version', 'percentage': 100}]}]

        def run(args, cwd=None):
            if list(args[-2:]) == ['npm', 'ci']:
                Path(cwd).mkdir(parents=True, exist_ok=True)
                return ''
            if 'deploy' not in args:
                return original_run(args, cwd)
            locked()
            self.events.append('deploy')
            app = Path(args[5]).parents[3]
            self.assertIn(self.state, app.parents)
            self.assertNotEqual(app, self.repo / 'apps/daily')
            self.assertEqual(self.git('-C', str(app.parents[1]), 'rev-parse', 'HEAD'), self.new)
            self.assertEqual([str(arg) for arg in args], [str(self.command.MISE), 'exec', 'node@22.23.3', '--', 'node', str(app / 'node_modules/wrangler/bin/wrangler.js'), 'deploy', '--config', str(app / 'wrangler.jsonc'), '--assets', str(self.cached)])
            self.assertEqual(Path(cwd), self.repo)
            self.assertEqual(os.environ['CLOUDFLARE_API_TOKEN'], self.token)
            if self.deploy_error:
                raise RuntimeError(self.deploy_error)
            self.deployed = True
            return 'Wrangler output must stay private ' + self.token

        def fetch(origin, route):
            locked()
            self.assertEqual(origin, self.command.ORIGIN)
            self.events.append(route)
            return original_fetch(self.origin, route)

        self.environment = patch.dict(os.environ, self.env)
        self.environment.start()
        self.addCleanup(self.environment.stop)
        for target, replacement in (('cloudflare_deployments', deployments), ('run', run), ('fetch', fetch)):
            mocked = patch.object(release, target, replacement)
            mocked.start()
            self.addCleanup(mocked.stop)

    def cli(self, *extra, request=True, credentials=True):
        out, error = io.StringIO(), io.StringIO()
        arguments = ['--commit', self.new]
        if credentials:
            arguments.extend(['--credentials', str(self.credentials)])
        if request:
            arguments.extend(['--request', str(self.request_file)])
        before = {name: os.environ.get(name) for name in ('CLOUDFLARE_API_TOKEN', 'CLOUDFLARE_ACCOUNT_ID')}
        with redirect_stdout(out), redirect_stderr(error):
            try:
                self.command.main([*arguments, *extra])
                code = 0
            except SystemExit as failure:
                code = failure.code
        self.assertEqual({name: os.environ.get(name) for name in before}, before)
        self.assertNotIn(self.token, out.getvalue() + error.getvalue())
        return code, out.getvalue(), error.getvalue()

    def previous_verified(self):
        previous = {'sourceRevision': self.old, 'version': 'prior-version'}
        for name, value in (('verified-redirects.json', {'redirects': {'/older': {'destination': '/older/'}}}), ('reader-release.json', previous)):
            (self.state / name).write_text(json.dumps(value))
        return {name: (self.state / name).read_bytes() for name in ('verified-redirects.json', 'reader-release.json')}

    def assert_preserved(self, previous):
        for name, value in previous.items():
            self.assertEqual((self.state / name).read_bytes(), value)
        self.assertEqual(json.loads(self.receipt.read_text())['phase'], 'readerpending')
        self.assertTrue((self.cached / 'index.html').is_file())
        self.assertTrue((self.state / 'reader-failure.json').is_file())

    def test_release_uses_cached_artifact_and_actual_version_without_completing_delivery(self):
        code, output, error = self.cli()
        self.assertEqual(code, 0, error)
        result = json.loads(output)
        self.assertEqual(result['version'], 'actual-version')
        self.assertEqual(result['sourceRevision'], self.new)
        self.assertEqual(result['origin'], 'https://daily.nishantkhurana.me')
        self.assertEqual(self.events[0], 'deployment lookup')
        deployed = self.events.index('deploy')
        self.assertEqual(self.events[deployed + 1], 'deployment lookup')
        self.assertIn('/rss.xml', self.events[deployed + 2:])
        receipt = json.loads(self.receipt.read_text())
        self.assertEqual(receipt['phase'], 'readerverified')
        self.assertNotIn('delivery_reference', receipt)
        self.assertEqual(json.loads((self.state / 'reader-release.json').read_text())['version'], 'actual-version')
        self.assertEqual(set(json.loads((self.state / 'verified-redirects.json').read_text())['redirects']), {'/digests/x-ai-2026-10-16'})

    def test_default_private_credentials_and_no_request_verify_without_touching_receipt(self):
        default = self.home / '.config/pawhouse-daily/cloudflare.json'
        default.parent.mkdir(parents=True)
        self.credentials.rename(default)
        receipt = self.receipt.read_bytes()
        with patch.dict(os.environ, HOME=str(self.home)):
            code, output, error = self.cli(request=False, credentials=False)
        self.assertEqual(code, 0, error)
        self.assertEqual(json.loads(output)['version'], 'actual-version')
        self.assertEqual(self.receipt.read_bytes(), receipt)

    def test_deployment_version_lookup_failure_preserves_previous_verified_state(self):
        previous = self.previous_verified()
        self.no_deployment_after_deploy = True
        code, _, _ = self.cli()
        self.assertNotEqual(code, 0)
        self.assertTrue(self.deployed)
        self.assert_preserved(previous)
        self.assertEqual(json.loads((self.state / 'reader-failure.json').read_text())['phase'], 'version')

    def test_deployment_failure_preserves_previous_verified_state_and_redacts_token(self):
        previous = self.previous_verified()
        self.deploy_error = 'fixture deployment failed with ' + self.token
        code, _, error = self.cli()
        self.assertNotEqual(code, 0)
        self.assertIn('fixture deployment failed', error)
        self.assert_preserved(previous)
        self.assertEqual(self.events.count('deployment lookup'), 1)
        self.assertNotIn(self.token, (self.state / 'reader-failure.json').read_text())

    def test_live_verification_failure_preserves_previous_state_and_pending_delivery(self):
        previous = self.previous_verified()
        (self.live / 'editions/2026-10-16/read/index.html').write_text('<main>Truncated</main>')
        code, _, _ = self.cli()
        self.assertNotEqual(code, 0)
        self.assertTrue(self.deployed)
        self.assert_preserved(previous)

    def test_missing_live_cloudflare_deployment_fails_before_deploy(self):
        previous = self.previous_verified()
        self.no_deployment = True
        code, _, _ = self.cli()
        self.assertNotEqual(code, 0)
        self.assertFalse(self.deployed)
        self.assert_preserved(previous)

    def test_missing_live_reader_manifest_fails_before_deploy(self):
        previous = self.previous_verified()
        (self.live / 'deployment.json').unlink()
        code, _, _ = self.cli()
        self.assertNotEqual(code, 0)
        self.assertFalse(self.deployed)
        self.assert_preserved(previous)

    def test_uncached_release_uses_pinned_private_tools_without_canonical_dependencies(self):
        from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
        import functools
        import threading
        import urllib.request
        from publication import run as real_run

        repo = self.home / 'clean-checkout'
        real_run(['git', 'clone', '--shared', '--no-checkout', ROOT, repo])
        commit = real_run(['git', '-C', ROOT, 'rev-parse', 'HEAD'])
        real_run(['git', '-C', repo, 'checkout', '--detach', commit])
        state = self.home / 'clean-state'
        deployed = {}
        release = self.command.release

        def deployments():
            return [{'created_on': '2026-10-15T00:00:00Z', 'versions': [{
                'version_id': 'dry-run-version' if deployed else 'previous-version', 'percentage': 100}]}]

        def run(args, cwd=None):
            if 'deploy' not in args:
                return real_run(args, cwd)
            app = Path(args[5]).parents[3]
            self.assertIn(state, app.parents)
            self.assertEqual(real_run(['git', '-C', app, 'rev-parse', 'HEAD']), commit)
            self.assertTrue(Path(args[5]).is_file())
            self.assertEqual((app / 'wrangler.jsonc').read_bytes(),
                             subprocess.check_output(['git', '-C', str(repo), 'show', commit + ':apps/daily/wrangler.jsonc']))
            output = real_run([*args, '--dry-run', '--outdir', self.home / 'wrangler-dry-run'], cwd)
            self.assertIn('--dry-run: exiting now.', output)
            deployed['artifact'] = Path(args[-1])
            class Handler(SimpleHTTPRequestHandler):
                extensions_map = {**SimpleHTTPRequestHandler.extensions_map, '.xml': 'application/rss+xml; charset=utf-8'}
                def log_message(self, *args):
                    pass
            server = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Handler, directory=str(deployed['artifact'])))
            threading.Thread(target=server.serve_forever, daemon=True).start()
            self.addCleanup(server.server_close)
            self.addCleanup(server.shutdown)
            deployed['origin'] = 'http://127.0.0.1:' + str(server.server_port)
            return output

        def fetch(origin, route):
            self.assertEqual(origin, self.command.ORIGIN)
            if not deployed:
                self.assertEqual(route, '/deployment.json')
                return json.dumps({'sourceRevision': commit, 'editions': []}), {}
            with urllib.request.urlopen(deployed['origin'] + route, timeout=30) as response:
                return response.read().decode(), response.headers

        self.assertFalse((repo / 'apps/daily/node_modules').exists())
        out, error = io.StringIO(), io.StringIO()
        with patch.dict(os.environ, PUBLISH_REPO=str(repo), PUBLISH_STATE_DIR=str(state)), \
             patch.object(release, 'run', run), patch.object(release, 'fetch', fetch), \
             patch.object(release, 'cloudflare_deployments', deployments), \
             redirect_stdout(out), redirect_stderr(error):
            self.command.main(['--commit', commit, '--credentials', str(self.credentials)])
        result = json.loads(out.getvalue())
        self.assertEqual(result['sourceRevision'], commit)
        self.assertEqual(result['version'], 'dry-run-version')
        self.assertIn('/rss.xml', result['tested_routes'])
        self.assertTrue((state / 'reader-release.json').is_file())
        self.assertFalse((repo / 'apps/daily/node_modules').exists())
        self.assertEqual(list(state.glob('reader-deploy-*')), [])
        self.assertEqual(list(state.glob('reader-build-*')), [])

    def test_missing_request_fails_before_deployment(self):
        self.request_file.unlink()
        code, _, _ = self.cli()
        self.assertNotEqual(code, 0)
        self.assertFalse(self.deployed)

    def test_ineligible_receipt_fails_before_deployment(self):
        receipt = json.loads(self.receipt.read_text())
        receipt['phase'] = 'complete'
        self.receipt.write_text(json.dumps(receipt))
        code, _, _ = self.cli()
        self.assertNotEqual(code, 0)
        self.assertFalse(self.deployed)
        self.assertEqual(json.loads(self.receipt.read_text())['phase'], 'complete')

    def test_mismatched_accepted_artifact_fails_before_deployment(self):
        manifest = json.loads((self.cached / 'deployment.json').read_text())
        manifest['editions'][0]['sourceSha256'] = 'b' * 64
        (self.cached / 'deployment.json').write_text(json.dumps(manifest))
        code, _, _ = self.cli()
        self.assertNotEqual(code, 0)
        self.assertFalse(self.deployed)
        self.assertEqual(json.loads(self.receipt.read_text())['phase'], 'readerpending')

    def test_failed_verified_retry_blocks_delivery_and_keeps_previous_proof(self):
        receipt = json.loads(self.receipt.read_text())
        receipt.update(phase='readerverified', reader={'version': 'prior-version'})
        self.receipt.write_text(json.dumps(receipt))
        (self.live / 'editions/2026-10-16/read/index.html').write_text('<main>Truncated retry</main>')
        code, _, _ = self.cli()
        self.assertNotEqual(code, 0)
        self.assertTrue(self.deployed)
        receipt = json.loads(self.receipt.read_text())
        self.assertEqual(receipt['phase'], 'readerpending')
        self.assertEqual(receipt['reader'], {'version': 'prior-version'})
        delivery = subprocess.run([sys.executable, str(ROOT / 'scripts/publication.py'), 'delivery-begin',
                                   '--request', str(self.request_file)], env=self.env, capture_output=True, text=True)
        self.assertNotEqual(delivery.returncode, 0)
        self.assertIn('dated delivery requires readerverified', delivery.stderr)

    def test_credentials_must_be_private_outside_public_trees_and_use_personal_account(self):
        for path in (self.repo / 'credentials.json', self.home / 'vault/credentials.json'):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(self.credentials.read_bytes())
            path.chmod(0o600)
            self.assertNotEqual(self.cli('--credentials', str(path))[0], 0)
        self.credentials.chmod(0o644)
        self.assertNotEqual(self.cli()[0], 0)
        self.credentials.chmod(0o600)
        self.credentials.write_text(json.dumps({'account_id': '0' * 32, 'api_token': self.token}))
        self.assertNotEqual(self.cli()[0], 0)
        self.assertFalse(self.deployed)
        self.assertEqual(self.events, [])


if __name__ == '__main__':
    unittest.main()
