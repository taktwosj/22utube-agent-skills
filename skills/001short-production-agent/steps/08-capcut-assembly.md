# 08 CapCut 조립

## 조립 전 하드게이트

`scripts/build_episode_capcut.py`만 사용한다. 빌더는 다른 검증이나 디렉터리 생성보다 먼저 `scripts/validate_capcut_grids.py`로 다음 파일을 검증한다.

```text
20_script/original-capcut-grid.md
20_script/urakkai-capcut-grid.md
```

두 완전표가 PASS하지 않으면 work root와 local draft를 생성·변경하지 않는다. `TABLE_EMPTY_CELL_FORBIDDEN`, `TABLE_UNVERIFIED_CELL`, 행·머리글 오류를 우회하지 않는다.

근본 CapCut ZIP을 root contract로 검증한 뒤 `source_authority`에 해제한다. root ZIP과 해제된 source-authority tree는 읽기 전용이다. `working_project` 복제본을 만들고 새 project ID, draft ID, timeline ID를 부여한 뒤 episode asset은 복제본에만 주입한다. 조립 완료 뒤 실제 clone의 material, audio, caption, path/SHA, project-ID mirror, Timeline mirror를 기존 validator로 검사한다.

형식 PASS 뒤에는 B/V 범위와 source Bxx 매핑을 `build_manifest.urakkai.video_clips`에, A9/A10/자막/STATE의 비움·채움 상태를 approved timeline과 caption lock에, T1/T2 문구를 잠긴 title segment에 대조한다. 완전표는 단순 보고서가 아니라 실제 조립 선언이다.

## 15트랙 조립

- Stage 07 잠금 `30_audio_srt/audio_lock.json`, `30_audio_srt/caption_lock.json`, `30_audio_srt/final.srt`를 입력으로 사용한다.
- `shrt_white_base_v2_15` 근본 템플릿만 사용한다.
- VIDEO는 승인된 영상 파일을 배치하고 `config.video_mute=true`, segment volume 0으로 둔다.
- T1/T2는 제목 두 줄이다.
- A9/A9_TEXT는 실제 나레이션 파일이 있을 때만 배치한다.
- A10/A10_TEXT는 원본 화자를 유지할 때만 배치한다.
- A10은 검증된 외부 Demucs stem만 사용한다. `CapCut built-in vocal separation`은 사용하지 않는다.
- 음성 없는 상황설명은 STATE_LASER에만 배치한다.
- STATE_GLITCH, STATE_FLICKER, A12_RESERVED_EMPTY는 비운다. A11은 실제 효과음이 있을 때만 배치한다.
- `CLEAN_VISUAL_READY`, `SOURCE_VIDEO_PROVISIONAL`, `USER_APPROVED_NONMATCHING_CLEAN_SOURCE`를 기존 계약대로 처리한다.
- CapCut 또는 백그라운드 프로세스가 열려 있으면 draft를 변경하지 않는다.

## W Flash 밀도 (폴리시 프로필)

`apply_capcut_polish_profile.py`가 컷마다 전환을 붙이던 방식을 폐기했다. W Flash는 두 조건으로만 선택된다.

- **진짜 점프에만.** 소스가 실제로 끊기는 컷 — 다른 소스 파일이거나, 다음 세그먼트의 source 시작이
  앞 세그먼트의 source 끝과 프레임 허용(`FRAME_TOLERANCE_US`)을 넘어 어긋나는 자리. 원본 순서를
  그대로 이어붙인 이음매는 화면이 안 바뀌므로 점프가 아니다.
- **10초당 1회 이상 2회 이하.** 롤링 10초 안에 3개가 몰리면 뒤엣것을 버린다. 반대로 어느 구간도
  10초를 넘게 비울 수 없어서, 점프가 없으면 평범한 컷을 승격해 채운다. 바닥 규칙이 상한보다 우선한다.

선택은 `select_flash_orders()` 하나가 정하고 applier와 validator가 같은 함수를 쓴다. 규칙이 고르지 않은
자리에 전환이 남아 있으면 `POLISH_W_FLASH_UNEXPECTED`다 — 복제본이 이전 빌드의 전환을 들고 오므로
applier가 직접 떼어낸다. 영수증의 `w_flashes_per_timeline`이 실제 개수다(다른 카운터와 달리 문서 수만큼
합산하지 않는다).

실측: 25컷 41.1초 에피소드에서 24개 → 6개(4.375·8.5·14.875·22.625·31.125·38.0초).

## 최종 보고

결과 보고의 첫 항목은 정확한 CapCut 프로젝트명이며, 프로젝트 폴더 이름만 담은 별도 복사 가능 코드 블록으로 출력한다.

그 다음 정적 validator와 실제 draft readback 결과를 한 줄로 보고한다. 실행하지 않았다면 `NOT RUN`으로 적고 PASS를 주장하지 않는다. `references/urakkai-artifact-contract.md`에 따라 readback의 `project_path`와 `media_source_path`를 확인한다.

그 뒤 아래 순서를 따른다.

```text
프로젝트 전체 경로

<절대경로만 담은 별도 코드 블록>

미디어 폴더 전체 경로

<실제 미디어 폴더 절대경로만 담은 별도 코드 블록>
```

CapCut 시각 승인·최종 다듬기, render, upload는 사용자 전용이며 자동 조립은 `WAIT_USER_CAPCUT_CHECK`에서 멈춘다.

`references/interim-capcut-project-sync.md`는 사용자가 explicit sync를 요청했을 때만 읽는다.
