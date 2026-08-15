# NORMAL_FAST 실행

`NORMAL_FAST`는 기본 실행 프로필이다. One single task-owner performs Stage 01 through Stage 04 sequentially and owns every canonical write.

## 기본 비활성화

다음 worker fanout은 `NORMAL_FAST`에서 모두 비활성이다.

- Stage 01 source probe/OCR/inventory workers
- Stage 03 hook/caption/audio/screen workers
- post-design workers
- Stage 08 postbuild workers

`evidence_only` 후보 승격, coordinator revalidation, duplicate barrier validation도 기본 경로에 없다. 새로운 병렬 프로필은 별도 작업지시와 승인 전에는 활성화할 수 없다.

## Validator 소유권

task-owner가 현재 artifact revision의 owning validator를 once per current artifact revision 실행한다. 같은 SHA와 같은 revision은 반복 검증하지 않는다. 관련 artifact가 실제로 변경된 경우에만 validator를 다시 실행한다. 누락 또는 실패는 state를 전진시키지 않는다.

## 백그라운드 작업과 GUI

source identity 검증 뒤 VMake 제출은 task-owner의 비차단 백그라운드 작업이다. 별도 worker fanout이 아니다. VMake와 CapCut의 GUI owner는 최대 1명이며, CapCut 또는 백그라운드 프로세스가 열린 동안 draft를 변경하지 않는다.

## Stage 08과 Stage 09

Stage 08 postbuild 검증은 task-owner가 실제 assembled clone에 대해 정해진 validator로 수행한다. worker status나 후보 evidence로 대체하지 않는다.

Stage 09는 `user_manual_only`다. 자동화는 `WAIT_USER_CAPCUT_CHECK`에서 끝나며 CapCut 시각 승인·수정, render, upload는 사용자가 수행한다.
