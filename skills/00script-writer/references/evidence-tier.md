# Evidence Tier

Use this for real incidents, history, finance, law, medical/health, statistics, quotes, scams, court outcomes, or any claim that could harm trust if wrong.

The script must separate fact, reporting, inference, reconstruction, and opinion.

## Required Output

```text
Evidence Pass
- Highest-risk claim:
- Source tier:
- What is verified:
- What is inference:
- What must be phrased as reconstruction:
- Lines to soften or remove:
```

## Tiers

### T0: Primary Verified

Official documents, court records, agency releases, original filings, public datasets, direct source material.

Use:

```text
자료에 따르면
공식 발표 기준으로
판결문에는
```

### T1: Reported Fact

Reliable news reports or named institutional statements, but not primary documents.

Use:

```text
보도에 따르면
경찰 발표를 인용한 보도에서는
```

### T2: Supported Inference

Reasonable interpretation from known facts.

Use:

```text
이 흐름으로 보면
가능성이 큽니다
이 대목에서 의심할 수 있습니다
```

### T3: Dramatic Reconstruction

Scene-building for retention when exact words, feelings, or private actions are unknown.

Must label or phrase carefully:

```text
당시 상황을 장면으로 재구성하면
이런 압박이 있었을 가능성이 있습니다
```

### T4: Opinion / Commentary

The channel's judgment, lesson, or framing.

Use:

```text
제 판단은
이 영상에서 봐야 할 건
우리가 기억할 건
```

## Hard Rules

- Do not invent victims, names, quotes, documents, verdicts, statistics, or private emotions.
- Do not state reconstruction as fact.
- Do not turn a suspect into a convicted person unless that is verified.
- For finance, never tell viewers to buy or sell; tell them what to check.
- For history, avoid presenting uncertain anecdotes as confirmed fact.
- For scam prevention, official numbers and procedures must be current or clearly sourced.

## Rewrite Examples

Risky:

```text
그는 돈 때문에 배신했습니다.
```

Safer:

```text
기록상 이해관계는 분명했습니다.
다만 속마음까지 단정할 수는 없습니다.
```

Risky:

```text
경찰이 이렇게 말했습니다.
```

Safer:

```text
사기범은 경찰처럼 말했습니다.
```
