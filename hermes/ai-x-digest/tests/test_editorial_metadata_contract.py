from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest


PACKAGE = Path(__file__).resolve().parents[1]
PRODUCER = PACKAGE / "runtime/skills/note-taking/ai-x-digest/SKILL.md"
VERIFY = PACKAGE / "runtime/skills/note-taking/obsidian/scripts/verify-x-ai-digest-format.py"


class EditorialMetadataContractTest(unittest.TestCase):
    def test_documented_metadata_edition_passes_packaged_checker(self):
        examples = re.findall(r"```markdown\n(---\n.*?)\n```", PRODUCER.read_text(), re.S)
        self.assertEqual(len(examples), 1, "The producer needs one complete authored edition example")
        example = examples[0]
        self.assertIn("\nstory_metadata:\n", example)
        example = example.replace("YYYY-MM-DD", "2026-10-15").replace("YYYY-MM", "2026-10").replace("YYYY", "2026")
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "public/digests"
            folder.mkdir(parents=True)
            (folder / "x-ai-2026-10-15.md").write_text(example)
            result = subprocess.run([sys.executable, str(VERIFY), tmp, '--digest-dir', str(Path(tmp) / 'public/digests')], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
