# Episode cards contract

Compile only approved Stage 2 inputs into:

```text
{episode_dir}/50_capcut_project/episode_cards.json
```

Do not give an operations dashboard or a full `production_console.json` to the
CapCut writer. Extract the approved `scenes[]` and bind each card to source and
lock hashes first.

```json
{
  "schema": "politics-longform-episode-cards.v1",
  "episode_id": "PL_YYYYMMDD_slug",
  "project_name": "PL_YYYYMMDD_slug_capcut_v1",
  "canvas": {"width": 1920, "height": 1080, "fps": 30},
  "cards": [
    {
      "card_id": "C001",
      "card_type": "INTRO",
      "target_start_us": 0,
      "target_duration_us": 5000000,
      "intro_text": "오늘 볼 쟁점\n확인할 핵심"
    },
    {
      "card_id": "C002",
      "card_type": "CHAPTER_CARD",
      "target_start_us": 5000000,
      "target_duration_us": 3000000,
      "image_file": "C:/local/chapter_01.png",
      "image_sha256": "<sha256>",
      "chapter_label": "챕터 1",
      "chapter_hook": "하루 만에 뒤집힌 숫자",
      "lower_mode": "NONE"
    },
    {
      "card_id": "C003",
      "card_type": "SOURCE_VIDEO",
      "target_start_us": 8000000,
      "target_duration_us": 27477000,
      "source_file": "C:/local/S03.mp4",
      "source_start_us": 242000000,
      "source_duration_us": 27477000,
      "source_identity_ref": "S03_LOCK",
      "source_channel": "MBCNEWS",
      "source_date": "2026.08.02",
      "original_audio_mode": "embedded",
      "lower_mode": "VIDEO100_EXPLAINER",
      "lower_text": "공식 득표 수치가\n판을 바꿨다"
    }
  ]
}
```

## Card types

```text
INTRO             5-second hook text over the root intro background
CHAPTER_CARD      16:9 episode image, default 3 seconds when silent
SOURCE_VIDEO      locked source video and its embedded source audio
NARRATION_IMAGE   episode image with a locked narration asset
NARRATION_VIDEO   video with a locked narration asset
TEXT_EXPLAINER    text-only information card when specifically approved
ENDING            ending card or closing source-video block
```

## Required invariants

- `C001` is `INTRO`, starts at zero, and is exactly 5,000,000 microseconds.
- Cards are sorted by `target_start_us`; every next start equals the previous
  end. No inferred blank time is allowed.
- A silent `CHAPTER_CARD` is exactly 3,000,000 microseconds and uses
  `lower_mode=NONE`.
- A `SOURCE_VIDEO` has a `source_identity_ref`, actual source channel/date,
  and `target_duration_us == source_duration_us`.
- The total project duration equals the final card end exactly.
- One video lane contains cards in declared time order. Decorative overlays may
  be separate tracks, but source clips cannot be stair-stepped across tracks.
- A chapter title persists from its card until the next chapter card; source
  and date persist only for the corresponding source-video card.

## Lower two-line slot

At each instant exactly one mode may apply:

```text
SOURCE_TTS
NARRATION_TTS
VIDEO100_EXPLAINER
NONE
```

- `SOURCE_TTS` requires the locked source SRT cues and preserves their text.
- `NARRATION_TTS` requires the locked 111 narration SRT cues.
- `VIDEO100_EXPLAINER` is a short evidence-bound explanation, not a new fact.
- `NONE` deliberately leaves the lower area empty.
- Do not make overlapping lower segments. Use no `·` character in generated
  VIDEO100 text; use a comma or a line break.

## Media portability

`source_file` and `image_file` are build-machine inputs, not a portable root
reference. The builder copies video/audio assets into a unique local `Media`
folder and writes intentionally offline paths for a single CapCut relink.
Chapter images are embedded in the local draft Resources folder.

The portable elements are the root contract, root ZIP, root manifest, cards,
hashes, and reports under `WORKSPACE_ROOT`. A cross-machine handoff never
declares a user profile, CapCut cache, or local media path as the root asset.
