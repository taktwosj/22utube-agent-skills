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

## Stage 01 자막 경계 검출은 STT로 교차검증하라

MAD 프레임 차분만으로 자막 경계를 뽑으면 **경계를 통째로 놓칠 수 있다.**
260817 에피소드에서 28.267초 경계가 임계 미달로 빠졌고, 그 뒤 자막 텍스트가 한 칸씩 밀린 채
표·오디오·자막 잠금까지 전부 통과했다. 조립 직전이 아니라 **Stage 01에서** 잡아야 한다.

교차검증 절차:

1. Demucs 보컬 스템에 faster-whisper를 돌린다(로컬, `~/.venvs/demucs`).
   ```
   ~/.venvs/demucs/bin/python -c "from faster_whisper import WhisperModel; ..."
   ```
   `WhisperModel("large-v3", device="cpu", compute_type="int8")`, `language="ko"`, `word_timestamps=True`.
2. 각 Bxx 구간의 자막 텍스트와 그 시간대의 발화를 대조한다.
   자막은 발화보다 **0.2~0.35초 늦게** 끝나는 것이 정상이다.
3. 어긋남이 0.5초를 넘는 구간이 있으면 그 구간에 **놓친 경계가 있다.**
   해당 창을 20ms 간격으로 프레임 차분해 정확한 지점을 찾는다(자막 전환은 MAD 40 이상으로 뚜렷하다).
4. 확정은 프레임 육안 판독으로 한다. STT는 어디를 봐야 하는지 알려줄 뿐 정본이 아니다.

`preflight_env.py`는 `whisper` 실행파일을 찾으므로 계속 MISSING으로 뜬다. OPTIONAL이고 무해하다.
