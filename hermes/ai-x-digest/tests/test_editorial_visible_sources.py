import unittest

import test_editorial_format as fixtures


class EditorialEdgeTest(unittest.TestCase):
    def test_link_rendered_as_code_is_not_a_source_citation(self):
        original = "[Developer's test report](https://example.com/hook-report)"
        for hidden in ('`' + original + '`', '<!-- ' + original + ' -->', '!' + original, '```md\n' + original + '\n```'):
            with self.subTest(hidden=hidden):
                story = fixtures.STORY.replace(original, hidden)
                result = fixtures.EditorialFormatTest().verify(fixtures.edition(story))
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertIn('missing adjacent HTTPS source link', result.stdout)

    def test_link_with_code_in_its_label_is_still_a_source(self):
        story = fixtures.STORY.replace("Developer's test report", "`README.md`")
        result = fixtures.EditorialFormatTest().verify(fixtures.edition(story))
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_fenced_shell_comment_does_not_become_a_page_title(self):
        story = fixtures.STORY.replace("\nSource:", "\n```sh\n# A shell comment\necho hello\n```\n\nSource:")
        result = fixtures.EditorialFormatTest().verify(fixtures.edition(story))
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_case_variant_of_reserved_heading_is_rejected(self):
        brief = '''

## In Brief

### A short reported development

A developer shares another small test of command rewriting with an example input and an observed result.

Source: [Report](https://example.com/brief).
'''
        result = fixtures.EditorialFormatTest().verify(fixtures.edition(fixtures.STORY + brief))
        self.assertNotEqual(result.returncode, 0, result.stdout)


if __name__ == '__main__':
    unittest.main()
