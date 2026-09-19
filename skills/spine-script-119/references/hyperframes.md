# 하이퍼프레임 — 상세

> 원문: `spine-script-119/SKILL.md` 에서 줄 단위로 옮김. 내용 수정 없음.


**나레이션 카드는 전부 움직이는 영상이다.** 정지 카드로 대체하지 않는다. 대체하면 회차 절반이 같은 결의 글자판으로 남는다.

먼저 무엇을 만들어야 하는지 뽑는다.

```bash
python plan_hyperframes.py --root <root>
python plan_hyperframes.py --root <root> --missing    # 아직 없는 것만
python plan_hyperframes.py --root <root> --tsv        # 표로
```

영상이 없는 나레이션 카드가 하나라도 있으면 `gen_script.py` 와 `gen_evidence.py` 가 `HYPERFRAME_MISSING` 으로 멈추고 필요한 장면 목록을 찍는다. 정지 카드로 조용히 넘어가지 않는다.

옛 회차를 복구할 때만 `cards_def.py` 에 `ALLOW_STATIC_NARRATION_CARDS = True` 를 두어 예외로 만든다. 새 회차에 쓰지 않는다.

디자인은 `hyperframes-news-graphics` 의 승인 템플릿을 기준으로 한다. 화면 문법은 `hyperframes-politics-119` 의 장면 모드다.
인물 사진은 NAS `119jungchi\_asset\people` 정본을 로컬 `_images\people\_src` 로 복사해 쓴다 → `hyperframes-politics-119/references/people-photos.md`.


## 장면 제작 — 상세

→ 비트·도식·화면 자리·실행: [장면 모드](../../hyperframes-politics-119/references/scene-mode.md).

**장면 쪽이 본래 쓰임이다.** 카드는 평균 삼사 초라 한 장에 한 편씩 만들면 짧은 클립이 줄줄이 이어져 화면이 계속 끊긴다. 나레이션이 이어지는 동안 그래픽도 이어져야 한다. 연속한 카드 서넛을 묶어 **십 초 안팎 한 장면**으로 만들고, 카드마다 그 장면의 다른 구간을 가져가게 한다.

```
NL88   video_start_us 0          dur 4458345
NL89   video_start_us 4458345    dur 4125011
NL90   video_start_us 8583356    dur 3083356
```

`gen_evidence.py` 가 타임라인 순서대로 구간을 잘라 넣는다. 카드 경계에서 끊기지 않는다.

`gen_script.py` 는 나레이션 카드를 전부 `NARRATION_VIDEO` 로 낸다.
`between_image` 와 `CHAPTER_LOCK_TABLE` 의 타입도 실제 카드 구성에서 뽑는다.
정지 이미지 카드가 0장이면 `between_image: NO` 로 나간다 — 고정값 `YES` 를 쓰면
119 의 compile 이 `PRE119_PLAN_IMAGE_CARD_REQUIRED` 로 막고 매 회차 손으로 고쳐야 한다. `style_profile` 은 비운다 — 인셋 템플릿으로 렌더한 물건이 아니다.

`render_cards.py` 와 `make_card_css.py` 는 나레이션용으로는 쓰지 않는다. 챕터 카드에만 남는다.

```
1920×1080  H.264 mp4  오디오 없음
길이       장면을 나눠 쓰는 카드 길이의 합 이상. 남으면 버린다
배치       한 장면을 쓰는 카드들은 타임라인에서 붙어 있어야 한다
```

멈추는 조건 셋이다. 만들기 전에 걸린다.

```
HYPERFRAME_SCENE_NOT_CONTIGUOUS   사이에 다른 카드가 끼었다. 장면이 갈라진다
HYPERFRAME_TOO_SHORT              영상이 카드 합계보다 짧다. 뒤가 검게 빈다
HYPERFRAME_DUPLICATE_CLAIM        한 줄을 단독 파일과 장면 파일이 같이 물었다
```

`출처` 자막이 붙지 않고 영상 자체의 소리도 쓰지 않는다. 나레이션 음성은 정지 카드와 같은 방식으로 붙는다. 인용 클립이 아니므로 `SOURCE_VIDEO` 로 넣지 않는다 — 그렇게 하면 화면에 `출처` 가 찍히고 나레이션이 빠진다.

인셋 템플릿으로 렌더한 물건이 아니라서 `style_profile` 은 비운다. 비우지 않으면 preflight 가 `INSET_CARD_IMAGE_REQUIRED` 로 막는다.

