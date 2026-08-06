from __future__ import annotations

import argparse
import json
from pathlib import Path

from v2_contract_runtime import SUPPORTED_OPERATIONS, build_project


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--capabilities", action="store_true")
    parser.add_argument("--production-plan", type=Path)
    parser.add_argument("--root-contract", type=Path)
    parser.add_argument("--workspace-root", type=Path)
    parser.add_argument("--asset-manifest", type=Path)
    parser.add_argument("--output-project", type=Path)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    if args.capabilities:
        print(json.dumps({"operations": sorted(SUPPORTED_OPERATIONS)}, ensure_ascii=False, indent=2))
        return 0
    required = {
        name: getattr(args, name)
        for name in (
            "production_plan",
            "root_contract",
            "workspace_root",
            "asset_manifest",
            "output_project",
            "receipt",
        )
    }
    missing = [name.replace("_", "-") for name, value in required.items() if value is None]
    if missing:
        parser.error("missing required arguments: " + ", ".join(f"--{name}" for name in missing))
    result = build_project(
        args.production_plan,
        args.root_contract,
        args.workspace_root,
        args.asset_manifest,
        args.output_project,
        args.receipt,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
