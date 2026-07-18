# TOP5 Profile

Use this profile for `style_profile=top5`.

## Structure

```text
hook -> 5위 -> 4위 -> 3위 -> 2위 -> 1위 -> close
```

- Each rank is a separate `ranking_item` block.
- Use one primary image or source visual per rank.
- Do not combine multiple ranks into one generated image.
- Keep rank order, source order, and timeline order explicit.
- Verify the date and source for money, statistics, records, and rankings.
- Mark estimates as estimates in visible or narration copy.

## Audio

- TTS is the primary narration lane.
- Source video audio is muted by default.
- A verified source quote may be retained only when the handoff identifies its
  source range and speaker role.

## Visuals

- Replace every root-template sample image.
- Preserve the assigned entrance effect while replacing its visual material.
- Keep rank labels readable without embedding essential Korean text inside AI
  generated images.
