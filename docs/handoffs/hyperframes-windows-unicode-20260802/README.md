# HyperFrames Windows Unicode `cpSync` Handoff

이 폴더는 **22utube production skill의 설치·수정본이 아닙니다.**
Windows에서 HyperFrames가 비ASCII 사용자 프로필/Temp 경로로 extracted frame directory를 materialize할 때 Node `fs.cpSync`가 fail-fast하는 문제를 다른 PC에서 안전하게 이어서 검토하기 위한 독립 handoff입니다.

## 이 브랜치의 범위

- 변경 경로: `docs/handoffs/hyperframes-windows-unicode-20260802/**`만
- 변경하지 않음: `skills/**`, `manifests/**`, 원본 미디어, 전역 HyperFrames, Node, FFmpeg
- 포함하지 않음: 영상·오디오·덤프·사용자 프로필 경로·토큰·세션값

정확한 상태와 무결성 해시는 `handoff.json`이 기준입니다.

## 다른 PC에서 시작

```bash
git clone --branch handoff/hyperframes-windows-unicode-20260802 \
  https://github.com/taktwosj/22utube-agent-skills.git
cd 22utube-agent-skills
python docs/handoffs/hyperframes-windows-unicode-20260802/scripts/verify_handoff.py
```

검사기가 통과하면 `handoff.json`을 읽습니다. 이 브랜치를 Hermes/Codex/Claude 런타임에 설치하거나 `update --prune`/`--strict`를 실행하지 마십시오.

## 포함 패치의 의미

| 파일 | 상태 | 용도 |
|---|---|---|
| `patches/hyperframes-v0.7.76-candidate-dist.patch` | `VERIFIED_CANDIDATE_ONLY` | 생성된 bundle 기준 후보. 실제 Unicode/ASCII 회귀와 5초 media gate를 통과했지만 전역·upstream 승격본은 아님. |
| `patches/hyperframes-v0.7.76-source-wip.patch` | `SOURCE_WIP_NOT_BUILT_OR_PROMOTED` | upstream `v0.7.76` source-level 후보와 테스트 초안. `git apply --unidiff-zero`로 새 worktree에만 적용하며, build/package/전역 smoke는 아직 하지 않았음. |

## 다른 PC의 재개 순서

1. 해당 PC에서 Node와 설치된 HyperFrames 버전·SHA를 새로 확인한다.
2. upstream `heygen-com/hyperframes` `v0.7.76`을 **새 worktree**로 준비한다.
3. source WIP patch를 검토·적용한 뒤 source test를 RED/Unicode GREEN/ASCII regression 순으로 수행한다.
4. source build·format·package를 성공시킨 뒤에만 새 isolated runtime에서 media smoke를 수행한다.
5. 전역 npm 설치 승격은 별도 명시 승인과 backup/rollback/해시/실제 global smoke가 모두 있을 때만 한다.

`handoff.json`은 과거 증거를 보존하지만, 현재 PC의 런타임 상태를 증명하지 않습니다. 항상 새로 읽고 검증하십시오.
