from pathlib import Path
import hashlib
import json
import re
import unittest

import test_publishing as publishing
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from story_identity import parse_edition


class ArchiveSourcesTest(unittest.TestCase):
    setUp = publishing.PublishingTest.setUp
    git = publishing.PublishingTest.git
    cli = publishing.PublishingTest.cli
    publish = publishing.PublishingTest.publish

    def identified_base(self):
        text = (publishing.ROOT / 'apps/daily/tests/fixtures/editorial-v2-four-stories.md').read_text()
        match = re.search(r"\[Anthropic's migration announcement\]\((https://[^)]+)\)", text)
        self.assertIsNotNone(match)
        self.source = match[1]
        text = text.replace(match[0], "[Anthropic's migration announcement][archive-source]")
        text += f"\n[archive-source]: {self.source}\n"
        self.old = text.encode()
        for base in (self.vault, self.repo / 'content'):
            (base / 'digests/x-ai-2026-10-15.md').write_bytes(self.old)
        self.git('add', 'content/digests/x-ai-2026-10-15.md')
        self.git('commit', '-m', 'Accepted identified source fixture')
        self.head = self.git('rev-parse', 'HEAD')
        return text

    def archived(self, text):
        story = parse_edition(text).stories[0]
        first = text.index('## ' + story.headline)
        following = text.index('\n## ', first + 1)
        result = text[:first] + text[following + 1:]
        block = f"## Archived stories\n\n### {story.headline}\n<!-- story-id: {story.story_id} -->\n\nCorrection: Retained for the fixture correction.\n\n{story.body}\n\n"
        return result.replace('## Navigation', block + '## Navigation', 1)

    def candidate(self, text):
        self.staged.write_text(text)
        request = json.loads(self.request.read_text())
        request['expected_head'] = self.git('rev-parse', 'HEAD')
        entry = request['files']['digests/x-ai-2026-10-15.md']
        entry['before_sha256'] = hashlib.sha256((self.vault / 'digests/x-ai-2026-10-15.md').read_bytes()).hexdigest()
        entry['staged_sha256'] = hashlib.sha256(self.staged.read_bytes()).hexdigest()
        self.request.write_text(json.dumps(request))

    def assert_rejected_untouched(self, text, previous):
        head = self.git('rev-parse', 'HEAD')
        self.candidate(text)
        result = self.publish()
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn('archived sources', result.stderr)
        self.assertEqual(self.git('rev-parse', 'HEAD'), head)
        self.assertEqual(self.git('status', '--porcelain'), '')
        for base in (self.vault, self.repo / 'content'):
            self.assertEqual((base / 'digests/x-ai-2026-10-15.md').read_bytes(), previous)

    def test_archiving_rejects_changed_external_reference_before_promotion(self):
        original = self.identified_base()
        candidate = self.archived(original).replace('[archive-source]: ' + self.source, '[archive-source]: https://example.com/replacement')
        self.assert_rejected_untouched(candidate, self.old)

    def test_existing_archive_rejects_reference_target_change(self):
        original = self.identified_base()
        archived = self.archived(original)
        self.candidate(archived)
        result = self.publish()
        self.assertEqual(result.returncode, 0, result.stderr)
        revised = archived.replace('[archive-source]: ' + self.source, '[archive-source]: https://example.com/replacement')
        self.assert_rejected_untouched(revised, archived.encode())

    def test_unchanged_archive_sources_allow_active_source_edits(self):
        original = self.identified_base()
        candidate = self.archived(original)
        active_url = re.search(r'https://x.com/hanghuang_/[^)\s]+', candidate)[0]
        candidate = candidate.replace(active_url, 'https://example.com/corrected-active-source')
        self.candidate(candidate)
        result = self.publish()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.vault / 'digests/x-ai-2026-10-15.md').read_text(), candidate)


if __name__ == '__main__':
    unittest.main()
