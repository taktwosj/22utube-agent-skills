from __future__ import annotations

import argparse
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
PROMPT_PATH = SKILL_DIR / "references" / "gemini-capcut-remake-system-prompt.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the Gemini 11short analysis request prompt.")
    parser.add_argument("--url", required=True, help="YouTube Shorts URL to analyze.")
    parser.add_argument("--out", required=True, type=Path, help="Output gemini_request.md path.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    prompt = PROMPT_PATH.read_text(encoding="utf-8-sig").rstrip()
    url = args.url.strip()
    if not url:
        raise ValueError("--url must not be empty")
    body = f"{prompt}\n\n[입력]\nvideo_url: {url}\n"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(body, encoding="utf-8")
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
