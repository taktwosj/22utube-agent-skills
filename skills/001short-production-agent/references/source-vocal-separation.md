# Source vocal separation

Use this only when approved source speech must remain audible. Do not use it for TTS-only or caption-only Shorts. Raw `SOURCE_CLIP` audio is not an A10 fallback: it can carry the original music back into the project.

1. Run `python scripts/separate_source_vocals.py --preflight`. It verifies an actual Demucs WAV-write path, not merely package presence. If it returns `WAIT_DEMUCS_RUNTIME`, install the one-time separator runtime with `py -3.12 -m pip install --force-reinstall -r requirements-vocal-separation.txt`, then rerun preflight. CapCut's vocal-retain metadata is not a substitute.
2. Run `python scripts/separate_source_vocals.py --source {source.mp4} --out-dir {episode_root}/30_audio_srt/source_vocals --episode-id {episode_id}`.
3. Run `python scripts/validate_vocal_stem.py --manifest {episode_root}/30_audio_srt/source_vocals/vocal_stem_manifest.json`.
4. Set the audio lock to `audio_source=SOURCE_VOCAL_STEM`; set its `audio_path` and its only A10 role file to `source_vocals/vocals.wav`; include the manifest path and SHA.
5. Pass the same `vocals.wav` as the builder's `source_audio`. VIDEO stays muted and A12 stays empty.

## Existing editable CapCut draft

When the approved draft already exists and its only nonempty audio track is the retained source-speech track, do not re-add raw source audio or use CapCut's vocal-retain setting. With CapCut fully closed, run:

```text
python scripts/rebind_existing_draft_vocal_stem.py --draft {local_capcut_draft} --manifest {episode_root}/30_audio_srt/source_vocals/vocal_stem_manifest.json
```

The rebind gate rejects an ambiguous/multi-audio draft, copies `vocals.wav` to the draft's portable `Resources/media/` tree, preserves every existing A10 source/target range, creates `draft_content.pre_vocal_stem.json`, and records `vocal_stem_rebind_receipt.json`. It does not add A12 or choose/add any BGM. Reopen CapCut after the static readback; it must show the expected A10 waveform and play all retained-speech cuts before reporting GUI success.

The separator manifest proves that an actual model generated the stem. It does not automatically prove that every trace of music is inaudible; listen at the hook, middle, and ending before completion reporting.
