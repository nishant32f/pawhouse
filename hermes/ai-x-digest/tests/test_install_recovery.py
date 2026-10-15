import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


path = Path(__file__).resolve().parents[1] / 'install.py'
spec = importlib.util.spec_from_file_location('digest_install', path)
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallRecoveryTest(unittest.TestCase):
    def test_failed_replacement_restores_existing_and_removes_new_files(self):
        for failure_at in (2, 3):
            with self.subTest(failure_at=failure_at), tempfile.TemporaryDirectory() as tmp:
                home = Path(tmp)
                existing = home / 'skills/note-taking/ai-x-digest/SKILL.md'
                existing.parent.mkdir(parents=True)
                existing.write_text('previous installed skill\n')
                sibling = home / 'skills/unrelated/SKILL.md'
                sibling.parent.mkdir(parents=True)
                sibling.write_text('leave this skill alone\n')
                real_replace = Path.replace
                replacements = 0

                def fail_second(source, target):
                    nonlocal replacements
                    replacements += 1
                    if replacements == failure_at:
                        raise OSError('injected replacement failure')
                    return real_replace(source, target)

                with patch('sys.argv', ['install.py', '--hermes-home', str(home)]), patch.object(Path, 'replace', fail_second):
                    with self.assertRaises(OSError):
                        installer.main()
                self.assertEqual(existing.read_text(), 'previous installed skill\n')
                self.assertFalse((home / 'skills/note-taking/unslop/SKILL.md').exists())
                self.assertEqual(sibling.read_text(), 'leave this skill alone\n')
                receipt = json.loads(next(home.glob('backups/*/receipt.json')).read_text())
                self.assertEqual(receipt['status'], 'rolled-back')
                self.assertTrue(receipt['files']['skills/note-taking/ai-x-digest/SKILL.md']['existed'])
                self.assertFalse(receipt['files']['skills/note-taking/unslop/SKILL.md']['existed'])


if __name__ == '__main__':
    unittest.main()
