# Parallel Persona Gate

This gate is the default writer-side script QA step for serious rewrite or
existing script/caption review. Run it after a complete draft exists and before
calling the rewrite wording clean.

This gate does not decide YouTube policy compliance. If the script, captions,
title, thumbnail, upload text, source, or links have policy risk, run
`youtube-policy-gate.md` separately. Personas judge comprehension and retention;
the policy gate judges platform safety, advertiser suitability, EDSA, metadata,
copyright, and link risk.

## Scale

Default writer mode, Shorts, midform, and longform use a random 5-persona gate.

Only an explicit user request for a full 10-persona gate uses the older 7-of-10 rule.

## Random 5-Persona Pool

For the first pass, randomly choose 5 unique personas from this pool:

```text
10대 남 / 10대 여
20대 남 / 20대 여
30대 남 / 30대 여
40대 남 / 40대 여
50대 남 / 50대 여
```

Do not always choose the same five. Record the chosen personas in the result JSON.

## Questions

Each selected persona must answer all of these:

```text
페르소나:
우리 한국어 텍스트만으로 이해: YES/NO
오디오 없이 이해: YES/NO
원본 외국어 자막 없이 이해: YES/NO
30초 이상/끝까지 시청: YES/NO
첫 3초 훅 이해: PASS/FAIL
가장 강한 훅:
헷갈린 문장:
빠지는 지점:
수정 요청 1개:
판정: PASS/REWRITE/FAIL
```

For videos shorter than 30 seconds, replace “30초 이상” with “끝까지 시청”.

## Live Board

After spawning or starting reviews, show:

```text
[5명 랜덤 페르소나 검수 - 진행]
- {persona 1}: RUNNING
- {persona 2}: RUNNING
- {persona 3}: RUNNING
- {persona 4}: RUNNING
- {persona 5}: RUNNING
```

When a persona finishes, update that row to `PASS`, `REWRITE`, or `FAIL`. If a real sub-agent id or nickname is available, show it beside the persona.

## Pass Rule

Rewrite gate PASS requires both metrics:

- `우리 한국어 텍스트만으로 이해`: at least 3 of 5 YES.
- `30초 이상/끝까지 시청`: at least 3 of 5 YES.

Audio-off comprehension should also pass for at least 3 of 5. If 3 or more personas fail audio-off comprehension, the draft is `REWRITE_REQUIRED`.

## Rewrite And Rerun

If either required metric is below 3 of 5:

1. Apply the concrete common complaints to the hook, bottom captions, purple overlays, or title.
2. Choose the remaining 5 personas from the pool.
3. Rerun the same questions.

If the rerun gets 3 of 5 or better for the required metrics, proceed.

If the rerun is still below 3 of 5, mark `REWRITE_REQUIRED` and block production. Do not call the script/caption package final.

## Required Summary Fields

The aggregation summary must include:

```text
persona_gate_size: 5
persona_threshold_required: 3_of_5
persona_pool: 10s_to_50s_male_female_random
chosen_personas:
우리 한국어 텍스트만으로 이해 YES: N/5
30초 이상/끝까지 시청 YES: N/5
오디오 없이 이해 PASS: N/5
공통 이탈 지점:
공통 이해불가 문장:
수정 반영 여부:
persona_rewrite_gate_status: PASS / REWRITE_REQUIRED
```

## JSON Records

For production folders, record these in `analysis.json` or `status.json`:

```json
{
  "persona_our_text_only_understanding_yes": 0,
  "persona_30s_hold_yes": 0,
  "parallel_persona_gate_mode": "real_subagents",
  "parallel_persona_gate_complete": true,
  "parallel_persona_gate_size": 5,
  "parallel_persona_gate_pool": "10s_to_50s_male_female_random",
  "parallel_persona_agents": [],
  "parallel_persona_second_pass_agents": [],
  "persona_threshold_required": "3_of_5"
}
```

## 10-Persona Mode

Use the full 10-persona gate only when the user explicitly asks for it. In that mode, use the same age/gender pool and require 7 of 10 YES for the required metrics.
