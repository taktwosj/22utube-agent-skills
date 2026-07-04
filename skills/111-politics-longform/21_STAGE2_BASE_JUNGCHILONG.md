# Stage 2 Base - jungchilong

Default base:

```text
visible CapCut project name: jungchilong
local draft folder: %LOCALAPPDATA%\CapCut\User Data\Projects\com.lveditor.draft\jungchilong
```

`jungchilong` is a visual skeleton, not an episode project. Use it only by
copying it to a new episode draft. Never patch the locked base itself.

Before use, validate the base with the public validator:

```powershell
python scripts/validate_clean_base.py --base "$env:LOCALAPPDATA/CapCut/User Data/Projects/com.lveditor.draft/jungchilong"
```

Base validation must check:

- base folder exists and is readable
- no `.bak`, `before_*`, `.before_*`, or `*_backup_*` files at any depth
- no `bottom_topic_comments_*`
- no `t1_topic_texts.json`
- no old source video path
- no roughcut or locked media path
- no real episode source label, date, person name, or channel name
- no old active `onlineMaterial` reference from a previous episode
- no Korean mojibake or replacement characters in active JSON text

Allowed visible text in the locked base:

```text
__SOURCE__
출처 __SOURCE__
__DATE__
__FLOW_1__
__FLOW_2__
__FLOW_3__
__FLOW_4__
__FLOW_5__
__FLOW_6__
__LOWER_T1_A__
__LOWER_T1_B__
구독과 좋아요는 큰힘이 됩니다. 감사합니다.
구독과 좋아요는 큰 힘이 됩니다. 감사합니다.
구독은 큰힘이 됩니다.
구독은 큰 힘이 됩니다.
```

If missing:

```text
WAIT_JUNGCHILONG_BASE_MISSING
```

If dirty:

```text
FAIL_JUNGCHILONG_DIRTY_BASE
```

Move leftovers to a backup folder before using the base. Treat these files as
contamination risk because copy/repair scripts can accidentally re-read old
paths from them; do not assume CapCut itself is actively reading every backup
file.
