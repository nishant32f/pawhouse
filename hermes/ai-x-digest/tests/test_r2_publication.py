from pathlib import Path
import importlib.util
import hashlib
import json
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts'))

class R2PublicationTest(unittest.TestCase):
    def test_backend_is_inactive_without_explicit_switch(self):
        from publication import Publisher
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict('os.environ', {'PUBLISH_STATE_DIR': tmp + '/state', 'PUBLISH_REPO': tmp + '/repo', 'PUBLISH_VAULT_PUBLIC': tmp + '/public'}):
                self.assertIsNone(Publisher().r2())

    def test_legacy_pending_receipt_blocks_activation(self):
        from publication import Publisher
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            state = home / 'state'
            (state / 'receipts').mkdir(parents=True)
            (state / 'receipts/old.json').write_text(json.dumps({'phase': 'readerpending'}))
            (state / 'backend.json').write_text(json.dumps({'schemaVersion': 1, 'backend': 'r2', 'vaultRoot': str(home / 'vault'), 'configPath': str(home / 's3.json')}))
            with patch.dict('os.environ', {'PUBLISH_STATE_DIR': str(state), 'PUBLISH_REPO': str(home / 'repo'), 'PUBLISH_VAULT_PUBLIC': str(home / 'public')}):
                with self.assertRaisesRegex(RuntimeError, 'legacy'):
                    Publisher().r2()


