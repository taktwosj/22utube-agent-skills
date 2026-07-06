from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


sys.dont_write_bytecode = True


def load_source_module_no_bytecode(module_name: str, path: Path):
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
