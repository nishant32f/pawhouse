from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


VERIFY = Path(__file__).resolve().parents[1] / "runtime/skills/note-taking/obsidian/scripts/verify-x-ai-digest-format.py"


def edition(stories, version="editorial-v1", intro=""):
    return f'''---
title: "X-AI-2026-10-15"
date: 2026-10-15
tags: [AI, digest, x]
type: daily-digest
source: bird-cli-json
digest_format: {version}
---

{intro}{stories}

## Navigation

- Previous: [[digests/x-ai-2026-10-14|X-AI-2026-10-14]]
- Next: None

## Backlinks

- [[index|Mindscape]]
- [[digests/x-ai-2026|X-AI 2026]]
- [[digests/x-ai-2026-10|X-AI-2026-10]]
'''


STORY = '''## A developer tests how hook arguments execute

A developer tested argument rewriting in a command hook and reported that one output shape left the original command unchanged. The report covers a limited set of versions and tools.

The developer compared the command requested by the agent with the command that actually ran. The mismatch is a reported test result. It does not show that every hook type or interactive session has the same behavior.

For workflows that depend on rewriting arguments, the result gives a specific behavior to check. A harmless command can expose whether the expected substitution reaches execution. The post provides no evidence about other tools or later releases.

Source: [Developer's test report](https://example.com/hook-report). Community report.
'''


class EditorialFormatTest(unittest.TestCase):
    def verify(self, text):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            folder = vault / "public/digests"
            folder.mkdir(parents=True)
            (folder / "x-ai-2026-10-15.md").write_text(text)
            return subprocess.run([sys.executable, str(VERIFY), str(vault)], text=True, capture_output=True)

    def test_editorial_edition_needs_no_duplicate_h1_or_takeaway(self):
        result = self.verify(edition(STORY))
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_legacy_edition_still_passes(self):
        legacy = edition("## Digest\n\n### Existing theme\n\nOriginal content.\n\n**Practical takeaway:** Original advice.")
        legacy = legacy.replace("digest_format: editorial-v1\n", "").replace("## Digest", "# X-AI-2026-10-15\n\n## Digest", 1)
        self.assertEqual(self.verify(legacy).returncode, 0)

    def test_unknown_format_fails(self):
        result = self.verify(edition(STORY, "editorial-v99"))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unsupported digest_format", result.stdout)

    def test_sources_must_be_beside_each_story(self):
        without_source = STORY.split("\nSource:")[0]
        result = self.verify(edition(without_source + "\n\n## Source provenance\n\n[Report](https://example.com/report)"))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("source", result.stdout.lower())

    def test_old_padding_and_duplicate_title_fail(self):
        for extra in ("# X-AI-2026-10-15\n\n", "Signal quality: strong today.\n\n", "**Practical takeaway:** Try a tool.\n\n"):
            with self.subTest(extra=extra):
                self.assertNotEqual(self.verify(edition(STORY, intro=extra)).returncode, 0)

    def test_filler_story_count_is_rejected(self):
        stories = "\n\n".join(STORY.replace("A developer", f"Developer {i}", 1) for i in range(6))
        result = self.verify(edition(stories))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("story count", result.stdout)

    def test_quiet_day_with_one_story_and_optional_brief_passes(self):
        brief = """\n\n## In brief

### Another developer publishes a small test

A second developer shared a short test of the same workflow. The post provides the input and the observed output. It does not compare performance with other tools or claim that the result applies outside that test.

Source: [Test details](https://example.com/brief). Community report.
"""
        result = self.verify(edition(STORY + brief))
        self.assertEqual(result.returncode, 0, result.stdout)


if __name__ == "__main__":
    unittest.main()
