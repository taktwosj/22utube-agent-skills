# Loan Product Shorts Evidence And Wording

## Trigger

Read this reference when a TOP55·군림보 episode explains a loan, deposit loan,
public-rental loan, credit product, rate, limit, approval path, refinancing, or
lender screening criteria.

## Evidence classes

Classify every financial claim before script lock:

1. `STRUCTURAL_GUIDANCE`
   - contract type, deposit-return structure, actual funding gap, due date,
     documents, income flow, existing debt, and repayment capacity;
   - may be explained as a checklist when supported by the supplied source.
2. `CONDITIONAL_PRODUCT_CLAIM`
   - another financial sector may review the case, alternative screening may
     exist, or additional documents may help;
   - always use conditional wording such as `검토 가능성이 있습니다` or
     `조건에 따라 확인할 수 있습니다`.
3. `LIVE_PRICE_OR_APPROVAL_CLAIM`
   - exact rate, maximum percentage, approved amount, lender availability,
     guaranteed execution date, or eligibility result;
   - do not make production authority from an operator article alone. Require a
     current official lender/BANKLY/MCP source. If unavailable, omit the number
     and say the result requires official individual screening.

An operator-supplied blog post or consultation draft is valid source material,
but it is not automatically current lender-policy authority. Preserve its
business intent while downgrading unsupported live numbers to conditional or
omitting them.

## Required wording

Use these patterns:

```text
계약 구조와 상환 조건이 맞으면 다른 금융권의 검토 가능성도 확인할 수 있습니다.
실제 승인 여부와 한도, 금리는 금융사의 공식 심사로 확인해야 합니다.
현재 연체나 월 부채 부담이 크면 검토가 제한될 수 있습니다.
```

Avoid:

```text
무조건 가능합니다.
최대 한도가 나옵니다.
누구나 5%대로 받을 수 있습니다.
기금에서 거절돼도 2금융권은 됩니다.
```

Do not present a consultation example as a guaranteed precedent. Do not imply
that public-rental tenants or low-income borrowers are automatically eligible.

## 60-second checklist structure

For `기준 N가지` explainers:

1. 3–5 second hook stating the practical problem;
2. one short sentence per criterion;
3. group related details rather than reading the whole source article;
4. keep live rate/limit details out unless officially verified;
5. end with the official-screening disclaimer;
6. for every 임대아파트·공공임대 loan video, end with the exact additional CTA below in both narration and display captions:

```text
임대아파트대출 상담이 필요하다면 고정댓글을 확인하세요
```

This CTA is an operator lock: do not add particles, punctuation-dependent rewrites, spaces that change the visible phrase, or a shorter paraphrase. It follows the disclaimer rather than replacing it.

Generate the fixed-speed Supertone audio and measure it. Reserve the CTA duration before writing the body. If the result exceeds the requested runtime, merge or shorten earlier criteria while preserving all checklist meanings and the official-screening disclaimer; never trim speech, change the exact CTA, or silently raise speed. If a merge changes sentence count or shifts indices, rebuild every sentence clip. Use selective sentence regeneration only while indices remain stable. After the last pronunciation repair, regenerate joined audio, loudnorm output, captions, image boundaries, and previews from the current TTS manifest. Keep display wording factual and use a separate spoken copy for pronunciation repair.

## Situation-first Image2

Prefer ordinary borrower situations over lender advertising:

- rental contract and deposit-return structure;
- paid contract money versus the remaining funding gap;
- income, debt, and document review;
- monthly burden and early-repayment comparison;
- due-date preparation and official screening.

Reject readable rates, amounts, approval stamps, lender logos, banknote text,
or imagery that implies guaranteed approval. Abstract tokens, blank forms, and
neutral consultants are acceptable only when they do not resemble a promise.

## Source and final report

When no publication URL is provided, record:

```text
source=operator-provided consultation manuscript
source_date=<provided date>
publication_url=null
current_lender_terms_verified=false
```

The final upload block must name the supplied manuscript as the source and add
that actual approval, limit, and rate require official lender screening. Never
invent a URL to make the source list look complete. For 임대아파트·공공임대
videos, the assembly report must also record exact readback of the fixed CTA in
both the final audio ASR and the last CapCut caption, and cloud completion still
requires direct readback from `TAKKTWO/macmini`.
