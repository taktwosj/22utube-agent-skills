# 04 완전표 보고와 승인

`20_script/URAKKAI_BLUEPRINT.md`에 승인 대상 구조, 순서, 오디오 정책을 기록하고 두 정본 표와 일치시킨다. 다음 명령을 실행한다.

```text
python -B scripts/validate_capcut_grids.py \
  --original <episode_root>/20_script/original-capcut-grid.md \
  --urakkai <episode_root>/20_script/urakkai-capcut-grid.md \
  --emit-report
```

검증이 PASS일 때 명령이 출력한 원본표와 우라까이표를 순서대로 대화창에 그대로 붙인다. 외부 AI 검토는 호출하지 않는다.

수동 모드는 `WAIT_USER_URAKKAI_APPROVAL`에서 사용자 승인을 기다린다. 자동 모드는 승인 질문 없이 `URAKKAI_AUTO_APPROVED`로 계속하지만, 완전표 검증과 대화창 출력은 동일하게 수행한다.

`TABLE_EMPTY_CELL_FORBIDDEN`, `TABLE_UNVERIFIED_CELL`, 행 순서 오류, 머리글 오류가 있으면 Stage 05로 진행하지 않는다.
