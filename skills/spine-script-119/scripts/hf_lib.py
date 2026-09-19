# -*- coding: utf-8 -*-
"""Compatibility entry point; scene implementation lives in hyperframes-politics-119/scripts/hf119.
Keep this bridge until two subsequent episodes pass and removal is reviewed.
"""
import os
import sys
from _common import CAPCUT_119, PEOPLE_ART, SKILL_ROOT
from runtime_paths import configured_path

renderer = configured_path('HF_POLITICS_119_SKILL', SKILL_ROOT.parent / 'hyperframes-politics-119')
sys.path.insert(0, str(renderer / 'scripts'))
import hf119
hf119.configure(
    people_art=PEOPLE_ART,
    capcut_119=CAPCUT_119,
    asset_source=os.environ.get('HF_ASSET_SOURCE') or
        SKILL_ROOT.parent / 'hyperframes-news-graphics' / 'assets' / 'news-institutional-flow' / 'assets',
)
from hf119 import init, build, T, P, Q, DIAGRAM_KINDS
