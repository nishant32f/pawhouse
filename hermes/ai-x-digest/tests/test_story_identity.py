from pathlib import Path
import re
import sys
import unittest


PACKAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE))
from story_identity import IdentityError, parse_edition, validate_revision


FIXTURES = PACKAGE.parents[1] / "apps/daily/tests/fixtures"


def fixture(name):
    return (FIXTURES / name).read_text(encoding="utf-8")


def edition(stories):
    return "---\ndigest_format: editorial-v2\n---\n\n" + stories + "\n\n## Navigation\n\n- Next: None\n\n## Backlinks\n\n- [[index|Mindscape]]\n"


def story(headline="Original headline", story_id="original-id", body="Original prose.\n\nSource: [Report](https://example.com/report).", level=2):
    return f'{"#" * level} {headline}\n<!-- story-id: {story_id} -->\n\n{body}'


class StoryIdentityTest(unittest.TestCase):
    def test_four_story_fixture_changes_only_version_and_id_markers(self):
        current = fixture("editorial-v2-four-stories.md")
        original = fixture("editorial-v1.md")
        restored = re.sub(r"^<!-- story-id: [a-z0-9-]+ -->\n", "", current, flags=re.M)
        self.assertEqual(restored.replace("digest_format: editorial-v2", "digest_format: editorial-v1"), original)
        parsed = parse_edition(current)
        self.assertEqual([item.story_id for item in parsed.stories], ["anthropic-monorepo", "cloud-computers", "gloss-x-import", "claude-code-hooks"])
        self.assertEqual(parsed.lead.story_id, "anthropic-monorepo")
        self.assertEqual(parsed.original_text, current)

    def test_headline_edit_and_reorder_preserve_identity(self):
        old = edition(story() + "\n\n" + story("Second headline", "second-id"))
        revised = edition(story("Renamed second headline", "second-id") + "\n\n" + story("Renamed first headline"))
        parsed = validate_revision(old, revised)
        self.assertEqual([item.story_id for item in parsed.active_stories], ["second-id", "original-id"])
        self.assertEqual(parsed.lead.story_id, "second-id")

    def test_legacy_editions_remain_unsplit_and_unchanged(self):
        for name in ("legacy-unversioned.md", "editorial-v1.md"):
            with self.subTest(name=name):
                text = fixture(name)
                parsed = parse_edition(text)
                self.assertEqual(parsed.original_text, text)
                self.assertEqual(parsed.stories, ())
                self.assertIsNone(parsed.lead)

    def test_missing_duplicate_and_unsafe_ids_fail(self):
        cases = [story().replace("<!-- story-id: original-id -->\n", ""), story() + "\n\n" + story("Other headline")]
        cases.extend(story(story_id=value) for value in ("../escape", "Uppercase", "under_score", "two--hyphens", "éclair", "bad/id", "", "-leading"))
        for text in cases:
            with self.subTest(text=text):
                with self.assertRaises(IdentityError):
                    parse_edition(edition(text))

    def test_marker_must_immediately_follow_its_heading(self):
        for text in (story().replace("\n<!--", "\n\n<!--", 1), story() + "\n<!-- story-id: extra-id -->"):
            with self.subTest(text=text):
                with self.assertRaises(IdentityError):
                    parse_edition(edition(text))

    def test_furniture_has_no_story_ids(self):
        parsed = parse_edition(edition(story()))
        self.assertEqual(len(parsed.stories), 1)
        for heading in ("Navigation", "Backlinks"):
            with self.subTest(heading=heading):
                text = edition(story()).replace("## " + heading, "## " + heading + "\n<!-- story-id: furniture -->")
                with self.assertRaises(IdentityError):
                    parse_edition(text)

    def test_briefs_and_archives_have_routes_but_only_active_items_navigate(self):
        parsed = parse_edition(fixture("editorial-v2-brief-archive.md"))
        self.assertEqual([(item.story_id, item.kind) for item in parsed.stories], [("reproducible-test", "story"), ("import-limit", "brief"), ("vendor-benchmark", "archived")])
        self.assertEqual([item.story_id for item in parsed.active_stories], ["reproducible-test", "import-limit"])
        self.assertEqual(parsed.archived_stories[0].story_id, "vendor-benchmark")
        self.assertIn("withdrew", parsed.archived_stories[0].correction)
        self.assertNotIn("Correction:", parsed.archived_stories[0].body)

    def test_removal_requires_archive_with_correction_and_original_prose(self):
        old = edition(story() + "\n\n" + story("Second headline", "second-id"))
        removed = edition(story("Second headline", "second-id"))
        with self.assertRaisesRegex(IdentityError, "original-id"):
            validate_revision(old, removed)
        archived = removed.replace("## Navigation", "## Archived stories\n\n" + story(level=3, body="Correction: This report was withdrawn.\n\nOriginal prose.\n\nSource: [Report](https://example.com/report).") + "\n\n## Navigation")
        self.assertEqual(validate_revision(old, archived).archived_stories[0].story_id, "original-id")
        with self.assertRaisesRegex(IdentityError, "prose"):
            validate_revision(old, archived.replace("Original prose.", "Rewritten archived prose."))
        with self.assertRaises(IdentityError):
            parse_edition(archived.replace("Correction: This report was withdrawn.\n\n", ""))

    def test_archived_id_cannot_disappear_in_later_revision(self):
        old = fixture("editorial-v2-brief-archive.md")
        start, rest = old.split("## Archived stories\n", 1)
        revised = start + "## Navigation\n" + rest.split("## Navigation\n", 1)[1]
        with self.assertRaisesRegex(IdentityError, "vendor-benchmark"):
            validate_revision(old, revised)

    def test_legacy_adoption_keeps_edition_text_and_sources(self):
        parsed = validate_revision(fixture("editorial-v1.md"), fixture("editorial-v2-four-stories.md"))
        self.assertEqual(len(parsed.active_stories), 4)
        with self.assertRaisesRegex(IdentityError, "downgrade"):
            validate_revision(fixture("editorial-v2-four-stories.md"), fixture("editorial-v1.md"))

    def test_reserved_headings_and_section_shapes_are_explicit(self):
        cases = [edition(story()).replace("## Navigation", "## navigation"), edition(story()).replace("## Backlinks", "## In brief"), edition("## In brief\n\n" + story(level=3)), edition(story() + "\n\n## In brief\n\n" + story(story_id="brief-id")), edition(story() + "\n\n" + story(level=3, story_id="uncontained-brief"))]
        for text in cases:
            with self.subTest(text=text):
                with self.assertRaises(IdentityError):
                    parse_edition(text)

    def test_lead_starts_edition_and_archive_ends_content(self):
        brief_first = edition("## In brief\n\n" + story(story_id="brief-id", level=3) + "\n\n" + story())
        archive = "## Archived stories\n\n" + story(story_id="archived-id", level=3, body="Correction: Withdrawn.\n\nRetained prose.")
        archive_first = edition(archive + "\n\n" + story())
        story_after_archive = edition(story() + "\n\n" + archive + "\n\n" + story(story_id="late-story"))
        brief_after_archive = edition(story() + "\n\n" + archive + "\n\n## In brief\n\n" + story(story_id="late-brief", level=3))
        for text in (brief_first, archive_first, story_after_archive, brief_after_archive):
            with self.subTest(text=text):
                with self.assertRaises(IdentityError):
                    parse_edition(text)

    def test_fenced_examples_do_not_add_headings_or_ids(self):
        body = "Original prose.\n\n```md\n## Example\n<!-- story-id: duplicate-id -->\n```\n\nSource: [Report](https://example.com/report)."
        parsed = parse_edition(edition(story(body=body)))
        self.assertEqual([item.story_id for item in parsed.stories], ["original-id"])
        self.assertIn("## Example", parsed.stories[0].body)

    def test_unknown_formats_and_non_editions_fail(self):
        for text in (edition(story()).replace("editorial-v2", "editorial-v99"), fixture("no-news.txt"), fixture("collection-error.txt")):
            with self.subTest(text=text):
                with self.assertRaises(IdentityError):
                    parse_edition(text)


if __name__ == "__main__":
    unittest.main()
