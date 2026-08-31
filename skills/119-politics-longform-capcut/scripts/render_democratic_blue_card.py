#!/usr/bin/env python3
"""Render Democratic Blue HTML cards into their declared image-card layer."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from inset_card_layout import INSET_CARD_STYLE_PROFILE, inset_card_profile


V1_STYLE_PROFILE = "DEMOCRATIC_BLUE_CENTER_INFO_CARD_V1"
SKILL_ROOT = Path(__file__).resolve().parents[1]

MAX_TEXT = {
    "top_label": 32,
    "headline_line1": 28,
    "headline_line2": 28,
    "footer_text": 52,
    "block_label": 16,
    "block_main": 24,
    "block_sub": 42,
}


def resolve_style_profile(payload: dict[str, Any]) -> dict[str, Any]:
    style_profile = str(payload.get("style_profile", INSET_CARD_STYLE_PROFILE)).strip() or INSET_CARD_STYLE_PROFILE
    if style_profile == V1_STYLE_PROFILE:
        return {
            "style_profile": V1_STYLE_PROFILE,
            "output_size": (1920, 1080),
            "render_size": (1920, 1080),
            "safe_area_top": 756,
            "template": SKILL_ROOT / "templates/democratic_blue_center_info_card_v1.html",
            "css": SKILL_ROOT / "templates/democratic_blue_center_info_card_v1.css",
        }
    if style_profile == INSET_CARD_STYLE_PROFILE:
        profile = inset_card_profile()
        raster_size = str(payload.get("raster_size", "1920x1080")).strip()
        raster_sizes = {"1920x1080": (1920, 1080)}
        if raster_size not in raster_sizes:
            raise RuntimeError("INSET_CARD_RASTER_SIZE_INVALID")
        profile["output_size"] = raster_sizes[raster_size]
        profile.update(
            {
                "safe_area_top": 720,
                "template": SKILL_ROOT / "templates/democratic_blue_inset_card_v2.html",
                "css": SKILL_ROOT / "templates/democratic_blue_inset_card_v2.css",
            }
        )
        return profile
    raise RuntimeError("STYLE_PROFILE_INVALID")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def require_text(payload: dict[str, Any], field: str, limit: int) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError(f"{field.upper()}_REQUIRED")
    value = value.strip()
    if len(value) > limit:
        raise RuntimeError(f"{field.upper()}_TOO_LONG")
    return value


def validate_payload(payload: dict[str, Any]) -> None:
    require_text(payload, "visual_id", 64)
    require_text(payload, "top_label", MAX_TEXT["top_label"])
    require_text(payload, "headline_line1", MAX_TEXT["headline_line1"])
    line2 = payload.get("headline_line2", "")
    if not isinstance(line2, str) or len(line2.strip()) > MAX_TEXT["headline_line2"]:
        raise RuntimeError("HEADLINE_LINE2_TOO_LONG")
    require_text(payload, "footer_text", MAX_TEXT["footer_text"])
    if payload.get("lower_safe_area") is not True:
        raise RuntimeError("LOWER_SAFE_AREA_REQUIRED")
    blocks = payload.get("info_blocks")
    style_profile = resolve_style_profile(payload)["style_profile"]
    if style_profile == INSET_CARD_STYLE_PROFILE and (
        not isinstance(blocks, list) or len(blocks) != 1
    ):
        raise RuntimeError("INSET_FOCUS_INFO_BLOCK_COUNT_INVALID")
    if style_profile == V1_STYLE_PROFILE and (
        not isinstance(blocks, list) or not 2 <= len(blocks) <= 4
    ):
        raise RuntimeError("INFO_BLOCK_COUNT_INVALID")
    for index, block in enumerate(blocks):
        if not isinstance(block, dict):
            raise RuntimeError(f"INFO_BLOCK_INVALID:{index}")
        require_text(block, "label", MAX_TEXT["block_label"])
        require_text(block, "main", MAX_TEXT["block_main"])
        sub = block.get("sub", "")
        if not isinstance(sub, str) or len(sub.strip()) > MAX_TEXT["block_sub"]:
            raise RuntimeError(f"INFO_BLOCK_SUB_TOO_LONG:{index}")
    highlights = payload.get("highlight_terms", [])
    if not isinstance(highlights, list) or any(not isinstance(value, str) for value in highlights):
        raise RuntimeError("HIGHLIGHT_TERMS_INVALID")


def highlighted(value: str, terms: list[str]) -> str:
    escaped = html.escape(value)
    for term in sorted((term for term in terms if term), key=len, reverse=True):
        escaped_term = html.escape(term)
        escaped = escaped.replace(escaped_term, f'<span class="highlight">{escaped_term}</span>')
    return escaped


def build_html(payload: dict[str, Any], template_path: Path, css_path: Path) -> str:
    validate_payload(payload)
    template = template_path.read_text(encoding="utf-8")
    css = css_path.read_text(encoding="utf-8")
    terms = list(payload.get("highlight_terms", []))
    blocks = []
    for block in payload["info_blocks"]:
        blocks.append(
            '<section class="info-block">'
            f'<div class="info-label">{html.escape(block["label"])}</div>'
            f'<div class="info-main">{highlighted(block["main"], terms)}</div>'
            f'<div class="info-sub">{html.escape(block.get("sub", ""))}</div>'
            '</section>'
        )
    line2 = str(payload.get("headline_line2", "")).strip()
    body = (
        '<main class="main-shell">'
        f'<div class="top-label">{html.escape(payload["top_label"])}</div>'
        '<h1 class="headline">'
        f'<span class="line">{highlighted(payload["headline_line1"], terms)}</span>'
        f'<span class="line">{highlighted(line2, terms) if line2 else ""}</span>'
        '</h1>'
        f'<div class="info-grid">{"".join(blocks)}</div>'
        f'<div class="footer">{html.escape(payload["footer_text"])}</div>'
        '</main><div class="lower-safe-area" aria-hidden="true"></div>'
    )
    if "{{INLINE_CSS}}" not in template or "{{BODY}}" not in template:
        raise RuntimeError("HTML_TEMPLATE_PLACEHOLDER_MISSING")
    document = template.replace("{{INLINE_CSS}}", css).replace("{{BODY}}", body)
    if "data-render-status=" not in document:
        document = '<div data-render-status="PASS">' + document + "</div>"
    return document


def find_browser(explicit: Path | None = None) -> Path:
    candidates: list[Path] = []
    if explicit is not None:
        candidates.append(explicit)
    if os.environ.get("CHROME_PATH"):
        candidates.append(Path(os.environ["CHROME_PATH"]))
    for name in ("msedge", "msedge.exe", "chrome", "chrome.exe", "chromium", "chromium-browser"):
        found = shutil.which(name)
        if found:
            candidates.append(Path(found))
    for env_name in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"):
        base = os.environ.get(env_name)
        if not base:
            continue
        candidates.extend(
            [
                Path(base) / "Microsoft/Edge/Application/msedge.exe",
                Path(base) / "Google/Chrome/Application/chrome.exe",
            ]
        )
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    raise RuntimeError("HEADLESS_BROWSER_NOT_FOUND")


def browser_base_args(
    browser: Path, *, platform_name: str | None = None, effective_uid: int | None = None
) -> list[str]:
    platform_name = os.name if platform_name is None else platform_name
    if effective_uid is None:
        getuid = getattr(os, "geteuid", None)
        effective_uid = getuid() if callable(getuid) else -1
    args = [str(browser), "--headless=new", "--disable-gpu"]
    if platform_name == "posix" and effective_uid == 0:
        args.append("--no-sandbox")
    return args


def png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise RuntimeError("PNG_DECODE_INVALID")
    return struct.unpack(">II", data[16:24])


def geometry_from_dom(dom: str) -> dict[str, Any]:
    marker = 'data-geometry="'
    start = dom.find(marker)
    if start < 0:
        raise RuntimeError("HTML_CARD_GEOMETRY_INVALID:DOM_GEOMETRY_MISSING")
    start += len(marker)
    end = dom.find('"', start)
    if end < 0:
        raise RuntimeError("HTML_CARD_GEOMETRY_INVALID:DOM_GEOMETRY_MALFORMED")
    try:
        geometry = json.loads(html.unescape(dom[start:end]))
    except json.JSONDecodeError as error:
        raise RuntimeError("HTML_CARD_GEOMETRY_INVALID:DOM_GEOMETRY_MALFORMED") from error
    if not isinstance(geometry, dict):
        raise RuntimeError("HTML_CARD_GEOMETRY_INVALID:DOM_GEOMETRY_MALFORMED")
    return geometry


def validate_geometry(
    geometry: dict[str, Any], *, expected_size: tuple[int, int] = (1920, 1080), safe_area_top: int = 756
) -> None:
    try:
        canvas = geometry["canvas"]
        main_shell = geometry["mainShell"]
        footer = geometry["footer"]
        blocks = geometry["blocks"]
        main_rect = main_shell["rect"]
        footer_rect = footer["rect"]
        padding_bottom = float(main_shell["padding"]["bottom"])
        minimum_gap = float(geometry["minimumGapPx"])
        actual_gap = float(geometry["info_grid_footer_gap_px"])
        declared_safe_area_top = float(geometry["safeAreaTop"])
        final_bottom = max(float(block["rect"]["bottom"]) for block in blocks)
    except (KeyError, TypeError, ValueError) as error:
        raise RuntimeError("HTML_CARD_GEOMETRY_INVALID:DOM_GEOMETRY_INCOMPLETE") from error
    failures: list[str] = []
    if declared_safe_area_top != float(safe_area_top):
        failures.append("SAFE_AREA_TOP_INVALID")
    if not float(footer_rect["bottom"]) <= float(main_rect["bottom"]) - padding_bottom:
        failures.append("FOOTER_OUTSIDE_RESERVED_MAIN_SHELL")
    if not actual_gap + 0.5 >= minimum_gap:
        failures.append("INFO_GRID_FOOTER_GAP_INVALID")
    if not float(footer_rect["bottom"]) < safe_area_top:
        failures.append("FOOTER_SAFE_AREA_INVALID")
    if not int(main_shell["scrollHeight"]) <= int(main_shell["clientHeight"]):
        failures.append("MAIN_SHELL_VERTICAL_OVERFLOW")
    if not int(footer["scrollHeight"]) <= int(footer["clientHeight"]):
        failures.append("FOOTER_VERTICAL_OVERFLOW")
    for block in blocks:
        if not int(block["scrollHeight"]) <= int(block["clientHeight"]):
            failures.append("INFO_BLOCK_VERTICAL_OVERFLOW")
            break
    footer_visibility = footer["visibility"]
    if not footer["text"] or not footer_visibility["visible"] or int(footer["scrollWidth"]) > int(footer["clientWidth"]):
        failures.append("FOOTER_TEXT_NOT_VISIBLE")
    core_rects = [main_rect, footer_rect, *(block["rect"] for block in blocks)]
    if (int(canvas.get("width", -1)), int(canvas.get("height", -1))) != expected_size:
        failures.append("CANVAS_DIMENSION_INVALID")
    for rect in core_rects:
        if not (float(rect["left"]) >= 0 and float(rect["top"]) >= 0 and float(rect["right"]) <= float(canvas["width"]) and float(rect["bottom"]) <= float(canvas["height"])):
            failures.append("CORE_OUTSIDE_CANVAS")
            break
    collisions = geometry.get("collisions", {})
    if collisions.get("blockToBlock") or collisions.get("blockToFooter"):
        failures.append("CORE_RECT_COLLISION")
    if geometry.get("valid") is not True or geometry.get("failures") or failures:
        details = geometry.get("failures") or failures or ["TEMPLATE_REPORTED_INVALID"]
        raise RuntimeError("HTML_CARD_GEOMETRY_INVALID:" + ",".join(str(value) for value in details))


def render_card(
    payload_path: Path,
    output_path: Path,
    *,
    template_path: Path | None = None,
    css_path: Path | None = None,
    browser_path: Path | None = None,
    manifest_path: Path | None = None,
) -> dict[str, Any]:
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError("VISUAL_PAYLOAD_OBJECT_REQUIRED")
    profile = resolve_style_profile(payload)
    template_path = template_path or profile["template"]
    css_path = css_path or profile["css"]
    document = build_html(payload, template_path, css_path)
    browser = find_browser(browser_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="politics-card-") as temporary:
        html_path = Path(temporary) / "card.html"
        html_path.write_text(document, encoding="utf-8")
        uri = html_path.resolve().as_uri()
        base_args = browser_base_args(browser)
        try:
            screenshot = subprocess.run(
                [
                    *base_args, "--hide-scrollbars", "--window-size=" + ",".join(map(str, profile["render_size"])),
                    f"--screenshot={output_path.resolve()}", uri,
                ],
                capture_output=True, text=True, check=False, timeout=45,
            )
        except subprocess.TimeoutExpired as error:
            raise RuntimeError("HTML_CARD_RENDER_TIMEOUT") from error
        if screenshot.returncode != 0 or not output_path.is_file():
            raise RuntimeError("HTML_CARD_RENDER_FAILED:" + screenshot.stderr.strip()[-300:])
        try:
            dump = subprocess.run(
                [*base_args, "--dump-dom", uri],
                capture_output=True, text=True, check=False, timeout=45,
            )
        except subprocess.TimeoutExpired as error:
            output_path.unlink(missing_ok=True)
            raise RuntimeError("HTML_CARD_DOM_CHECK_TIMEOUT") from error
        if dump.returncode != 0:
            output_path.unlink(missing_ok=True)
            raise RuntimeError("HTML_CARD_DOM_CHECK_FAILED")
        geometry = geometry_from_dom(dump.stdout)
        try:
            validate_geometry(
                geometry,
                expected_size=profile["render_size"],
                safe_area_top=int(profile["safe_area_top"]),
            )
        except RuntimeError:
            raise
    if profile["output_size"] != profile["render_size"]:
        temporary_output = output_path.with_suffix(".render.png")
        output_path.replace(temporary_output)
        resized = subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-i", str(temporary_output), "-vf", "scale=" + ":".join(map(str, profile["output_size"])), str(output_path)],
            capture_output=True,
            text=True,
            check=False,
            timeout=45,
        )
        temporary_output.unlink(missing_ok=True)
        if resized.returncode != 0 or not output_path.is_file():
            raise RuntimeError("HTML_CARD_RESIZE_FAILED")
    width, height = png_size(output_path)
    if (width, height) != profile["output_size"]:
        output_path.unlink(missing_ok=True)
        raise RuntimeError("HTML_CARD_DIMENSION_INVALID")
    report = {
        "schema": "democratic-blue-center-info-card.v2",
        "status": "PASS",
        "visual_id": payload["visual_id"],
        "style_profile": profile["style_profile"],
        "output": str(output_path),
        "sha256": sha256(output_path),
        "width": width,
        "height": height,
        "layout": {
            key: profile[key]
            for key in ("canvas", "image_frame", "caption_safe_area")
            if key in profile
        },
        "browser": browser.name,
        "geometry": geometry,
    }
    if manifest_path is not None:
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--template", type=Path)
    parser.add_argument("--css", type=Path)
    parser.add_argument("--browser", type=Path)
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    report = render_card(
        args.input, args.output, template_path=args.template, css_path=args.css,
        browser_path=args.browser, manifest_path=args.manifest,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, OSError, UnicodeError, json.JSONDecodeError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(2)
