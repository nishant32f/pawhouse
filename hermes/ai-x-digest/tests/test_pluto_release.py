"""Private credentials, pinned SSR builds, actual deployment versions and no delivery completion."""
from contextlib import redirect_stderr, redirect_stdout
import fcntl
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import unittest
from unittest.mock import patch
import daily_release_fixtures as fixtures

ROOT = fixtures.ROOT


class PlutoReleaseTest(fixtures.Fixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        spec = importlib.util.spec_from_file_location('pluto_release', ROOT / 'scripts/release-daily-from-pluto.py')
        self.command = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.command)
        self.credentials = self.home / 'cloudflare.json'
        self.token = 'private-fixture-token'
        self.credentials.write_text(json.dumps({'account_id': self.command.ACCOUNT, 'api_token': self.token}))
        self.credentials.chmod(0o600)
        self.cached = self.state / 'artifacts' / self.new
        shutil.copytree(self.artifact, self.cached)
        self.request_file, self.receipt = self.pending_request()
        self.events = []
        self.deployed = False
        self.deploy_error = None
        self.no_deployment = False
        self.no_deployment_after_deploy = False
        release = self.command.release
        original_run, original_fetch = release.run, release.fetch

        def locked():
            with (self.state / 'host.lock').open('a') as lock:
                with self.assertRaises(BlockingIOError):
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)

        def deployments(bootstrap=False):
            locked()
            self.events.append('deployment lookup')
            self.assertEqual(os.environ['CLOUDFLARE_API_TOKEN'], self.token)
            self.assertEqual(os.environ['CLOUDFLARE_ACCOUNT_ID'], self.command.ACCOUNT)
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
            self.assertEqual([str(arg) for arg in args], [str(self.command.MISE), 'exec', 'node@22.23.3', '--', 'node', str(app / 'node_modules/wrangler/bin/wrangler.js'), 'deploy', '--config', str(self.cached / 'server/wrangler.json')])
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

    def invoke(self, *extra, request=True, credentials=True, bundle=False):
        out, error = io.StringIO(), io.StringIO()
        arguments = ['--commit', self.new]
        if credentials:
            arguments.extend(['--credentials', str(self.credentials)])
        if request:
            arguments.extend(['--request', str(self.request_file)])
        if bundle:
            arguments.extend(['--bundle', str(self.bundle)])
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
        previous = {'codeRevision': self.old, 'version': 'prior-version'}
        for name, value in (('verified-redirects.json', {'redirects': {'/older': {'destination': '/older/'}}}), ('reader-release.json', previous)):
            (self.state / name).write_text(json.dumps(value))
        return {name: (self.state / name).read_bytes() for name in ('verified-redirects.json', 'reader-release.json')}

    def assert_preserved(self, previous):
        for name, value in previous.items():
            self.assertEqual((self.state / name).read_bytes(), value)
        self.assertEqual(json.loads(self.receipt.read_text())['phase'], 'published')
        self.assertTrue((self.cached / 'server/entry.mjs').is_file())
        self.assertTrue((self.state / 'reader-failure.json').is_file())

    def test_release_uses_cached_ssr_artifact_and_actual_version_without_completing_delivery(self):
        code, output, error = self.invoke()
        self.assertEqual(code, 0, error)
        result = json.loads(output)
        self.assertEqual(result['version'], 'actual-version')
        self.assertEqual(result['codeRevision'], self.new)
        self.assertEqual(result['origin'], self.command.ORIGIN)
        self.assertEqual(self.events[0], 'deployment lookup')
        deployed = self.events.index('deploy')
        self.assertEqual(self.events[deployed + 1], 'deployment lookup')
        self.assertIn('/rss.xml', self.events[deployed + 2:])
        receipt = json.loads(self.receipt.read_text())
        self.assertEqual(receipt['phase'], 'readerverified')
        self.assertNotIn('delivery_reference', receipt)
        self.assertNotIn('verificationError', receipt)
        self.assertEqual(json.loads((self.state / 'reader-release.json').read_text())['version'], 'actual-version')

    def test_default_private_credentials_and_code_only_release_keep_receipt_unchanged(self):
        default = self.home / '.config/pawhouse-daily/cloudflare.json'
        default.parent.mkdir(parents=True)
        self.credentials.rename(default)
        receipt = self.receipt.read_bytes()
        with patch.dict(os.environ, HOME=str(self.home)):
            code, output, error = self.invoke(request=False, credentials=False, bundle=True)
        self.assertEqual(code, 0, error)
        self.assertEqual(json.loads(output)['version'], 'actual-version')
        self.assertEqual(self.receipt.read_bytes(), receipt)

    def test_explicit_bundle_works_before_production_backend_activation(self):
        (self.state / 'backend.json').unlink()
        code, output, error = self.invoke(request=False, bundle=True)
        self.assertEqual(code, 0, error)
        self.assertEqual(json.loads(output)['version'], 'actual-version')
        self.assertFalse((self.state / 'backend.json').exists())

    def test_deployment_version_lookup_failure_preserves_previous_verified_state(self):
        previous = self.previous_verified()
        self.no_deployment_after_deploy = True
        code, _, _ = self.invoke()
        self.assertNotEqual(code, 0)
        self.assertTrue(self.deployed)
        self.assert_preserved(previous)
        self.assertEqual(json.loads((self.state / 'reader-failure.json').read_text())['phase'], 'version')

    def test_deployment_failure_preserves_previous_verified_state_and_redacts_token(self):
        previous = self.previous_verified()
        self.deploy_error = 'fixture deployment failed with ' + self.token
        code, _, error = self.invoke()
        self.assertNotEqual(code, 0)
        self.assertIn('fixture deployment failed', error)
        self.assert_preserved(previous)
        self.assertEqual(self.events.count('deployment lookup'), 1)
        self.assertNotIn(self.token, (self.state / 'reader-failure.json').read_text())

    def test_live_verification_failure_preserves_previous_state_and_blocks_delivery(self):
        previous = self.previous_verified()
        (self.live / 'editions/2026-10-16/read/index.html').write_text('<main>Truncated</main>')
        code, _, _ = self.invoke()
        self.assertNotEqual(code, 0)
        self.assertTrue(self.deployed)
        self.assert_preserved(previous)
        self.assertIn('verificationError', json.loads(self.receipt.read_text()))

    def test_missing_live_cloudflare_deployment_fails_before_deploy(self):
        previous = self.previous_verified()
        self.no_deployment = True
        code, _, _ = self.invoke()
        self.assertNotEqual(code, 0)
        self.assertFalse(self.deployed)
        self.assert_preserved(previous)

    def test_missing_live_reader_manifest_fails_before_deploy(self):
        previous = self.previous_verified()
        (self.live / 'deployment.json').unlink()
        code, _, _ = self.invoke()
        self.assertNotEqual(code, 0)
        self.assertFalse(self.deployed)
        self.assert_preserved(previous)

    def test_uncached_pinned_build_and_generated_ssr_config_pass_real_wrangler_dry_run(self):
        # This proves a pinned code build and local packaging. It makes no Cloudflare or live-proof claim.
        from publication import Publisher, run as real_run
        repo = self.home / 'clean-checkout'
        real_run(['git', 'clone', '--shared', '--no-checkout', ROOT, repo])
        commit = real_run(['git', '-C', ROOT, 'rev-parse', 'HEAD'])
        real_run(['git', '-C', repo, 'checkout', '--detach', commit])
        state = self.home / 'clean-state'
        with patch.dict(os.environ, PUBLISH_REPO=str(repo), PUBLISH_STATE_DIR=str(state)):
            publisher = Publisher()
            built = fixtures.release.build(publisher, commit)
        artifact = Path(built['artifact'])
        self.assertEqual(built['codeRevision'], commit)
        self.assertTrue((artifact / 'server/entry.mjs').is_file())
        self.assertTrue((artifact / 'client').is_dir())
        self.assertFalse((artifact / 'deployment.json').exists())
        tools = self.home / 'tools'
        real_run(['git', 'clone', '--shared', '--no-checkout', repo, tools])
        real_run(['git', '-C', tools, 'checkout', '--detach', commit])
        app = tools / 'apps/daily'
        real_run([fixtures.MISE, 'exec', 'node@22.23.3', '--', 'npm', 'ci'], app)
        # No real token reaches the dry-run and no real Cloudflare API is called.
        with patch.dict(os.environ, CLOUDFLARE_API_TOKEN='', CLOUDFLARE_ACCOUNT_ID=self.command.ACCOUNT):
            output = real_run([fixtures.MISE, 'exec', 'node@22.23.3', '--', 'node', app / 'node_modules/wrangler/bin/wrangler.js',
                               'deploy', '--config', artifact / 'server/wrangler.json', '--dry-run', '--outdir', self.home / 'wrangler-dry-run'], repo)
        self.assertIn('--dry-run: exiting now.', output)
        self.assertFalse((repo / 'apps/daily/node_modules').exists())
        self.assertFalse((repo / 'hermes/ai-x-digest/content/node_modules').exists())
        self.assertEqual(list(state.glob('reader-build-*')), [])
        self.assertFalse((state / 'reader-release.json').exists())
        self.assertEqual(fixtures.release.code_artifact(artifact)['codeRevision'], commit)

    def test_missing_request_fails_before_deployment(self):
        self.request_file.unlink()
        self.assertNotEqual(self.invoke()[0], 0)
        self.assertFalse(self.deployed)

    def test_ineligible_receipt_fails_before_deployment(self):
        for phase in ('complete', 'deliverypending', 'objects-verified'):
            receipt = json.loads(self.receipt.read_text())
            receipt['phase'] = phase
            self.receipt.write_text(json.dumps(receipt))
            before = self.receipt.read_bytes()
            self.assertNotEqual(self.invoke()[0], 0)
            self.assertFalse(self.deployed)
            self.assertEqual(self.receipt.read_bytes(), before)

    def test_mismatched_accepted_bundle_fails_before_deployment(self):
        metadata = json.loads((self.bundle / 'bundle.json').read_text())
        (self.bundle / metadata['manifest']['editions'][0]['object']['key']).write_text('tampered')
        self.assertNotEqual(self.invoke()[0], 0)
        self.assertFalse(self.deployed)
        self.assertEqual(json.loads(self.receipt.read_text())['phase'], 'published')

    def test_failed_verified_retry_blocks_delivery_and_keeps_previous_proof(self):
        receipt = json.loads(self.receipt.read_text())
        receipt.update(phase='readerverified', reader={'version': 'prior-version'})
        self.receipt.write_text(json.dumps(receipt))
        (self.live / 'editions/2026-10-16/read/index.html').write_text('<main>Truncated retry</main>')
        code, _, _ = self.invoke()
        self.assertNotEqual(code, 0)
        self.assertTrue(self.deployed)
        receipt = json.loads(self.receipt.read_text())
        self.assertEqual(receipt['phase'], 'published')
        self.assertEqual(receipt['reader'], {'version': 'prior-version'})
        delivery = subprocess.run(['python3', str(ROOT / 'scripts/publication.py'), 'delivery-begin', '--request', str(self.request_file)], env=self.env, capture_output=True, text=True)
        self.assertNotEqual(delivery.returncode, 0)
        self.assertIn('readerverified', delivery.stderr)

    def test_credentials_must_be_private_outside_public_trees_and_use_personal_account(self):
        for path in (self.repo / 'credentials.json', self.home / 'vault/credentials.json'):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(self.credentials.read_bytes())
            path.chmod(0o600)
            self.assertNotEqual(self.invoke('--credentials', str(path))[0], 0)
        self.credentials.chmod(0o644)
        self.assertNotEqual(self.invoke()[0], 0)
        self.credentials.chmod(0o600)
        self.credentials.write_text(json.dumps({'account_id': '0' * 32, 'api_token': self.token}))
        self.assertNotEqual(self.invoke()[0], 0)
        self.assertFalse(self.deployed)
        self.assertEqual(self.events, [])


if __name__ == '__main__':
    unittest.main()
