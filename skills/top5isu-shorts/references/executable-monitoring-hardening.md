# TOP5 실행 감시체계 보강

## 목적

TOP5 제작의 기존 `production_contract.yaml`, 상태기계, 하네스 및 validator를 유지하면서 실제 누락이 확인된 감시 조건만 최소 변경으로 보강한다. 다른 스킬의 프로토콜은 구조 참고용이며 TOP5 제작 규칙을 복사하는 근거가 아니다.

## 권위와 중복 방지

권위 순서는 다음과 같다.

1. 현재 워크스페이스 지침
2. TOP5 `production_contract.yaml`
3. 기존 TOP5 상태기계와 `top5_harness.py`
4. `top5isu-shorts` validator와 profile 계약
5. 과거 대화 또는 다른 스킬의 구현 예시

새 `protocol.json`, Schema, validator 또는 하네스는 기존 체계가 실제 필수 조건을 표현하지 못할 때만 추가한다. 이름과 형식의 대칭을 위해 두 번째 상태 권위를 만들지 않는다.

## 보강 절차

1. 스킬 검색 경로 밖에 백업하고 파일별 SHA-256 manifest를 만든다.
2. Git 정본·branch·commit과 활성 설치본을 확인한다.
3. 기존 계약, 상태, validator, 테스트, completion report 필드를 표로 정리한다.
4. 요구사항마다 `기존 gate`, `부분 구현`, `미구현`으로 분류한다.
5. `부분 구현`과 `미구현`만 최소 diff로 수정한다.
6. 수정 전 실패 fixture를 실행해 RED를 확인한다.
7. 최소 구현 후 해당 fixture와 기존 회귀 테스트를 GREEN으로 만든다.
8. 완전히 새로운 임시 폴더에서 self-check와 정상·실패 fixture를 다시 실행한다.
9. 파일 수, directory SHA-256, manifest 및 validator 버전을 기록한다.
10. Git commit·push·merge와 공개 업로드는 별도 승인 범위로 취급한다.

## 필수 감시 범주

기존 gate가 아래 범주를 실제로 막는지 확인한다.

- 고정 인사 → 주제 안내 → 5위 → 4위 → 3위 → 2위 → 1위 → 마무리 순서
- 금액형 순위의 숫자·화면표기·낭독표기·출처 검증
- 빈 이미지 manifest 승인 금지
- 승인 이미지·음성 SHA 변경 후 렌더 금지
- 승인 SuperTone voice/model과 자동 대체 금지
- 자막 최대 2줄·안전폭·display/spoken 분리
- 이미지별 transition 1개와 필요한 고강도 효과 수
- root template 불변, 신규 project/timeline ID, 샘플 미디어 0개
- 필수 트랙 매핑과 root·Timeline·subdraft mirror 일치
- stale staging prefix 0개와 모든 media path 존재
- CapCut 클라우드 행 이름·크기·길이·유형·수정시간 readback
- 업로드 제목·설명·원본 출처 누락 금지
- 사용자 승인 없는 공개·예약 업로드 완료 금지
- `NOT_RUN` 또는 `BLOCKED` gate가 하나라도 있으면 FINAL 금지

## 실패 fixture 원칙

각 감시 범주에는 최소 하나의 실패 fixture가 있어야 한다. 실패 fixture는 validator의 non-zero exit와 고정 오류코드를 검증한다. 테스트를 통과시키기 위해 gate를 약화하거나 미검증 값을 기본 PASS로 바꾸지 않는다.

대표 fixture:

- 인사 직후 바로 5위로 이동
- 순위 순서 변경
- 금액 또는 출처 누락
- 빈 이미지 manifest를 승인 처리
- 승인 자산 SHA 변경
- 잘못된 TTS voice/model
- 자막 3줄 또는 안전폭 초과
- transition 누락
- 샘플 미디어·stale path·mirror 불일치
- 완료 메타데이터 또는 클라우드 행 필드 누락
- 승인 없는 공개 업로드
- 일부 gate가 `NOT_RUN`인데 FINAL 처리

## 완료 증거

완료보고는 최소한 다음을 기계 판독 가능하게 기록한다.

- episode/production/profile/template ID
- contract version과 SHA-256
- 최종 프로젝트명·경로·hash·duration
- 현재 draft readback
- 승인 이미지·음성·자막 hash
- validator 결과
- CapCut 클라우드 목적지와 행 readback
- 업로드 제목·설명·원본 출처
- 공개 업로드 상태와 명시 승인
- Trend Hunter·OneDrive 메타데이터 동기화 상태

증거가 없으면 `PASS`, `FINAL`, `COMPLETE` 대신 `WAIT`, `NOT_RUN`, `BLOCKED`, `FAIL`을 사용한다.

## 외부 AI 압박시험

외부 AI가 실행되지 못한 경우 이를 스킬 실패로 해석하지 않는다. 외부 시험은 `NOT_RUN`과 실제 원인을 기록하고, 독립된 새 임시 폴더의 결정론적 fixture 시험 결과와 분리한다. 외부 에이전트의 성공 보고는 Git diff, 파일 readback, 테스트 출력으로 독립 검증한다.
