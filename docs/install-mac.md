# macOS Install

```bash
git clone https://github.com/taktwosj/22utube-agent-skills.git "$HOME/agent-skills"
bash "$HOME/agent-skills/scripts/install.sh" --target all
bash "$HOME/agent-skills/scripts/verify.sh" --target all
```

Update:

```bash
bash "$HOME/agent-skills/scripts/update.sh" --target all --prune --dry-run
bash "$HOME/agent-skills/scripts/update.sh" --target all --prune
```

Single-skill update:

```bash
bash "$HOME/agent-skills/scripts/update.sh" --target all --only 000brainstorm --only 111-politics-longform
```
