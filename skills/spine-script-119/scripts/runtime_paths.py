"""Resolve shared inputs and local application folders without a machine account path."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

def settings() -> dict:
    if os.name == 'nt':
        base=Path(os.environ.get('LOCALAPPDATA',str(Path.home()/'AppData/Local')))/'ZSkillSync'
    else:
        base=Path.home()/'Library/Application Support/ZSkillSync'
    file=Path(os.environ.get('Z_SKILLS_PATH_CONFIG',str(base/'paths.json')))
    return json.loads(file.read_text(encoding='utf-8-sig')) if file.is_file() else {}

def configured_path(name: str, fallback: Path) -> Path:
    raw=os.environ.get(name) or settings().get(name)
    return Path(os.path.expandvars(os.path.expanduser(raw))) if raw else fallback

def shared_root() -> Path:
    configured=os.environ.get('SHARED_DATA_ROOT') or settings().get('SHARED_DATA_ROOT')
    if configured:
        return Path(os.path.expandvars(os.path.expanduser(configured)))
    raise RuntimeError('SHARED_DATA_ROOT_REQUIRED: configure ZSkillSync/paths.json or SHARED_DATA_ROOT for this machine')

def require_local_path(path: Path, label: str) -> Path:
    path=Path(path).expanduser().absolute()
    def network(candidate: Path) -> bool:
        if str(candidate).startswith(('\\\\','//')):
            return True
        if os.name=='nt':
            import ctypes
            if ctypes.windll.kernel32.GetDriveTypeW(str(candidate.anchor))==4:
                return True
        shared=os.environ.get('SHARED_DATA_ROOT') or settings().get('SHARED_DATA_ROOT')
        return bool(shared and candidate.is_relative_to(Path(shared).expanduser().absolute()))
    if network(path):
        raise RuntimeError(f'{label}_MUST_BE_LOCAL: copy the handoff package to a local working folder first')
    resolved=path.resolve()
    if network(resolved):
        raise RuntimeError(f'{label}_MUST_BE_LOCAL: linked working folder points to a network share')
    return resolved

def local_production_root() -> Path:
    folder='Movies' if sys.platform=='darwin' else 'Videos'
    default=Path.home()/folder/'22utube-work'
    return require_local_path(configured_path('LOCAL_PRODUCTION_ROOT',default),'LOCAL_PRODUCTION_ROOT')

def production_path(name: str, relative: str) -> Path:
    return require_local_path(configured_path(name,local_production_root()/relative),name)

def capcut_draft_root() -> Path:
    if sys.platform=='darwin':
        fallback=Path.home()/'Movies/CapCut/User Data/Projects/com.lveditor.draft'
    elif os.name=='nt':
        fallback=Path(os.environ.get('LOCALAPPDATA',str(Path.home()/'AppData/Local')))/'CapCut/User Data/Projects/com.lveditor.draft'
    else:
        raise RuntimeError('CAPCUT_UNSUPPORTED_OS: use the configured Windows or macOS production host')
    return require_local_path(configured_path('CAPCUT_DRAFT_ROOT',fallback),'CAPCUT_DRAFT_ROOT')
