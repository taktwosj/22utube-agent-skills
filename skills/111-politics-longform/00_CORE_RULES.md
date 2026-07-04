# Core Rules

Use one episode folder for both stages:

```text
22factory_20260628\02_politics_longform\episodes\PL_YYYYMMDD_slug
```

Hard rules:

1. Stage 1 stops before CapCut.
2. Stage 2 validates Stage 1 before making a CapCut draft.
3. Default CapCut base is `jungchilong` only.
4. Never fall back to YP007, YP005, YM007, YSM, or generated derivatives unless the user explicitly names one in the current request.
5. Source label comes from real source metadata, not the template name.
6. Korean corruption such as `�`, `占`, `?뺤`, or mojibake means `WAIT_ENCODING_UNSAFE`.
7. If CapCut is open or background processes remain, do not overwrite an existing draft folder.
8. Never claim `PASS`, `FINAL`, `upload_ready`, or `검증 통과` without evidence from the matching stage contract or final harness.

Legacy `22utube\11utube\yellow\episodes` is read-only reference unless the user explicitly asks for legacy repair. Local CapCut drafts stay under the local `com.lveditor.draft` directory; OneDrive stores manifests, snapshots, reports, upload text, and pointers.
