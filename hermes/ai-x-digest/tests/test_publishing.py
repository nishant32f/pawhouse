from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
PUBLISH = ROOT / 'scripts/publication.py'
FIXTURE = ROOT / 'apps/daily/tests/fixtures/editorial-v1.md'

class PublishingTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        self.repo = self.home / 'repo'
        self.repo.mkdir()
        self.vault = self.home / 'vault'
        self.vault.mkdir()
        self.state = self.home / 'state'
        self.env = dict(os.environ, PUBLISH_REPO=str(self.repo), PUBLISH_VAULT_PUBLIC=str(self.vault), PUBLISH_STATE_DIR=str(self.state))
        self.git('init', '-b', 'main')
        self.git('config', 'user.email', 'fixture@example.com')
        self.git('config', 'user.name', 'Fixture')
        self.remote = self.home / 'remote.git'
        subprocess.run(['git', 'init', '--bare', str(self.remote)], check=True, capture_output=True)
        self.git('remote', 'add', 'origin', str(self.remote))
        path = 'digests/x-ai-2026-10-15.md'
        self.old = FIXTURE.read_bytes()
        for base in (self.repo / 'content', self.vault):
            (base / 'digests').mkdir(parents=True)
            (base / path).write_bytes(self.old)
            (base / 'note.md').write_text('An ordinary note.\n')
        self.git('add', '.')
        self.git('commit', '-m', 'Initial source')
        self.git('push', '-u', 'origin', 'main')
        self.head = self.git('rev-parse', 'HEAD')
        self.staged = self.home / 'accepted.md'
        self.staged.write_bytes(self.old.replace(b'Vendor claim.', b'Vendor claim, corrected.'))
        self.request = self.home / 'request.json'
        self.request.write_text(json.dumps({'date': '2026-10-15', 'expected_head': self.head, 'files': {path: {'staged': str(self.staged), 'before_sha256': hashlib.sha256(self.old).hexdigest(), 'staged_sha256': hashlib.sha256(self.staged.read_bytes()).hexdigest()}}}))

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.repo), *args], capture_output=True, text=True, check=True).stdout.strip()

    def cli(self, *args):
        return subprocess.run([sys.executable, str(PUBLISH), *args], env=self.env, capture_output=True, text=True)

    def publish(self):
        return self.cli('digest', '--request', str(self.request))

    def receipt(self):
        return json.loads(next((self.state / 'receipts').glob('*.json')).read_text())

    def test_declared_paths_commit_and_retry_reuses_accepted_commit(self):
        result = self.publish()
        self.assertEqual(result.returncode, 0, result.stderr)
        accepted = json.loads(result.stdout)['commit']
        self.assertNotEqual(accepted, self.head)
        self.assertEqual(self.git('diff', '--name-only', self.head, accepted), 'content/digests/x-ai-2026-10-15.md')
        self.assertEqual(self.receipt()['phase'], 'readerpending')
        self.assertEqual(json.loads(self.publish().stdout)['commit'], accepted)
        self.assertEqual(self.git('rev-list', '--count', 'HEAD'), '2')
        self.assertEqual((self.vault / 'digests/x-ai-2026-10-15.md').read_bytes(), self.staged.read_bytes())

    def test_unrelated_repo_or_vault_changes_abort_without_promotion(self):
        for base in (self.repo, self.vault):
            dirty = base / 'unrelated.md'
            dirty.write_text('keep me')
            self.assertNotEqual(self.publish().returncode, 0)
            self.assertEqual(self.git('rev-parse', 'HEAD'), self.head)
            self.assertEqual((self.vault / 'digests/x-ai-2026-10-15.md').read_bytes(), self.old)
            self.assertEqual(dirty.read_text(), 'keep me')
            dirty.unlink()

    def test_staged_hash_mismatch_aborts(self):
        self.staged.write_text('changed after acceptance')
        self.assertNotEqual(self.publish().returncode, 0)
        self.assertEqual(self.git('rev-parse', 'HEAD'), self.head)

    def test_push_failure_retries_same_commit(self):
        self.git('remote', 'set-url', 'origin', str(self.home / 'missing.git'))
        self.assertNotEqual(self.publish().returncode, 0)
        accepted = self.git('rev-parse', 'HEAD')
        self.assertEqual(self.receipt()['commit'], accepted)
        self.git('remote', 'set-url', 'origin', str(self.remote))
        self.assertEqual(json.loads(self.publish().stdout)['commit'], accepted)
        self.assertEqual(self.git('rev-list', '--count', 'HEAD'), '2')

    def test_interrupted_promotion_restores_before_next_sync(self):
        self.state.mkdir()
        backup = self.state / 'backups'
        backup.mkdir()
        targets = []
        for n, base in enumerate((self.vault, self.repo / 'content')):
            target = base / 'digests/x-ai-2026-10-15.md'
            copy = backup / str(n)
            copy.write_bytes(target.read_bytes())
            targets.append({'target': str(target), 'backup': str(copy)})
            target.write_text('partial promotion')
        (self.state / 'promotion.json').write_text(json.dumps({'targets': targets, 'expected_head': self.head, 'files': {'digests/x-ai-2026-10-15.md': hashlib.sha256(b'partial promotion').hexdigest()}, 'receipt': None}))
        result = self.cli('recover')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.vault / 'digests/x-ai-2026-10-15.md').read_bytes(), self.old)
        self.assertEqual(self.git('status', '--porcelain'), '')

    def test_successful_delivery_suppresses_retry_and_ambiguous_delivery_blocks(self):
        result = self.publish()
        self.assertEqual(result.returncode, 0, result.stderr)
        receipt = self.receipt()
        receipt['phase'] = 'readerverified'
        receipt['reader'] = {'origin': 'https://reader.example', 'tested_routes': ['/editions/2026-10-15/']}
        receipt_file = next((self.state / 'receipts').glob('*.json'))
        receipt_file.write_text(json.dumps(receipt))
        self.assertEqual(self.cli('delivery-begin', '--request', str(self.request)).returncode, 0)
        self.assertNotEqual(self.cli('delivery-begin', '--request', str(self.request)).returncode, 0)
        self.assertNotEqual(self.publish().returncode, 0)
        self.assertEqual(self.cli('delivery-complete', '--request', str(self.request), '--reference', 'fixture-delivery').returncode, 0)
        self.assertEqual(json.loads(self.publish().stdout)['phase'], 'complete')

    def test_retry_after_remote_main_advanced_reuses_accepted_commit(self):
        self.assertEqual(self.publish().returncode, 0)
        accepted = self.git('rev-parse', 'HEAD')
        other = self.home / 'other'
        subprocess.run(['git', 'clone', '--branch', 'main', str(self.remote), str(other)], capture_output=True, check=True)
        def remote_git(*args):
            return subprocess.run(['git', '-C', str(other), *args], capture_output=True, text=True, check=True).stdout.strip()
        remote_git('config', 'user.email', 'other@example.com')
        remote_git('config', 'user.name', 'Other')
        (other / 'extra.md').write_text('descendant')
        remote_git('add', '.')
        remote_git('commit', '-m', 'descendant')
        remote_git('push', 'origin', 'main')
        descendant = remote_git('rev-parse', 'HEAD')
        result = self.publish()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['commit'], accepted)
        self.assertEqual(subprocess.check_output(['git', '--git-dir', str(self.remote), 'rev-parse', 'main'], text=True).strip(), descendant)

    def test_crash_after_commit_recovers_unchanged_declared_index(self):
        index = 'digests/x-ai-2026-10.md'
        for base in (self.vault, self.repo / 'content'):
            (base / index).write_text('Monthly index\n')
        self.git('add', '.')
        self.git('commit', '-m', 'index')
        self.head = self.git('rev-parse', 'HEAD')
        staged_index = self.home / 'index.md'
        staged_index.write_text('Monthly index\n')
        request = json.loads(self.request.read_text())
        request['expected_head'] = self.head
        request['files'][index] = {'staged': str(staged_index), 'before_sha256': hashlib.sha256(staged_index.read_bytes()).hexdigest(), 'staged_sha256': hashlib.sha256(staged_index.read_bytes()).hexdigest()}
        self.request.write_text(json.dumps(request))
        self.assertEqual(self.publish().returncode, 0)
        accepted = self.git('rev-parse', 'HEAD')
        receipt_file = next((self.state / 'receipts').glob('*.json'))
        receipt = self.receipt()
        receipt.pop('commit')
        receipt['phase'] = 'promoted'
        receipt_file.write_text(json.dumps(receipt))
        (self.state / 'promotion.json').write_text(json.dumps({'expected_head': self.head, 'files': receipt['files'], 'receipt': str(receipt_file), 'targets': []}))
        result = self.cli('recover')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.receipt()['commit'], accepted)

    def test_recovery_preserves_manual_edit_after_interruption(self):
        self.state.mkdir()
        backup = self.state / 'old.md'
        backup.write_bytes(self.old)
        target = self.vault / 'digests/x-ai-2026-10-15.md'
        target.write_text('manual edit after the crash')
        (self.state / 'promotion.json').write_text(json.dumps({'expected_head': self.head, 'files': {'digests/x-ai-2026-10-15.md': hashlib.sha256(self.staged.read_bytes()).hexdigest()}, 'receipt': None, 'targets': [{'target': str(target), 'backup': str(backup)}]}))
        self.assertNotEqual(self.cli('recover').returncode, 0)
        self.assertEqual(target.read_text(), 'manual edit after the crash')

    def test_unsafe_link_beside_valid_source_aborts_before_promotion(self):
        data = self.staged.read_bytes().replace(b'Vendor claim, corrected.', b'Vendor claim, corrected. [unsafe](javascript:alert(1))')
        self.staged.write_bytes(data)
        request = json.loads(self.request.read_text())
        request['files']['digests/x-ai-2026-10-15.md']['staged_sha256'] = hashlib.sha256(data).hexdigest()
        self.request.write_text(json.dumps(request))
        result = self.publish()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.git('rev-parse', 'HEAD'), self.head)
        self.assertEqual((self.vault / 'digests/x-ai-2026-10-15.md').read_bytes(), self.old)

    def test_lock_serializes_manual_sync_and_digest(self):
        import fcntl
        self.state.mkdir()
        lock = (self.state / 'host.lock').open('a')
        self.addCleanup(lock.close)
        fcntl.flock(lock, fcntl.LOCK_EX)
        processes = [subprocess.Popen([sys.executable, str(PUBLISH), *args], env=self.env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for args in [('sync',), ('digest', '--request', str(self.request))]]
        try:
            for process in processes:
                with self.assertRaises(subprocess.TimeoutExpired):
                    process.wait(timeout=0.15)
            self.assertEqual(self.git('rev-parse', 'HEAD'), self.head)
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)
        for process in processes:
            stdout, stderr = process.communicate(timeout=30)
            self.assertEqual(process.returncode, 0, stderr)
        self.assertEqual((self.vault / 'digests/x-ai-2026-10-15.md').read_bytes(), self.staged.read_bytes())

    def test_sigkill_before_public_rename_repairs_before_sync(self):
        import signal
        for base in (self.vault, self.repo / 'content'):
            with self.subTest(interrupted_target=str(base)):
                target = (base / 'digests/x-ai-2026-10-15.md').resolve()
                code = '''
import os
from pathlib import Path
import signal
import sys
sys.path.insert(0, sys.argv[1])
import publication
original = os.replace
def interrupt_before_rename(source, destination):
    if Path(destination).resolve() == Path(sys.argv[3]).resolve():
        os.kill(os.getpid(), signal.SIGKILL)
    return original(source, destination)
os.replace = interrupt_before_rename
publisher = publication.Publisher()
with publisher.locked():
    publisher.digest(sys.argv[2])
'''
                result = subprocess.run([sys.executable, '-c', code, str(PUBLISH.parent), str(self.request), str(target)], env=self.env, capture_output=True, text=True)
                self.assertEqual(result.returncode, -signal.SIGKILL, result.stderr)
                self.assertTrue((self.state / 'promotion.json').exists())
                result = self.cli('sync')
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(self.git('status', '--porcelain'), '')
                self.assertEqual((self.vault / 'digests/x-ai-2026-10-15.md').read_bytes(), self.old)
                self.assertFalse(list(self.vault.rglob('*.pawhouse-*')))
                self.assertFalse(list(self.vault.rglob('*.tmp')))

    @unittest.skipUnless(sys.platform == 'darwin' and Path('/opt/homebrew/bin/mise').exists(), 'Pluto Homebrew fallback')
    def test_absolute_wrapper_works_with_pluto_minimal_path(self):
        self.env['PATH'] = '/usr/bin:/bin:/usr/sbin:/sbin'
        wrapper = ROOT / 'scripts/publish-from-vault.sh'
        result = subprocess.run(['/bin/bash', str(wrapper), '--digest', str(self.request)], env=self.env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['phase'], 'readerpending')

if __name__ == '__main__':
    unittest.main()
