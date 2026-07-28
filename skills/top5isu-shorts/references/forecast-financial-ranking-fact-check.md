# Forecast Financial Ranking Fact-Check

Use this for TOP5 scripts ranking companies by expected operating profit, net income, revenue, market capitalization, or another forecast metric.

## Evidence gate

A user-supplied script is source material, not production authority. Preserve it verbatim, then verify every ranked amount before TTS or CapCut assembly.

For each company require:

- exact metric (`operating income`, `operating profit`, `EBIT`, `net income`, etc.)
- forecast year and whether it is calendar or company fiscal year
- forecast author/source and publication date
- native reporting currency and source amount
- FX rate/date used for KRW conversion
- whether the value is consensus, a single analyst's high case, company guidance, or an agent scenario

Do not mix operating profit, EBITDA, net income, or market capitalization in one ranking.

## Comparable ranking contract

Create one table with:

```text
company
metric
forecast_period
native_currency
native_amount
source_type
source_url
published_at
krw_fx_rate
krw_amount
confidence
```

Use one stated FX convention across all companies. If sources use different fiscal periods, either normalize them or disclose that the ranking is approximate and not directly comparable.

## Same-snapshot rule

A ranking is only internally comparable when all rows come from the same forecast snapshot or an explicitly normalized update.

- Do not keep lower-ranked rows from an older consensus table while silently replacing only the top one or two rows with newer high-case analyst revisions.
- If an April consensus table says `NVIDIA 357 / Samsung 327 / Aramco 294 / Microsoft 245 / Alphabet 241`, a later July high case such as `Samsung 371.9` belongs in a separate `latest_revision` field, not in the April ranking.
- To publish a newer mixed-source ranking, refresh every row, record every publication date, recompute FX, and rerun the sort. If that is impossible, use the complete older snapshot and disclose its date.
- When the operator delegates judgment (`너가 하려던 대로 해`, `알아서 해`) or does not answer a routine choice after already approving production, default to the complete same-snapshot table rather than the more sensational mixed snapshot.
- Keep later analyst revisions available as a closing comparison or outlook only when their source, metric, and period are explicit.

Record both fields when useful:

```text
ranking_authority = same_snapshot_consensus
latest_revision = separate_non_ranking_context
```

## Forecast wording

- `예상`, `전망`, `컨센서스` must remain visible in the title, narration, and captions.
- A single optimistic analyst estimate must not be narrated as a settled annual result.
- Use `최대`, `가능성`, or `강세 시나리오` only when the source itself supports that case.
- `내년에 A가 B를 제치고 1위` requires a source-backed A-versus-B comparison on the same metric and period. Otherwise say `추월 가능성을 제기하는 전망도 있지만 아직 불확실합니다` or remove the claim.
- Distinguish `영업이익 세계 1위`, `순이익 세계 1위`, and `시가총액 세계 1위`; none implies the others.

## Calculation checks

1. Recalculate every currency conversion with a deterministic tool.
2. Preserve both native and converted values in the evidence packet.
3. Sort using the recalculated values, not the prose order.
4. Record rounding policy (`nearest 1 trillion KRW`, etc.).
5. Flag rankings where adjacent values overlap within forecast error or FX movement.

## Stop conditions

Stop at `WAIT_FINANCIAL_EVIDENCE` when:

- a rank amount has no traceable source,
- the metric differs between companies,
- a truncated number is being guessed,
- forecast period or currency basis is missing,
- a sensational future-leadership claim cannot be tied to comparable evidence.

The operator may still provide images while this gate is unresolved; preserve and QA them without treating the visuals as proof of the ranking.
