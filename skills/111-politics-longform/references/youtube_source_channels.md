# YouTube Source Channels

Use this reference in Stage 1 source intake before selecting source URLs. This
is a discovery pool for Korean 민주진영 political longform work, not a proof
source and not a licensing clearance list.

Last reviewed: 2026-07-05.

Rules:

- Never use a channel listed under `Hard Blacklist`. If a user-provided URL,
  search result, playlist item, or downloaded metadata matches a blacklist
  locator, stop Stage 1 with `WAIT_FORBIDDEN_SOURCE_CHANNEL`.
- Start with the hard whitelist, then add priority current-affairs channels.
  Prior tests showed that a mix of official/public-record video and 시사채널
  video gives the best result for this lane.
- Trust the downloaded video's metadata over this list. Record `channel`,
  `channel_id`, `channel_url`, `webpage_url`, `upload_date`, and `title` from
  `source_full.info.json` or equivalent `yt-dlp` metadata.
- Do not use this list as the visible source label. Visible source labels come
  from the actual source metadata and Stage 2 T1 lock.
- If a channel is renamed, unavailable, missing, or issue-specific research
  requires another channel, record `CHANNEL_LIST_STALE` or
  `ISSUE_SPECIFIC_SOURCE_ADDED` in the Stage 1 report.
- For hostile, opposition, or right-leaning channels, use them only when the
  video needs contrast/context evidence. Label them neutrally and do not let
  them drive 민주진영 framing.

## Hard Blacklist

Do not use these channels for source research, source download, roughcut EDL,
source labels, upload copy, or visible source labels.

| Label | Forbidden locator | Action |
| --- | --- | --- |
| MBC 라디오 시사 | `https://www.youtube.com/@mbcradio_sisa` / `@mbcradio_sisa` | Stop with `WAIT_FORBIDDEN_SOURCE_CHANNEL`; choose another source. Do not use as contrast/context either. |

This blacklist does not ban `MBCNEWS @MBCNEWS11`. Keep `MBCNEWS` available only
for mainstream/context footage when needed.

## Hard Whitelist +++

Use these first when looking for official/public-record footage.

| Label | YouTube locator | Use |
| --- | --- | --- |
| KTV 국민방송 | `https://www.youtube.com/@KTV_korea` | government/public policy footage, briefings, official 대통령/정부 일정 |
| KTV 이매진 | `https://www.youtube.com/@KTV이매진` / `https://www.youtube.com/channel/UCj8Snyrs1y-wnBQiUmGrTjw` | 이재명 대통령 영상 기록, 국정 행보, 메가 프로젝트 source |
| NATV 국회방송 | `https://www.youtube.com/@NATV_korea` | National Assembly hearings, public-record footage |
| 이재명 | `https://www.youtube.com/@이재명tv` / `https://www.youtube.com/channel/UCNJM6dqu70Qr6VaseiW1Org` | 이재명 official/live channel, speeches, events |

## Proven Current-Affairs Mix +++

Use these with the hard whitelist to build the stronger official + 시사채널 mix.

| Label | YouTube locator | Use |
| --- | --- | --- |
| 김어준의 겸손은힘들다 뉴스공장 | `https://www.youtube.com/@gyeomsonisnothing` | daily issue anchor, interviews, 현안 흐름 |
| 딴지방송국 / 김어준의 다스뵈이다 | `https://www.youtube.com/@BUNKER1MEMBERSHIP` | longform talks, 다스뵈이다, 유시민/김어준 context |
| [팟빵] 최욱의 매불쇼 | `https://www.youtube.com/@maebulshow` | panel talk, debate, issue reactions |
| 스픽스 | `https://www.youtube.com/channel/UCgeOlLcX6PReHdWImEnUVTg` | interviews, issue panels, political commentary |
| 오마이TV / 박정호의 핫스팟 | `https://www.youtube.com/@OhmynewsTV` / `https://www.youtube.com/channel/UClAfLVQYZSLrMAQQ_SXPVZw` | 박정호의 핫스팟, field/interview videos, progressive news context |

Known high-fit source patterns:

- `김어준의 뉴스공장 '겸손은 힘들다'`
- `오마이TV, 박정호의 핫스팟`

## Additional Commentary

| Label | YouTube locator | Use |
| --- | --- | --- |
| 이동형TV | `https://www.youtube.com/@DHLeeTV` | political commentary, party dynamics |
| 박시영TV | `https://www.youtube.com/@parksiyoungTV` | polling, strategy, election/party analysis |
| [공식] 새날 | `https://www.youtube.com/@saenal` | progressive commentary and daily issue framing |
| 뉴스타파 Newstapa | `https://www.youtube.com/@news_tapa` | investigative context and source corroboration |

## Official And Public Record

| Label | YouTube locator | Use |
| --- | --- | --- |
| 델리민주 [더불어민주당] | `https://www.youtube.com/@dailyminjoo` | party meetings, briefings, official statements |
| 사람사는세상노무현재단 RohMoohyunFoundation | `https://www.youtube.com/@443RohmoohyunFoundation` | Roh Moo-hyun archive, speeches, foundation context |
| 국회 유튜브 | `https://www.youtube.com/channel/UCsWa6xl7KxOolVhROUJ4Ghw` | official Assembly clips and committee material |

## Mainstream And Context

| Label | YouTube locator | Use |
| --- | --- | --- |
| MBCNEWS | `https://www.youtube.com/@MBCNEWS11` | mainstream news context and source footage |
| JTBC News | `https://www.youtube.com/@jtbc_news` | mainstream news context and explainers |
| KBS News | `https://www.youtube.com/channel/UCcQTRi69dsVYHN3exePtZ1A` | public broadcaster news context |
| SBS 뉴스 | `https://www.youtube.com/@sbsnews8` | mainstream news context |
| YTN | `https://www.youtube.com/@ytnnews24` | live/fast news context |
| 연합뉴스TV | `https://www.youtube.com/@yonhapnewstv23` | wire-service TV context |
| CBS노컷뉴스 | `https://www.youtube.com/@cbs_nocut` | news clips, interviews, field context |
| Channel A News (Korea) | `https://www.youtube.com/@channelA-news` | contrast/context source only when needed |

## Regional And Issue-Specific

Use regional broadcasters when the issue is local or when they hold the clearest
original footage.

Known examples from prior politics-longform Stage 1 packages:

- 광주MBC
- 부산MBC뉴스
- 대구MBC뉴스

When a regional or issue-specific source becomes important, add the exact
YouTube metadata to `source_manifest.json`; do not rely on this free-text list.
