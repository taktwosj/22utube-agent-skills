# 정치 TOP5 인물 이미지·TOP55 조립 실전 규칙

정치 TOP5에서 공식 인물사진과 웹툰 쌍을 사용하고 TOP55 CapCut 프로젝트로 조립할 때 적용한다. 팩트 표현 규칙은 `political-top5-evidence-safety.md`를 함께 따른다.

## 공식 의원사진 확보

뉴스 썸네일보다 국회 공식 의원정보를 우선한다.

1. 열린국회정보 현역 의원 API를 `HG_NM=<이름>`으로 조회한다.
2. 응답의 `MONA_CD`로 의원 프로필 페이지를 연다.
3. 프로필 사진 `img`의 출처를 기록한다.
4. 이미지 URL이 `/new/thumb/<hash>.jpg`이면 `/new/<hash>.jpg` 원본 경로를 먼저 확인한다.
5. 원본 URL·원본 크기·SHA-256을 manifest에 저장한다.

썸네일을 억지로 확대하지 않는다. 실제 원본이 없을 때만 다른 공식 의원실·국회 자료를 찾는다.

## 실사 5장 + 웹툰 5장

TOP5 한 회차의 기본 쌍은 순위별 `공식 실사 → 독립 웹툰`이다.

- 최종 이미지는 각각 1000×800 PNG로 정규화한다.
- 순위·인물·역할을 filename과 manifest에 고정한다.
- 웹툰은 이름만 넣어 생성하지 않는다. 이름 지식만 사용하면 나이, 안경, 얼굴형이 다른 인물이 나올 수 있다.
- 공식 원본 사진을 이미지 입력으로 직접 첨부하고, 얼굴형·눈·코·헤어스타일·연령대·안경 유무를 보존하도록 요청한다.
- 실사와 웹툰의 동일인 유사성, 1인 중심, 얼굴·상반신 잘림, 왜곡, 글자·숫자·로고·워터마크를 contact sheet로 검사한다.
- 유사성이 약한 웹툰은 결과 수량에 포함하지 말고 참고 이미지 기반으로 다시 생성한다.

### ChatGPT CDP 참고 이미지 업로드

관리 브라우저에서 숨겨진 `#upload-photos` 입력을 사용할 수 있다.

1. CDP `DOM.getDocument`와 `DOM.querySelector`로 `#upload-photos` node를 찾는다.
2. `DOM.setFileInputFiles`로 로컬 공식 사진 한 장을 첨부한다.
3. 첨부 미리보기가 나타난 **뒤에** 현재 image src 집합을 기록한다.
4. 프롬프트를 전송하고 기록된 집합에 없던 새 생성 이미지만 결과로 저장한다.

첨부 전에 src 집합을 기록하면 참고 사진 미리보기를 생성 결과로 오인할 수 있다. 브라우저 URL·탭 ID·대화 ID·쿠키는 manifest에 저장하지 않는다.

## TTS 길이 보정 진동

ChatGPT duration repair가 `길음 → 너무 짧음 → 다시 너무 길음`으로 진동할 수 있다.

- 자동 repair는 계약에 정한 횟수만 사용한다.
- 진동하면 추가 호출을 반복하지 않는다.
- 이미 PASS한 후보 중 목표에 가장 가까운 대본을 복구한다.
- 복구본을 writer validator로 다시 검증한 뒤 TTS를 재생성한다.
- 사실, fact ID, 순위, 고정 인사는 보존한다.
- waveform을 잘라 대본 길이를 강제로 맞추지 않는다. 시작·끝의 비정상 무음 정리는 허용한다.

## TOP55 builder 입력

현재 builder는 이미지 디렉터리에서 다음 패턴을 읽는다.

```text
asset_*.png
scene_*.png
```

`01_rank_*.png`처럼 manifest용 이름만 있으면 builder가 이미지 0개로 판단할 수 있다. 조립용 디렉터리에는 순서대로 `asset_01.png`부터 복사한다.

- 이미지 N장이면 boundary는 N+1개다.
- 마지막 boundary는 실제 오디오 duration과 맞춘다.
- 2줄 제목은 builder의 `\n` 입력 규칙을 사용한다.
- build contract의 image count, track mapping, high-impact indices를 실제 조립 수량과 일치시킨다.
- 설계도 `## 트랙별 타임라인`에는 실제 Markdown 표를 넣어 blueprint validator를 통과시킨다.

## 정본 검증과 staging

- package validator에는 ZIP·`template_manifest.json`·template 폴더가 함께 있는 package root를 준다.
- 새로 압축 해제한 template 폴더만 주면 외부 manifest가 없어 무결성 검증이 실패할 수 있다.
- 실제 build 입력은 검증된 ZIP에서 매번 새로 압축 해제한 template를 사용한다.
- CapCut과 백그라운드 프로세스가 닫힌 상태에서 같은 로컬 draft 볼륨의 짧은 `._b-<UUID>` staging에 조립한다.
- builder에는 최종 설치 경로를 `final_draft_path`로 전달한다.
- staging build가 성공한 뒤에만 최종 폴더명으로 원자적 승격한다.

## 설치 후 실제 검증

프로젝트 폴더 생성만으로 완료하지 않는다.

1. `validate_top5isu_capcut_draft.py`로 최종 경로를 다시 읽는다.
2. 루트와 Timeline의 네 content mirror가 byte-identical인지 확인한다.
3. `draft_content.id`와 Timeline 폴더 ID를 확인한다.
4. 프로젝트 미디어와 입력 asset의 SHA가 일치하는지 확인한다.
5. 누락 경로, sample, placeholder, `.bak`, `.before_*`, staging 잔존을 확인한다.
6. `root_meta_info.json`에 프로젝트명·project ID·최종 폴더 경로가 정확히 한 건 등록됐는지 확인한다.

builder가 root 목록을 자동 등록하지 않았다면 CapCut이 닫힌 상태에서 `draft_meta_info.json`을 기존 root entry schema로 변환해 같은 디렉터리의 임시 파일에 쓴 뒤, JSON 재검증·fsync 후 `root_meta_info.json`으로 원자적 교체한다. 의미가 불분명한 legacy 카운터는 추정해서 변경하지 않는다.

`template-2.tmp`와 `Timelines/<ID>/template-2.tmp`는 필수 content mirror이므로 삭제하거나 `*.tmp` 전역 금지에 걸지 않는다. 금지 대상은 helper·backup·staging 임시파일이며, 필수 mirror는 allowlist다.

## 완료 증거

최소 완료 증거:

- writer·blueprint·contract·package·track mapping·actual draft·assembly report PASS
- 공식 실사와 참고 이미지 기반 웹툰 contact sheet QA
- TTS/자막 원문 결합 일치와 최대 2줄
- 이미지 수·애니메이션 수·high-impact 수
- 네 mirror 공통 SHA
- root 목록 등록 1건
- missing media 0, forbidden files 0, staging 0
- TOP5ISU 전용 회귀 테스트 PASS

전체 저장소 테스트에 다른 lane의 누락 경로가 섞여 있으면 이번 lane의 전용 테스트 결과와 별도로 보고한다. 관련 없는 실패를 TOP5 프로젝트 PASS로 숨기지도, TOP5 자체 실패로 오인하지도 않는다.
