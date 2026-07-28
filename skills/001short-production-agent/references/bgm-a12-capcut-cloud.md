# BGM-only A12 CapCut + VMAKE/Cloud 안전 절차

## 적용 조건

- 사용자가 `영상에 깔린 BGM만 남기고 음성은 빼기`, `나레이션 없음`, `BGM 모드`를 요청한 쇼츠.
- 편집 프로젝트는 기존 CapCut root template의 고정 12개 anchor를 유지한다.
- 이 문서는 회차별 값이 아니라 재사용 가능한 절차와 검증 기준만 기록한다.

## 1. BGM stem 잠금

1. 원본 오디오를 Demucs 등으로 분리하고 `no_vocals` stem을 사용한다.
2. 최종 timeline 길이에 맞춰 `apad + atrim`으로 sample-accurate duration을 만든다.
3. `ffprobe`로 실제 duration·codec을 읽고 `audio_lock.json`에 기록한다.
4. ASR이 음악에서 `구독과 좋아요` 같은 관용구를 환각할 수 있다. BGM stem 결과만 보고 음성 잔존으로 단정하지 말고, vocals stem과 함께 `avg_logprob`·`no_speech_prob`를 비교한다.
5. 음성 제거가 확인되면:
   - `audio_source`: `SOURCE_CLIP`
   - `role_files`: `A12`
   - `spoken_narration`: `false`
   - `original_audio`: `false`
   - `bgm_only`: `true`

## 2. CapCut anchor 배치

- `A10`: 원본 음성 전용. BGM-only에서는 모든 source-audio row를 `mute`로 두고 segment count를 0으로 검증한다.
- `A12`: BGM 전용. 동일 BGM 파일을 source/target `[0, duration_us]`의 **단일 full-duration segment**로 배치한다.
- builder config에는 `audio_role: "A12"`를 명시한다.
- `T1/T2`는 root style을 보존해 텍스트만 치환한다.
- 화면 설명은 `STATE` cue로 배치하며 SRT/caption lock과 segment range를 일치시킨다.

## 3. VMAKE 잔존 그래픽 fallback

1. Auto 결과를 초반 고밀도(예: 0.25초 간격)와 전체 저밀도(예: 1초 간격) contact sheet로 검사한다.
2. Auto pass 2까지 동일한 transient 그래픽이 남은 경우에만 localized fallback을 허용한다.
3. fallback은 시간·영역을 좁게 고정하고, 오버레이가 사라진 동기 프레임을 정렬해 복원한다. 단순 색 인페인트가 어두운 패치나 가장자리 잔존을 만들면 사용하지 않는다.
4. 처리 방법·시간 범위·bbox/마스크·전후 contact sheet·canonical SHA를 QA report에 남긴다.
5. 원본의 새 객체·장면을 생성하거나 스토리 내용을 바꾸는 복원은 금지한다.

## 4. 브라우저 다운로드 회수

- 다운로드 helper가 sandbox timeout을 낼 때 signed URL을 출력하거나 저장하지 않는다.
- CDP에서 `Browser.setDownloadBehavior(behavior="allowAndName", eventsEnabled=true)`를 설정하고 Download를 클릭한 뒤 `Browser.downloadProgress.state == "completed"`를 기다린다.
- GUID 파일의 non-zero size를 확인한 후 canonical asset 폴더로 승격한다.

## 5. CapCut cloud-safe 준비

프로젝트를 local CapCut root에 publish한 뒤 앱을 열기 전에 다음을 수행한다.

1. root `draft_content.json`을 `draft_info.json`, `template-2.tmp`로 mirror한다.
2. 각 main timeline의 `draft_content.json`도 같은 두 mirror로 복제한다.
3. parse 가능한 모든 `.json`/`.tmp`를 재귀 순회하며 Windows 절대경로를 제거한다.
   - `path`, `media_path`만 보지 않는다.
   - `draft_file_path`, `draft_cover_path`, `draft_config_path`, `audio_path` 및 JSON 문자열 내부도 검사한다.
4. root contract상 runtime role을 갖지 않는 legacy `subdraft/` residue는 제거한다. role-bearing 문서인지 확인하지 않고 삭제하면 안 된다.
5. `draft_meta_info.json`의 draft ID/name/fold/root/duration/cloud-local 필드를 갱신한다.
6. 정적 validator와 postbuild가 PASS한 뒤에만 `root_meta_info.json`을 백업하고 단일 행으로 등록한다.

## 6. 필수 검증

- `validate_clean_visual`: PASS
- `validate_audio_caption`: PASS
- `validate_prebuild`: PASS
- 전체 unit tests: PASS
- `validate_capcut_project`: PASS
- `validate_postbuild`: PASS
- `validate_capcut_cloud_media`: 다음 배열이 모두 empty
  - `missing_required_files`
  - `missing_live_materials`
  - `missing_live_paths`
  - `windows_path_files`
  - `unreferenced_missing_paths`
  - `bak_files`
  - `subdraft_files`
- ID mirror validator: PASS
- draft readback:
  - VIDEO source starts가 locked permutation과 일치
  - A10 count = 0
  - A12 count = 1
  - A12 source/target = full duration
  - STATE cue count/텍스트 일치
  - T1/T2 일치
- `root_meta_info.json`: 프로젝트명 match가 정확히 1개이며 `draft_json_file`은 해당 프로젝트의 `draft_info.json`을 가리킨다.

## 7. 완료보고 BGM 추천

BGM 모드 완료보고에는 실제 삽입 BGM과 별도로 분위기에 맞는 노래 후보를 **정확히 3개** 적는다. 각 항목에는 곡명 또는 검색 가능한 키워드, 추천 이유, 미확인 시 `사용 전 권리/제공 여부 확인`을 포함한다.
