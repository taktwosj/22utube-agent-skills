# 2026-08-22 배치에서 확인된 조립 제약 (별별지구인g9 3건)

맥미니에서 유형 2(`full_tts`) 3건을 Stage 01~08 완주하며 실측한 것만 적는다.
전부 실제 실행으로 확인했고, 추정은 그렇다고 표시했다.

## 1. V열은 Bxx 하나와 1:1이다

우라까이표에서 여러 Bxx를 묶어 한 V열로 만들 수 없다. 네 곳이 각각 막는다.

- `validate_capcut_grids.HEADER_PATTERNS["urakkai"]` — 열 머리글이 `B\d{2}` 하나만 받는다
- `validate_capcut_grids.validate_locked_assembly` — `original_ranges[source_index]`를
  클립 `source_range_us`와 완전일치 비교한다
- `validate_audio_caption` caption-timing v2 — V열 소스 범위를 **원본표 헤더에서 다시 계산**한다
- `validate_prebuild` — 소스 길이와 타깃 길이가 1프레임 넘게 다르면 `E_VIDEO_RANGE`

따라서 **V열 길이 = 그 Bxx 길이**로 고정된다. 최종 길이를 조절하는 방법은 V열을 묶는 것이 아니라
**쓸 Bxx를 빼는 것**이다. 유형 2에서는 열 수만큼 나레이션 cue가 생기므로,
원본 B구간이 1~2초로 잘게 쪼개져 있으면 나레이션도 그만큼 짧은 문장들이 된다.

실측: 김치 23B → 15열/26.302초(8개 제외), K푸드 30B → 30열/46.934초(제외 없음),
독일 38B → 22열/28.583초(16개 제외).

## 2. `CLEAN_VISUAL_READY`는 clean_visual 증거 2종이 필요하다

`build_episode_capcut.py`가 `_stage_prerequisites`에서 아래 둘을 요구한다. 없으면
`RuntimeError: STAGE06_EVIDENCE_MISSING`으로 조립 직전에 멈춘다.

- `40_assets_used/clean_visual_manifest.json`
- `40_assets_used/clean_visual_receipt.json`

receipt는 손으로 쓰지 말고 `validate_clean_visual.py`로 생성한다.

```bash
python3 scripts/validate_clean_visual.py \
  --manifest <ep>/40_assets_used/clean_visual_manifest.json \
  --source-identity <ep>/00_input/source_identity.json \
  --design-lock-evidence <ep>/20_script/design_lock_evidence.json \
  --clean-visual-evidence <ep>/40_assets_used/clean_visual_receipt.json \
  --approved-evidence-root <ep>/40_assets_used
```

manifest의 `clean_source_origin`은 `build_manifest.clean_source.origin`과 같아야 한다
(다르면 `STAGE06_CLEAN_SOURCE_ORIGIN_MISMATCH`). receipt가 이미 있으면
`CLEAN_VISUAL_EVIDENCE_PATH_EXISTS`로 막히므로 재생성 전에 지운다.

`build_episode_locks.py`가 만드는 `vmake_final_download_evidence.json`은 별개 파일이라
그것만으로는 조립이 통과하지 않는다.

## 3. Stage 01에서 `--emit-report`는 쓸 수 없다

`validate_capcut_grids.py --emit-report`는 `--urakkai`를 요구한다
(`--urakkai is required unless --original-only is set`). 원본표만 있는 Stage 01의
정본 호출은 `--original-only`다.

## 4. `validate_capcut_cloud_media.py`의 subdraft 판정이 현행 템플릿과 어긋난다

3건 모두 `status=FAIL`이었으나 유일한 blocker가 `subdraft_files`였다
(missing_live_paths 0 / windows_path_files 0 / bak_files 0 / 필수 미러 전부 존재).

- `shrt_white_base_v2` 템플릿에서 상속된 subdraft 9개 중 **5개가 root
  `draft_content.json`·`draft_info.json`에서 실제로 참조**된다. 미참조 프로토타입이 아니다
- 이미 클라우드 업로드까지 끝난 `260820_cat-treadmill` 프로젝트도 동일한 subdraft 9개를 갖는다

`interim-capcut-project-sync.md`가 "참조되는 subdraft를 증명 없이 지우지 마라"라고 명시하므로
삭제하지 않고 업로드했고, 업로드는 정상 동작했다. 검사기 기준을 템플릿 현실에 맞출지는 별도 판단이 필요하다.

## 5. VMake 공식 API 실행 경로

`~/.local/share/vmake_sdk`의 SDK는 **전용 venv로만** 실행된다. 시스템 `python3`로 돌리면
`ModuleNotFoundError: No module named 'requests'`(PEP 668로 설치 불가).

```bash
set -a; . ~/.openclaw/.env >/dev/null 2>&1; set +a
cd ~/.local/share/vmake_sdk
./.venv/bin/python3 sdk/cli.py run-task --task videoscreenclear --input <source.mp4>
```

3건 모두 성공했다. 원본 대비 길이 차이는 각각 0.000초 / 0.001초 / 0.017초, 해상도 그대로.
macOS에는 `timeout`이 없으니 명령 앞에 붙이지 말 것.

## 6. CapCut 클라우드 목적지

`TAKKTWO / macmini`가 머신 매핑(macmini→macmini)에 맞는 목적지이고 용량 여유도 크다
(24.1GB / 1024.0GB). 개인 공간 `User3160027826975의 공간`은 843.0MB / 1024.0MB로 거의 차 있고,
52MB 프로젝트 업로드가 **오류 없이 2회 연속 실패**했다(다이얼로그는 정상적으로 닫혔다).

- 다이얼로그가 닫힌 것은 성공의 증거가 아니다. 반드시 폴더를 열어 행을 읽어 확인한다
- CapCut을 켜면 로컬 프로젝트가 `TAKKTWO/macmini`로 자동 동기화된다. 내가 올리지 않은
  프로젝트도 같은 시각에 찍히므로, 그 타임스탬프를 업로드 성공 증거로 삼으면 안 된다

## 7. 병렬 서브에이전트는 스크래치패드를 분리해야 한다

에이전트 3개를 동시에 돌렸을 때 공유 스크래치패드에서 같은 이름의 크롭 파일이 서로 덮였다.
에피소드별 하위 폴더를 지정해서 격리하면 해결된다. 판독 결과가 다른 에피소드 것으로
바뀌면 사실 오염으로 이어질 수 있는 문제다.
