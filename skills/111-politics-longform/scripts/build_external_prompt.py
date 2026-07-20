"""Build an external narration/review prompt packet for the Politics lane.

Thin lane adapter over the shared prompt factory. Reads the named template
from skills/111-politics-longform/prompt_templates/, the named input
artifacts, and the shared contracts, then writes:

    <episode-root>/20_script/external_packets/<packet>.md
    <episode-root>/20_script/external_packets/<packet>.manifest.json

The packet is generated locally only. It does NOT call an API or transport
a packet (manual external transport, NORM-005).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
SHARED_CORE = REPO_ROOT / "shared" / "workflow-harness" / "core" / "prompt_factory.py"
SKILL_TEMPLATES = REPO_ROOT / "skills" / "111-politics-longform" / "prompt_templates"
SHARED_TEMPLATES = REPO_ROOT / "shared" / "workflow-harness" / "prompt_templates"


def _import_prompt_factory():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "politics_prompt_factory", SHARED_CORE
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["politics_prompt_factory"] = mod
    spec.loader.exec_module(mod)
    return mod


def _read_input(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"STOP_PROMPT_INPUT_MISSING: {path}")
    return {"path": str(path), "content": path.read_text(encoding="utf-8")}


def build_packet(
    *,
    template_name: str,
    inputs: list[Path],
    included_segment_ids: list[str],
    excluded_fields: list[str],
    output_dir: Path,
    packet_name: str,
) -> dict:
    pf = _import_prompt_factory()
    template_path = SKILL_TEMPLATES / template_name
    if not template_path.exists():
        raise FileNotFoundError(
            f"STOP_TEMPLATE_MISSING: {template_path}"
        )
    template_text = template_path.read_text(encoding="utf-8")
    input_payloads = [_read_input(p) for p in inputs]
    result = pf.build_prompt(
        template_path=str(template_path),
        template_text=template_text,
        inputs=input_payloads,
        included_segment_ids=included_segment_ids,
        excluded_fields=excluded_fields,
        language_quality_contract=str(
            SHARED_TEMPLATES / "shared_language_quality_contract.md"
        ),
        external_authority_contract=str(
            SHARED_TEMPLATES / "shared_external_authority_contract.md"
        ),
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    packet_md = output_dir / f"{packet_name}.md"
    packet_manifest = output_dir / f"{packet_name}.manifest.json"
    packet_md.write_text(result["packet_text"], encoding="utf-8")
    manifest = dict(result["manifest"])
    manifest.pop("packet_text", None)
    packet_manifest.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return {
        "packet_path": str(packet_md),
        "manifest_path": str(packet_manifest),
        "packet_sha256": manifest["packet_sha256"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build a Politics external narration/review prompt packet."
    )
    parser.add_argument("--template", required=True)
    parser.add_argument("--input", action="append", type=Path, default=[])
    parser.add_argument("--segment-id", action="append", default=[])
    parser.add_argument("--exclude-field", action="append", default=[])
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--packet-name", required=True)
    args = parser.parse_args(argv)
    result = build_packet(
        template_name=args.template,
        inputs=args.input,
        included_segment_ids=args.segment_id,
        excluded_fields=args.exclude_field,
        output_dir=args.output_dir,
        packet_name=args.packet_name,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
