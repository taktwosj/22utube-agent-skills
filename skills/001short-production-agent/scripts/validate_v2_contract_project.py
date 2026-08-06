from __future__ import annotations

import argparse
import json
from pathlib import Path

from v2_contract_runtime import validate_project


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--production-plan", type=Path, required=True)
    parser.add_argument("--layout-contract", type=Path, required=True)
    args = parser.parse_args()
    result = validate_project(args.project, args.production_plan, args.layout_contract)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
