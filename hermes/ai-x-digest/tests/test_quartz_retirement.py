from pathlib import Path
import os
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]


class QuartzRetirementTest(unittest.TestCase):
    def test_normal_sync_excludes_root_digests_without_deleting_legacy_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vault, content = root / 'vault', root / 'repo/content'
            for base in (vault, content):
                (base / 'digests').mkdir(parents=True)
            (vault / 'digests/misplaced.md').write_text('Must stay out')
            (content / 'digests/legacy.md').write_text('Keep until verified retirement')
            for name in ('wisdom', 'summaries', 'wisdom/digests'):
                (vault / name).mkdir(parents=True, exist_ok=True)
                (vault / name / 'note.md').write_text('Ordinary note ' + name)
            (content / 'stale.md').write_text('Delete ordinary stale note')
            env = dict(os.environ, PUBLISH_REPO=str(root / 'repo'),
                       PUBLISH_VAULT_PUBLIC=str(vault), PUBLISH_STATE_DIR=str(root / 'state'))
            result = subprocess.run(['bash', str(ROOT / 'scripts/sync-content-from-vault.sh')],
                                    env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((content / 'digests/misplaced.md').exists())
            self.assertEqual((content / 'digests/legacy.md').read_text(), 'Keep until verified retirement')
            self.assertEqual((vault / 'digests/misplaced.md').read_text(), 'Must stay out')
            self.assertFalse((content / 'stale.md').exists())
            for name in ('wisdom', 'summaries', 'wisdom/digests'):
                self.assertEqual((content / name / 'note.md').read_text(), 'Ordinary note ' + name)
            import shutil
            shutil.rmtree(content / 'digests')
            result = subprocess.run(['bash', str(ROOT / 'scripts/sync-content-from-vault.sh')],
                                    env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((content / 'digests').exists())