class LifecycleTest(unittest.TestCase):
    def setUp(self):
        import publication
        from r2_publication import R2Publisher
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        self.env = patch.dict('os.environ', {'PUBLISH_STATE_DIR': str(self.home / 'state'), 'PUBLISH_REPO': str(self.home / 'repo'), 'PUBLISH_VAULT_PUBLIC': str(self.home / 'public')})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.owner = publication.Publisher()
        original_run = __import__('publication').run
        def fixture_run(args, cwd=None):
            if str(args[1]).endswith('verify-x-ai-digest-format.py'):
                args[1] = ROOT / 'hermes/ai-x-digest/runtime/skills/note-taking/obsidian/scripts/verify-x-ai-digest-format.py'
            return original_run(args, cwd)
        run_patch = patch('publication.run', fixture_run)
        run_patch.start()
        self.addCleanup(run_patch.stop)
        self.owner.git = lambda *args: 'a' * 40 if args == ('rev-parse', 'HEAD') else ''
        self.active = R2Publisher(self.owner, {'vaultRoot': str(self.home / 'vault'), 'configPath': str(self.home / 's3.json')})
        self.active.package = ROOT / 'hermes/ai-x-digest/content'
        self.current = {'head': None, 'manifest': None, 'etag': None}
        self.uploads = 0
        self.fail_upload = False
        self.active.transport = self.transport
        self.fixture = (ROOT / 'apps/daily/tests/fixtures/editorial-v2-four-stories.md').read_bytes()
        self.request_path = self.home / 'request.json'
        self.request = {'schemaVersion': 2, 'backend': 'r2', 'kind': 'backfill', 'date': '2026-10-15', 'compilerRevision': 'a' * 40, 'expected': {'manifestSha256': None, 'etag': None}, 'files': {}}
        self.stage('x-ai-2026-10-15.md', self.fixture)

    def stage(self, name, data):
        staged = self.home / ('staged-' + name)
        staged.write_bytes(data)
        self.request['files'][name] = {'staged': str(staged), 'stagedSha256': hashlib.sha256(data).hexdigest(), 'beforeSha256': self.active.sha(self.active.sources / name)}
        self.request_path.write_text(json.dumps(self.request))

    def transport(self, action, *args):
        if action == 'inspect':
            return dict(self.current)
        if action == 'objects':
            if self.fail_upload:
                raise RuntimeError('lost upload response')
            return dict(self.current)
        if action == 'publish':
            self.uploads += 1
            if self.fail_upload:
                raise RuntimeError('lost upload response')
            bundle = Path(args[0])
            metadata = json.loads((bundle / 'bundle.json').read_text())
            self.current = {'head': metadata['head'], 'manifest': metadata['manifest'], 'etag': '"opaque-etag"'}
            return dict(self.current)
        raise AssertionError(action)

    def bootstrap(self):
        return self.active.digest(self.request_path)

    def next_request(self, kind='scheduled'):
        self.request_path = self.home / 'next.json'
        self.request = {'schemaVersion': 2, 'backend': 'r2', 'kind': kind, 'date': '2026-10-16' if kind == 'scheduled' else '2026-10-15', 'compilerRevision': 'a' * 40,
                        'expected': {'manifestSha256': self.current['head']['manifest']['sha256'], 'etag': self.current['etag']}, 'files': {}}

    def test_bootstrap_freezes_all_sources_and_retries_are_inert(self):
        self.stage('x-ai-2026-10.md', b'Monthly index\n')
        receipt = self.bootstrap()
        self.assertEqual(receipt['phase'], 'published')
        self.assertEqual(receipt['manifest']['compilerRevision'], 'a' * 40)
        self.assertEqual(len(receipt['manifest']['editions']), 1)
        self.assertEqual((self.active.sources / 'x-ai-2026-10.md').read_bytes(), b'Monthly index\n')
        Path(self.request['files']['x-ai-2026-10-15.md']['staged']).write_text('changed staged draft')
        self.assertEqual(self.bootstrap()['publicationId'], receipt['publicationId'])
        self.assertEqual(self.uploads, 1)
        self.assertEqual(self.active.load_publication(self.request_path)['receipt']['publicationId'], receipt['publicationId'])

    def test_new_day_uses_published_snapshots_ignoring_unrelated_private_edits(self):
        self.bootstrap()
        (self.active.sources / 'x-ai-2026-10-15.md').write_text('manual private edit not accepted')
        self.next_request()
        self.stage('x-ai-2026-10-16.md', self.fixture.replace(b'2026-10-15', b'2026-10-16'))
        receipt = self.active.digest(self.request_path)
        self.assertEqual([entry['date'] for entry in receipt['manifest']['editions']], ['2026-10-16', '2026-10-15'])
        self.assertEqual((self.active.sources / 'x-ai-2026-10-15.md').read_text(), 'manual private edit not accepted')

    def test_changed_staged_or_before_hash_rejects_without_promoting(self):
        Path(self.request['files']['x-ai-2026-10-15.md']['staged']).write_text('changed')
        with self.assertRaisesRegex(RuntimeError, 'staged accepted hash'):
            self.bootstrap()
        self.assertIsNone(self.current['head'])
        self.assertFalse(self.active.sources.exists())

    def test_lost_upload_resumes_frozen_candidate_and_preserves_manual_edits(self):
        self.fail_upload = True
        with self.assertRaisesRegex(RuntimeError, 'lost upload'):
            self.bootstrap()
        self.assertTrue(self.active.journal.exists())
        original_request = self.request_path
        Path(self.request['files']['x-ai-2026-10-15.md']['staged']).write_text('draft changed after acceptance')
        self.fail_upload = False
        self.active.recover()
        self.assertEqual(self.active.load_publication(original_request)['receipt']['phase'], 'published')
        self.assertEqual((self.active.sources / 'x-ai-2026-10-15.md').read_bytes(), self.fixture)

    def test_recovery_checks_published_head_before_touching_manual_sources(self):
        self.fail_upload = True
        with self.assertRaises(RuntimeError):
            self.bootstrap()
        loaded = self.active.load_publication(self.request_path)
        self.current = {'head': loaded['receipt']['head'], 'manifest': loaded['receipt']['manifest'], 'etag': '"committed"'}
        (self.active.sources / 'x-ai-2026-10-15.md').write_text('manual edit after lost head response')
        self.active.recover()
        self.assertEqual(self.active.load_publication(self.request_path)['receipt']['phase'], 'published')
        self.assertEqual((self.active.sources / 'x-ai-2026-10-15.md').read_text(), 'manual edit after lost head response')

    def test_unexpected_new_head_blocks_recovery_and_preserves_sources(self):
        self.fail_upload = True
        with self.assertRaises(RuntimeError):
            self.bootstrap()
        (self.active.sources / 'x-ai-2026-10-15.md').write_text('manual edit')
        self.current = {'head': {'manifest': {'sha256': 'b' * 64}}, 'manifest': {}, 'etag': '"newer"'}
        with self.assertRaisesRegex(RuntimeError, 'publication conflict'):
            self.active.recover()
        self.assertEqual((self.active.sources / 'x-ai-2026-10-15.md').read_text(), 'manual edit')

    def test_correction_rejects_lost_story_identity(self):
        self.bootstrap()
        self.next_request('correction')
        self.stage('x-ai-2026-10-15.md', self.fixture.replace(b'anthropic-monorepo', b'renamed-story-id'))
        with self.assertRaisesRegex(RuntimeError, 'lost a story ID'):
            self.active.digest(self.request_path)

    def test_tampered_frozen_objects_reject(self):
        self.bootstrap()
        loaded = self.active.load_publication(self.request_path)
        (loaded['bundle'] / loaded['receipt']['objects'][0]['key']).write_text('changed')
        with self.assertRaisesRegex(ValueError, 'frozen publication object changed'):
            self.active.load_publication(self.request_path)

    def test_index_backups_precede_source_promotion(self):
        self.active.sources.mkdir(parents=True)
        (self.active.sources / 'x-ai-2026-10.md').write_bytes(b'Original month\n')
        self.stage('x-ai-2026-10.md', b'Changed month\n')
        self.fail_upload = True
        with self.assertRaises(RuntimeError):
            self.bootstrap()
        journal = json.loads(self.active.journal.read_text())
        item = next(item for item in journal['targets'] if item['name'] == 'x-ai-2026-10.md')
        self.assertEqual(Path(item['backup']).read_bytes(), b'Original month\n')

    def test_immutable_readback_phase_precedes_head_write(self):
        original = self.active.transport
        def observe(action, *args):
            if action == 'publish':
                loaded = self.active.load_publication(self.request_path)
                self.assertEqual(loaded['receipt']['phase'], 'objects-verified')
                self.assertIsNone(self.current['head'])
            return original(action, *args)
        self.active.transport = observe
        self.bootstrap()

    def test_manual_source_edit_before_head_publication_blocks_resume(self):
        self.fail_upload = True
        with self.assertRaises(RuntimeError):
            self.bootstrap()
        target = self.active.sources / 'x-ai-2026-10-15.md'
        target.write_text('manual edit after interruption')
        self.fail_upload = False
        with self.assertRaisesRegex(RuntimeError, 'manual edit'):
            self.active.recover()
        self.assertIsNone(self.current['head'])
        self.assertEqual(target.read_text(), 'manual edit after interruption')

    def test_freeze_before_receipt_failure_adopts_same_bytes(self):
        original_save = self.active.save
        def lose_receipt(path, value):
            if path.parent.name == 'receipts':
                raise OSError('receipt rename interrupted')
            original_save(path, value)
        self.active.save = lose_receipt
        with self.assertRaisesRegex(OSError, 'receipt rename interrupted'):
            self.bootstrap()
        self.assertFalse(self.active.sources.exists())
        self.active.save = original_save
        Path(self.request['files']['x-ai-2026-10-15.md']['staged']).write_text('draft changed before retry')
        receipt = self.bootstrap()
        self.assertEqual(receipt['phase'], 'published')
        self.assertEqual((self.active.sources / 'x-ai-2026-10-15.md').read_bytes(), self.fixture)

    def test_partial_preparation_blocks_without_promoting(self):
        _, receipt_path = self.active.request(self.request_path)
        (self.active.state / 'bundles' / receipt_path.stem).mkdir(parents=True)
        with self.assertRaisesRegex(RuntimeError, 'incomplete unreceipted bundle'):
            self.bootstrap()
        self.assertFalse(self.active.sources.exists())
        self.assertIsNone(self.current['head'])

    def test_wrong_compiler_revision_and_legacy_requests_fail(self):
        self.request['compilerRevision'] = 'b' * 40
        self.request_path.write_text(json.dumps(self.request))
        with self.assertRaisesRegex(RuntimeError, 'executing compiler code'):
            self.bootstrap()
        self.request_path.write_text(json.dumps({'expected_head': 'a' * 40, 'date': '2026-10-15', 'files': {}}))
        with self.assertRaisesRegex(ValueError, 'legacy Git requests'):
            self.active.request(self.request_path)
