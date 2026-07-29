# Source SRT term review

이 절차는 **처음 수집한 원본 SRT**를 `source_packet_v1.json`에 넣기 전에
검수한다. 111의 최종 나레이션 SRT 검수와 다른 단계다.

## 권위

| 상태 | 용도 | 자동 교정 |
|---|---|---|
| `observed` | 기사 코퍼스에서 실제로 관찰된 후보. 회차 선별·검수 힌트 | 금지 |
| `approved` | 사람이 표기와 근거를 확인한 정식 용어 | 금지 |
| 승인된 `asr_confusions` | 실제 오인식 증거, 승인자, 승인시각을 가진 쌍 | 금지. 차단·제안만 |

용어 DB는 음성과 SRT가 같다는 증명이 아니다. 오디오 대조 receipt가 없으면
용어 경고가 0건이어도 `WAIT_SOURCE_ASR_REVIEW`다.

## 실행

```bash
python scripts/build_politics_term_index.py \
  --episode <episode>

python scripts/select_episode_terms.py \
  --episode <episode> \
  --context <승인한 기사 또는 조사 문서>

python scripts/gate_source_srt_quality.py \
  --episode <episode>
```

첫 게이트는 다음 파일을 만들고 의도적으로 멈춘다.

```text
10_analysis/episode_term_pack_v1.json
90_reports/source_srt_quality_report_v1.json
status = WAIT_SOURCE_ASR_REVIEW
```

처음 보거나 확신이 낮은 표현은 다음 형식으로
`10_analysis/source_term_candidates_v1.json`에 기록한다. 원본 SRT만으로
회차 용어팩을 고르는 입력이 아니며 사용자 알림을 만드는 검수 큐다.

```json
{
  "schema": "politics-longform-source-term-candidates.v1",
  "episode_id": "PL_YYYYMMDD_slug",
  "generated_by": "PROJECT_GPT",
  "transcripts": {"S01": "<current S01.srt sha256>"},
  "candidates": [
    {
      "source_id": "S01",
      "cue": 14,
      "raw_term": "구분응선",
      "proposed_term": "9부 능선",
      "confidence": "LOW",
      "reason": "FIRST_SEEN_POLITICAL_EXPRESSION"
    }
  ]
}
```

경고가 생기면 사용자에게 `source_id`, cue, 원본 시작·종료 시각, `raw_asr`,
교정 후보 문장, 발견 이유, confidence와 발화 전후 3초의
`audio_review_start_sec` / `audio_review_end_sec`를 모두 보여 준다. 사용자가
음성을 확인하기 전에는 어느 후보도 SRT에 자동 적용하지 않는다.

검수자는 원본 오디오와 SRT를 cue 단위로 대조한다. 오기는 SRT에서 고친 뒤
게이트를 다시 실행한다. 현재 남은 경고를 수용하거나 오탐으로 판정할 때는
근거를 receipt의 `decisions`에 기록한다.

## Receipt

`90_reports/source_srt_review_receipt_v1.json`:

```json
{
  "schema_version": "source_srt_review_receipt_v1",
  "reviewed_by": "HUMAN_REVIEWER",
  "reviewed_at": "2026-07-29T12:00:00+09:00",
  "review_origin": "USER_AUDIO_REVIEW",
  "recorded_by": "PROJECT_GPT",
  "audio_compared": true,
  "registry_sha256": "<64 hex>",
  "term_pack_sha256": "<64 hex>",
  "episode_candidates_sha256": "<64 hex>",
  "transcripts": {
    "S01": "<final S01.srt sha256>"
  },
  "decisions": [
    {
      "issue_id": "srt_<id>",
      "action": "false_positive",
      "rationale": "원본 음성에서 실제로 이 발음과 표기를 사용함"
    }
  ]
}
```

`corrected`로 판정한 경고가 현재 SRT에 그대로 남아 있으면 PASS하지 않는다.
SRT를 고치고 게이트를 다시 실행해야 한다. registry, term pack, SRT 중 하나라도
first-seen term scan, SRT 중 하나라도 receipt 이후 변경되면 receipt는 무효다.

## DB 갱신

새 기사 CSV에서 후보를 추가할 때:

```bash
python scripts/build_politics_term_candidates.py \
  --input <articles.csv> \
  --source-id <source-id> \
  --output <review-candidates.jsonl>
```

이 출력은 전부 `observed`다. 빈도가 높다는 이유만으로 `approved`나
`asr_confusions`로 승격하지 않는다. 원문 기사 전문은 registry에 넣지 않고
집계 빈도와 출처 ID만 남긴다.

검수 결정은
[politics_term_review.schema.json](politics_term_review.schema.json)에 맞춰
작성하고 별도 출력으로 적용한다.

```bash
python scripts/apply_politics_term_review.py \
  --registry references/politics_terms_v1.jsonl \
  --review <politics_term_review_v1.json> \
  --output <reviewed-politics-terms.jsonl>
```

원본 registry의 제자리 덮어쓰기는 금지한다. 결과 검증 후 Git diff로 확인해
master registry와 출처 metadata를 함께 갱신한다.
