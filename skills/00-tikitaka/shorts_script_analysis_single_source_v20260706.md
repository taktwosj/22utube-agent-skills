# 쇼츠대본분석 단일 지침소스 v2026-07-06

This file is the active authority for current 11short/Tikitaka Shorts script
analysis. Use this file as the single project-attached source MD for Shorts
script analysis. Do not attach or apply legacy lower-caption, 3-layer, or
bottom-first-line instruction documents for current work.

## Authority

- Active output contract: `상단 + timed 중단 + 중단 TTS 글자만 복사`.
- Legacy output contracts are disabled for current work:
  - `하단`
  - `하단 원문`
  - separate bottom narration layer
  - 3-layer script package
  - `하단 첫마디 후보`
- If any older reference says `TTS 만들 글자만 복사`, read it as
  `중단 TTS 글자만 복사`.

## Layer Contract

```text
상단
고정 후킹 제목. 시간표를 붙이지 않는다.

중단
[0~3초]
(감정 / 반응 / 상황 / 장난 / 밈 / 화면 포인트)
"검증된 실제 인물 발화"
일반 텍스트 TTS/설명 후보

중단 TTS 글자만 복사
timed 중단 중 voice/TTS 의도 줄만 시간표 없이 모은 순수 원문
```

## Middle Caption Rules

- `중단` is the timed visible-caption authority.
- `"..."` is verified source speech only. Do not invent quoted speech.
- `(...)` is reaction, emotion, situation, visual point, SFX, meme framing, or
  viewer-read caption.
- Plain text can be narration-like middle caption text and may be included in
  `중단 TTS 글자만 복사` when it is intended for voice.
- Visual-only parenthesized captions are excluded from TTS copy unless the user
  explicitly wants them voiced.

## Prohibited Current Outputs

Do not create these for current Tikitaka script output:

- `하단`
- `하단 원문`
- `하단 첫마디 후보 5개`
- separate timed narration timeline outside `중단`
- 3-layer script package
- bottom/body caption narration layer

Allowed alias:

- `TTS 만들 글자만 복사` may appear only as a legacy alias of
  `중단 TTS 글자만 복사`. It is not a separate output contract.

## Assembly Design Authority

Current Tikitaka output is not only source reorder.

Before speaker-range design, complete this source-analysis order:

```text
source_identity_lock.json
-> prepare_source_voice.py
-> 10_analysis/audio/full_source_audio.wav
-> Demucs FULL_SOURCE_AUDIO separation
-> 10_analysis/audio/vocals.wav
-> SOURCE_VOICE_SEPARATION_GATE
-> speaker range design
```

The only valid skip is `NOT_REQUIRED_NO_SOURCE_SPEECH`, supported by a source
with no audio stream or explicit user/source-evidence confirmation. Missing
Demucs is `WAIT_DEMUCS_AVAILABLE`; do not use raw mixed audio as a fallback.
`no_vocals.wav` is not used.

`timeline_design.json` must describe a new Shorts assembly design with:

```text
source_order
timeline_order
assembly_role
caption_type
visible_text_role
audio_role
time_start
time_end
duration_basis
duration_status
audio_policy
visual_strategy
```

`source_order` and `timeline_order` must be separated.

`assembly_role` defines the function of the beat in the remake, such as intro
narration, verified speaker quote, reaction caption, payoff narration, or
transition.

`TTS` alone can mean visible caption text only. A voice/audio file is implied
only when narration is explicit, such as `caption_type=tts_narration` or
`audio_role=audio.narration_tts`.

Production must implement the locked assembly design without reinterpretation.

Every `speaker_quote` must use:

```text
source_audio_ref=10_analysis/audio/vocals.wav
source_audio_provenance=demucs_full_source_vocals
```

Any raw-video, pre-cut-before-separation, or missing source is
`WAIT_SOURCE_VOICE_Q_PROVENANCE`. In the handoff, `source_audio=on` means the
separate speaker/Q lane, never embedded source-video audio.

