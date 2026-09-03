# 해외 바이럴 대화형 V1

해외 바이럴 원본을 우라까이하고 원본 화자 음성을 유지하는 001 Type 3
프리셋이다. 별도 제작 엔진이 아니며 원본표, 우라까이표, 공용 lock,
공용 builder, 공용 validator를 그대로 사용한다.

## Stage 08 선택값

- `--profile presets/foreign-viral-dialogue-v1/profile.json`
- `--root-profile home_windows_black_headline_dialogue_v1`
- `--root-contract-path 00_asset_tools/templates/capcut/shrt_black_headline_dialogue_v1/shorts_capcut_root_contract_v1.json`

루트 resolver가 아카이브 SHA, manifest, layout contract, 15개 기본 트랙을
확인한 뒤에만 조립한다. 기본 15트랙 순서는 바꾸지 않는다.

## 화면 문법

- `T1`, `T2`: 검은 상단 헤드라인 안의 고정 제목 두 줄. `T2`는
  `emphasis_range: [시작, 끝]`으로 승인한 한 구간만 빨강, 앞뒤는 노랑으로 유지한다.
- `A10`: 우라까이 순서에 맞춰 재조립한 원본 화자 음성.
- `A10_TEXT_WHITE`, `A10_TEXT_YELLOW`: 하나의 텍스트 객체를 정확히 두 줄로 쓴다.
  첫 줄은 파란 화자명, 둘째 줄은 흰 대사다. 예: `엄마\n약속이 있거든..`.
- `STATE_GLITCH`: 약 `-4도` 기울어진 검은 상황 바에 빨강 문구를 쓴다.
  `GLITCH_SHAKE`만 이 프리셋의 STATE 효과로 허용한다.
- 점진 문구는 한 비트 안에 짧은 STATE cue를 연속 배치한다. 예:
  `그대로` → `그대로 떠나버리는` → `그대로 떠나버리는 딸`.

## 키보드 소리

타자 효과음은 템플릿의 `Resources/combination` AAC를 재사용하지 않는다.
회차에서 직접 만든 `typing_sfx_mix.wav`를 전체 타임라인 길이로 준비하고,
파일 경로, SHA-256, 실제 duration을 가진
`001short-user-provided-media-overlay-layout-v1` audio 항목으로 15번 이후
확장 트랙에 한 번만 배치한다. 조립 후 프로젝트 `Resources/media`의 실제
WAV 경로와 ffmpeg 전체 디코딩을 검증한다.

## 멈춤 화면과 노란 외곽선

필요한 장면에서만 회차별 실제 자산 두 개를 만든다.

- `freeze_frame.png`: 원본에서 고른 정지 프레임. 권장 유지 시간 0.8~1.8초.
- `subject_outline_rgba.png`: 같은 프레임의 인물 누끼. 투명 배경에
  `#efff19`, 1080×1920 기준 12~20px 외곽선.

두 PNG도 경로, SHA-256, 크기, 실제 target range를 선언한 image overlay로
15번 이후 별도 확장 트랙에 `freeze_frame.png` 다음 `subject_outline_rgba.png`
순서로 둔다. builder는 이 시각 확장 트랙의 render index를 원본 화면보다 위,
모든 제목·자막보다 아래로 고정한다. 얼굴, 입, 손, 제품, 사건의 핵심 증거를
가리면 안 된다. 정지 진입의 짧은 flash는 선택 사항이다.

## 완료 경계

정적 builder와 validator PASS는 CapCut 화면 PASS가 아니다. 실제 CapCut에서
파란 화자명/흰 대사, 기울어진 상황 바, 키보드 소리 싱크, 정지 프레임,
노란 외곽선, 가림 여부를 확인하고 `WAIT_USER_CAPCUT_CHECK`에서 멈춘다.
