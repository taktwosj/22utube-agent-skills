#!/usr/bin/env python3
"""Extract and render Mara lecture PDFs for canonical-card authoring."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import fitz


BOILERPLATE_PATTERNS = (
    re.compile(r"Digital\s+Nomad\s+High\s+Class", re.IGNORECASE),
    re.compile(r"©?\s*Copyright\s+(?:Mara|마라하기)(?:\.\s*All\s+Rights\s+Reserved)?", re.IGNORECASE),
)


def clean_text(text: str) -> str:
    cleaned = text.replace("\x00", " ").replace("\u0001", " ")
    lines: list[str] = []
    for raw_line in cleaned.splitlines():
        line = " ".join(raw_line.split()).strip()
        for pattern in BOILERPLATE_PATTERNS:
            line = pattern.sub("", line).strip()
        if not line:
            continue
        if re.fullmatch(r"(?:[A-Za-z]\s+){3,}[A-Za-z]", line):
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def extract_pdf(pdf_path: Path | str, lecture_title: str) -> list[dict[str, Any]]:
    path = Path(pdf_path)
    source_hash = sha256_file(path)
    document = fitz.open(path)
    records: list[dict[str, Any]] = []
    try:
        for index, page in enumerate(document):
            text = clean_text(page.get_text("text"))
            image_count = len(page.get_images(full=True))
            records.append(
                {
                    "lecture_title": lecture_title,
                    "source_file": path.name,
                    "source_sha256": source_hash,
                    "page": index + 1,
                    "text": text,
                    "text_chars": len(text),
                    "image_count": image_count,
                    "needs_visual_review": len(text) < 20,
                }
            )
    finally:
        document.close()
    return records


def render_pdf(pdf_path: Path | str, output_dir: Path | str, dpi: int = 120) -> list[Path]:
    path = Path(pdf_path)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    document = fitz.open(path)
    rendered: list[Path] = []
    try:
        matrix = fitz.Matrix(dpi / 72, dpi / 72)
        for index, page in enumerate(document):
            output_path = target / f"page-{index + 1:03d}.png"
            page.get_pixmap(matrix=matrix, alpha=False).save(output_path)
            rendered.append(output_path)
    finally:
        document.close()
    return rendered


def write_jsonl(records: list[dict[str, Any]], output_path: Path | str) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extract one Mara lecture PDF")
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--render-dir", type=Path)
    parser.add_argument("--dpi", type=int, default=120)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    records = extract_pdf(args.pdf, args.title)
    write_jsonl(records, args.output)
    rendered = render_pdf(args.pdf, args.render_dir, args.dpi) if args.render_dir else []
    print(
        json.dumps(
            {
                "source": str(args.pdf),
                "pages": len(records),
                "needs_visual_review": sum(item["needs_visual_review"] for item in records),
                "rendered": len(rendered),
                "output": str(args.output),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
