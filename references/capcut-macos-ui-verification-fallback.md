# CapCut macOS Verification and Recovery

## 1. Root ZIP authority recovery

근본 ZIP이 현재 설치 폴더에 없더라도 비슷한 이름의 ZIP이나 이전 회차 내부 ZIP을 바로 대체하지 않는다.

1. `root_contract.json`의 `root_zip_sha256`, 원본 Git remote, base commit, repo-relative path를 확인한다.
2. 정확한 base commit을 shallow fetch/checkout한다.
3. 해당 경로의 ZIP을 episode-local authority 폴더로 복사한다.
4. SHA-256과 `unzip -t`가 모두 PASS할 때만 사용한다.
5. 외부 handoff ZIP, 이전 회차에 중첩된 `shrt white.zip`, 이름만 같은 사본은 SHA가 다르면 근본 정본이 아니다.

## 2. Home card와 editor-open 증거를 분리

CapCut Home 검색 결과에 프로젝트 카드와 길이가 보이는 것은 **등록·발견 증거**일 뿐 편집기 로드 증거가 아니다.

편집기 open PASS는 다음을 함께 확인해야 한다.

- Home의 `프로젝트 만들기` 배너와 프로젝트 목록 화면이 사라졌다.
- 프리뷰, 타임라인 ruler, VIDEO/A10/text 트랙이 보인다.
- 프로젝트명과 전체 길이가 승인안과 일치한다.
- 미디어 누락·경로 손실 경고가 없다.
- 시작·첫 구조 전환·중간·끝 위치에서 실제 프리뷰가 바뀐다.

더블클릭 후에도 Home 검색 결과가 그대로면 `editor opened`로 보고하지 않는다.

## 3. macOS GUI fallback

기본 순서는 `computer_use(capture, mode=som, app=CapCut)`이다. 앱 창이 존재하는데 캡처 결과가 비어 있을 때만 다음의 읽기 중심 fallback을 쓴다.

상태 변경 입력은 항상 아래 검증 사다리를 따른다.

1. `delivery_mode=background`로 실행하고 가능하면 `capture_after=true`로 재확인한다.
2. `effect=confirmed`와 `verified=true`면 완료한다. `effect=unverifiable`이면 새 SOM 캡처로 화면·AX 상태를 직접 확인한다.
3. `effect=suspected_noop`, `code=background_unavailable` 또는 `escalation.recommended=px`면 동일 동작을 캡처에서 읽은 좌표로 한 번 재실행한다.
4. 좌표 동작도 실패했거나 `escalation.recommended=foreground`일 때만 동일 동작을 `delivery_mode=foreground`로 재실행한다. 드라이버 신호 없이 앱 종류만 보고 foreground를 선사용하지 않는다.
5. 모든 상태 변경 뒤 새 캡처로 결과를 검증한다. 권한·비밀번호·결제·게시 확인창은 자동 승인하지 않는다.

1. `System Events`에서 CapCut process의 `visible`, `frontmost`, window count를 확인한다.
2. front window의 position/size를 읽고 그 창 영역만 `screencapture -R`로 저장한다. 전체 화면을 찍어 다른 창을 노출하지 않는다.
3. Home 검색은 top-level `AXTextField`에 정확한 프로젝트명을 넣고, `HomePageDraftTitle:<name>`가 정확히 하나인지 확인한다.
4. 클릭 좌표를 쓰기 전 대상 title element의 position/size를 다시 읽는다.
5. 상태 변경 후에는 새 창 영역 캡처로 반드시 재검증한다.

권한·비밀번호·결제·저장 확인 대화상자가 나타나면 대신 누르지 않는다.

## 4. Cloud validator path rule

`validate_capcut_cloud_media.py`의 Windows 경로 판정은 JSON 문자열 시작 따옴표 직후의 `<drive>:/` 또는 `<drive>:\\`만 잡아야 한다. `https://`의 `s:/`를 Windows drive로 오탐하면 안 된다.

- validator 통과를 위해 정상 `https://` icon/preview URL을 삭제하지 않는다.
- rich-text `content` 내부 font cache path를 정리할 때는 JSON을 파싱해 machine-local `font.path`만 비우고 text, font/resource ID, fill/stroke, range를 유지한다.
- live media는 project-relative `Resources/` 경로와 파일 존재를 함께 검사한다.
- `.bak`, subdraft 잔존, unreferenced machine-local path도 업로드 전 blocker다.

## 5. Upload and reopen proof

업로드 성공은 버튼 클릭이나 Home 카드만으로 확정하지 않는다.

1. 목적지가 `User3160027826975의 공간/MAC`인지 확인한다.
2. 동명 확인창은 사용자가 승인한 재업로드 범위에서만 처리한다.
3. MAC cloud row의 이름·크기·길이·최근 시각을 읽는다.
4. 그 cloud row를 다시 열어 editor-open 조건, T1/T2, 첫 구조 전환, 오프라인 미디어 부재를 확인한다.
5. 로컬 project, cloud upload, cloud reopen을 별도 evidence로 기록한다.
