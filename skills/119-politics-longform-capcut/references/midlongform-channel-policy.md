# 미드롱폼 채널 정책

이 목록은 트렌드헌터 미드롱폼 탭의 2026-07-19 등록값을 정치 롱폼 자동 소스
탐색용으로 고정한 기준이다.

## 적용 순서

1. 채널 ID를 이름보다 우선해 대조한다.
2. `BLOCK`은 모든 허용 그룹보다 우선한다.
3. `ALLOW` 24개 밖의 자동 탐색 결과는 `WAIT_CHANNEL_NOT_ALLOWLISTED`로 둔다.
4. 사용자가 특정 URL을 직접 지정한 경우에만 명시적 예외로 검토한다.
5. `ALLOW`는 소재 검토 허용일 뿐 `rights/fair-use PASS를 뜻하지 않는다`.

## 채널 목록

| 상태 | 그룹 | 채널 | YouTube 식별자 |
|---|---|---|---|
| BLOCK | 블랙리스트 | MBC 라디오 시사 | `@mbcradio_sisa` |
| ALLOW | 화이트리스트 | KTV 국민방송 | `UCIMOytYIzaUpoAM2bpT4JZQ` |
| ALLOW | 화이트리스트 | KTV 이매진 | `UCj8Snyrs1y-wnBQiUmGrTjw` |
| ALLOW | 화이트리스트 | NATV 국회방송 | `UCL-WOj1FxKR8Hlzg5tvnWKg` |
| ALLOW | 화이트리스트 | 이재명 | `UCNJM6dqu70Qr6VaseiW1Org` |
| ALLOW | 시사믹스 | 김어준의 겸손은힘들다 뉴스공장 | `UCAAvO0ehWox1bbym3rXKBZw` |
| ALLOW | 시사믹스 | 딴지방송국/다스뵈이다 | `UCxvU6bRtYhNLvZleAIGa-FQ` |
| ALLOW | 시사믹스 | 최욱의 매불쇼 | `UCMYhq9OyGI5UEz_NTAoHY7A` |
| ALLOW | 시사믹스 | 스픽스 | `UCgeOlLcX6PReHdWImEnUVTg` |
| ALLOW | 시사믹스 | 오마이TV/박정호 핫스팟 | `UClAfLVQYZSLrMAQQ_SXPVZw` |
| ALLOW | 코멘터리 | 이동형TV | `UCd4BxCKyMHG2J0X1SerTPaQ` |
| ALLOW | 코멘터리 | 박시영TV | `UCIMv9bOOGWGIfg6wPcRLItQ` |
| ALLOW | 코멘터리 | 새날 | `UCu1FzjrHosuKGvgIx8oBi8w` |
| ALLOW | 코멘터리 | 뉴스타파 Newstapa | `UCeFUGS2VCOb6DO3BiUgvwNA` |
| ALLOW | 공식/공적 | 델리민주 [더민주당] | `UCoQD2xsqwzJA93PTIYERokg` |
| ALLOW | 공식/공적 | 사람사는세상 노무현재단 | `UCJS9VvReVkplPwCIbxnbsjQ` |
| ALLOW | 공식/공적 | 국회 유튜브 | `UCsWa6xl7KxOolVhROUJ4Ghw` |
| ALLOW | 메인스트림 | MBCNEWS | `UCF4Wxdo3inmxP-Y59wXDsFw` |
| ALLOW | 메인스트림 | JTBC News | `UCsU-I-vHLiaMfV_ceaYz5rQ` |
| ALLOW | 메인스트림 | KBS News | `UCcQTRi69dsVYHN3exePtZ1A` |
| ALLOW | 메인스트림 | SBS 뉴스 | `UCkinYTS9IHqOEwR1Sze2JTw` |
| ALLOW | 메인스트림 | YTN | `UChlgI3UHCOnwUGzWzbJ3H5w` |
| ALLOW | 메인스트림 | 연합뉴스TV | `UCTHCOPwqNfZ0uiKOvFyhGwg` |
| ALLOW | 메인스트림 | CBS노컷뉴스 | `UCa97kDUvLn9OSn9xTX0uM_g` |
| ALLOW | 메인스트림 | Channel A News | `UCfq4V1DAuaojnr2ryvWNysw` |

트렌드헌터 화면의 `김어준의 겸불뉴스공장` 표기는 위 채널 ID를 기준으로
`김어준의 겸손은힘들다 뉴스공장`으로 정규화한다. `MBC 라디오 시사`의 기준
URL은 `https://www.youtube.com/@mbcradio_sisa`다.
