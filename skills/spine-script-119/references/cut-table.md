# 컷표·나레이션 줄 끼워 넣기 — 상세

> 원문: `spine-script-119/SKILL.md` 에서 줄 단위로 옮김. 내용 수정 없음.


컷은 `work/final_cuts.py` 한 곳에 적는다. 틀은 `templates/final_cuts.template.py`.

```text
MONTAGE    오프닝 몽타주 행. kind=H
BODY       (나레이션 블록, 그 블록 뒤 컷들). 순서가 곧 타임라인. 컷 없는 블록도 적는다
CHAPTERS   블록 → (챕터 짧은 이름, 챕터 제목). 화면 칩·동행 문장 집계에 쓴다
행         (key, kind, video_id, in, out, 메모)   kind  H 몽타주 / S 척추(진행자 평론·증언) / B 사건 원본·살
```

경계는 자동자막 cue 만 믿지 않는다. cue 는 문장 중간에서 끊기는 일이 많다. 후보 구간만 받아써서 말이 시작·끝나는 시각을 단어 단위로 보고 찍는다.

```bash
python asr_window.py --root <root> --video 32uRfOiLT5I --start 18:00 --end 20:20
python asr_window.py --root <root> --batch work/asr_jobs.tsv --edges 8
```

`work/asr/<video_id>_<start>-<end>.json` 에 절대 시각으로 남는다. 한 번에 20분 이하, 컷 후보 구간만. 찍은 뒤 `TOPIC_RANGE` 를 채운다. `python final_cuts.py` 가 H/S/B 합계를 찍는다.

컷이 여럿이면 `work/asr_jobs.tsv` 에 `video_id<TAB>start<TAB>end` 로 모아 `--batch` 로 한 번에 돌린다. 모델을 한 번만 올린다. 경계만 필요하면 `--edges 8` — 시작·끝 앞뒤 8초씩 두 창만 받아쓴다. 컷 전체를 받아쓰면 쓰는 길이의 두 배를 받아쓰게 된다 (2026-09-18 회차 42컷 70분). 영상 ID 가 `-` 로 시작하면 `--video=-abc` 처럼 `=` 로 붙인다. 첫 실행에서 cuBLAS·cuDNN DLL 이 없다고 CPU 로 떨어지면 멈추고 사용자 터미널에서 `pip install nvidia-cublas-cu12 nvidia-cudnn-cu12` 를 받는다. CPU 는 GPU 의 십수 배 느리다.

**길이 초과 시 줄이는 순서.** 러닝타임 목표(30분)를 넘기면 `B`(사건 원본·살) 컷부터 줄인다. `S`(척추) 컷은 `build_assets.py` 의 50% 비율 검사가 여유 있을 때만 손댄다. `S` 를 먼저 줄이면 비율이 깨져 되살리게 된다 (2026-09-18 회차, 트림 두 번).

```bash
python make_cards.py --root <root>
```

`cards_def.py` 의 `CARDS = [` 아래를 새로 쓴다. 그 위 회차 정의는 두고, 순서는 `몽타주 → CTA → 블록마다 [나레이션 줄 → 그 블록 뒤 컷] → 마무리 CTA` 다. 컷표나 나레이션을 고치면 다시 돌린다. `CARDS` 를 손으로 고치지 않는다 — 다음 실행에서 지워진다.

```text
CHAPTER_LABEL_MISSING           BODY 블록이 CHAPTERS 에 없다
NARRATION_BLOCK_NOT_IN_BODY     나레이션 블록이 컷표에 없다. 줄이 조용히 빠진다
CUT_KIND_UNKNOWN                본편 컷이 S·B 가 아니다
SHORTS_BLOCK_IN_BODY            쇼츠 전용 블록 N_SHORTS 가 컷표에 있다. 롱폼에 넣지 않는다
```

## 나레이션 줄 끼워 넣기

합성까지 끝난 뒤 줄을 더하거나 빼면 NL 번호가 전부 밀린다. 다시 합성하지 않는다.

```text
1  work/narration_lines.json 을 work/_backup_before_insert/ 로 복사
2  narration/<block>.txt 수정 → check_narration.py
3  renumber_narration.py --dry      매핑 확인
4  renumber_narration.py            wav·장면 mp4·scenes.py 이름을 새 번호로
5  tts_lines.py                     새 줄만 합성
6  make_cards.py → render_scenes.py --missing
```

장면 mp4 는 전부 `_old_numbering/` 으로 옮긴 **뒤에** 새 이름으로 복사한다. 옮기면서 바로 복사하면 새 이름이 아직 안 옮긴 원본과 겹쳐 덮어쓴다(2026-09-14 장면 3개 유실). 걸친 줄이 바뀐 장면은 `HF_NEEDS_RERENDER` 로 찍히고, `scenes.py` 에는 `NLxx_OLD` 로 남는다. 고친 뒤 다시 렌더한다.

