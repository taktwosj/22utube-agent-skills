# Migration From OneDrive

The Git repo is the only skill source of truth. Old OneDrive skill-source and
skill-sync mirrors are retired and must not be recreated. OneDrive is for
production files and handoff packages only.

Migration flow:

1. Keep selected active skills in `skills/<skill>`.
2. Remove any old OneDrive skill-source and skill-sync mirrors.
3. Remove backups, runtime garbage, production media, archives, and secrets.
4. Replace machine-specific user paths with `$HOME`, `$env:UTUBE_ROOT`, `$env:WORKSPACE_ROOT`, or `$env:LOCALAPPDATA`.
5. Run repo verification.
6. Install to Codex, Claude, and Hermes targets from Git.
7. Run target verification.

Do not edit runtime folders directly after migration.

Current managed set includes the core Shorts/longform stack, conditional support skills for Gemini remake intake, comment-card/reple formats, common 22utube rules, Korean history Shorts, Korean humanization, and video watching/transcript intake.

HyperFrames/video-composition helper skills are intentionally not part of this v1 managed set unless the operator explicitly re-adds that route later.
