# Operator-authored CapCut root rebuild

Use this when the operator designates a local CapCut project as the new canonical `top5isu` root.

## Safe transaction

1. Read the real project folder and active timeline; CapCut 8.9+ may keep current content under `Timelines/<id>/template-2.tmp` even when root `draft_content.json` is absent.
2. Confirm track roles and active material IDs from the saved draft. Never infer them from a screenshot alone.
3. Close CapCut before copying or writing project files.
4. Back up the current canonical ZIP, manifest, restore notes, and their hashes outside every skill-discovery directory.
5. Build a candidate under a separate staging root. Do not overwrite canonical files yet.
6. Localize every active external media, font, logo, frame, and animation resource under `Resources/`; rewrite active paths to the draft-path placeholder.
7. Remove `.bak`, user absolute paths, and machine identifiers from control JSON. Preserve only reusable CapCut resources.
8. Normalize root/timeline control targets (`draft_content.json`, `draft_info.json`, `template-2.tmp`) and track names.
9. Validate the candidate ZIP, extract it fresh, create a derived project with fresh project/timeline IDs, and read back media links, title lines, captions, source text, frame/logo durations, and animation names.
10. Replace canonical archive/notes first and manifest last. Re-run package validation and hash measurement from the canonical directory.
11. Sync source skill to the active runtime only after tests pass; compare hashes of builders, validators, schema, SKILL.md, and contract references.

### Root media identity lock

- Never retain a remote stock sample as an image prototype. Use four text-free neutral local placeholders.
- Every prototype must have a distinct local `material_id`, `source=0`, `source_platform=0`, empty category fields, and `is_copyright=false`.
- Root `key_value.json` must be `{}`. Remove stock provenance from `draft_meta_info.json`, `template.json`, `mini_draft.json`, every full-content mirror, and the canonical ZIP.
- A direct-copy regression build must replace all four neutral placeholders, leave zero placeholder files active or inert in the derived project, and produce unique material IDs for every episode image.

## TOP55 animation policy

- Every episode image gets exactly one transition animation.
- Generic prototypes alternate: `레트로 페이드 인`, `스트레치 인`.
- Exactly one or two semantic peak images use an approved fire effect: `불꽃 회오리`, `불꽃 스와이프`, or `불꽃 마법`.
- High-impact indices come from the blueprint/build contract when available; do not spray fire effects across all images.

## Completion boundary

Default completion is the editable project folder plus current draft readback/hash, package/draft validators, and assembly report. Opening or playing CapCut is optional and happens only when explicitly requested.

## Pitfalls

- Do not place backups beneath `~/.hermes/skills` or any configured skill-discovery root. A backup containing `SKILL.md` becomes a second discoverable skill and makes bare-name loading ambiguous.
- A packaging status string is not proof; remeasure archive SHA-256 and packaged file count.
- Do not use a previous episode as the new root. Import only a specifically required reusable resource from the prior verified canonical archive, then validate the new operator-authored layout independently.
- Shell title arguments need one literal `\n`; double escaping can leave a visible backslash at the end of T1.
