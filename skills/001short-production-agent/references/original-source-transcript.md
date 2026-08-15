# 원본 5분류 대본 계약

Stage 01에서 증거를 확보하고 Stage 02의 `original-capcut-grid.md`에 기록한다. 15개 물리 트랙과 15행 표는 그대로 유지한다.

새 에피소드 bootstrap은 intake receipt v2와 state에 `original_analysis_contract_version=001short-original-source-transcript-v1`을 함께 기록한다. 기존 state와 intake v1에 이 값이 없으면 legacy resume이며 5분류 대본을 새로 요구하지 않는다. 한쪽에만 값이 있거나 값이 다르면 실패다.

## 증거 확인

각 자막·화자·나레이션·화면 변화점에서 `B01…BN`을 나눈다. 화면 글자가 흐리거나 겹치면 해당 구간의 고해상도 키프레임을 다시 뽑아 확대 확인한다. 원음은 source audio와 원본 caption/transcript를 함께 대조한다. OCR을 끝내 판독하지 못하면 `WAIT_OCR_UNRESOLVED`로 멈춘다. 상황 자체가 미확정이면 `ORIGINAL_TRANSCRIPT_UNVERIFIED`로 멈춘다.

OCR은 들린 말이 아니다. 화면에 baked된 글자는 `(상황설명)`의 `화면 OCR:` 뒤에 원문 그대로 쓰고, 원음은 `"화자발언"` 또는 `<나레이션>`에만 쓴다. 원본 단계에서 새 TTS를 추정하거나 작성하지 않는다.

새 계약의 Stage 01은 `10_analysis/original-source-evidence.json`을 `schemas/original_source_evidence.schema.json`으로 작성한다. state는 이 경로와 SHA-256을 `original_source_evidence_path`, `original_source_evidence_sha256`에 고정한다. 각 B구간 증거는 다음을 모두 가진다.

- source identity 경로·SHA와 source media 경로·SHA
- source range
- 고해상도 keyframe 경로·SHA·timestamp·literal OCR
- source transcript/caption evidence 경로·SHA
- source audio evidence 경로·SHA
- 다섯 분류의 확정 문자열; 두 TTS 값은 `없음`

## 고정 형식

15행 표보다 먼저 모든 B구간을 source 순서대로 쓴다. 구간 ID와 시작·종료 시간은 바로 뒤 15행 표의 `Bxx <start>–<end>` 머리글과 정확히 같아야 한다. 각 블록은 다음 다섯 줄을 같은 순서로 한 번씩만 가진다.

```text
### B01 0.000–3.900
(상황설명) 실제 보이는 상황. 화면 OCR: 원문 또는 없음
"화자발언" 실제 원음 발언 또는 없음
<나레이션> 실제 원본 보이스오버 또는 없음
TTS화자발언 없음
TTS나레이션 없음
```

- `(상황설명)`: 인물·행동·사물·구도와 literal baked OCR. OCR이 없으면 `화면 OCR: 없음`.
- `"화자발언"`: 화면 속 인물에게서 실제 들리는 원음 발언. 화면자막을 복사해 발언으로 만들지 않는다.
- 같은 B구간에 화자가 둘이면 한 줄에 `"화자발언" [A] 첫 화자 원문 / [B] 둘째 화자 원문`으로 쓴다. A는 `A10_TEXT_WHITE`, B는 `A10_TEXT_YELLOW`에 대응한다. 한 명뿐이면 `[A]`만 쓴다.
- `<나레이션>`: 실제 source voiceover나 off-screen 해설. source narration을 TTS로 분류하지 않는다.
- `TTS화자발언`, `TTS나레이션`: 편집으로 새로 추가할 음성 자리. 원본 재구성에서는 항상 `없음`.
- 부재는 정확히 `없음`; 빈값·`비움`·`미확인`·`확인 필요`를 쓰지 않는다.

## 검증

Stage 02에서 원본표만 먼저 검증한다.

```text
python -B scripts/validate_capcut_grids.py \
  --original <episode_root>/20_script/original-capcut-grid.md \
  --original-only
```

검증기는 canonical episode 경로에서 state와 intake를 자동으로 읽는다. CLI flag로 계약 버전을 선택하지 않는다. 새 버전이면 evidence 파일과 모든 참조 파일의 SHA, B구간·시간·OCR·화자발언·나레이션·TTS 값을 원본표와 대조한다. Stage 03 이후에는 기존 원본표·우라까이표 전체 검증 명령을 그대로 실행한다.
