# G60 — Clean CapCut Assembly and Static Harness

> Lane: `general_shorts_production`
> Owner skill: `000short-production-agent`
> Requires: G50 PASS (track plan)
> CapCut root: `shrt white`
> Schema version: `shared-gates-separated-lanes-v2`

## Purpose

Clone the clean `shrt white` root and replace only episode content.
Static harness verifies the assembly against the template contract
without opening the CapCut GUI.

## Hard rules

```text
clone only clean shrt white (never use a failed prior project as input)
assemble only approved roles/assets from the G50 track plan
enforce template x, y, scale, rotation, font, font_size, alignment,
    opacity, text box, layer, track locks (P02 contract)
never open or close CapCut automatically
```

REFERENCE_ONLY materials in the timeline = HARD FAIL.
Unapproved visible text = HARD FAIL.
Source/order/hash mismatch = HARD FAIL.
Stale template image/video/audio/text = HARD FAIL.
Structural contamination = clean rebuild, not partial patch.

## Static PASS transitions to

```text
WAIT_USER_VISUAL_GATE
```

Static PASS never implies visual PASS. The user must open CapCut and
report visual problems. Only a `USER_VISUAL_PASS` ledger event advances
the lane past G60.USER.

## Template contract authority

`manifests/capcut-template-contracts/shrt_white_base_v1.json` carries the
locked slot values. Production must NOT regenerate them from memory.
HARD FAIL codes (V2 design section 41):
```text
FAIL_TEMPLATE_X_CHANGED
FAIL_TEMPLATE_Y_CHANGED
FAIL_TEMPLATE_SCALE_CHANGED
FAIL_TEMPLATE_ROTATION_CHANGED
FAIL_TEMPLATE_ALIGNMENT_CHANGED
FAIL_TEMPLATE_OPACITY_CHANGED
FAIL_TEMPLATE_TEXTBOX_CHANGED
FAIL_TEMPLATE_FONT_CHANGED
FAIL_TEMPLATE_FONT_SIZE_CHANGED
FAIL_LAYER_ORDER_CHANGED
FAIL_TRACK_ORDER_CHANGED
FAIL_STALE_TEMPLATE_IMAGE
FAIL_STALE_TEMPLATE_VIDEO
FAIL_STALE_TEMPLATE_AUDIO
FAIL_STALE_TEMPLATE_TEXT
FAIL_UNAPPROVED_TEMPLATE_MATERIAL
FAIL_MEDIA_MISSING
FAIL_MEDIA_PATH_UNRESOLVED
FAIL_MEDIA_HASH_MISMATCH
FAIL_MEDIA_DURATION_MISMATCH
```

## Validator contract

Static only. Never opens CapCut. On PASS, `auto_advance_class=DETERMINISTIC_ONLY`.
