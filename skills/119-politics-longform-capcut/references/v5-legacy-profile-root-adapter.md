# v5 legacy profile root adapter

Use only when the resolved active root's bundle contains
`runtime_adapters/v5_legacy_profile_adapter_v1.json`. It is a host compatibility
layer, not a replacement root and not a ZIP mutation.

## Invariants

1. Resolve the active root first; require the adapter config's `root_version`
and archive SHA to match the resolver output exactly.
2. Never edit or rezip the immutable archive. Extract only to a temporary
staging directory.
3. In staging only, replace the configured legacy root prefix. Bind every
`__CAPCUT_RELINK_REQUIRED__/{episode}/Media/` path to the newly copied episode
Media directory.
4. Replace only adapter-configured embedded legacy resource/test-media paths.
All final `.json`/`.tmp` files must contain zero legacy-profile paths and zero
relink placeholders.
5. If CapCut metadata requires a source registry row, back up
`root_meta_info.json`, add a temporary seed, register the new project, then
remove the seed. On any failure restore the original metadata bytes and remove
only the new target project/Media directory.
6. Verify: exact archive SHA, project registry entry count 1, seed count 0,
all primary draft mirrors hash-identical, every bound local media file exists,
and timeline duration is unchanged.

## Portability gate

The only acceptable bundled entry point is:

```text
scripts/build_politics_v5_legacy_adapter.py
```

It may be added only from the actual previously used source with its source
SHA-256 recorded and an arbitrary-working-directory test passing. The named
legacy Hermes location and the supplied 36-file artifacts do not currently
contain that verified source, so this package status is:

```text
WAIT_V5_ADAPTER_SOURCE_REQUIRED
```

When this blocker is present, do not call the stock card builder for an adapter
root and do not fabricate, reconstruct, or copy an unverified replacement. A
normal resolved root without the adapter config still uses the stock builder.

## Completion boundary

`MEDIA_RELINK=PASS_LOCAL_PATH_BOUND` is a static binding result, not visual
approval. Open/readback/visual QA remain mandatory before CapCut completion.
