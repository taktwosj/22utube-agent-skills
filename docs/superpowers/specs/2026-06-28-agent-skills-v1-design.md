# 22utube Agent Skills v1.0 Design

## Goal

Move the active 22utube/11utube agent skills from OneDrive shared folders into a Git source of truth named `22utube-agent-skills`, with copy-only installation into Codex, Claude, and Hermes runtime folders.

## Source And Targets

- Source: `$HOME/agent-skills/skills/<skill>`
- Codex target: `$HOME/.codex/skills/<skill>`
- Claude target: `$HOME/.claude/skills/<skill>`
- Hermes target: `$HOME/.hermes/skills/22utube/<skill>`
- OneDrive role: production data only

## Safety

The install path uses copy-only deployment. Symlinks, automatic stash, and dirty updates are not allowed. Prune is allowed only for folders that contain a managed marker file. Existing target folders are backed up before overwrite.

## Verification

Verification checks manifest validity, skill folder/frontmatter consistency, forbidden file types, secret-like names, machine-specific absolute paths, target markers, and SHA256 values.