## Production Boundary

`00-tikitaka` may write draft script text, script handoff information, and the
two required source-analysis WAV artifacts created by `prepare_source_voice.py`.
It must not create Q clips, TTS voice files, SRT files, layout JSON, CapCut
drafts, exports, or upload packages. Production assets belong to
`000short-production-agent` after the user explicitly requests that stage.

## ChatGPT Project Two-Pass Review Contract

This file is the only review contract attached to the ChatGPT project
`쇼츠대본분석`. Do not attach a political-longform contract, a political-
shortform contract, an archived Shorts contract, or a second Shorts contract.

Every Shorts review packet must begin with:

```yaml
content_type: shorts
review_round: 1 | 2
review_cycle_id: stable ID shared by both rounds
packet_id: unique packet ID
sent_packet_sha256: SHA-256 of the canonical packet text with the first top-level hash metadata line removed
episode_id: episode ID
source_fingerprint_sha256: verified source SHA-256
truth_mode: fact_first | hook_first_writer_premise
```

The first response line must be `ROUTE=SHORTS`. The response must echo
`review_round`, `review_cycle_id`, `packet_id`, and `sent_packet_sha256`.
The sender computes `sent_packet_sha256` after normalizing line endings to LF
and removing only the first top-level `sent_packet_sha256:` line in the
current packet header. Embedded Round 1 response text in a Round 2 packet stays
unchanged, including its echoed hash line. This avoids both a self-referential
hash and ambiguous removal. The review gate separately records
`packet_sha256` as the SHA-256 of the complete saved packet file.
Every ChatGPT response ends with:

```text
external_review_status: PENDING_CODEX_REVIEW
```

ChatGPT is an external reviewer, not the final design owner. It must not declare
`ADOPTED`, `FINAL`, `PASS`, `SCRIPT_LOCK`, or production approval. Codex alone
assigns `ADOPTED`, `PARTIALLY_ADOPTED`, `REJECTED`, or `PENDING_EVIDENCE`
after checking the response against source evidence.

### Round 1 - INDEPENDENT_REVIEW and REVISION_PROPOSAL

Run Round 1 only after `timeline_design_gate.json status=PASS`. The packet must
contain the verified source identity, source evidence summary, Gemini raw notes
when available, `design_blueprint.md`, `timeline_design.json`,
`caption_beat_map.json`, the protected fields, and unresolved evidence items.

Review:

- first-three-second hook and viewer question
- remake order, similarity reduction, escalation, reversal, and payoff
- verified speech, OCR, names, relationships, numbers, and source ranges
- TTS/source-audio separation and caption semantic roles
- 10-character, one-line caption beats
- timing, hold/freeze/reuse strategy, and ending logic
- the selected `truth_mode`

Do not rewrite the whole design by preference. Diagnose first, then propose only
changes tied to a diagnosed issue. Each proposal uses:

```yaml
suggestion_id:
source_id:
segment_id:
before:
after:
revision_type:
reason:
evidence:
derived_from:
expected_effect:
expected_duration_change:
meaning_preserved:
protected_field_impact:
verification_state:
```

Round 1 output order:

```text
ROUTE=SHORTS
review_round: 1
review_cycle_id: ...
packet_id: ...
sent_packet_sha256: ...

## 1. INDEPENDENT_REVIEW
## 2. REVISION_PROPOSAL
## 3. HARD_BLOCKERS

external_review_status: PENDING_CODEX_REVIEW
```

Codex saves the unedited response, evaluates every suggestion, writes
`round1_codex_decisions.json`, applies accepted changes, and reruns every gate
invalidated by a structural or timing change.

### Round 2 - EVIDENCE_AUDIT

Run Round 2 after Humanize, block maps, TTS copy, and TTS timing reconciliation
are complete, but before `SCRIPT_HANDOFF_GATE`.

The Round 2 packet must contain the Round 1 response, Codex decision ledger,
revised design and timeline, current gate results, and an exact change summary.
Round 2 audits the revised candidate; it must not start a new creative rewrite.

