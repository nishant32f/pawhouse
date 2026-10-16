import importlib.util
import json
import hashlib
import io
from contextlib import redirect_stdout, redirect_stderr
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


    def test_complete_install_matches_all_eleven_reviewed_files(self):
        package = Path(__file__).resolve().parents[1]
        manifest = json.loads((package / 'runtime-manifest.json').read_text())
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            with patch('sys.argv', ['install.py', '--hermes-home', str(home)]), redirect_stdout(io.StringIO()):
                installer.main()
            self.assertEqual(len(manifest['files']), 11)
            for relative in manifest['files']:
                self.assertEqual(hashlib.sha256((home / relative).read_bytes()).hexdigest(), manifest['sha256'][relative])
            receipt = json.loads(next(home.glob('backups/*/receipt.json')).read_text())
            self.assertEqual(receipt['status'], 'installed')
            self.assertEqual(set(receipt['files']), set(manifest['files']))

    def test_changed_package_bytes_stop_before_installation(self):
        package = Path(__file__).resolve().parents[1]
        manifest = json.loads((package / 'runtime-manifest.json').read_text())
        with tempfile.TemporaryDirectory() as tmp:
            home, copied = Path(tmp) / 'home', Path(tmp) / 'package'
            home.mkdir()
            copied.mkdir()
            (copied / 'runtime-manifest.json').write_text(json.dumps(manifest))
            for relative in manifest['files']:
                name = manifest.get('sources', {}).get(relative, 'runtime/' + relative)
                target = copied / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((package / name).read_bytes())
            changed = copied / 'runtime' / manifest['files'][-1]
            changed.write_text('unreviewed instructions')
            with patch.object(installer, '__file__', str(copied / 'install.py')), patch('sys.argv', ['install.py', '--hermes-home', str(home)]), redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    installer.main()
            self.assertEqual(list(home.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
