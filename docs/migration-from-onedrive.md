# Migration From OneDrive

The Git repo is now the only skill source of truth. OneDrive is no longer a
skill-source or skill-cache location.

Migration flow:

1. Copy selected active skills into `skills/<skill>`.
2. Remove backups, runtime garbage, production media, archives, and secrets.
3. Replace machine-specific user paths with `$HOME`, `$env:UTUBE_ROOT`, `$env:WORKSPACE_ROOT`, or `$env:LOCALAPPDATA`.
4. Run repo verification.
5. Install to Codex, Claude, and Hermes targets.
6. Run target verification.

Do not edit runtime folders directly after migration.

Current managed set includes the core Shorts/longform stack, conditional support skills for Gemini remake intake, comment-card/reple formats, common 22utube rules, Korean history Shorts, Korean humanization, and video watching/transcript intake.

HyperFrames/video-composition helper skills are intentionally not part of this v1 managed set unless the operator explicitly re-adds that route later.
