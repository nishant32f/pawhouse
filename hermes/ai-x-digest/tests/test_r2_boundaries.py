"""Transport timeouts and private accepted-source boundaries use real child processes."""
from pathlib import Path
import fcntl
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts'))


class PrivateRootTest(unittest.TestCase):
    def test_public_and_repository_descendants_including_aliases_are_rejected(self):
        from publication import Publisher
        from r2_publication import R2Publisher
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp).resolve()
            vault = home / 'vault'
            public = vault / 'public'
            repo = home / 'repo'
            public.mkdir(parents=True)
            repo.mkdir()
            alias = home / 'public-alias'
            alias.symlink_to(public, target_is_directory=True)
            with patch.dict(os.environ, {'PUBLISH_STATE_DIR': str(home / 'state'), 'PUBLISH_REPO': str(repo), 'PUBLISH_VAULT_PUBLIC': str(public)}):
                owner = Publisher()
                for root in (public, public / 'accepted', alias / 'accepted', repo, repo / 'accepted'):
                    with self.subTest(root=root), self.assertRaisesRegex(ValueError, 'private vault root'):
                        R2Publisher(owner, {'vaultRoot': str(root), 'configPath': str(home / 's3.json')})
                active = R2Publisher(owner, {'vaultRoot': str(vault), 'configPath': str(home / 's3.json')})
                active.sources.mkdir()
                (active.sources / 'x-ai-2026-10-16.md').write_text('Private accepted content\n')
                (public / 'ordinary.md').write_text('An ordinary note\n')
                with owner.locked():
                    owner.sync()
                self.assertEqual((repo / 'content/ordinary.md').read_text(), 'An ordinary note\n')
                self.assertFalse(any('Private accepted content' in path.read_text() for path in (repo / 'content').rglob('*.md')))


class TransportTimeoutTest(unittest.TestCase):
    def test_each_transport_action_kills_its_descendant_before_releasing_lock(self):
        for action in ('inspect', 'objects', 'publish'):
            with self.subTest(action=action):
                self.exercise(action)

    def test_sigint_kills_transport_descendants_and_preserves_interrupt(self):
        self.exercise('publish', interrupt=True)

    def exercise(self, action, interrupt=False):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp).resolve()
            package = home / 'repo/hermes/ai-x-digest/content'
            package.mkdir(parents=True)
            runner = home / 'hanging-mise'
            child = """import os, pathlib, signal, sys, time
home = pathlib.Path(sys.argv[1])
signal.signal(signal.SIGTERM, signal.SIG_IGN)
(home / 'descendant.pid').write_text(str(os.getpid()))
while True:
    with (home / 'heartbeat').open('a') as stream:
        stream.write('alive\\n')
    time.sleep(0.03)
"""
            runner.write_text('#!' + sys.executable + '\n' +
                'import os, pathlib, signal, subprocess, sys\n' +
                'home = pathlib.Path(' + repr(str(home)) + ')\n' +
                'signal.signal(signal.SIGTERM, signal.SIG_IGN)\n' +
                '(home / "transport.pid").write_text(str(os.getpid()))\n' +
                'subprocess.Popen([sys.executable, "-c", ' + repr(child) + ', str(home)]).wait()\n')
            runner.chmod(0o700)
            harness = """import json, os, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import publication, r2_publication
home = Path(sys.argv[2])
publication.MISE = str(home / 'hanging-mise')
deadline = 60 if sys.argv[4] == 'interrupt' else 1
r2_publication.TRANSPORT_TIMEOUTS = dict.fromkeys(('inspect', 'objects', 'publish'), deadline)
owner = publication.Publisher()
active = r2_publication.R2Publisher(owner, {'vaultRoot': str(home / 'vault'), 'configPath': str(home / 's3.json')})
try:
    with owner.locked():
        active.transport(sys.argv[3])
except RuntimeError as error:
    (home / 'result.json').write_text(json.dumps({'error': str(error)}))
"""
            env = dict(os.environ, PUBLISH_STATE_DIR=str(home / 'state'), PUBLISH_REPO=str(home / 'repo'), PUBLISH_VAULT_PUBLIC=str(home / 'public'))
            process = subprocess.Popen([sys.executable, '-B', '-c', harness, str(ROOT / 'scripts'), str(home), action, 'interrupt' if interrupt else 'timeout'], env=env, start_new_session=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            timed_out = False
            try:
                if interrupt:
                    deadline = time.monotonic() + 3
                    while not (home / 'descendant.pid').exists() and time.monotonic() < deadline:
                        time.sleep(0.02)
                    self.assertTrue((home / 'descendant.pid').exists(), 'fixture did not launch the descendant')
                    os.kill(process.pid, signal.SIGINT)
                try:
                    stdout, stderr = process.communicate(timeout=5)
                except subprocess.TimeoutExpired:
                    timed_out = True
                    os.killpg(process.pid, signal.SIGKILL)
                    stdout, stderr = process.communicate(timeout=5)
                self.assertFalse(timed_out, 'transport kept the common publication lock beyond its deadline')
                if interrupt:
                    self.assertNotEqual(process.returncode, 0, stdout + stderr)
                    self.assertIn('KeyboardInterrupt', stderr)
                else:
                    self.assertEqual(process.returncode, 0, stdout + stderr)
                    result = json.loads((home / 'result.json').read_text())
                    self.assertIn(action, result['error'])
                    self.assertIn('timed out', result['error'])
                self.assertTrue((home / 'descendant.pid').exists(), 'fixture did not launch the descendant')
                for name in ('transport.pid', 'descendant.pid'):
                    pid = (home / name).read_text()
                    state = subprocess.run(['ps', '-o', 'stat=', '-p', pid], capture_output=True, text=True, check=False).stdout.strip()
                    self.assertTrue(not state or state.startswith('Z'), f'{name} still executes after lock release: {state}')
                heartbeat = (home / 'heartbeat').read_bytes()
                time.sleep(0.15)
                self.assertEqual((home / 'heartbeat').read_bytes(), heartbeat)
                with (home / 'state/host.lock').open('a') as lock:
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            finally:
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGKILL)
                for name in ('transport.pid', 'descendant.pid'):
                    if (home / name).exists():
                        try:
                            os.kill(int((home / name).read_text()), signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                process.communicate(timeout=5)


if __name__ == '__main__':
    unittest.main()
