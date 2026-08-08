# 단일 단계 재개

실패 단계가 불명확할 때만 이 문서를 읽는다. 아래에서 처음 만족하는 행 하나를 고르고
지정 reference 하나만 읽는다. 선택한 뒤 이 표나 다른 단계 문서를 다시 읽지 않는다.

| 실제 상태 | 재개 reference | 다시 하는 범위 |
|---|---|---|
| 최종 대본 미승인 | `direct-script.md` | 대본과 사용자 승인 |
| 필요한 source/SRT/cut이 없거나 download·ffprobe 실패 | `source-media.md` | 실패 source 하나 |
| narration media/SRT가 없거나 API·정렬 실패 | `narration.md` | 실패 문장·파일 |
| 지원되는 필수 이미지가 없거나 자산 검사 실패 | `visual-assets.md` | 실패 자산 하나 |
| legacy Stage 2 사용이 명시됨 | `legacy-stage2.md` | preflight 실패 입력 하나 |
| root·target·cards·build·relink·visual 문제 | `capcut-assembly.md` | 최초 실패 gate 하나 |

실제 source media, captions, narration media/SRT, Resources, `episode_cards.json`, build report,
relink readback이 재개점이다. 새 상태 파일, receipt, checkpoint, 비공식 schema를 만들지 않는다.
완료된 산출물의 hash·duration·검사 결과가 그대로면 앞 단계를 다시 읽거나 실행하지 않는다.

활성 단계에 필요한 media·integrity·build·relink·visual 검사에서 구체적 실패가 있을 때만
멈춘다. 원인을 최소 수정하고 같은 검사를 재실행한다. PASS 전에는 다음 단계로 진행하지
않지만, 다른 병렬 작업의 정상 산출물은 폐기하거나 재생성하지 않는다.
