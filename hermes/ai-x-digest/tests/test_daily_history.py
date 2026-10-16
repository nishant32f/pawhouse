from pathlib import Path
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("daily_history", ROOT / "scripts/daily-history.py")
history = importlib.util.module_from_spec(spec)
spec.loader.exec_module(history)


class HistoryTest(unittest.TestCase):
    def test_relocation_keeps_exact_bytes_and_conflicts_stop_before_delete(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, destination, backup = [root / name for name in ("source", "destination", "backup")]
            source.mkdir()
            data = b"accepted\r\nbytes\n"
            (source / "x-ai-2026-10-15.md").write_bytes(data)
            expected = {"x-ai-2026-10-15.md": hashlib.sha256(data).hexdigest()}
            history.relocate(source, destination, backup, expected)
            history.relocate(source, destination, backup, expected)
            self.assertEqual((destination / next(iter(expected))).read_bytes(), data)
            self.assertEqual((backup / next(iter(expected))).read_bytes(), data)
            self.assertTrue((source / next(iter(expected))).exists())
            (destination / next(iter(expected))).write_bytes(b"manual edit")
            with self.assertRaisesRegex(ValueError, "different bytes"):
                history.relocate(source, destination, backup, expected, remove_source=True)
            self.assertTrue((source / next(iter(expected))).exists())

    def test_relocation_rejects_equal_byte_destination_symlink_before_removal(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, destination, backup = [Path(tmp) / name for name in ('source', 'destination', 'backup')]
            source.mkdir()
            destination.mkdir()
            name = 'x-ai-2026-10-15.md'
            data = b'Accepted source\n'
            (source / name).write_bytes(data)
            (destination / name).symlink_to(source / name)
            with self.assertRaisesRegex(ValueError, 'symlink'):
                history.relocate(source, destination, backup, {name: hashlib.sha256(data).hexdigest()}, remove_source=True)
            self.assertEqual((source / name).read_bytes(), data)

    def test_r2_rejects_digest_directory_symlink_to_public_sources(self):
        from publication import Publisher
        from r2_publication import R2Publisher
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'vault').mkdir()
            (root / 'public/digests').mkdir(parents=True)
            (root / 'vault/digests').symlink_to(root / 'public/digests', target_is_directory=True)
            with patch.dict('os.environ', {'PUBLISH_STATE_DIR': str(root / 'state'), 'PUBLISH_REPO': str(root / 'repo'), 'PUBLISH_VAULT_PUBLIC': str(root / 'public')}):
                with self.assertRaisesRegex(ValueError, 'symlink'):
                    R2Publisher(Publisher(), {'vaultRoot': str(root / 'vault'), 'configPath': str(root / 'config')})

    def test_published_history_excludes_candidate_and_uses_accepted_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            from publication import Publisher
            from r2_publication import R2Publisher
            from unittest.mock import patch
            with patch.dict("os.environ", {"PUBLISH_STATE_DIR": str(root / "state"), "PUBLISH_REPO": str(root / "repo"), "PUBLISH_VAULT_PUBLIC": str(root / "public")}):
                owner = Publisher()
                active = R2Publisher(owner, {"vaultRoot": str(root / "vault"), "configPath": str(root / "config")})
                data = b"published accepted source\r\n"
                digest = hashlib.sha256(data).hexdigest()
                (owner.state / "accepted").mkdir()
                (owner.state / "accepted" / (digest + ".md")).write_bytes(data)
                active.sources.mkdir(parents=True)
                (active.sources / "x-ai-2026-10-15.md").write_text("pending candidate")
                active.transport = lambda action: {"head": {"manifest": {"sha256": "a" * 64}}, "etag": "etag", "manifest": {"editions": [{"date": "2026-10-%02d" % day, "sourceSha256": digest} for day in range(8, 16)]}}
                result = active.published_history()
                self.assertEqual(len(result["editions"]), 7)
                self.assertEqual([entry["date"] for entry in result["editions"]], ["2026-10-%02d" % day for day in range(15, 8, -1)])
                self.assertEqual(result["editions"][0]["text"], data.decode())
                self.assertEqual(result["editions"][0]["sourceSha256"], digest)

    def test_legacy_operator_closure_needs_evidence_and_preserves_delivery_ambiguity(self):
        from publication import close_legacy
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "receipt.json"
            path.write_text(json.dumps({"phase": "readerverified", "commit": "a" * 40}))
            with self.assertRaises(ValueError):
                close_legacy(path, "", "operator review")
            result = close_legacy(path, "manual correction with no scheduled send", "operator ticket 123")
            self.assertEqual(result["phase"], "complete")
            self.assertNotIn("delivery_reference", result)
            self.assertEqual(result["legacyResolution"]["classification"], "operator-no-delivery")
            path.write_text(json.dumps({"phase": "deliverypending"}))
            with self.assertRaisesRegex(ValueError, "readerverified"):
                close_legacy(path, "operator", "ticket")


    def test_operator_closure_unblocks_only_classified_receipt(self):
        from publication import Publisher, close_legacy
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = root / 'state'
            (state / 'receipts').mkdir(parents=True)
            path = state / 'receipts' / ('a' * 64 + '.json')
            path.write_text(json.dumps({'phase': 'readerverified', 'commit': 'b' * 40}))
            (state / 'backend.json').write_text(json.dumps({'schemaVersion': 1, 'backend': 'r2', 'vaultRoot': str(root / 'vault'), 'configPath': str(root / 'config')}))
            env = {'PUBLISH_STATE_DIR': str(state), 'PUBLISH_REPO': str(root / 'repo'), 'PUBLISH_VAULT_PUBLIC': str(root / 'public')}
            with patch.dict('os.environ', env):
                owner = Publisher()
                with self.assertRaisesRegex(RuntimeError, 'legacy'):
                    owner.r2()
                closed = subprocess.run([sys.executable, str(ROOT / 'scripts/publication.py'), 'legacy-close', '--receipt', 'a' * 64,
                                         '--classification', 'operator-no-delivery', '--reason', 'manual correction owed no send', '--evidence', 'operator ticket 123'],
                                        capture_output=True, text=True)
                self.assertEqual(closed.returncode, 0, closed.stderr)
                self.assertNotIn('delivery_reference', json.loads(closed.stdout))
                self.assertIsNotNone(owner.r2())
                ambiguous = state / 'receipts' / ('c' * 64 + '.json')
                ambiguous.write_text(json.dumps({'phase': 'deliverypending'}))
                with self.assertRaisesRegex(ValueError, 'readerverified'):
                    close_legacy(ambiguous, 'no inference from status', 'job log is not provider proof')
                with self.assertRaisesRegex(RuntimeError, 'legacy'):
                    owner.r2()

    def test_relocation_removal_is_idempotent_after_verified_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, destination, backup = [Path(tmp) / name for name in ('source', 'destination', 'backup')]
            source.mkdir()
            name = 'x-ai-2026-10.md'
            data = b'Accepted index and links\n'
            (source / name).write_bytes(data)
            hashes = {name: hashlib.sha256(data).hexdigest()}
            history.relocate(source, destination, backup, hashes, remove_source=True)
            history.relocate(source, destination, backup, hashes, remove_source=True)
            self.assertFalse((source / name).exists())
            self.assertEqual((backup / name).read_bytes(), data)
            self.assertEqual((destination / name).read_bytes(), data)

    def test_pinned_full_inventory_is_repeatable_without_current_content_directory(self):
        legacy = 'd6d6a71d42dd3b8e7d9359ddba7e656548368d16'
        revision = history.run(['git', 'rev-parse', 'HEAD'], ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'inventory'
            first = history.inventory(legacy, output, revision)
            before = {path.relative_to(output).as_posix(): path.read_bytes() for path in output.rglob('*') if path.is_file()}
            second = history.inventory(legacy, output, revision)
            after = {path.relative_to(output).as_posix(): path.read_bytes() for path in output.rglob('*') if path.is_file()}
            self.assertEqual(first, second)
            self.assertEqual(before, after)
            self.assertEqual((first['editionCount'], first['indexCount'], first['sourceCount']), (179, 9, 188))
            self.assertIn({'path': '/digests/index.html', 'target': '/archive/'}, first['redirects'])
            for entry in first['sources']:
                original = subprocess.check_output(['git', 'show', legacy + ':content/digests/' + entry['filename']], cwd=ROOT)
                self.assertEqual((output / 'sources' / entry['filename']).read_bytes(), original)
                self.assertEqual(entry['sourceSha256'], hashlib.sha256(original).hexdigest())
                if entry['kind'] == 'edition':
                    self.assertEqual(entry['rss']['guid'], 'https://daily.nishantkhurana.me/editions/' + entry['date'] + '/')
                    if b'digest_format: editorial-v2' not in original:
                        self.assertEqual(entry['stories'], [])
            self.assertTrue(any(entry['aliasSlugs'] for entry in first['sources']))

    def test_old_aliases_use_actual_quartz_paths_and_heading_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Path(tmp) / 'sources.json'
            fixture.write_text(json.dumps([{'filename': 'x-ai-2026-10-15.md', 'text': '---\naliases: ["Bare Alias & 50%?", "./Local Name", "章節"]\npermalink: CustomRoute\n---\n# Duplicate\n# Duplicate\n## A *word* & value\n'}]))
            result = json.loads(history.run([history.MISE, 'exec', 'node@22.23.3', '--', 'node', '--import', 'tsx', ROOT / 'scripts/daily-history-urls.mjs', fixture], ROOT))[0]
            self.assertEqual(result['aliasSlugs'], ['Bare-Alias--and--50-percent', 'digests/Local-Name', '章節', 'CustomRoute'])
            self.assertEqual(result['anchors'], ['duplicate', 'duplicate-1', 'a-word--value'])


class InventoryStagingTest(unittest.TestCase):
    def test_inventory_rejects_extra_valid_edition_in_reused_sources(self):
        legacy = 'd6d6a71d42dd3b8e7d9359ddba7e656548368d16'
        revision = history.run(['git', 'rev-parse', 'HEAD'], ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'inventory'
            staged = output / 'sources'
            staged.mkdir(parents=True)
            extra = staged / 'x-ai-2000-01-01.md'
            extra.write_text('---\ndate: 2000-01-01\ntitle: Extra accepted-looking edition\n---\n# Extra edition\n\nThis file is outside the pinned legacy snapshot.\n')
            before = extra.read_bytes()
            with self.assertRaisesRegex(ValueError, 'unexpected staged source.*x-ai-2000-01-01.md'):
                history.inventory(legacy, output, revision)
            self.assertEqual(extra.read_bytes(), before)
            self.assertEqual(list(staged.iterdir()), [extra])
            self.assertFalse((output / 'bundle').exists())
            self.assertFalse((output / 'inventory.json').exists())

    def test_inventory_rejects_sources_symlink_before_writing_external_files(self):
        legacy = 'd6d6a71d42dd3b8e7d9359ddba7e656548368d16'
        revision = history.run(['git', 'rev-parse', 'HEAD'], ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'inventory'
            output.mkdir()
            external = Path(tmp) / 'external'
            external.mkdir()
            (output / 'sources').symlink_to(external, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, 'symlink'):
                history.inventory(legacy, output, revision)
            self.assertEqual(list(external.iterdir()), [])
            self.assertTrue((output / 'sources').is_symlink())
            self.assertFalse((output / 'bundle').exists())


class InventoryVaultAliasTest(unittest.TestCase):
    def test_inventory_rejects_output_beneath_symlinked_vault_root_before_reading_sources(self):
        from unittest.mock import patch
        revision = 'a' * 40
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp) / 'real-vault'
            vault.mkdir()
            alias = Path(tmp) / 'vault-alias'
            alias.symlink_to(vault, target_is_directory=True)

            def configured_path(value):
                return alias if str(value) == '/Users/skypawalker/Dropbox/Obsidian' else Path(value)

            def read_git(args, cwd):
                if args[1:3] == ['rev-parse', 'HEAD']:
                    return revision
                if args[1:3] == ['diff', '--quiet']:
                    return ''
                raise AssertionError('inventory reached source reading inside the vault')

            for root in (alias, vault):
                with self.subTest(root=root):
                    with patch.object(history, 'Path', side_effect=configured_path), patch.object(history, 'run', side_effect=read_git):
                        with self.assertRaisesRegex(ValueError, 'outside repository and vault'):
                            history.inventory(revision, root / 'inventory', revision)
            self.assertEqual(list(vault.iterdir()), [])


class HistoryCliTest(unittest.TestCase):
    from test_r2_cli import CliPublicationTest as Fixture
    setUp = Fixture.setUp
    stop_server = Fixture.stop_server
    git = Fixture.git
    write_request = Fixture.write_request
    cli = Fixture.cli
    assert_git_unchanged = Fixture.assert_git_unchanged

    def test_backfill_retries_reuse_objects_and_published_history_ignores_pending_candidate(self):
        legacy = self.home / 'legacy-request.json'
        legacy.write_text(json.dumps({'date': '2026-10-15', 'expected_head': self.head, 'files': {}}))
        rejected = self.cli('digest', '--request', str(legacy))
        self.assertNotEqual(rejected.returncode, 0)
        self.assertIn('legacy Git requests', rejected.stderr)
        self.assertEqual(self.objects, {})
        legacy_source = self.repo / 'content/digests/x-ai-2026-10-15.md'
        legacy_source.parent.mkdir(parents=True)
        legacy_source.write_bytes(self.fixture)
        self.git('add', 'content/digests')
        self.git('commit', '-m', 'Pin accepted legacy fixture')
        self.head = self.git('rev-parse', 'HEAD')
        directory = self.home / 'inventory'
        (directory / 'sources').mkdir(parents=True)
        name = 'x-ai-2026-10-15.md'
        (directory / 'sources' / name).write_bytes(self.fixture)
        (directory / 'inventory.json').write_text(json.dumps({'schemaVersion': 1, 'legacyRevision': self.head, 'compilerRevision': self.head,
            'sources': [{'filename': name, 'date': '2026-10-15', 'sourceSha256': hashlib.sha256(self.fixture).hexdigest()}]}))
        command = [sys.executable, str(ROOT / 'scripts/daily-history.py'), 'backfill', '--inventory-dir', str(directory)]
        first = subprocess.run(command, env=self.env, text=True, capture_output=True)
        self.assertEqual(first.returncode, 0, first.stderr)
        before = {key: value.copy() for key, value in self.objects.items()}
        second = subprocess.run(command, env=self.env, text=True, capture_output=True)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(json.loads(first.stdout)['publicationId'], json.loads(second.stdout)['publicationId'])
        self.assertEqual(self.objects, before)
        saved_request = directory / 'backfill-request.json'
        request = json.loads(saved_request.read_text())
        request['kind'] = 'scheduled'
        saved_request.write_text(json.dumps(request))
        rejected = subprocess.run(command, env=self.env, text=True, capture_output=True)
        self.assertNotEqual(rejected.returncode, 0)
        self.assertIn('bootstrap request differs', rejected.stderr)
        self.assertEqual(self.objects, before)
        (self.vault / 'digests' / name).write_text('unaccepted private candidate')
        published = subprocess.run([sys.executable, str(ROOT / 'scripts/daily-history.py'), 'published'], env=self.env, text=True, capture_output=True)
        self.assertEqual(published.returncode, 0, published.stderr)
        self.assertEqual(json.loads(published.stdout)['editions'][0]['text'].encode(), self.fixture)
        self.assert_git_unchanged()


if __name__ == "__main__":
    unittest.main()
