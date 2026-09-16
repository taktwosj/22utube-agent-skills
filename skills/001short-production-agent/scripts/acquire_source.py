#!/usr/bin/env python3
"""Download one approved YouTube original and write its 001 intake receipt.

This is the only source-acquisition script the 001 lane exposes to
factory_episode_run with network=true. It refuses every host outside the
YouTube allowlist, writes nothing outside the episode folder, and ends by
running the offline intake validator so the receipt is proven, not asserted.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from common import sha256_file
from validate_source_intake import validate_receipt

ALLOWED_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"}
RECEIPT_VERSION = "001short-source-intake-receipt-v2"
ORIGINAL_ANALYSIS_CONTRACT_VERSION = "001short-original-source-transcript-v1"


def _source_id(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or parsed.netloc not in ALLOWED_HOSTS:
        raise SystemExit("SOURCE_ACQUIRE_HOST_NOT_ALLOWED")
    candidate = parse_qs(parsed.query).get("v", [None])[0] or next((part for part in reversed(parsed.path.split("/")) if part), None)
    if not candidate or not re.fullmatch(r"[A-Za-z0-9_-]{5,32}", candidate):
        raise SystemExit("SOURCE_ACQUIRE_SOURCE_ID_UNRESOLVED")
    return candidate


def _probe_duration_us(path: Path) -> int:
    completed = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise SystemExit("SOURCE_ACQUIRE_FFPROBE_FAILED")
    try:
        duration = float(completed.stdout.strip())
    except ValueError as exc:
        raise SystemExit("SOURCE_ACQUIRE_FFPROBE_FAILED") from exc
    if duration <= 0:
        raise SystemExit("SOURCE_ACQUIRE_DURATION_INVALID")
    return round(duration * 1_000_000)


def _download(url: str, source_id: str, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    template = str(out_dir / f"{source_id}.%(ext)s")
    completed = subprocess.run(
        [
            "yt-dlp",
            "--no-playlist",
            # Default android_vr needs a PO Token bgutil cannot mint: 403, then a
            # 360p fallback. mweb/web_embedded is the lane's proven client set.
            "--extractor-args", "youtube:player_client=mweb,web_embedded;fetch_pot=always",
            "--no-continue",
            "--force-overwrites",
            "--merge-output-format", "mp4",
            "-f", "bv*[height<=1080]+ba/b[height<=1080]/b",
            "-o", template,
            url,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    print(completed.stdout[-4000:])
    print(completed.stderr[-4000:])
    if completed.returncode != 0:
        raise SystemExit("SOURCE_ACQUIRE_DOWNLOAD_FAILED")
    media = sorted(out_dir.glob(f"{source_id}.*"))
    media = [item for item in media if item.suffix.lower() in {".mp4", ".mkv", ".webm", ".mov"}]
    if len(media) != 1:
        raise SystemExit("SOURCE_ACQUIRE_MEDIA_AMBIGUOUS")
    return media[0]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--episode-id", required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--out-dir", type=Path, default=Path("00_source"))
    args = parser.parse_args()

    source_id = _source_id(args.url)
    out_dir = args.out_dir
    media = _download(args.url, source_id, out_dir)
    media_sha = sha256_file(media)
    duration_us = _probe_duration_us(media)
    media_rel = media.name

    identity_path = out_dir / "source-identity.json"
    identity: dict[str, Any] = {
        "schema_version": "source-identity-v1",
        "episode_id": args.episode_id,
        "source_id": source_id,
        "media_path": media_rel,
        "media_sha256": media_sha,
    }
    identity_path.write_text(json.dumps(identity, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    receipt_path = out_dir / "source-intake-receipt.json"
    receipt = {
        "schema_version": RECEIPT_VERSION,
        "original_analysis_contract_version": ORIGINAL_ANALYSIS_CONTRACT_VERSION,
        "episode_id": args.episode_id,
        "intake_kind": "URL",
        "source_id": source_id,
        "source_locator": args.url,
        "local_media_path": media_rel,
        "local_media_sha256": media_sha,
        "local_media_duration_us": duration_us,
        "source_identity_path": identity_path.name,
        "source_identity_sha256": sha256_file(identity_path),
    }
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    errors = validate_receipt(receipt_path)
    print(json.dumps({
        "status": "PASS" if not errors else "FAIL",
        "receipt": str(receipt_path),
        "media": str(media),
        "source_id": source_id,
        "duration_us": duration_us,
        "errors": errors,
    }, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
