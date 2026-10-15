import unittest

import test_editorial_format as fixtures


class SourceAdjacencyTest(unittest.TestCase):
    def test_one_sourced_story_does_not_cover_another_story(self):
        second = fixtures.STORY.replace('A developer tests how hook arguments execute',
                               'A second developer checks the same command')
        second = second.split('\nSource:')[0]
        result = fixtures.EditorialFormatTest().verify(fixtures.edition(fixtures.STORY + '\n\n' + second))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('missing adjacent HTTPS source link', result.stdout)
        self.assertNotIn('legacy boilerplate', result.stdout)


if __name__ == '__main__':
    unittest.main()
