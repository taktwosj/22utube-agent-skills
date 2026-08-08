#!/usr/bin/env python3
"""Resolve and verify the active politics-longform CapCut root bundle."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from root_bundle import resolve_active_root


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-root", type=Path, required=True)
    args = parser.parse_args()
    resolved = resolve_active_root(args.workspace_root)
    print(json.dumps(resolved.to_report(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(2)
