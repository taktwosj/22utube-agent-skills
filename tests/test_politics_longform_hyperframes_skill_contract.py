import hashlib
import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "112-politics-longform-hyperframes"
TEMPLATE = SKILL / "assets" / "templates" / "politics-longform-template-v1"


class PoliticsLongformHyperframesSkillContractTest(unittest.TestCase):
    def test_skill_is_managed_and_bundles_the_locked_template(self):
        manifest = json.loads(
            (ROOT / "manifests" / "skill-set.json").read_text(encoding="utf-8")
        )
        managed = {item["name"]: item for item in manifest["skills"]}

        self.assertIn("112-politics-longform-hyperframes", managed)
        self.assertTrue(managed["112-politics-longform-hyperframes"]["enabled"])
        self.assertEqual(
            ["codex", "claude", "hermes"],
            managed["112-politics-longform-hyperframes"]["targets"],
        )
        self.assertTrue((SKILL / "SKILL.md").is_file())
        self.assertTrue((SKILL / "scripts" / "validate_template.py").is_file())
        self.assertTrue((SKILL / "references" / "template-contract.md").is_file())
        self.assertTrue((SKILL / "references" / "template-v1-handoff.md").is_file())
        self.assertTrue((TEMPLATE / "template_lock.json").is_file())
        self.assertIn(
            "112-politics-longform-hyperframes",
            (ROOT / "README.md").read_text(encoding="utf-8"),
        )

    def test_skill_routes_to_the_bundled_template(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn(
            "assets/templates/politics-longform-template-v1",
            text.replace("\\", "/"),
        )
        self.assertIn("CapCut fallback=FORBIDDEN", text)

    def test_template_lock_hashes_match_every_bundled_file(self):
        lock = json.loads((TEMPLATE / "template_lock.json").read_text(encoding="utf-8"))
        self.assertEqual("TEMPLATE_V1_LOCKED", lock["status"])
        self.assertTrue(lock["hashes_valid"])
        for relative_path, expected_digest in lock["files"].items():
            path = TEMPLATE / relative_path
            self.assertTrue(path.is_file(), relative_path)
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(expected_digest, digest, relative_path)

    def test_bundle_contains_only_placeholder_av_media(self):
        av_files = sorted(
            path.relative_to(TEMPLATE).as_posix()
            for path in TEMPLATE.rglob("*")
            if path.is_file() and path.suffix.lower() in {".mp4", ".wav", ".srt"}
        )
        self.assertEqual(
            [
                "assets/audio/source-placeholder.wav",
                "assets/media/source-placeholder.mp4",
            ],
            av_files,
        )

    def test_required_template_assets_are_not_gitignored(self):
        required = [
            TEMPLATE / "style_tokens.json",
            TEMPLATE / "assets" / "audio" / "source-placeholder.wav",
            TEMPLATE / "assets" / "media" / "source-placeholder.mp4",
            TEMPLATE / "evidence" / "first-frame-at-0s.png",
            TEMPLATE / "evidence" / "template-v1-approved.png",
        ]
        for path in required:
            relative_path = path.relative_to(ROOT).as_posix()
            result = subprocess.run(
                ["git", "check-ignore", "--quiet", "--", relative_path],
                cwd=ROOT,
                check=False,
            )
            self.assertEqual(1, result.returncode, relative_path)

    def test_locked_web_text_assets_enforce_lf_checkout(self):
        for path in [
            TEMPLATE / "index.html",
            TEMPLATE / "fonts.css",
            TEMPLATE / "src" / "styles.css",
            TEMPLATE / "src" / "template.js",
            TEMPLATE / "compositions" / "source-video.html",
        ]:
            relative_path = path.relative_to(ROOT).as_posix()
            result = subprocess.run(
                ["git", "check-attr", "eol", "--", relative_path],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertTrue(result.stdout.rstrip().endswith(": eol: lf"), result.stdout)


if __name__ == "__main__":
    unittest.main()
