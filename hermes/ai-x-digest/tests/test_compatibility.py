from pathlib import Path
import hashlib
import importlib.util
import io
from contextlib import redirect_stdout
from unittest.mock import patch
import json
import subprocess
import sys
import tempfile
import unittest

import test_publishing as publishing

PACKAGE = Path(__file__).resolve().parents[1]
ROOT = PACKAGE.parents[1]
FIXTURES = ROOT / 'apps/daily/tests/fixtures'
VERIFY = PACKAGE / 'runtime/skills/note-taking/obsidian/scripts/verify-x-ai-digest-format.py'
SCRIPT = 'skills/note-taking/obsidian/scripts/'


class CompatibilityTest(unittest.TestCase):
    def test_v2_four_stories_and_quiet_day(self):
        for source in ('editorial-v2-four-stories.md', 'editorial-v2-brief-archive.md'):
            with self.subTest(source=source), tempfile.TemporaryDirectory() as tmp:
                vault = Path(tmp)
                text = (FIXTURES / source).read_text()
                day = '2026-10-16' if 'archive' in source else '2026-10-15'
                text += '\n- [[digests/x-ai-2026|X-AI 2026]]\n- [[digests/x-ai-2026-10|X-AI-2026-10]]\n'
                folder = vault / 'public/digests'
                folder.mkdir(parents=True)
                (folder / f'x-ai-{day}.md').write_text(text)
                result = subprocess.run([sys.executable, str(VERIFY), str(vault), '--digest-dir', str(vault / 'public/digests')], text=True, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_v2_one_lead_with_reference_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            text = (FIXTURES / 'editorial-v2-four-stories.md').read_text()
            text = text.split('## Hang Huang')[0] + '## Navigation' + text.split('## Navigation')[1]
            text = text.replace("[Anthropic's migration announcement](https://x.com/AnthropicAI/status/2110047081414987957)", "[Anthropic's migration announcement][migration]")
            text += '\n[migration]: https://x.com/AnthropicAI/status/2110047081414987957\n'
            folder = Path(tmp) / 'public/digests'
            folder.mkdir(parents=True)
            (folder / 'x-ai-2026-10-15.md').write_text(text)
            result = subprocess.run([sys.executable, str(VERIFY), tmp, '--digest-dir', str(Path(tmp) / 'public/digests')], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_verifier_phase_packages_canonical_identity_before_producer(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            producer = home / 'skills/note-taking/ai-x-digest/SKILL.md'
            producer.parent.mkdir(parents=True)
            producer.write_text('existing editorial-v1 producer')
            sibling = home / 'skills/unrelated/SKILL.md'
            sibling.parent.mkdir(parents=True)
            sibling.write_text('preserve me')
            result = subprocess.run([sys.executable, str(PACKAGE / 'install.py'), '--hermes-home', str(home), '--phase', 'verifier'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(producer.read_text(), 'existing editorial-v1 producer')
            self.assertEqual(sibling.read_text(), 'preserve me')
            self.assertEqual((home / SCRIPT / 'story_identity.py').read_bytes(), (PACKAGE / 'story_identity.py').read_bytes())
            with tempfile.TemporaryDirectory() as staged:
                folder = Path(staged) / 'public/digests'
                folder.mkdir(parents=True)
                (folder / 'x-ai-2026-10-15.md').write_bytes((FIXTURES / 'editorial-v2-four-stories.md').read_bytes())
                verified = subprocess.run([sys.executable, str(home / SCRIPT / 'verify-x-ai-digest-format.py'), staged, '--digest-dir', str(Path(staged) / 'public/digests')], capture_output=True, text=True)
                self.assertEqual(verified.returncode, 0, verified.stdout + verified.stderr)


    def test_installed_checker_runs_at_every_replacement_boundary(self):
        spec = importlib.util.spec_from_file_location('boundary_install', PACKAGE / 'install.py')
        installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer)
        for phase in ('verifier', 'producer'):
            with self.subTest(phase=phase), tempfile.TemporaryDirectory() as tmp:
                home = Path(tmp) / 'home'
                home.mkdir()
                vault = Path(tmp) / 'vault'
                folder = vault / 'public/digests'
                folder.mkdir(parents=True)
                (folder / 'x-ai-2026-10-15.md').write_bytes((FIXTURES / 'editorial-v2-four-stories.md').read_bytes())
                original = Path.replace
                checks = []
                def replace_and_probe(source, target):
                    result = original(source, target)
                    checker = home / SCRIPT / 'verify-x-ai-digest-format.py'
                    if checker.exists():
                        probe = subprocess.run([sys.executable, str(checker), str(vault), '--digest-dir', str(vault / 'public/digests')], capture_output=True, text=True)
                        checks.append((str(target), probe.returncode, probe.stderr + probe.stdout))
                    return result
                with patch('sys.argv', ['install.py', '--hermes-home', str(home), '--phase', phase]), patch.object(Path, 'replace', replace_and_probe), redirect_stdout(io.StringIO()):
                    installer.main()
                self.assertTrue(checks)
                self.assertTrue(all(code == 0 for _, code, _ in checks), checks)

    def test_verifier_phase_rolls_back_without_replacing_producer(self):
        spec = importlib.util.spec_from_file_location('compat_install', PACKAGE / 'install.py')
        installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer)
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            checker = home / SCRIPT / 'verify-x-ai-digest-format.py'
            checker.parent.mkdir(parents=True)
            checker.write_text('old dual checker')
            producer = home / 'skills/note-taking/ai-x-digest/SKILL.md'
            producer.parent.mkdir(parents=True)
            producer.write_text('old producer')
            original = Path.replace
            count = 0
            def fail_helper(source, target):
                nonlocal count
                count += 1
                if count == 2:
                    raise OSError('fixture helper replacement failure')
                return original(source, target)
            with patch('sys.argv', ['install.py', '--hermes-home', str(home), '--phase', 'verifier']), patch.object(Path, 'replace', fail_helper):
                with self.assertRaises(OSError):
                    installer.main()
            self.assertEqual(checker.read_text(), 'old dual checker')
            self.assertEqual(producer.read_text(), 'old producer')
            self.assertFalse((home / SCRIPT / 'story_identity.py').exists())
            self.assertEqual(json.loads(next(home.glob('backups/*/receipt.json')).read_text())['status'], 'rolled-back')

    def test_v2_archive_requires_its_own_visible_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / 'public/digests'
            folder.mkdir(parents=True)
            text = (FIXTURES / 'editorial-v2-brief-archive.md').read_text()
            text = text.replace('[Original benchmark report](https://example.com/benchmark)', 'Original benchmark report')
            text += '\n- [[digests/x-ai-2026|X-AI 2026]]\n- [[digests/x-ai-2026-10|X-AI-2026-10]]\n'
            (folder / 'x-ai-2026-10-16.md').write_text(text)
            result = subprocess.run([sys.executable, str(VERIFY), tmp, '--digest-dir', str(Path(tmp) / 'public/digests')], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('missing adjacent HTTPS source', result.stdout)

class V2PublishingTest(unittest.TestCase):
    setUp = publishing.PublishingTest.setUp
    git = publishing.PublishingTest.git
    cli = publishing.PublishingTest.cli
    publish = publishing.PublishingTest.publish
    receipt = publishing.PublishingTest.receipt

    def candidate(self, data):
        self.staged.write_bytes(data)
        request = json.loads(self.request.read_text())
        entry = request['files']['digests/x-ai-2026-10-15.md']
        entry['staged_sha256'] = hashlib.sha256(data).hexdigest()
        self.request.write_text(json.dumps(request))

    def test_actual_v2_publication_and_retry_reuses_identity(self):
        self.candidate((FIXTURES / 'editorial-v2-four-stories.md').read_bytes())
        result = self.publish()
        self.assertEqual(result.returncode, 0, result.stderr)
        accepted = json.loads(result.stdout)['commit']
        self.assertEqual((self.vault / 'digests/x-ai-2026-10-15.md').read_bytes(), self.staged.read_bytes())
        self.assertEqual(json.loads(self.publish().stdout)['commit'], accepted)
        self.assertEqual(self.git('rev-list', '--count', 'HEAD'), '2')
        self.assertEqual(self.receipt()['phase'], 'readerpending')

    def test_missing_id_and_mutated_published_id_never_promote(self):
        identified = (FIXTURES / 'editorial-v2-four-stories.md').read_bytes()
        self.candidate(identified.replace(b'<!-- story-id: anthropic-monorepo -->', b''))
        result = self.publish()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.git('rev-parse', 'HEAD'), self.head)
        for base in (self.vault, self.repo / 'content'):
            self.assertEqual((base / 'digests/x-ai-2026-10-15.md').read_bytes(), self.old)
        self.candidate(identified)
        result = self.publish()
        self.assertEqual(result.returncode, 0, result.stderr)
        accepted = self.git('rev-parse', 'HEAD')
        request = json.loads(self.request.read_text())
        request['expected_head'] = accepted
        request['files']['digests/x-ai-2026-10-15.md']['before_sha256'] = hashlib.sha256(identified).hexdigest()
        self.request.write_text(json.dumps(request))
        self.candidate(identified.replace(b'story-id: anthropic-monorepo', b'story-id: changed-headline'))
        result = self.publish()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('removed story-id', result.stderr)
        self.assertEqual(self.git('rev-parse', 'HEAD'), accepted)
        for base in (self.vault, self.repo / 'content'):
            self.assertEqual((base / 'digests/x-ai-2026-10-15.md').read_bytes(), identified)


class CronCompatibilityTest(unittest.TestCase):
    @unittest.skipUnless(Path('/Users/skypawalker/.hermes/hermes-agent/hermes_cli/subcommands/cron.py').exists() and Path('/Users/skypawalker/.hermes/hermes-agent/venv/bin/python').exists(), 'requires Pluto Hermes CLI source; never touches live cron')
    def test_supported_cron_edit_preserves_job_fields_and_other_jobs(self):
        code = r'''import argparse
import copy
import json
import sys
import types
from unittest.mock import patch
sys.path.insert(0, '/Users/skypawalker/.hermes/hermes-agent')
from hermes_cli.subcommands.cron import build_cron_parser
from hermes_cli import cron
parser = argparse.ArgumentParser()
build_cron_parser(parser.add_subparsers(), cmd_cron=lambda args: None)
prompt = open(sys.argv[1]).read()
args = parser.parse_args(['cron', 'edit', '4eb8e806b8bc', '--prompt', prompt, '--add-skill', 'ai-x-digest', '--add-skill', 'obsidian', '--add-skill', 'bird', '--add-skill', 'unslop'])
jobs = [dict(id='4eb8e806b8bc', job_id='4eb8e806b8bc', name='daily-ai-x-digest-to-obsidian', skill='ai-x-digest', skills=['ai-x-digest', 'obsidian', 'bird'], schedule='0 8 * * *', timezone='Asia/Kolkata', enabled=False, paused_reason='fixture', model=None, model_provider=None, deliver='telegram', delivery_target='fixture-chat'), dict(id='other', prompt='preserve the other job')]
before = copy.deepcopy(jobs)
fake = types.ModuleType('cron.jobs')
fake.AmbiguousJobReference = ValueError
fake.resolve_job_ref = lambda job_id: jobs[0] if job_id == jobs[0]['id'] else None
calls = []
def update(**kwargs):
    calls.append(kwargs)
    for key, value in kwargs.items():
        if key not in ('action', 'job_id') and value is not None:
            jobs[0][key] = value
    return dict(success=True, job=jobs[0])
with patch.dict(sys.modules, {'cron.jobs': fake}), patch.object(cron, '_cron_api', update):
    assert cron.cron_edit(args) == 0
expected = copy.deepcopy(before)
expected[0]['prompt'] = prompt
expected[0]['skills'].append('unslop')
assert jobs == expected, (jobs, expected)
assert {k for k, v in calls[0].items() if v is not None} == {'action', 'job_id', 'prompt', 'skills'}
print('Only the fixture prompt and skills changed. No live jobs or Telegram calls.')
'''
        result = subprocess.run(['/Users/skypawalker/.hermes/hermes-agent/venv/bin/python', '-B', '-c', code, str(PACKAGE / 'cron-prompt.md')], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
