# Stage 2 Patch Rules

Patch these root files and mirrors together:

```text
{draft}\draft_content.json
{draft}\template-2.tmp
{draft}\draft_meta_info.json
{draft}\Timelines\*\draft_content.json
{draft}\Timelines\*\template-2.tmp
```

Never patch root only.

Post-copy cleanup is mandatory on the copied episode draft, not only on the
locked `jungchilong` base.

After copying `jungchilong` to a new episode draft, remove or fail on:

- `draft_content.json.bak`
- `*.bak`
- `.before_*`
- `before_*`
- `*_backup_*`
- `crypto_key_store.dat.bak`
- `bottom_topic_comments_*`
- `t1_topic_texts.json`
- old roughcut media paths
- old locked media paths
- old `source_full` paths
- old active `onlineMaterial` references

If any leftover remains in the copied episode draft after cleanup, report
`FAIL_EPISODE_DRAFT_DIRTY_COPY`.

End-of-work cleanup gate:

- Before every final response after creating, repairing, patching, or validating
  a politics-longform CapCut draft, scan the active local draft folder again.
- Do not leave `*.bak`, `.before_*`, `before_*`, `*_backup_*`,
  `draft_content.json.bak`, `template-2.tmp.bak`, temporary helper scripts, or
  work notes inside the active draft/project tree.
- Move necessary backups to a backup folder outside the active draft tree, or
  delete safe leftovers. Never keep backup files beside `draft_content.json`,
  `template-2.tmp`, `draft_meta_info.json`, or any `Timelines/*` JSON.
- Rerun `validate_politics_longform_draft.py` after cleanup when a draft was
  modified. If cleanup cannot be completed, report `FAIL_PROJECT_CLEANUP` or
  `WAIT_PROJECT_CLEANUP` instead of claiming PASS.
- The final answer must mention the project cleanup status when a CapCut draft
  was touched.

Mirror sync rule:

- There are 3 logical locations and at least 4 files to synchronize.
- Root `draft_content.json` and root `template-2.tmp` must be byte-identical.
- Every `Timelines\{GUID}\draft_content.json` must match the root MD5.
- Every `Timelines\{GUID}\template-2.tmp` must match the root MD5.
- If any MD5 differs after patching, report `FAIL_JSON_MIRROR_MD5` and fix
  before opening CapCut or claiming PASS.

Visible text roles:

- `t1`: source channel only, `출처 {채널명}`
- `t2`: source upload date only, `YYYY.MM.DD`
- `t3`: flow strap
- `t4`: lower T1 commentary
- `t5`: fixed subscribe line

Rules:

- split t1/t2 at every source-video transition
- never put date text in t1
- never put channel text in t2
- use role detection before hard-coded track index
- preserve `jungchilong` geometry, font, stroke, color, render order, banners, subscribe graphics, transitions, and effects unless user asks to redesign
- keep source speech embedded unless user explicitly asks for TTS, narration, BGM, or detached audio repair
- visible text must not expose internal terms such as `M1-`, `roughcut`, `edl`, or `진입`
- use UTF-8 file IO; stop at `WAIT_ENCODING_UNSAFE` if Korean is corrupted

Cache folder scan is mandatory after copying and patching. Scan these folders
if present:

```text
{draft}\{GUID}\materials\
{draft}\{GUID}\Resources\
{draft}\{GUID}\common_attachment\
{draft}\Resources\
{draft}\common_attachment\
```

Fail if they contain or actively reference previous episode media, old source
video, old locked clips, old onlineMaterial media, or unknown media not
whitelisted by the current episode manifest.

If `{draft}\subdraft\` exists, scan every subdraft JSON and media reference.
No old source path, old locked clip, old onlineMaterial reference, or previous
episode media may remain. If found, report `FAIL_SUBDRAFT_OLD_REFERENCE`.

After patching and cleanup, run:

```powershell
python scripts/validate_politics_longform_draft.py --draft "<local CapCut draft path>" --manifest "<episode>/00_source/source_manifest.json" --require-locked-clips
```

If CapCut is open or background processes remain, do not overwrite an existing
target draft folder.
