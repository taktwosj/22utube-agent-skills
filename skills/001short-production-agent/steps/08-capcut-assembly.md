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

## 최종 보고

정적 validator와 실제 draft readback을 실행한 뒤 결과를 한 줄로 보고한다. 실행하지 않았다면 `NOT RUN`으로 적고 PASS를 주장하지 않는다.
`references/urakkai-artifact-contract.md`에 따라 readback의 `project_path`와 `media_source_path`를 확인한다.

그 다음 아래 순서를 반드시 지킨다.

```text
프로젝트 파일명

<프로젝트 폴더 이름만 담은 별도 코드 블록>

프로젝트 전체 경로

<절대경로만 담은 별도 코드 블록>
```

CapCut 시각 승인·최종 다듬기, render, upload는 사용자 전용이며 자동 조립은 `WAIT_USER_CAPCUT_CHECK`에서 멈춘다.

`references/interim-capcut-project-sync.md`는 사용자가 explicit sync를 요청했을 때만 읽는다.
