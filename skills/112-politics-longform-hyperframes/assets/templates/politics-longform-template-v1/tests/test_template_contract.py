import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMPOSITIONS = (
    "narration-explainer",
    "source-video",
    "chapter-transition",
)
ROLES = (
    "top-frame",
    "bottom-frame",
    "focus-lines",
    "chapter-number",
    "chapter-title",
    "source-label",
    "source-date",
    "comment-label",
    "subscribe-label",
    "lower-caption-band",
    "caption-text",
)
TOKEN_GROUPS = (
    "canvas",
    "safeArea",
    "frame",
    "focusLines",
    "chapter",
    "source",
    "comment",
    "subscribe",
    "captionBand",
    "captionText",
    "animation",
    "zIndex",
)


class TemplateContract(unittest.TestCase):
    def test_required_project_files_exist(self):
        for relative in (
            "hyperframes.json",
            "package.json",
            "index.html",
            "style_tokens.json",
            "fonts.css",
            "design.md",
            "validation_report.json",
            "compositions/timeline_manifest.json",
            "src/styles.css",
            "src/template.js",
        ):
            self.assertTrue((ROOT / relative).is_file(), relative)

    def test_manifest_registers_three_compositions(self):
        manifest = json.loads((ROOT / "compositions/timeline_manifest.json").read_text(encoding="utf-8"))
        ids = {item["id"] for item in manifest["compositions"]}
        self.assertEqual(set(COMPOSITIONS), ids)
        for composition in COMPOSITIONS:
            self.assertTrue((ROOT / "compositions" / f"{composition}.html").is_file())

    def test_style_tokens_are_complete(self):
        tokens = json.loads((ROOT / "style_tokens.json").read_text(encoding="utf-8"))
        self.assertTrue(set(TOKEN_GROUPS).issubset(tokens))
        self.assertEqual(1920, tokens["canvas"]["width"])
        self.assertEqual(1080, tokens["canvas"]["height"])
        self.assertEqual(2, tokens["captionText"]["maxLines"])

    def test_each_composition_declares_all_editable_roles(self):
        for composition in COMPOSITIONS:
            html = (ROOT / "compositions" / f"{composition}.html").read_text(encoding="utf-8")
            self.assertIn(f'data-composition-id="{composition}"', html)
            for role in ROLES:
                self.assertIn(f'data-role="{role}"', html, f"{composition}:{role}")
            ids = re.findall(r'(?<!-)\bid="([^"]+)"', html)
            hf_ids = re.findall(r'data-hf-id="([^"]+)"', html)
            self.assertEqual(len(ids), len(set(ids)), f"duplicate id in {composition}")
            self.assertEqual(len(hf_ids), len(set(hf_ids)), f"duplicate data-hf-id in {composition}")

    def test_each_composition_registers_its_timeline(self):
        for composition in COMPOSITIONS:
            html = (ROOT / "compositions" / f"{composition}.html").read_text(encoding="utf-8")
            self.assertIn("window.__timelines = window.__timelines || {};", html)
            self.assertIn(f'window.__timelines["{composition}"] =', html)

    def test_source_video_media_contract(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        root = re.search(r'<main[^>]*data-composition-id="politics-longform-template-v1"[^>]*>(.*?)</main>', html, re.S)
        self.assertIsNotNone(root)
        body = root.group(1)
        self.assertRegex(body, r'<video[^>]*muted[^>]*src="assets/media/source-placeholder\.mp4"')
        self.assertRegex(body, r'<audio[^>]*src="assets/audio/source-placeholder\.wav"')
        self.assertNotRegex(body, r'<(?:div|section)[^>]*>\s*<(?:video|audio)')

    def test_caption_and_remote_asset_rules(self):
        combined = "\n".join(path.read_text(encoding="utf-8") for path in ROOT.rglob("*.html"))
        self.assertIn("정치는 말보다", combined)
        self.assertIn("결과로 평가받습니다", combined)
        self.assertNotRegex(combined, r'https?://[^\s"\']+\.(?:png|jpe?g|svg|mp4|webm|wav|mp3|css|js|woff2?)')

    def test_chosungs_font_is_bundled_and_global(self):
        font_path = ROOT / "assets/fonts/ChosunGs.TTF"
        font_css = ROOT / "fonts.css"
        self.assertTrue(font_css.is_file())
        css = font_css.read_text(encoding="utf-8")
        tokens = json.loads((ROOT / "style_tokens.json").read_text(encoding="utf-8"))
        self.assertTrue(font_path.is_file())
        self.assertGreater(font_path.stat().st_size, 0)
        self.assertIn('font-family: "ChosunGs";', css)
        self.assertIn('url("assets/fonts/ChosunGs.TTF") format("truetype")', css)
        self.assertEqual("ChosunGs, serif", tokens["captionText"]["fontFamily"])


if __name__ == "__main__":
    unittest.main()
