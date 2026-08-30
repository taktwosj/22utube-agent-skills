# GitHub branch cleanup recovery record (2026-08-30)

This record preserves the exact remote branch tips immediately before cleanup.
Deleted branches can be restored with:

```text
git push origin <SHA>:refs/heads/<branch-name>
```

## Repository state

- Repository: `taktwosj/22utube-agent-skills`
- `main`: `6392cd4eea5d838dc407b340b390530d3da6dfc4`
- Remote branches before cleanup: 50
- Open pull requests before cleanup: 15
- Branch protection: pull request required; force-push and deletion blocked on `main`
- Repository setting: merged pull-request head branches are deleted automatically

## Branches deleted

| Branch | Preserved SHA |
|---|---|
| `agent/001short-authoring-canonical-20260811` | `6b44785e9794a4a0807e02202eab3399d7625acb` |
| `agent/001short-three-stage-grid-contract-20260810` | `657c6e061274fee6a21e73cefc401011683a4218` |
| `agent/112-politics-longform-hyperframes-template-v1` | `c78844bb43ace9fe46856be868190f78b7b1466e` |
| `agent/hyperframes-112-113-contract` | `f8bc1cfcc97a58b1c294af5bf8249d1617e43ac8` |
| `agent/local-all-skill-update-20260809` | `34bdd5462be0c0dd2c61c37214ed3f3757f553f2` |
| `agent/shared-gates-separated-lanes-v2` | `df597ee0f07c3e9380d800b183bebe88dd332da4` |
| `agent/shorts-capcut-portable-root-20260803` | `df73564b8f597788901c396981843befb199dc59` |
| `agent/verified-runtime-release-reconcile-20260809` | `2d2828ca8e7fe58cd12e4481bfd7c24b13be3f54` |
| `chore/remove-011-shorts-factory-20260809` | `bd08a723635fe1c27010d5c9dac991e2ad6b0c48` |
| `claude/google-drive-accessibility-qcgc1h` | `157b438084b8f09f4ebbe5cdef357d1f80f723b4` |
| `codex/119-postmilestone-production-20260808` | `de693b38b79947c47d2586a971a040ce1f5c1bc2` |
| `codex/119-readback-hardening-20260807` | `1f60b2367fb30fb2189c6c14c6c3d8c4d18c5117` |
| `codex/119-v2-8-apply-20260811` | `f66ec089df6cf354415289a7a03b26f55759cf13` |
| `codex/longform-montage-hook-20260822` | `f734d91224db02cb6626ba82e89a0319223d15e5` |
| `codex/pr12-script-lock-schema` | `13c6305f9858afbd46b08df5fd4ac5228e1d56e8` |
| `codex/tikitaka-demucs-first` | `3e8fddae09c3762c491207339493dd7c3ad9ea5f` |
| `codex/top5isu-standalone-factory` | `7fbb0ff27e188544a4d6df07150af155b37653e9` |
| `feat/011-shorts-factory` | `0c1d7c47f16d0145fa292ca64fbb8290e09baca1` |
| `feat/119-v2-7-assembly-only-caption-layout` | `377d1ae682296f27a1de0e145a777d8c9fe22f2a` |
| `feat/verified-skill-releases` | `370035bfa57c646bc8c0457f8032274fe722259b` |
| `fix/001short-canonical-provisional-stage07` | `1e4cd78afa01739cd082f48f389c671d18fcd0ba` |
| `fix/119-material-paths-deep-module-20260814` | `0cbdbe9b3303d44b80343b4b1fa8d755c96a7306` |
| `fix/119-portable-root-bundle-20260824` | `d018cfbd43cfde34085924f387acd78cc9e88af0` |
| `fix/119-review-findings-20260814` | `42e323290691c67f4c7881f22d53b8f1aeb43f25` |
| `fix/a9-text-15-char-unify` | `9fbbae0075626dfbe8870fffd720baf4a1d05505` |
| `handoff/hyperframes-windows-unicode-20260802` | `2c9359b5d769bf78bff4e391848d9fb3c2b5132a` |
| `paperclip-001short-p0-20260801` | `3f33fe05b8dbc9f64e503208747584c38f651b45` |
| `paperclip/001short-production-agent-p0-20260801` | `3f33fe05b8dbc9f64e503208747584c38f651b45` |
| `release/typecast-active-source-20260816` | `03b4dd85918ea734122d584dd1c86df420730312` |
| `release/typecast-cross-machine-20260816` | `5c846005811143a1743b5a94972fc8d1599e4f2a` |
| `repair/001short-capcut-batch-root-causes` | `2cee71bb6a060fb7b1a97e24cb1426c5969b9207` |
| `rubric/stage04-onto-publish-20260806` | `5cd22842004d0c697851cd5037fcff6b64ba083d` |

## Unmerged patches preserved as tags

Two commits contain patches not present on `main`. They were intentionally not
cherry-picked during branch cleanup because that would mix skill-contract changes
into a repository-maintenance task.

| Tag | Commit | Patch |
|---|---|---|
| `archive-unmerged-119-pre119-authoring-20260829` | `f734d91224db02cb6626ba82e89a0319223d15e5` | PRE-119 authoring-tool assumptions |
| `archive-unmerged-typecast-runbook-20260829` | `5c846005811143a1743b5a94972fc8d1599e4f2a` | shared Typecast runbook links |

## Branches retained

- `main`
- Every open pull-request head branch except PR #38, which is superseded by this record
- `backup/20260722-pre-tikitaka-ultra-redesign`
- `review/shorts-skills-20260720`

PR #38 was not merged as-is because it also added an automatic branch-hygiene
workflow and agent-rule files that are outside the approved operating setup.

Local branches and linked worktrees are not deleted by this cleanup. Existing dirty
worktrees, `.bak` files, caches, and media remain untouched.
