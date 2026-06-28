# Image Agent Route

Use this route for landscape midform/longform image generation unless a later user instruction overrides it.

## Default Route

Google Flow is the default bulk image route for 22utube landscape midform/longform.

Use this priority:

1. Google Flow / Google image generation for normal 20+ cut and 100+ cut production.
2. Official Image2 only when Flow is blocked, the user requests Image2, a harness requires Image2, or a thumbnail/high-quality still specifically needs it.
3. No local placeholder images, Codex `image_gen`, or CapCut internal image generation for production stills.

The agent owns the Flow planning and tracking loop:

1. Calculate the required cut count from runtime and density rules.
2. Write one image prompt per cut in `06_longform_flow_prompts.md`.
3. Update `production_console.json` with cut, prompt, asset path, and status.
4. Generate images through Flow.
5. Save generated images into `images/flow/scene_01.*` through `scene_NN.*`.
6. Maintain `images/flow/flow_manifest.json`.
7. Sync assets into `video/images/flow/`.
8. Update the production console so the new images appear immediately.
9. Run Flow manifest validation before CapCut:

```powershell
py -3 tools\google_flow_manifest.py {episode_dir} --sync-video-assets
py -3 tools\n8n_youtube_runner.py --action flow_manifest --episode-dir {episode_dir} --channel {channel} --mode longform --strict-exit
```

The Flow manifest must catch missing files, failed scenes, duplicate hashes, and sequence mismatch before CapCut import. Do not allow scene numbers to drift.

Do not search for image API keys in files, environment variables, browser state, chat history, or system settings. Do not require `OPENAI_API_KEY` unless an explicit direct API image mode is selected. If Flow cannot be used, mark the stage as `BLOCKED - Flow unavailable` and only then use an approved fallback.

## Image2 / Chrome Exceptions

Official Image2 / Chrome Prompt Runner is not the default image route. Use it only when one of these is true:

- The user explicitly asks for Image2 or Chrome Prompt Runner.
- Image generation is impossible in the current Codex session, the stage has been reported as blocked, and the user approves Chrome fallback.
- Existing official Image2 browser work must be resumed.
- A harness or project gate explicitly requires official browser Image2.

When none of those conditions applies, do not silently switch to Image2 or Chrome. Keep the image stage blocked until an available approved route is confirmed.

## Prompt Shape

Each prompt must be complete enough to generate without reading the script:

```text
16:9 cinematic infographic illustration, {scene subject}, {financial mechanism}, {main objects}, {directional flow}, high contrast, readable composition, no text, no watermark
```

For Google Flow, write prompts as image-and-video friendly scene briefs:

- visual subject and background first
- camera movement or motion idea second
- overlays/effects third
- negative text rule last: no burned-in Korean, no watermark, no UI

Keep Korean captions out of the image prompt unless the user explicitly wants burned-in text. Text belongs in CapCut, HyperFrames, or production-console overlays.

## Status Wording

Use clear stage status in reports and `production_console.json`:

```text
WAIT - image prompts ready
RUNNING - generating Flow images
PASS - images saved and console updated
BLOCKED - Flow unavailable
```
