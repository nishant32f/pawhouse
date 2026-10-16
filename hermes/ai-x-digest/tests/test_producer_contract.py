from pathlib import Path
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest

PACKAGE = Path(__file__).resolve().parents[1]
ROOT = PACKAGE.parents[1]
CHECKER = PACKAGE / "runtime/skills/note-taking/obsidian/scripts/verify-x-ai-digest-format.py"


class ProducerContractTest(unittest.TestCase):
    def test_checker_defaults_to_private_sources_and_supports_explicit_legacy_directory(self):
        fixture = (ROOT / "apps/daily/tests/fixtures/editorial-v1.md").read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            for relative in ("digests", "public/digests"):
                folder = vault / relative
                folder.mkdir(parents=True)
                (folder / "x-ai-2026-10-15.md").write_bytes(fixture)
            (vault / "public/digests/x-ai-2026-10-15.md").write_text("invalid public candidate")
            result = subprocess.run([sys.executable, str(CHECKER), str(vault)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            (vault / "public/digests/x-ai-2026-10-15.md").write_bytes(fixture)
            result = subprocess.run([sys.executable, str(CHECKER), str(vault), "--digest-dir", str(vault / "public/digests")], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_runtime_manifest_hashes_cover_every_owned_file(self):
        manifest = json.loads((PACKAGE / "runtime-manifest.json").read_text())
        for relative in manifest["files"]:
            source = PACKAGE / manifest.get("sources", {}).get(relative, "runtime/" + relative)
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), manifest["sha256"][relative], relative)
        self.assertEqual(len(manifest["files"]), 11)
        text = "\n".join((PACKAGE / "runtime" / relative).read_text() for relative in manifest["files"] if relative.endswith(".md"))
        self.assertNotIn("public/digests/", text)
        self.assertNotIn("release-daily-from-pluto.py", text)
        self.assertIn("last seven published accepted editions", text)
        self.assertIn("reader-release.json", text)
        self.assertIn("140 to 200", text)
        self.assertIn("70 to 120", text)
        self.assertIn("25 to 45", text)


if __name__ == "__main__":
    unittest.main()
