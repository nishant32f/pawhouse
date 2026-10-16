"""Code releases and accepted content have independent identities and failure gates."""
import json
from pathlib import Path
import shutil
import sys
import unittest
from unittest.mock import patch
import daily_release_fixtures as fixtures


class ReleaseTest(fixtures.Fixture, unittest.TestCase):
    def test_real_ssr_local_r2_verifies_all_history_without_build_or_git_content(self):
        from publication import Publisher
        with patch.dict('os.environ', self.env):
            publisher = Publisher()
            publisher.git = lambda *args: self.fail('content verification must not use Git')
            result = fixtures.release.verify_publication(publisher, self.bundle, self.runtime_origin, self.actual_code)
        self.assertEqual(len(result['dates']), 3)
        self.assertIn('/editions/2026-10-16/stories/vendor-benchmark/', result['tested_routes'])
        self.assertIsNone(result['version'])

    def test_verified_day_extends_exact_redirects_and_failed_new_day_adds_none(self):
        result = self.verify()
        self.assertEqual(result.returncode, 0, result.stderr)
        mapping = self.state / 'verified-redirects.json'
        self.assertEqual(len(json.loads(mapping.read_text())['redirects']), 3)
        before = mapping.read_bytes()
        (self.live / 'editions/2026-10-16/read/index.html').write_text('<main><p>Truncated</p></main>')
        self.assertNotEqual(self.verify().returncode, 0)
        self.assertEqual(mapping.read_bytes(), before)

    def test_manifest_and_http200_cannot_cover_truncated_body(self):
        (self.live / 'editions/2026-10-16/stories/reproducible-test/index.html').write_text('<main>A full story</main>')
        self.assertNotEqual(self.verify().returncode, 0)
        self.assertFalse((self.state / 'verified-redirects.json').exists())

    def test_reverse_finish_blocks_older_build(self):
        result, marker = self.deploy(self.old)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(marker.exists())
        result, marker = self.deploy(self.new)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(marker.exists())

    def test_bootstrap_does_not_treat_http_failure_as_absent_deployment(self):
        (self.live / 'deployment.json').unlink()
        self.assertNotEqual(self.cli('guard', '--candidate', self.new, '--origin', self.origin).returncode, 0)
        self.assertEqual(self.cli('guard', '--candidate', self.new, '--origin', self.origin, '--bootstrap').returncode, 0)
        (self.live / 'deployment.json').write_text('invalid JSON')
        self.assertNotEqual(self.cli('guard', '--candidate', self.new, '--origin', self.origin, '--bootstrap').returncode, 0)

    def test_legacy_code_identity_allows_initial_upgrade_but_not_content_proof(self):
        path = self.live / 'deployment.json'
        manifest = json.loads(path.read_text())
        manifest['sourceRevision'] = manifest.pop('codeRevision')
        manifest.pop('publicationRevision')
        path.write_text(json.dumps(manifest))
        self.assertEqual(self.cli('guard', '--candidate', self.new, '--origin', self.origin).returncode, 0)
        self.assertNotEqual(self.verify().returncode, 0)

    def test_failed_verification_preserves_last_verified_release(self):
        self.assertEqual(self.verify().returncode, 0)
        prior = (self.state / 'reader-release.json').read_bytes()
        (self.live / 'rss.xml').write_text('<rss><channel/></rss>')
        self.assertNotEqual(self.verify().returncode, 0)
        self.assertEqual((self.state / 'reader-release.json').read_bytes(), prior)

    def test_failed_deployment_preserves_previous_artifact_mapping_and_pending_delivery(self):
        self.assertEqual(self.verify().returncode, 0)
        before = {name: (self.state / name).read_bytes() for name in ('reader-release.json', 'verified-redirects.json')}
        result = self.cli('deploy', '--artifact', self.artifact, '--bundle', self.bundle, '--origin', self.origin, '--',
                          sys.executable, '-c', 'raise SystemExit(7)', '--config', self.artifact / 'server/wrangler.json')
        self.assertNotEqual(result.returncode, 0)
        for name, value in before.items():
            self.assertEqual((self.state / name).read_bytes(), value)
        self.assertTrue((self.state / 'reader-failure.json').exists())

    def test_correct_code_with_stale_content_is_rejected(self):
        request, receipt = self.pending_request()
        manifest = json.loads((self.live / 'deployment.json').read_text())
        accepted_manifest = dict(manifest)
        publication = json.loads(receipt.read_text())['publicationId']
        manifest['publicationRevision'] = '0' * 64
        (self.live / 'deployment.json').write_text(json.dumps(manifest))
        result = self.verify('--request', request, '--code-revision', self.new)
        self.assertNotEqual(result.returncode, 0)
        actual = json.loads(receipt.read_text())
        self.assertEqual(actual['phase'], 'published')
        self.assertIn('verificationError', actual)
        (self.live / 'deployment.json').write_text(json.dumps(accepted_manifest))
        resumed = self.verify('--request', request)
        self.assertEqual(resumed.returncode, 0, resumed.stderr)
        restored = json.loads(receipt.read_text())
        self.assertEqual(restored['publicationId'], publication)
        self.assertEqual(restored['phase'], 'readerverified')
        self.assertNotIn('verificationError', restored)

    def test_failed_new_build_preserves_prior_complete_artifact(self):
        prior = self.state / 'artifacts' / self.old
        prior.mkdir(parents=True)
        (prior / 'prior').write_text('previous complete artifact')
        result = self.cli('build', '--commit', self.new)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((prior / 'prior').read_text(), 'previous complete artifact')
        self.assertFalse((self.state / 'artifacts' / self.new).exists())

    def test_cloudflare_version_is_recorded_separately_and_split_traffic_rejected(self):
        deployments = self.home / 'deployments.json'
        deployments.write_text(json.dumps([{'created_on': '2026-10-15T00:00:00Z', 'versions': [{'version_id': 'first-real-version', 'percentage': 100}]}, {'created_on': '2026-10-16T00:00:00Z', 'versions': [{'version_id': 'second-real-version', 'percentage': 100}]}]))
        result = self.cli('version', '--deployments', deployments)
        self.assertEqual(result.stdout.strip(), 'second-real-version')
        deployments.write_text(json.dumps([{'created_on': '2026-10-16T00:00:00Z', 'versions': [{'version_id': 'split', 'percentage': 50}]}]))
        self.assertNotEqual(self.cli('version', '--deployments', deployments).returncode, 0)

    def test_historical_route_deletion_is_rejected_before_deploy(self):
        path = self.live / 'deployment.json'
        manifest = json.loads(path.read_text())
        manifest['routes'].append('/editions/2026-01-01/')
        path.write_text(json.dumps(manifest))
        result, marker = self.deploy()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(marker.exists())

    def test_code_rollback_cannot_remove_ssr_handler_or_assets(self):
        for relative in ('server/entry.mjs', 'client'):
            path = self.artifact / relative
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            result, marker = self.deploy()
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(marker.exists())
            if relative == 'server/entry.mjs':
                path.write_text('export default {}')

    def test_cloudflare_bootstrap_distinguishes_missing_deployment_from_bad_response(self):
        release = fixtures.release
        import os
        with patch.dict(os.environ, CLOUDFLARE_ACCOUNT_ID=release.ACCOUNT, CLOUDFLARE_API_TOKEN='fixture-token'), patch.object(release, 'CLOUDFLARE_API', self.origin):
            with self.assertRaises(Exception):
                release.cloudflare_deployments()
            self.assertEqual(release.cloudflare_deployments(True), [])
            metadata = self.live / ('accounts/' + release.ACCOUNT + '/workers/scripts/pawhouse-daily/deployments')
            metadata.parent.mkdir(parents=True)
            for value in ('not JSON', json.dumps({'success': False})):
                metadata.write_text(value)
                with self.assertRaises((ValueError, KeyError)):
                    release.cloudflare_deployments(True)
            metadata.write_text(json.dumps({'success': True, 'result': {'deployments': [{'versions': [{'version_id': 'actual'}]}]}}))
            self.assertEqual(release.cloudflare_deployments()[0]['versions'][0]['version_id'], 'actual')

    def test_selected_publication_must_stay_current_for_code_only_release(self):
        manifest = json.loads((self.live / 'deployment.json').read_text())
        manifest['publicationRevision'] = 'a' * 64
        (self.live / 'deployment.json').write_text(json.dumps(manifest))
        result, marker = self.deploy()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(marker.exists())

    def test_content_only_request_needs_no_git_ancestry_and_resume_reuses_publication(self):
        request, receipt = self.pending_request()
        before = json.loads(receipt.read_text())['publicationId']
        result = self.cli('verify', '--request', request, '--origin', self.origin, '--code-revision', self.new)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(receipt.read_text())['phase'], 'readerverified')
        self.assertEqual(json.loads(receipt.read_text())['publicationId'], before)
        self.assertFalse((self.state / 'artifacts').exists())
        self.assertEqual(self.git('rev-parse', 'HEAD'), self.new)

    def test_complete_and_deliverypending_receipts_are_inert(self):
        for phase in ('accepted', 'objects-verified', 'complete', 'deliverypending'):
            request, receipt = self.pending_request(phase)
            before = receipt.read_bytes()
            result = self.verify('--request', request)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(receipt.read_bytes(), before)

    def test_frozen_object_tampering_is_rejected(self):
        metadata = json.loads((self.bundle / 'bundle.json').read_text())
        (self.bundle / metadata['manifest']['rss']['key']).write_text('tampered')
        self.assertNotEqual(self.verify().returncode, 0)
        self.assertFalse((self.state / 'reader-release.json').exists())

    def test_assets_only_command_is_rejected(self):
        result = self.cli('deploy', '--artifact', self.artifact, '--bundle', self.bundle, '--origin', self.origin, '--',
                          sys.executable, '--assets', self.artifact)
        self.assertNotEqual(result.returncode, 0)


    def test_initial_legacy_upgrade_ignores_only_static_error_document(self):
        path = self.live / 'deployment.json'
        manifest = json.loads(path.read_text())
        manifest['sourceRevision'] = manifest.pop('codeRevision')
        manifest.pop('publicationRevision')
        manifest['routes'] = fixtures.release.routes(manifest) | {'/404.html'}
        manifest['routes'] = sorted(manifest['routes'])
        path.write_text(json.dumps(manifest))
        result, marker = self.deploy()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(marker.exists())

    def test_legacy_upgrade_still_rejects_missing_content_route(self):
        path = self.live / 'deployment.json'
        manifest = json.loads(path.read_text())
        manifest['sourceRevision'] = manifest.pop('codeRevision')
        manifest.pop('publicationRevision')
        manifest['routes'] = sorted(fixtures.release.routes(manifest) | {'/404.html', '/editions/2026-01-01/'})
        path.write_text(json.dumps(manifest))
        result, marker = self.deploy()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(marker.exists())

    def test_r2_upgrade_cannot_discard_declared_error_document(self):
        path = self.live / 'deployment.json'
        manifest = json.loads(path.read_text())
        manifest['routes'] = sorted(fixtures.release.routes(manifest) | {'/404.html'})
        path.write_text(json.dumps(manifest))
        result, marker = self.deploy()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(marker.exists())


if __name__ == '__main__':
    unittest.main()
