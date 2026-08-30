from __future__ import annotations

import json
import re
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import render_democratic_blue_card as renderer


class DemocraticBlueCardRendererTests(unittest.TestCase):
    def geometry(self, *, gap: float = 14, footer_scroll: int = 48, footer_client: int = 48) -> dict[str, object]:
        footer_top = 658.5
        return {
            "canvas": {"width": 1920, "height": 1080},
            "safeAreaTop": 756,
            "minimumGapPx": 14,
            "infoGridFooterGapPx": gap,
            "info_grid_footer_gap_px": gap,
            "mainShell": {
                "rect": {"left": 150, "top": 54, "right": 1770, "bottom": 736},
                "padding": {"bottom": 28},
                "scrollHeight": 680,
                "clientHeight": 680,
            },
            "footer": {
                "rect": {"left": 216, "top": footer_top, "right": 1704, "bottom": 706.5},
                "scrollHeight": footer_scroll,
                "clientHeight": footer_client,
                "scrollWidth": 100,
                "clientWidth": 100,
                "text": "다음 발언에서 시행 시점을 확인합니다",
                "visibility": {"visible": True},
            },
            "blocks": [{
                "rect": {"left": 216, "top": 297, "right": 960, "bottom": footer_top - gap},
                "scrollHeight": 100,
                "clientHeight": 100,
            }],
            "collisions": {"blockToBlock": False, "blockToFooter": False},
            "valid": True,
            "failures": [],
        }

    def test_geometry_accepts_exact_minimum_footer_gap_with_tolerance(self) -> None:
        renderer.validate_geometry(self.geometry(gap=14))

    def test_geometry_rejects_one_pixel_footer_vertical_overflow(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "FOOTER_VERTICAL_OVERFLOW"):
            renderer.validate_geometry(self.geometry(footer_scroll=48, footer_client=47))

    def test_geometry_rejects_a_template_that_claims_a_different_safe_area(self) -> None:
        geometry = self.geometry()
        geometry["safeAreaTop"] = 1000
        with self.assertRaisesRegex(RuntimeError, "SAFE_AREA_TOP_INVALID"):
            renderer.validate_geometry(geometry)

    def payload(self) -> dict[str, object]:
        return {
            "visual_id": "V001",
            "top_label": "POLICY CHECK",
            "headline_line1": "정책 방향과 실제 집행",
            "headline_line2": "무엇이 달랐나",
            "highlight_terms": ["실제 집행"],
            "info_blocks": [
                {"label": "방향", "main": "수사권 조정", "sub": "정책 목표"},
                {"label": "집행", "main": "세부 시행", "sub": "현장 작동"},
            ],
            "footer_text": "다음 발언에서 시행 시점을 확인합니다",
            "lower_safe_area": True,
        }

    def long_valid_payload(self, count: int) -> dict[str, object]:
        payload = self.payload()
        payload["headline_line1"] = "국정 운영의 약속과 실제 집행을 끝까지 확인합니다"
        payload["headline_line2"] = "국민이 체감할 수 있는 변화가 핵심입니다"
        payload["footer_text"] = "다음 발언에서 시행 시점과 책임 주체를 반드시 확인합니다"
        blocks = [
            {"label": "방향", "main": "수사권 조정의 원칙", "sub": "정책 목표와 현장 집행의 차이를 끝까지 점검합니다"},
            {"label": "집행", "main": "세부 시행의 기준", "sub": "국민이 실제로 체감하는 변화와 책임을 확인합니다"},
            {"label": "검증", "main": "후속 결과의 확인", "sub": "다음 발언에서 시행 시점과 책임 주체를 확인합니다"},
            {"label": "책임", "main": "공개 검증의 원칙", "sub": "약속한 변화가 현장에서 작동하는지 끝까지 확인합니다"},
        ]
        payload["info_blocks"] = blocks[:count]
        return payload

    def test_build_html_escapes_and_highlights(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            template = root / "template.html"
            css = root / "template.css"
            template.write_text("<style>{{INLINE_CSS}}</style>{{BODY}}", encoding="utf-8")
            css.write_text("body{margin:0}", encoding="utf-8")
            payload = self.payload()
            payload["headline_line1"] = "정책 <방향>과 실제 집행"
            html = renderer.build_html(payload, template, css)
            self.assertIn("&lt;방향&gt;", html)
            self.assertIn('class="highlight"', html)
            self.assertIn('data-render-status="PASS"', html)

    def test_more_than_four_info_blocks_fails(self) -> None:
        payload = self.payload()
        payload["info_blocks"] = [
            {"label": str(index), "main": "값", "sub": "설명"} for index in range(5)
        ]
        with self.assertRaisesRegex(RuntimeError, "INFO_BLOCK_COUNT_INVALID"):
            renderer.validate_payload(payload)

    def test_lower_safe_area_must_be_true(self) -> None:
        payload = self.payload()
        payload["lower_safe_area"] = False
        with self.assertRaisesRegex(RuntimeError, "LOWER_SAFE_AREA_REQUIRED"):
            renderer.validate_payload(payload)

    def test_inset_profile_matches_the_manual_v8_root_card_geometry(self) -> None:
        payload = self.payload()
        payload["style_profile"] = "DEMOCRATIC_BLUE_INSET_CARD_V2"

        profile = renderer.resolve_style_profile(payload)

        self.assertEqual(profile["output_size"], (1920, 1080))
        self.assertEqual(
            profile["image_frame"],
            {"x": 336, "y": 189, "width": 1248, "height": 702},
        )
        self.assertEqual(
            profile["caption_safe_area"],
            {"x": 0, "y": 891, "width": 1920, "height": 189},
        )
        payload["raster_size"] = "1280x720"
        with self.assertRaisesRegex(RuntimeError, "INSET_CARD_RASTER_SIZE_INVALID"):
            renderer.resolve_style_profile(payload)

    def test_linux_root_browser_flags_include_no_sandbox(self) -> None:
        flags = renderer.browser_base_args(
            Path("/usr/bin/chromium"), platform_name="posix", effective_uid=0
        )
        self.assertIn("--no-sandbox", flags)

    def test_browser_timeout_is_controlled_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            payload = root / "payload.json"
            template = root / "template.html"
            css = root / "template.css"
            browser = root / "browser.exe"
            payload.write_text(json.dumps(self.payload(), ensure_ascii=False), encoding="utf-8")
            template.write_text("<style>{{INLINE_CSS}}</style>{{BODY}}", encoding="utf-8")
            css.write_text("body{margin:0}", encoding="utf-8")
            browser.write_bytes(b"browser")
            with mock.patch.object(
                renderer.subprocess,
                "run",
                side_effect=renderer.subprocess.TimeoutExpired([str(browser)], 45),
            ):
                with self.assertRaisesRegex(RuntimeError, "HTML_CARD_RENDER_TIMEOUT"):
                    renderer.render_card(
                        payload,
                        root / "card.png",
                        template_path=template,
                        css_path=css,
                        browser_path=browser,
                    )

    def test_png_size_reads_ihdr(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "image.png"
            signature = b"\x89PNG\r\n\x1a\n"
            ihdr = struct.pack(">I", 13) + b"IHDR" + struct.pack(">II", 1920, 1080)
            path.write_bytes(signature + ihdr + b"\x00" * 17)
            self.assertEqual(renderer.png_size(path), (1920, 1080))

    def test_three_blocks_reserve_footer_and_safe_area_in_browser_layout(self) -> None:
        """Long valid three-block content must fit above the footer's reserved padding."""
        payload = self.long_valid_payload(3)
        template = SCRIPTS.parent / "templates" / "democratic_blue_center_info_card_v1.html"
        css = SCRIPTS.parent / "templates" / "democratic_blue_center_info_card_v1.css"
        document = renderer.build_html(payload, template, css)
        probe = """
<script>
(() => {
  const safeTop = 756;
  const panel = document.querySelector('.main-shell').getBoundingClientRect();
  const panelStyle = getComputedStyle(document.querySelector('.main-shell'));
  const footer = document.querySelector('.footer').getBoundingClientRect();
  const blocks = [...document.querySelectorAll('.info-block')].map((node) => node.getBoundingClientRect());
  const collision = blocks.some((block) => block.bottom > footer.top && block.top < footer.bottom);
  const blockCollision = blocks.some((block, index) => blocks.slice(index + 1).some((other) =>
    block.left < other.right && block.right > other.left && block.top < other.bottom && block.bottom > other.top));
  const coreBottom = Math.max(footer.bottom, ...blocks.map((block) => block.bottom));
  document.documentElement.dataset.geometryCollision = String(collision);
  document.documentElement.dataset.geometryBlockCollision = String(blockCollision);
  document.documentElement.dataset.geometryCoreBottom = String(coreBottom);
  document.documentElement.dataset.geometryFooterBottom = String(footer.bottom);
  document.documentElement.dataset.geometryMainBottom = String(panel.bottom);
  document.documentElement.dataset.geometryMainPaddingBottom = panelStyle.paddingBottom;
  document.documentElement.dataset.geometryFooterFitsReservedSpace = String(
    footer.bottom <= panel.bottom - parseFloat(panelStyle.paddingBottom));
})();
</script>
"""
        document = document.replace("</body>", probe + "</body>")
        browser = renderer.find_browser()
        with tempfile.TemporaryDirectory() as temporary:
            html_path = Path(temporary) / "three-block-card.html"
            html_path.write_text(document, encoding="utf-8")
            completed = subprocess.run(
                [*renderer.browser_base_args(browser), "--dump-dom", html_path.resolve().as_uri()],
                capture_output=True,
                text=True,
                check=False,
                timeout=45,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        attributes = dict(re.findall(r'data-geometry-([a-z-]+)="([^"]+)"', completed.stdout))
        self.assertEqual(attributes.get("collision"), "false", attributes)
        self.assertEqual(attributes.get("block-collision"), "false", attributes)
        self.assertEqual(attributes.get("footer-fits-reserved-space"), "true", attributes)
        self.assertLess(float(attributes["core-bottom"]), 756, attributes)
        self.assertLess(float(attributes["footer-bottom"]), 756, attributes)

    def test_two_to_four_blocks_render_without_layout_collisions(self) -> None:
        template = SCRIPTS.parent / "templates" / "democratic_blue_center_info_card_v1.html"
        css = SCRIPTS.parent / "templates" / "democratic_blue_center_info_card_v1.css"
        output_root = Path(tempfile.gettempdir()) / "119_v2_8_html_card_matrix_v3"
        browser = renderer.find_browser()
        measurements = []
        failures = []
        for count in (2, 3, 4):
            payload = self.long_valid_payload(count)
            payload_path = output_root / f"{count}_blocks_payload.json"
            png_path = output_root / f"{count}_blocks_card.png"
            manifest_path = output_root / f"{count}_blocks_manifest.json"
            diagnostic_path = output_root / f"{count}_blocks_diagnostic.json"
            payload_path.parent.mkdir(parents=True, exist_ok=True)
            payload_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            try:
                report = renderer.render_card(
                    payload_path, png_path, template_path=template, css_path=css, browser_path=browser,
                    manifest_path=manifest_path,
                )
            except RuntimeError as error:
                diagnostic_path.write_text(json.dumps({"info_blocks": count, "error": str(error), "png": str(png_path), "png_exists": png_path.is_file()}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                failures.append(f"{count}:{error}")
                continue
            geometry = report["geometry"]
            blocks = geometry["blocks"]
            self.assertEqual((report["width"], report["height"]), (1920, 1080))
            self.assertTrue(geometry["valid"], geometry)
            self.assertGreaterEqual(geometry["info_grid_footer_gap_px"] + 0.5, geometry["minimumGapPx"], geometry)
            self.assertLessEqual(geometry["mainShell"]["scrollHeight"], geometry["mainShell"]["clientHeight"], geometry)
            self.assertLessEqual(geometry["footer"]["scrollHeight"], geometry["footer"]["clientHeight"], geometry)
            self.assertFalse(geometry["collisions"]["blockToBlock"], geometry)
            self.assertFalse(geometry["collisions"]["blockToFooter"], geometry)
            self.assertLess(geometry["footer"]["rect"]["bottom"], geometry["safeAreaTop"], geometry)
            if count == 3:
                self.assertEqual(blocks[2]["rect"]["left"], blocks[0]["rect"]["left"], geometry)
                self.assertGreater(blocks[2]["rect"]["width"], blocks[0]["rect"]["width"], geometry)
            if count == 4:
                self.assertEqual(blocks[0]["rect"]["top"], blocks[1]["rect"]["top"], geometry)
                self.assertEqual(blocks[2]["rect"]["top"], blocks[3]["rect"]["top"], geometry)
                self.assertGreater(blocks[2]["rect"]["top"], blocks[0]["rect"]["top"], geometry)
            measurements.append({"info_blocks": count, "png": str(png_path), "manifest": str(manifest_path), "png_size": [report["width"], report["height"]], "dom_status": "PASS", "geometry": geometry})
        (output_root / "geometry.json").write_text(
            json.dumps(measurements, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        self.assertFalse(failures, failures)


if __name__ == "__main__":
    unittest.main()