Verify:

- every Round 1 issue was resolved or explicitly rejected with evidence
- accepted changes preserve source meaning
- quotes, relationships, names, numbers, and time ranges still match evidence
- protected time, track, role, and audio fields were not silently changed
- caption and TTS timing still fit the revised visual plan
- no unresolved hard blocker remains

Round 2 output order:

```text
ROUTE=SHORTS
review_round: 2
review_cycle_id: ...
packet_id: ...
sent_packet_sha256: ...

## 1. EVIDENCE_AUDIT
## 2. ROUND1_RESOLUTION_CHECK
## 3. REMAINING_BLOCKERS
## 4. EXTERNAL_RECOMMENDATION
PASS_RECOMMENDED | REVISE_REQUIRED | EVIDENCE_REQUIRED

external_review_status: PENDING_CODEX_REVIEW
```

Only `PASS_RECOMMENDED` may continue to Codex's
`CHATGPT_PROJECT_TWO_PASS_REVIEW_GATE`. `REVISE_REQUIRED` or
`EVIDENCE_REQUIRED` returns to design repair and blocks handoff. A structural
change proposed after handoff is `DESIGN_REOPEN_REQUIRED`.

### Browser-Assisted Automation Sequence

Generate and validate the file artifacts with the local CLI. Use the signed-in
normal Chrome session only for the two messages in the `쇼츠대본분석` project.

```powershell
py -3 skills/00-tikitaka/scripts/chatgpt_review_workflow.py build-round1 --work-dir <20_script-dir> --review-cycle-id <cycle-id>
py -3 skills/00-tikitaka/scripts/chatgpt_review_workflow.py record-response --work-dir <20_script-dir> --round 1 --input <copied-round1-response.md>
py -3 skills/00-tikitaka/scripts/chatgpt_review_workflow.py build-round2 --work-dir <20_script-dir> --review-cycle-id <cycle-id>
py -3 skills/00-tikitaka/scripts/chatgpt_review_workflow.py record-response --work-dir <20_script-dir> --round 2 --input <copied-round2-response.md>
py -3 skills/00-tikitaka/scripts/chatgpt_review_workflow.py finalize-gate --work-dir <20_script-dir>
```

If the project returns `SOURCE_CONTRACT_MISSING`, attach this exact file,
`shorts_script_analysis_single_source_v20260706.md`, as the only review
contract in the project and rerun the packet. Remove political contracts and
do not attach an archived or second Shorts contract.

### Hard Blockers and Truth Mode

Use these states when applicable:

```text
NEEDS_EVIDENCE
FACT_CHECK_REQUIRED
SOURCE_MISMATCH
CONTEXT_REQUIRED
FACT_LOCK_CONFLICT
PROTECTED_FIELD_CONFLICT
TIMING_CONFLICT
DESIGN_REOPEN_REQUIRED
```

Quote distortion, wrong people or relationships, incorrect dates/numbers,
source mismatch, or unresolved fact-lock conflict blocks a passing
recommendation regardless of prose quality.

For news, politics, medical, legal, safety, crime, finance, and other high-risk
lanes, use `truth_mode=fact_first`. Ordinary comedy, family, and emotional
Shorts may use `truth_mode=hook_first_writer_premise` only when the premise is
clearly labeled `plausible_unverified` or `fictionalized_hook` and does not add
harmful high-risk facts.

For ranking Shorts, do not copy the original rank order and rank numbers as the
remake structure. Record `source_rank`, `remake_rank`, and the new
`ranking_criterion`. Do not distort an official objective ranking; declare a
new criterion or convert the remake to a non-ranking structure.

## Production Boundary

`00-tikitaka` may write draft script text and script handoff information. It
must not create voice files, SRT files, layout JSON, CapCut drafts, exports, or
upload packages. Production assets belong to `000short-production-agent` after
the user explicitly requests that stage.
