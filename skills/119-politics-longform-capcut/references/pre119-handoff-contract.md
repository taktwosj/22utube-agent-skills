# PRE-119 handoff validation

강한 PRE-119 표식 하나 또는 보조 표식 두 개 이상이 있으면 `direct-script.md`보다 먼저 이 문서를 읽는다. PRE-119 route 잠금과 validation PASS는 별개다.

강한 표식:

```text
20_script/pre119_handoff.json
togun-pre119-handoff-v3
TOGUN_PRE119_TO_119_DIRECT
EDITORIAL_OWNER=TOGUN_PRE119
PRE119_SOURCE_CANDIDATE
```

보조 표식:

```text
20_script/119_final_script.md
10_analysis/pre119_editorial_packet.md
00_source/source_packet.md
90_reports/source_gap_and_status.md
00_README.md
```

한 개 보조 표식만으로는 PRE-119를 선택하지 않는다. PRE-119가 선택된 뒤 identity가 틀려도 direct-script로 fallback하지 않는다.

필수 handoff 필드:

```text
schema=togun-pre119-handoff-v3
route=TOGUN_PRE119_TO_119_DIRECT
editorial_owner=TOGUN_PRE119
source_state=PRE119_SOURCE_CANDIDATE
episode_id
project_name
central_question
selected_thesis
chapter_order
between_image
between_narration
lower_mode = SRT | COMMENTARY_2LINE | NONE | MIXED
execution_mode = ASSEMBLY_ONLY
cta_like_subscribe = ON | OFF
```

실행:

```powershell
python scripts/validate_pre119_handoff.py `
  --package-root <pre119-package> `
  --approved-script-sha256 <sha256-calculated-at-user-approval> `
  --approval-evidence <user_message:id-or-runtime_approval:id>
```

validator는 `119_final_script.md` raw SHA, packet `script_lock.current_final_script_sha256`, 외부 승인 SHA를 비교한다. 세 SHA가 일치한 뒤 기존 `ASSEMBLY_ONLY_SEED`를 한 번 파싱해 고유한 카드 순서와 잠금 필드를 `assembly_only_seed` 및 결정적 `assembly_only_seed_sha256`으로 같은 PASS 보고서에 결합한다. 패킷 내부 승인 필드는 외부 사용자 승인을 대신하지 못한다. 절대경로·상위경로 traversal은 거부한다.

PASS 뒤 A/D와 요청된 B/C를 실행한다. join owner는 같은 PASS seed evidence를 재사용해 seed `card_id`와 순서대로 1:1 compile하며 실제 path·SHA·duration·검증된 source range/channel/date/speaker·narration/SRT/rendered asset·target timing만 결합한다. 카드 누락·추가·재정렬 또는 잠금 필드 override는 차단한다. compile 결과는 `execution_mode=ASSEMBLY_ONLY`이며 build 전 `run_politics_assembly_preflight.py` PASS를 요구한다.
