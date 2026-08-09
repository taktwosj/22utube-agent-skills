# Episode cards contract

Compile only approved inputs from A/D and any explicitly requested B/C into:

```text
{episode_dir}/50_capcut_project/episode_cards.json
```

Do not give an operations dashboard or a full `production_console.json` to the
CapCut writer. Extract the approved `scenes[]` and bind each card to source and
lock hashes first.

For PRE-119, validation produces a report/plan only. After A/D and requested B/C
have real assets, run `compile_pre119_episode_cards.py` with the validation report
and `politics-pre119-abcd-assets.v1` evidence. Every used audiovisual or image
asset requires an existing local file, literal matching SHA-256, and positive
duration evidence before this file is emitted.

The compiler also binds cards to `validated_plan`: requested narration or image
lanes must contribute their matching card type, unrequested lanes cannot inject
those card types, and every source/narration card's `lower_mode` must match the
validated PRE-119 selector. A lane status PASS without a matching card is not
sufficient evidence.

```json
{
  "schema": "politics-longform-episode-cards.v1",
  "episode_id": "PL_YYYYMMDD_slug",
  "project_name": "PL_YYYYMMDD_slug_capcut_v1",
  "canvas": {"width": 1920, "height": 1080, "fps": 30},
  "cards": [
    {
      "card_id": "C001",
      "card_type": "SOURCE_VIDEO",
      "target_start_us": 0,
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
INTRO             optional root-duration hook text over the root intro background
CHAPTER_CARD      optional 16:9 episode image, default 3 seconds when silent
SOURCE_VIDEO      locked source video and its embedded source audio
NARRATION_IMAGE   optional episode image with a requested narration asset
NARRATION_VIDEO   optional video with a requested narration asset
TEXT_EXPLAINER    text-only information card when specifically approved
ENDING            ending card or closing source-video block
```

The default no-extras build is contiguous `SOURCE_VIDEO` chapters 1→2→3→4 from
t=0 with embedded source audio. It has no intro, chapter image, narration card,
narration audio, or narration SRT. Image placement is flexible
from 0..N: chapter guides and/or strong emphasis or narration beats. A selected
`CHAPTER_CARD` requires its image. Select `NARRATION_IMAGE` only when both
narration and images were explicitly requested. Do not invent a replacement
card type or schema field when images are absent.

## Independent editorial selectors

These are required target modes, not claims of current builder support and not
new JSON fields. A mode needs implementation and validation evidence before PASS.

| Target card | Required visual+audio |
|---|---|
| `SOURCE_VIDEO` | `VIDEO+SOURCE` |
| `NARRATION_VIDEO` | `VIDEO+NARRATION` |
| `CHAPTER_CARD` | `IMAGE+SILENT` |
| `NARRATION_IMAGE` | `IMAGE+NARRATION` |

Do not claim `VIDEO+SILENT` or `IMAGE+SOURCE` without separate implementation.
For narration plus video, keep video visible and require proven narration/source-audio routing.

| Scenario | visual | audio | active optional lane | Result |
|---|---|---|---|---|
| video100 chapters 1→2→3→4 | `VIDEO` | `SOURCE` | none | t=0 sequential `SOURCE_VIDEO`, no intro |
| narration plus video | `VIDEO` | `NARRATION` | B | video stays visible; narration active |
| image between chapters | `IMAGE` | `NARRATION` or `SILENT` | C, plus B only for narration | emphasis or chapter image |
| narration between chapters | `VIDEO` or `IMAGE` | `NARRATION` | B, plus C only for image | requested narration beat |
| neither optional lane | `VIDEO` | `SOURCE` | none | plain sequential source videos |

## Required invariants

- Without an intro request, `C001` is `SOURCE_VIDEO` and starts at zero even when
  the resolved root layout has a nonzero `content_start_us`. If an intro is
  explicitly requested, `C001` is `INTRO` and its duration equals the resolved
  layout contract's `content_start_us`. A requested duration that contradicts the
  root boundary is invalid; no fixed five-second fallback is allowed.
- Cards are sorted by `target_start_us`; every next start equals the previous
  end. No inferred blank time is allowed.
- A silent `CHAPTER_CARD` is exactly 3,000,000 microseconds and uses
  `lower_mode=NONE`; a selected chapter card has valid `image_file` and
  `image_sha256`.
- A `SOURCE_VIDEO` has a `source_identity_ref`, actual source channel/date,
  and `target_duration_us == source_duration_us`.
- The total project duration equals the final card end exactly.
- One video lane contains cards in declared time order. Decorative overlays may
  be separate tracks, but source clips cannot be stair-stepped across tracks.
- A chapter title persists from its card until the next chapter card; source
  and date persist only for the corresponding source-video card.

## Lower two-line slot

The user-facing lower selector is exactly one of `SRT`, `COMMENTARY_2LINE`, or
`NONE`. Map it by active audio:

```text
SOURCE + SRT       -> SOURCE_TTS with source SRT
NARRATION + SRT    -> NARRATION_TTS with narration SRT
SILENT + SRT       -> invalid; omit
COMMENTARY_2LINE   -> VIDEO100_EXPLAINER
NONE               -> NONE
```

- `SOURCE_TTS` requires the locked source SRT cues and preserves their text.
- `NARRATION_TTS` uses the direct-119 generated and aligned narration SRT.
- `VIDEO100_EXPLAINER` is a short evidence-bound explanation, not a new fact.
- `NONE` deliberately leaves the lower area empty.
- Do not make overlapping lower segments. Use no `·` character in generated
  VIDEO100 text; use a comma or a line break.

A user-supplied 111 narration SRT is optional, not a prerequisite.

For PRE-119 `SOURCE_TTS`, the post-cut card evidence also carries
`raw_transcript_path`, `raw_transcript_sha256`, `display_srt_path`,
`display_srt_sha256`, and `display_transform`. Allowed display transforms are
only `SPLIT`, `CLAMP`, `LINE_BREAK`, and `DIALOGUE_MARKER_REMOVAL`. The compiler
maps the verified DISPLAY SRT to builder `source_srt_file` while retaining the
RAW hash as provenance. It never rewrites RAW transcript bytes.

## Media portability

`source_file` and `image_file` are build-machine inputs, not a portable root
reference. The builder copies video/audio assets into a unique local `Media`
folder and writes intentionally offline paths for a single CapCut relink.
Chapter images are embedded in the local draft Resources folder.

The portable elements are the root contract, root ZIP, root manifest, cards,
hashes, and reports under `WORKSPACE_ROOT`. A cross-machine handoff never
declares a user profile, CapCut cache, or local media path as the root asset.
