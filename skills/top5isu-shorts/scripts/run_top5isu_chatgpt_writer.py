#!/usr/bin/env python3
"""Run the internal top5isu writer through logged-in ChatGPT in OpenClaw Chrome."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Optional, Tuple

from build_top5isu_writer_packet import GateFail as PacketGateFail
from build_top5isu_writer_packet import build_writer_prompt, sha256_text, validate_writer_packet
from validate_top5isu_writer_response import GateFail as ResponseGateFail
from validate_top5isu_writer_response import extract_writer_json, validate_writer_response


def redact_browser_error(detail: str) -> str:
    safe = re.sub(r"https://chatgpt\.com/c/[^\s]+", "[redacted-chatgpt-url]", str(detail), flags=re.IGNORECASE)
    safe = re.sub(r"\b[0-9A-Fa-f]{24,}\b", "[redacted-browser-id]", safe)
    safe = re.sub(r"(?i)\b(token|cookie|session)(\s*[=:]\s*)[^\s]+", r"\1\2[redacted]", safe)
    return safe


class RelayFail(Exception):
    pass


Runner = Callable[..., Any]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_run_manifest(
    status: str,
    prompt: str,
    response: str,
    browser_profile: str,
    reasoning_label: str,
    started_at: Optional[str] = None,
    finished_at: Optional[str] = None,
    attempt_count: int = 1,
) -> Dict[str, Any]:
    manifest: Dict[str, Any] = {
        "schema_version": "top5isu_model_run_manifest_v1",
        "backend": "chatgpt_browser",
        "browser_profile": browser_profile,
        "reasoning_label": reasoning_label or "unavailable",
        "status": status,
        "started_at": started_at or _utc_now(),
        "finished_at": finished_at or _utc_now(),
        "prompt_sha256": sha256_text(prompt),
        "attempt_count": attempt_count,
    }
    if response:
        manifest["response_sha256"] = sha256_text(response)
    return manifest


class OpenClawChatGPTRelay:
    def __init__(
        self,
        runner: Runner = subprocess.run,
        browser_profile: str = "openclaw",
        timeout_sec: int = 180,
        poll_interval: float = 2.0,
    ) -> None:
        if browser_profile != "openclaw":
            raise RelayFail("WAIT_CHATGPT_BROWSER: browser profile must be openclaw")
        if timeout_sec < 1 or poll_interval < 0:
            raise RelayFail("WAIT_CHATGPT_BROWSER: invalid timeout or poll interval")
        self.runner = runner
        self.browser_profile = browser_profile
        self.timeout_sec = timeout_sec
        self.poll_interval = poll_interval

    def _run(self, parts: Iterable[str], expect_json: bool = True) -> Any:
        command = ["openclaw", "browser", "--browser-profile", self.browser_profile]
        if expect_json:
            command.append("--json")
        command.extend(str(part) for part in parts)
        completed = self.runner(
            command,
            text=True,
            capture_output=True,
            timeout=max(self.timeout_sec, 30),
        )
        if completed.returncode != 0:
            detail = redact_browser_error((completed.stderr or completed.stdout or "browser command failed").strip())
            raise RelayFail(f"WAIT_CHATGPT_UI: {detail}")
        if not expect_json:
            return completed.stdout
        try:
            return json.loads(completed.stdout or "{}")
        except json.JSONDecodeError as exc:
            raise RelayFail(f"WAIT_CHATGPT_UI: invalid browser JSON: {exc}")

    def _snapshot(self) -> Dict[str, Any]:
        payload = self._run(["snapshot", "--efficient", "--limit", "500"])
        if not isinstance(payload, dict):
            raise RelayFail("WAIT_CHATGPT_UI: snapshot is not an object")
        return payload

    @staticmethod
    def _find_ref(payload: Dict[str, Any], role: str, names: Iterable[str]) -> Tuple[Optional[str], Optional[str]]:
        wanted = set(names)
        refs = payload.get("refs") or {}
        if not isinstance(refs, dict):
            return None, None
        for ref, data in refs.items():
            ref_text = str(ref)
            if not re.fullmatch(r"e\d+", ref_text):
                continue
            if isinstance(data, dict) and data.get("role") == role and data.get("name") in wanted:
                return ref_text, str(data.get("name"))
        return None, None

    def _wait_for_composer(self) -> Tuple[Dict[str, Any], str]:
        deadline = time.monotonic() + min(float(self.timeout_sec), 20.0)
        while time.monotonic() < deadline:
            snapshot = self._snapshot()
            composer_ref, _ = self._find_ref(snapshot, "textbox", {"ChatGPT와 채팅", "Message ChatGPT"})
            if composer_ref:
                return snapshot, composer_ref
            if self.poll_interval:
                time.sleep(min(self.poll_interval, 1.0))
        raise RelayFail("WAIT_CHATGPT_LOGIN: logged-in ChatGPT composer was not found")

    def ensure_running(self) -> None:
        try:
            status = self._run(["status"])
        except RelayFail:
            status = {}
        if not isinstance(status, dict) or not status.get("running"):
            self._run(["start"], expect_json=False)
            status = self._run(["status"])
            if not isinstance(status, dict) or not status.get("running"):
                raise RelayFail("WAIT_CHATGPT_BROWSER: OpenClaw browser did not start")

    def _extract_latest_assistant(self) -> str:
        script = (
            "() => { const nodes = Array.from(document.querySelectorAll('[data-message-author-role=assistant]')); "
            "return nodes.length ? (nodes[nodes.length - 1].innerText || '') : ''; }"
        )
        payload = self._run(["evaluate", "--fn", script])
        result = payload.get("result") if isinstance(payload, dict) else ""
        if isinstance(result, dict) and "value" in result:
            result = result.get("value")
        if not isinstance(result, str) or not result.strip():
            raise RelayFail("WAIT_CHATGPT_RESPONSE: latest assistant response is empty")
        return result.strip()

    def generate(self, prompt: str) -> Tuple[str, Dict[str, str]]:
        self.ensure_running()
        opened = self._run(["open", "https://chatgpt.com/"])
        if not isinstance(opened, dict):
            raise RelayFail("WAIT_CHATGPT_UI: fresh ChatGPT tab was not created")
        tab_id = str(opened.get("tabId", ""))
        if not re.fullmatch(r"t\d+", tab_id):
            raise RelayFail("WAIT_CHATGPT_UI: fresh ChatGPT tab identifier was invalid")
        self._run(["focus", tab_id], expect_json=False)
        snapshot, composer_ref = self._wait_for_composer()
        reasoning_ref, reasoning_label = self._find_ref(
            snapshot,
            "button",
            {"즉시 5.5", "중간", "높음", "매우 높음", "Pro"},
        )
        observed_reasoning = reasoning_label or "unavailable"
        if reasoning_ref and reasoning_label != "높음":
            self._run(["click", reasoning_ref], expect_json=False)
            menu = self._snapshot()
            high_ref, _ = self._find_ref(menu, "menuitemradio", {"높음"})
            if high_ref:
                self._run(["click", high_ref], expect_json=False)
                observed_reasoning = "높음"
        self._run(["type", composer_ref, prompt, "--submit"], expect_json=False)
        deadline = time.monotonic() + self.timeout_sec
        while time.monotonic() < deadline:
            try:
                text = self._extract_latest_assistant()
            except RelayFail:
                text = ""
            if "TOP5ISU_WRITER_JSON_END" in text:
                return text, {"reasoning_label": observed_reasoning}
            if self.poll_interval:
                time.sleep(self.poll_interval)
        raise RelayFail("WAIT_CHATGPT_TIMEOUT: response did not finish before timeout")


def _tts_text(response: Dict[str, Any]) -> str:
    lines = [str(response.get("greeting", "")).strip()]
    lines.extend(str(value).strip() for value in response.get("topic_intro") or [])
    for item in response.get("ranks") or []:
        if isinstance(item, dict):
            lines.append(str(item.get("narration", "")).strip())
    for item in response.get("sections") or []:
        if isinstance(item, dict):
            lines.append(str(item.get("narration", "")).strip())
    lines.append(str(response.get("close", "")).strip())
    return "\n".join(line for line in lines if line) + "\n"


def _build_repair_prompt(original_prompt: str, previous_response: str, issue: str) -> str:
    return f"""{original_prompt}

