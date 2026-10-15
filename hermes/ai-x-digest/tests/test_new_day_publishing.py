import hashlib
import json
import signal
import subprocess
import sys
import unittest

import test_publishing as publishing


class NewDayPublishingTest(unittest.TestCase):
    git = publishing.PublishingTest.git
    cli = publishing.PublishingTest.cli
    publish = publishing.PublishingTest.publish
    receipt = publishing.PublishingTest.receipt

    def setUp(self):
        publishing.PublishingTest.setUp(self)
        self.edition = 'digests/x-ai-2026-10-16.md'
        self.previous = 'digests/x-ai-2026-10-15.md'
        self.month = 'digests/x-ai-2026-10.md'
        self.year = 'digests/x-ai-2026.md'
        self.bases = (self.vault, self.repo / 'content')
        self.original_indexes = {
            self.month: b'# X-AI October 2026\n\n- [[digests/x-ai-2026-10-15|X-AI-2026-10-15]]\n',
            self.year: b'# X-AI 2026\n\n- [[digests/x-ai-2026-10|X-AI October 2026]]\n',
        }
        for base in self.bases:
            for relative, data in self.original_indexes.items():
                (base / relative).write_bytes(data)
        self.git('add', '.')
        self.git('commit', '-m', 'Seed digest indexes')
        self.git('push', 'origin', 'main')
        self.head = self.git('rev-parse', 'HEAD')
        self.before_count = int(self.git('rev-list', '--count', 'HEAD'))
        self.before = self.public_trees()
        next_link = b'- Next: [[digests/x-ai-2026-10-16|X-AI-2026-10-16]]'
        self.accepted = {
            self.edition: self.old.replace(b'2026-10-15', b'2026-10-16').replace(b'2026-10-14', b'2026-10-15'),
            self.month: self.original_indexes[self.month] + b'- [[digests/x-ai-2026-10-16|X-AI-2026-10-16]]\n',
            self.year: self.original_indexes[self.year] + b'- Latest: [[digests/x-ai-2026-10-16|X-AI-2026-10-16]]\n',
            self.previous: self.old.replace(b'- Next: None', next_link),
        }
        self.write_request()

    def public_trees(self):
        return [{path.relative_to(base).as_posix(): path.read_bytes()
                 for path in base.rglob('*') if path.is_file()} for base in self.bases]

    def write_request(self):
        files = {}
        for number, (relative, data) in enumerate(self.accepted.items()):
            staged = self.home / f'accepted-{number}.md'
            staged.write_bytes(data)
            original = self.before[0].get(relative)
            files[relative] = {
                'staged': str(staged),
                'before_sha256': hashlib.sha256(original).hexdigest() if original is not None else None,
                'staged_sha256': hashlib.sha256(data).hexdigest(),
            }
        self.request.write_text(json.dumps({'date': '2026-10-16', 'expected_head': self.head, 'files': files}))

    def assert_original_history(self):
        self.assertEqual(self.git('rev-parse', 'HEAD'), self.head)
        self.assertEqual(int(self.git('rev-list', '--count', 'HEAD')), self.before_count)
        self.assertEqual(self.git('status', '--porcelain', '--untracked-files=all'), '')
        self.assertEqual(self.git('diff', '--cached', '--name-only'), '')
        remote = subprocess.check_output(['git', '--git-dir', str(self.remote), 'rev-parse', 'main'], text=True).strip()
        self.assertEqual(remote, self.head)

    def test_new_day_promotes_exact_files_and_retry_reuses_commit(self):
        request = json.loads(self.request.read_text())
        self.assertIsNone(request['files'][self.edition]['before_sha256'])
        result = self.publish()
        self.assertEqual(result.returncode, 0, result.stderr)
        accepted = json.loads(result.stdout)['commit']
        self.assertNotEqual(accepted, self.head)
        expected_trees = [dict(before, **self.accepted) for before in self.before]
        self.assertEqual(self.public_trees(), expected_trees)
        expected_paths = {'content/' + path for path in self.accepted}
        self.assertEqual(set(self.git('diff', '--name-only', self.head, accepted).splitlines()), expected_paths)
        self.assertEqual(self.git('diff', '--diff-filter=A', '--name-only', self.head, accepted), 'content/' + self.edition)
        for relative, data in self.accepted.items():
            blob = subprocess.check_output(['git', '-C', str(self.repo), 'show', accepted + ':content/' + relative])
            self.assertEqual(blob, data, relative)
        self.assertEqual(self.git('status', '--porcelain', '--untracked-files=all'), '')
        self.assertEqual(self.receipt()['phase'], 'readerpending')
        remote = subprocess.check_output(['git', '--git-dir', str(self.remote), 'rev-parse', 'main'], text=True).strip()
        self.assertEqual(remote, accepted)
        retry = self.publish()
        self.assertEqual(retry.returncode, 0, retry.stderr)
        self.assertEqual(json.loads(retry.stdout)['commit'], accepted)
        self.assertEqual(self.git('rev-parse', 'HEAD'), accepted)
        self.assertEqual(int(self.git('rev-list', '--count', 'HEAD')), self.before_count + 1)
        self.assertEqual(self.public_trees(), expected_trees)
        self.assertEqual(len(list((self.state / 'receipts').glob('*.json'))), 1)

    def test_previous_day_prose_edit_rejects_before_publication(self):
        self.accepted[self.previous] = self.accepted[self.previous].replace(b'Vendor claim.', b'Vendor claim, rewritten.')
        self.write_request()
        result = self.publish()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('previous edition may change only its Next navigation link', result.stderr)
        self.assertEqual(self.public_trees(), self.before)
        self.assert_original_history()
        self.assertFalse((self.state / 'promotion.json').exists())
        self.assertFalse(list((self.state / 'receipts').glob('*.json')))

    def test_sigkill_after_new_and_existing_file_renames_rolls_back(self):
        code = '''
import os
from pathlib import Path
import runpy
import signal
import sys
publisher, request, target = sys.argv[1:]
original = os.replace
def interrupt_after_rename(source, destination):
    result = original(source, destination)
    if Path(destination).resolve() == Path(target).resolve():
        os.kill(os.getpid(), signal.SIGKILL)
    return result
os.replace = interrupt_after_rename
sys.argv = [publisher, 'digest', '--request', request]
runpy.run_path(publisher, run_name='__main__')
'''
        for relative in (self.edition, self.month):
            with self.subTest(interrupted_after=relative):
                target = self.repo / 'content' / relative
                result = subprocess.run([sys.executable, '-c', code, str(publishing.PUBLISH), str(self.request), str(target)],
                                        env=self.env, capture_output=True, text=True)
                self.assertEqual(result.returncode, -signal.SIGKILL, result.stderr)
                self.assertEqual(target.read_bytes(), self.accepted[relative])
                for base in self.bases:
                    self.assertEqual((base / self.edition).read_bytes(), self.accepted[self.edition])
                self.assertEqual((self.vault / self.month).read_bytes(), self.accepted[self.month])
                journal = self.state / 'promotion.json'
                self.assertTrue(journal.exists())
                self.assertEqual(self.git('rev-parse', 'HEAD'), self.head)
                self.assertNotIn('commit', self.receipt())
                recovery = self.cli('recover')
                self.assertEqual(recovery.returncode, 0, recovery.stderr)
                self.assertEqual(self.public_trees(), self.before)
                for base in self.bases:
                    self.assertFalse((base / self.edition).exists())
                self.assert_original_history()
                self.assertFalse(journal.exists())
                self.assertEqual(self.receipt()['phase'], 'accepted')
                self.assertNotIn('commit', self.receipt())
                self.assertEqual(len(list((self.state / 'receipts').glob('*.json'))), 1)


if __name__ == '__main__':
    unittest.main()
