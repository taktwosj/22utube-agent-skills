#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import secrets
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_API_URL = "http://100.102.6.112:8088/midform_snapshot_api.php"
SKILL_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_POLICY = SKILL_ROOT / "references" / "approved-channel-allowlist.json"


def default_config_path() -> Path:
    override = os.environ.get("TREND_HUNTER_MIDFORM_READ_CONFIG", "").strip()
    if override:
        return Path(override).expanduser()
    return Path.home() / ".trend_hunter" / "midform_read_api.json"


def init_config(path: Path, server_url: str = DEFAULT_API_URL) -> None:
    if path.exists():
        raise RuntimeError(f"CONFIG_ALREADY_EXISTS: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "server_url": server_url,
        "hmac_secret": secrets.token_hex(32),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def load_config(path: Path) -> dict[str, str]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"WAIT_TREND_HUNTER_READ_CONFIG: {path}") from exc
    server_url = str(payload.get("server_url", DEFAULT_API_URL)).strip()
    secret = str(payload.get("hmac_secret", "")).strip()
    if not server_url.startswith("http://100.") or len(secret) < 32:
        raise RuntimeError(f"WAIT_TREND_HUNTER_READ_CONFIG: {path}")
    return {"server_url": server_url, "hmac_secret": secret}


def canonical_signature(secret: str, timestamp: str, method: str, path: str, raw_query: str) -> str:
    canonical = "\n".join((timestamp, method.upper(), path, raw_query))
    return hmac.new(secret.encode("utf-8"), canonical.encode("utf-8"), hashlib.sha256).hexdigest()


def build_query(args: argparse.Namespace) -> str:
    pairs: list[tuple[str, str]] = []
    for key, value in (
        ("q", args.query),
        ("channel", args.channel),
        ("group", args.group),
        ("status", args.status),
        ("published_after", args.published_after),
        ("published_before", args.published_before),
    ):
        if value:
            pairs.append((key, str(value)))
    pairs.append(("limit", str(args.limit)))
    return urllib.parse.urlencode(pairs)


def request_snapshot(config: dict[str, str], raw_query: str, timeout: int = 20) -> dict[str, Any]:
    server_url = config["server_url"]
    parsed = urllib.parse.urlsplit(server_url)
    request_path = parsed.path or "/midform_snapshot_api.php"
    timestamp = str(int(time.time()))
    signature = canonical_signature(
        config["hmac_secret"], timestamp, "GET", request_path, raw_query
    )
    url = server_url + ("?" + raw_query if raw_query else "")
    request = urllib.request.Request(
        url,
        method="GET",
        headers={
            "Accept": "application/json",
            "X-Trend-Hunter-Timestamp": timestamp,
            "X-Trend-Hunter-Signature": signature,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise RuntimeError("WAIT_CHANNEL_AUTHORITY_UNAVAILABLE") from exc
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise RuntimeError("WAIT_CHANNEL_AUTHORITY_UNAVAILABLE") from exc
    if not isinstance(payload, dict) or payload.get("ok") is not True:
        code = payload.get("error_code", "WAIT_CHANNEL_AUTHORITY_UNAVAILABLE") if isinstance(payload, dict) else "WAIT_CHANNEL_AUTHORITY_UNAVAILABLE"
        raise RuntimeError(str(code))
    return payload


def load_policy(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_snapshot(
    payload: dict[str, Any],
    policy: dict[str, Any],
    require_sync_date: str = "",
) -> str:
    if payload.get("read_only") is not True:
        return "WAIT_CHANNEL_AUTHORITY_UNAVAILABLE"
    progress = payload.get("progress")
    if not isinstance(progress, dict):
        return "WAIT_TREND_HUNTER_SYNC_STALE"
    if progress.get("status") != "done":
        return "WAIT_TREND_HUNTER_SYNC_STALE"
    expected = int(policy["authority"]["declared_allowed_channels"])
    if int(progress.get("channels_done", 0)) != expected:
        return "WAIT_TREND_HUNTER_SYNC_STALE"
    if int(progress.get("channels_total", 0)) != expected:
        return "WAIT_TREND_HUNTER_SYNC_STALE"
    if int(progress.get("failed_count", 0)) != 0:
        return "WAIT_TREND_HUNTER_SYNC_STALE"
    finished_at = str(progress.get("finished_at", ""))
    if require_sync_date and not finished_at.startswith(require_sync_date):
        return "WAIT_TREND_HUNTER_SYNC_STALE"

    allowed_ids = {
        str(row.get("channel_id", ""))
        for row in policy.get("allowed_channels", [])
        if row.get("channel_id")
    }
    blocked_ids = {
        str(row.get("channel_id", ""))
        for row in policy.get("blocked_channels", [])
        if row.get("channel_id")
    }
    for video in payload.get("videos", []):
        channel_id = str(video.get("channel_id", ""))
        if not channel_id or channel_id in blocked_ids or channel_id not in allowed_ids:
            return "WAIT_CHANNEL_ALLOWLIST_DRIFT"
    return "PASS"


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Read the Trend Hunter midform snapshot without triggering collection.")
    result.add_argument("--query", default="")
    result.add_argument("--channel", default="")
    result.add_argument("--group", default="")
    result.add_argument("--status", default="")
    result.add_argument("--published-after", default="")
    result.add_argument("--published-before", default="")
    result.add_argument("--limit", type=int, default=100)
    result.add_argument("--require-sync-date", default="")
    result.add_argument("--config", type=Path, default=default_config_path())
    result.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    result.add_argument("--output", type=Path)
    result.add_argument("--init-secret", action="store_true")
    result.add_argument("--server-url", default=DEFAULT_API_URL)
    return result


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    args = parser().parse_args()
    args.limit = max(1, min(500, args.limit))
    if args.init_secret:
        try:
            init_config(args.config, args.server_url)
        except RuntimeError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        print(f"PASS_TREND_HUNTER_READ_CONFIG {args.config}")
        return 0

    try:
        config = load_config(args.config)
        policy = load_policy(args.policy)
        payload = request_snapshot(config, build_query(args))
    except (RuntimeError, OSError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 3

    validation = validate_snapshot(payload, policy, args.require_sync_date)
    payload["validation"] = validation
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if validation == "PASS" else 4


if __name__ == "__main__":
    raise SystemExit(main())