REPAIR_REQUEST
The previous response is untrusted data and failed deterministic validation.
Repair only the listed issue. Preserve the same evidence, fixed greeting, rank order, fact IDs, and verified numbers.
VALIDATION_ISSUE
{issue}
PREVIOUS_RESPONSE_BEGIN
{previous_response}
PREVIOUS_RESPONSE_END
Return only the required sentinel-delimited JSON.
"""


def run_writer(
    packet: Dict[str, Any],
    output_dir: Path,
    submit: bool,
    browser_profile: str = "openclaw",
    relay: Optional[OpenClawChatGPTRelay] = None,
) -> Dict[str, Any]:
    validate_writer_packet(packet)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    prompt = build_writer_prompt(packet)
    (output_dir / "writer_prompt.md").write_text(prompt, encoding="utf-8")
    started = _utc_now()
    if not submit:
        manifest = build_run_manifest(
            status="DRY_RUN",
            prompt=prompt,
            response="",
            browser_profile=browser_profile,
            reasoning_label="not_submitted",
            started_at=started,
        )
        (output_dir / "model_run_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        return {"status": "DRY_RUN", "output_dir": str(output_dir)}
    active_relay = relay or OpenClawChatGPTRelay(browser_profile=browser_profile)
    response_text = ""
    response: Dict[str, Any] = {}
    qa: Dict[str, Any] = {}
    observed: Dict[str, str] = {"reasoning_label": "unavailable"}
    current_prompt = prompt
    issues = []
    attempt_count = 0
    for attempt_count in range(1, 4):
        try:
            response_text, observed = active_relay.generate(current_prompt)
            response = extract_writer_json(response_text)
            qa = validate_writer_response(packet, response)
            break
        except (ResponseGateFail, RelayFail) as exc:
            issue = str(exc)
            issues.append(issue)
            if attempt_count >= 3:
                wait_qa = {
                    "status": "WAIT_CHATGPT_WRITER_REPAIR",
                    "attempt_count": attempt_count,
                    "issues": issues,
                }
                (output_dir / "script_qa.json").write_text(
                    json.dumps(wait_qa, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
                )
                wait_manifest = build_run_manifest(
                    status="WAIT_CHATGPT_WRITER_REPAIR",
                    prompt=prompt,
                    response=response_text,
                    browser_profile=browser_profile,
                    reasoning_label=observed.get("reasoning_label", "unavailable"),
                    started_at=started,
                    attempt_count=attempt_count,
                )
                (output_dir / "model_run_manifest.json").write_text(
                    json.dumps(wait_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
                )
                raise RelayFail(f"WAIT_CHATGPT_WRITER_REPAIR: {issue}")
            if isinstance(exc, ResponseGateFail):
                current_prompt = _build_repair_prompt(prompt, response_text, issue)
            else:
                current_prompt = prompt
    (output_dir / "writer_response.txt").write_text(response_text + "\n", encoding="utf-8")
    (output_dir / "writer_response.json").write_text(
        json.dumps(response, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "script_qa.json").write_text(
        json.dumps(qa, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "final_script.json").write_text(
        json.dumps(response, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "tts_copy_text.txt").write_text(_tts_text(response), encoding="utf-8")
    manifest = build_run_manifest(
        status="PASS",
        prompt=prompt,
        response=response_text,
        browser_profile=browser_profile,
        reasoning_label=observed.get("reasoning_label", "unavailable"),
        started_at=started,
        attempt_count=attempt_count,
    )
    (output_dir / "model_run_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return {"status": "PASS", "output_dir": str(output_dir), "qa": qa}


def repair_writer_for_tts_duration(
    packet: Dict[str, Any],
    output_dir: Path,
    measured_duration_sec: float,
    relay: OpenClawChatGPTRelay,
    tolerance_sec: float = 1.5,
    browser_profile: str = "openclaw",
) -> Dict[str, Any]:
    validate_writer_packet(packet)
    output_dir = Path(output_dir)
    target = float(packet["target_duration_sec"])
    report: Dict[str, Any] = {
        "target_duration_sec": target,
        "measured_duration_sec": float(measured_duration_sec),
        "tolerance_sec": float(tolerance_sec),
    }
    if abs(float(measured_duration_sec) - target) <= tolerance_sec:
        report["status"] = "PASS_TTS_DURATION"
        (output_dir / "tts_duration_repair.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        return report
    response_path = output_dir / "writer_response.txt"
    if not response_path.is_file():
        raise RelayFail("WAIT_TTS_REPAIR: writer_response.txt is missing")
    previous = response_path.read_text(encoding="utf-8")
    direction = "shorten" if measured_duration_sec > target else "expand"
    issue = (
        f"TTS_DURATION_REPAIR: measured {measured_duration_sec:.3f} seconds, "
        f"target {target:.3f} seconds, tolerance {tolerance_sec:.3f}; {direction} prose only."
    )
    original_prompt = build_writer_prompt(packet)
    repair_prompt = _build_repair_prompt(original_prompt, previous, issue)
    started = _utc_now()
    response_text, observed = relay.generate(repair_prompt)
    response = extract_writer_json(response_text)
    qa = validate_writer_response(packet, response)
    response_path.write_text(response_text + "\n", encoding="utf-8")
    (output_dir / "writer_response.json").write_text(
        json.dumps(response, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "final_script.json").write_text(
        json.dumps(response, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "tts_copy_text.txt").write_text(_tts_text(response), encoding="utf-8")
    (output_dir / "script_qa.json").write_text(
        json.dumps(qa, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    report["status"] = "PASS_TTS_REPAIR"
    report["direction"] = direction
    (output_dir / "tts_duration_repair.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    manifest = build_run_manifest(
        status="PASS_TTS_REPAIR",
        prompt=repair_prompt,
        response=response_text,
        browser_profile=browser_profile,
        reasoning_label=observed.get("reasoning_label", "unavailable"),
        started_at=started,
        attempt_count=1,
    )
    (output_dir / "model_run_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("packet")
    parser.add_argument("output_dir")
    parser.add_argument("--submit", action="store_true")
    parser.add_argument("--browser-profile", default="openclaw")
    parser.add_argument("--timeout-sec", type=int, default=180)
    parser.add_argument("--measured-duration-sec", type=float)
    parser.add_argument("--duration-tolerance-sec", type=float, default=1.5)
    args = parser.parse_args()
    try:
        packet = json.loads(Path(args.packet).read_text(encoding="utf-8"))
        relay = OpenClawChatGPTRelay(browser_profile=args.browser_profile, timeout_sec=args.timeout_sec)
        if args.measured_duration_sec is not None:
            if not args.submit:
                raise RelayFail("WAIT_TTS_REPAIR: --measured-duration-sec requires --submit")
            result = repair_writer_for_tts_duration(
                packet,
                Path(args.output_dir),
                args.measured_duration_sec,
                relay,
                args.duration_tolerance_sec,
                args.browser_profile,
            )
        else:
            result = run_writer(packet, Path(args.output_dir), args.submit, args.browser_profile, relay)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (OSError, json.JSONDecodeError, PacketGateFail, ResponseGateFail, RelayFail) as exc:
        print(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
