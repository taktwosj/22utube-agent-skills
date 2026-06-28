# 11short CapCut Text Effect Presets

11short has a stricter text contract than 0shrt. The normal harness draft must keep exactly three visible text classes:

```text
top fixed title
bottom yellow caption
middle purple overlay
```

Therefore the shared text-effect presets are attached to 11short only as explicit opt-in custom effects. Do not add fire, neon, or repeated laugh layers to a normal 11short remake unless the user explicitly asks for a meme/text-effect variant and accepts that it is not the default harness profile.

Shared preset source:

```text
${env:UTUBE_ROOT}\0shrt\assets\emotion_pack\text_effect_presets.md
```

Reusable overlay bank source:

```text
${env:UTUBE_ROOT}\0shrt\assets\effect_bank
```

These finished overlay exports are custom/test only for 11short:

```text
video/fire/BANK_FIRE_OVERLAY_BLACK.mp4
video/laugh/BANK_LAUGH_RING_KKK_GREEN.mp4
video/laugh/BANK_LAUGH_POP_KKK_GREEN.mp4
video/text/BANK_TEXT_POP_TIRED_GREEN.mp4
```

Available opt-in presets:

```text
TXT_FIRE_레전드
TXT_FIRE_분노폭발
TXT_NEON_샤갈
TXT_NEON_핑크대사
TXT_CUTE_반짝
TXT_POP_하하하증식
TXT_POP_조롱폭발
TXT_COMIC_말풍선웃음
```

## 11short Guardrails

- Default 11short production: do not use these presets.
- If the user asks for a custom effect draft, report it as `layout_variant=custom_text_effect`.
- Keep the original default draft or create a separate variant draft; never overwrite a user-edited draft.
- Do not hide or replace required bottom yellow captions.
- Do not add extra text tracks to a harness-targeted draft.
- `TXT_POP_하하하증식` requires overlapping duplicate text layers, so it is invalid for the normal 11short harness. Use only in a separate custom/test draft.
- `TXT_FIRE_레전드`, `TXT_FIRE_분노폭발`, `TXT_NEON_샤갈`, `TXT_NEON_핑크대사`, and `TXT_CUTE_반짝` are also custom/test only unless the generator is explicitly changed and the harness is updated.

## Safer 11short Alternative

When the user wants extra punch but still needs a valid 11short harness draft, use only the existing allowed middle purple overlay and scene motion:

```text
middle purple overlay text: short Korean reaction
video motion: zoom, pan, or light shake
SFX: source audio or normal 11short audio rules only
no extra text class
no overlapping middle overlays
```

This preserves the 3-text layout and avoids a false PASS/real visual fail mismatch.
