# Migration From OneDrive

OneDrive `codex_skills_source` is now legacy cache. The Git repo is the source of truth.

Migration flow:

1. Copy selected active skills into `skills/<skill>`.
2. Remove backups, runtime garbage, production media, archives, and secrets.
3. Replace machine-specific user paths with `$HOME`, `$env:UTUBE_ROOT`, `$env:WORKSPACE_ROOT`, or `$env:LOCALAPPDATA`.
4. Run repo verification.
5. Install to Codex, Claude, and Hermes targets.
6. Run target verification.

Do not edit runtime folders directly after migration.
