# Stage 2 Validation Harness

Final harness is mandatory. Do not claim PASS from JSON existence or parsing.

Required report:

```text
90_reports\final_harness_report.json
```

Frame evidence block - required before PASS:

1. Produce or locate a review/export MP4 for the built draft.
2. Use ffmpeg to extract first, middle, and final-section frames.
3. Save the frame paths under the episode report/evidence folder.
4. Inspect those frames for source label placement, flow strap, lower T1, clipping, old media, black frames, and wrong base visuals.
5. Record the frame paths and human/agent verdict in `final_harness_report.json`.

If a review/export MP4 cannot be produced and no equivalent CapCut preview
screenshots exist, report `WAIT_FRAME_EVIDENCE`. Do not PASS.

Validator evidence block - required before PASS:

- `scripts/validate_clean_base.py` was run against `jungchilong`
- `scripts/validate_politics_longform_draft.py` was run against the copied episode draft
- the command outputs or JSON reports are saved or summarized in `final_harness_report.json`
- Claude hooks, when available, are only a guardrail; they do not replace these validator commands

Required gates:

- `stage1_download`: Stage 1 says `PASS_SOURCE_DOWNLOADED`, each used source file exists, and ffprobe evidence is present
- `validator_clean_base`: `validate_clean_base.py` returned PASS for current `jungchilong`
- `validator_episode_draft`: `validate_politics_longform_draft.py` returned PASS for the copied episode draft
- `base_standard`: draft was copied from current `jungchilong`
- `jungchilong_clean_base`: base had placeholders/fixed subscribe text only and no dirty files or old active refs
- `episode_draft_clean_copy`: copied draft contains no `.bak`, `before_*`, `*_backup_*`, `bottom_topic_comments_*`, `t1_topic_texts.json`, old media path, or old active refs
- `cache_folder_scan`: root `{GUID}` materials, Resources, common_attachment, and subdraft folders contain no previous episode media or active old references
- `encoding_safety`: no Korean corruption, `�`, `占`, `?뺤`, or mojibake
- `speech_tail`: every locked clip includes the completed final syllable and natural tail room or a documented phrase-break reason
- `source_label_safe_area`: t1/t2 are inside the 1280x720 visible frame
- `flow_strap_quality`: two-line flow when needed, at most six understandable items, no isolated 1-2 character labels
- `lower_t1_quality`: concrete two-line commentary, each lower line 26 characters or less including spaces, no overflow or lower banner conflict
- `lower_t1_analysis_angle`: lower T1 was written from video subtitles/source speech and gives a richer favorable interpretation for Yoo Si-min, Lee Jae-myung, the Democratic Party, or the democratic/progressive camp when supported by the source
- `preview_visual`: required frame evidence or screenshots exist and were inspected
- `json_mirror_sync`: root and `Timelines/*` mirrors are synchronized
- `json_mirror_md5`: root `draft_content.json`, root `template-2.tmp`,
  every `Timelines/{GUID}/draft_content.json`, and every
  `Timelines/{GUID}/template-2.tmp` share the same MD5 after patching
- `no_internal_terms`: no `M1-`, `roughcut`, `edl`, `진입` in visible text
- `open_capcut_safety`: no existing draft was overwritten while CapCut was open

Gate statuses:

- unchecked evidence => `WAIT`
- failed evidence => `FAIL`
- all gates passed => `PASS`
