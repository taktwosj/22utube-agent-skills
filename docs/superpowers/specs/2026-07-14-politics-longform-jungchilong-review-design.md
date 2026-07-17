# Politics Longform Jungchilong Review Design

## Goal

Replace the stale YP007/source-only Stage 1 contract with a portable two-stage
politics-longform workflow whose only CapCut root is the verified `jungchilong`
archive. Stage 1 produces a rough timeline design plus one chronological review
packet. Stage 2 validates the returned external commentary, locks speech-safe
clips, assembles a cloned local `jungchilong` project, and reports actual state.

## Authority

- Skill source of truth: `%USERPROFILE%\agent-skills\skills\111-politics-longform`.
- Factory policy: `{WORKSPACE_ROOT}\22factory_20260628\AGENTS.md` and
  `docs\YOUTUBE_PRODUCTION_WORK_ORDER.md`.
- CapCut root archive:
  `00_asset_tools/templates/capcut/jungchilong/jungchilong_CAPCUT_20260714.zip`.
- Target profile: `jungchilong_base_v3_intro15`.
- Archive SHA-256: `WAIT_V3_TEMPLATE_PROMOTION`; pin the generated value only
  after CapCut close, internal intro packaging, and restore validation PASS.
- Canvas: `1920x1080` for political-longform projects. Thumbnail dimensions are
  a separate `1280x720` upload-asset rule.
- YP007, YP005, and YM007 are legacy visual references only.

## Stage 1: Rough Design and Review Packet

Stage 1 downloads/probes every production source, stores a complete local
transcript, and creates candidate source ranges, source/date labels, topic flow,
and lower two-line commentary. Every source records URL, video id, local path,
byte size, SHA-256, download state, and ffprobe PASS evidence.

The human-facing review artifact is one file,
`20_script/commentary_review_packet_sent.md`, ordered by final timeline. Each
stable `segment_id` block contains final timeline, original source range,
channel/date/topic, the complete transcript for that commentary interval, the
Stage 1 two-line draft, and blank external proposal/reason fields. Instructions
appear once at the top, not once per block. The sent packet hash, segment order,
and immutable payload digest are recorded in
`commentary_review_packet_manifest.json`.

The returned file is saved separately as
`commentary_review_packet_returned.md`. Stage 1 does not create CapCut drafts,
speech locks, locked clips, exports, or final/upload-ready claims.

## Stage 2: Editorial Approval, Locks, and Assembly

Stage 2 verifies that the sent packet still matches the Stage 1 packet manifest,
then checks returned segment ids and immutable transcript/timing fields. It
compares source transcript, Stage 1 draft, and
external proposal, then records `keep_stage1`, `accept_external`, `merge`, or
`rewrite` with a reason and final two lines in `commentary_decisions.json`.

Any source range, ordering, or commentary interval change invalidates
`SOURCE_TRANSCRIPT_VERIFIED`, `EXTERNAL_REVIEW_REFLECTED`, and
`DESIGN_APPROVED`, returning all three to `WAIT`. Approved assembly consumes
`timeline_design_approved.json`, never `timeline_design_draft.json`.

Before CapCut assembly, Stage 2 must create and validate:

- `speech_boundary_lock.json`
- `roughcut_edl_locked.json`
- `source_labels_locked.json`
- `locked_clips_manifest.json`
- ffprobe PASS evidence for every locked clip

The builder pins the archive member root and packaged file count independently
of the mutable manifest. It verifies the archive hash and a machine/owner/hash-
bound GUI restore gate,
clones the local `jungchilong` root to a new episode project, and edits only the
clone. It supports arbitrary clip/commentary counts and reads approved data
rather than episode-specific constants. Preassembly has no bypass. If any
post-rename step fails, project files, the CapCut registry, and report outputs
are rolled back.

## Timeline and Audio Rules

- With the v3 intro, commentary coverage starts at `15.083333` and is continuous
  with half-open ranges. Only explicitly intro-free legacy projects start at
  `00:00`.
- Segment lengths are speech-paragraph driven; target about 20 seconds, allowing
  10-35 seconds when source/topic boundaries require it.
- Line 1 summarizes the actual speech/fact. Line 2 adds a logically supported
  interpretation. Generic slogans, contradictions, unsupported claims, and
  adjacent repetition fail editorial review.
- Source speech remains embedded in video. Unless explicitly requested:
  `audio_track_count == 0`, `materials.audios == []`, each video segment volume
  is `1.0`, and locked-clip audio duration must be at least video duration minus
  `0.25` seconds.

## Portability and Evidence

Every episode records `active_writer_machine`, `lock_owner`,
`capcut_mode=local_only`, and `raw_capcut_sync=false`. Raw CapCut drafts, source
media, and locked clips stay machine-local; OneDrive stores relative manifests,
hashes, snapshots, restore notes, review text, and reports.

`PASS`, `FINAL_DESIGN`, and `upload_ready` remain separate. Archive integrity
PASS does not replace `LOCAL_GUI_RESTORE=PASS` on the active writer machine.

## Validation

Automated tests must prove contract wording, packet generation/parsing,
manifest-anchored immutable-field tamper detection, real media probing,
nonempty Stage 1 schemas, gate invalidation, mandatory preassembly, strong GUI
evidence, exact final text/timing, transactional rollback, dynamic counts,
1920x1080 output, audio coverage, portable paths, and required
`restore_notes.md`. The legacy July 14 rebuild remains a one-off
repair utility and must not be routed as the generic builder.
