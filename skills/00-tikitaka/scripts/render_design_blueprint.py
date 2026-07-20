"""Render design_blueprint.json to design_blueprint.md deterministically.

Thin lane adapter over shared/workflow-harness/core/canonical_render.py.
The MD is a projection of the canonical JSON; never hand-edited.

If a hand-edited MD diverges, raise HUMAN_MD_CANONICAL_JSON_MISMATCH
(V2 design section 37).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
GENERATED_CORE = (
    REPO_ROOT
    / "skills"
    / "00-tikitaka"
    / "scripts"
    / "_generated"
    / "workflow_harness_core.py"
)


def _import_core():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "tikitaka_render_core", GENERATED_CORE
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["tikitaka_render_core"] = mod
    spec.loader.exec_module(mod)
    return mod


def render(*, canonical_json_path: Path, output_md_path: Path) -> dict:
    core = _import_core()
    canonical = json.loads(canonical_json_path.read_text(encoding="utf-8"))
    md = core.render_markdown(canonical)
    output_md_path.parent.mkdir(parents=True, exist_ok=True)
    output_md_path.write_text(md, encoding="utf-8")
    return {
        "canonical_path": str(canonical_json_path),
        "rendered_md_path": str(output_md_path),
        "status": "PASS",
    }


def reconcile(*, canonical_json_path: Path, human_md_path: Path) -> dict:
    core = _import_core()
    canonical = json.loads(canonical_json_path.read_text(encoding="utf-8"))
    human_md = human_md_path.read_text(encoding="utf-8")
    return core.reconcile_human_md(canonical=canonical, human_md=human_md)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Render (or reconcile) the Shorts design blueprint MD from canonical JSON."
    )
    parser.add_argument("--canonical", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--reconcile-md", type=Path,
                        help="If set, reconcile this MD against the canonical instead of rendering.")
    args = parser.parse_args(argv)

    if args.reconcile_md:
        result = reconcile(
            canonical_json_path=args.canonical,
            human_md_path=args.reconcile_md,
        )
    else:
        if not args.output:
            print("--output is required when not reconciling", file=sys.stderr)
            return 2
        result = render(
            canonical_json_path=args.canonical,
            output_md_path=args.output,
        )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
