# My Skills

Reusable skills for Codex, Claude Code, and other agents. Each skill is a self-contained directory with a required `SKILL.md` and optional `agents/`, `references/`, `scripts/`, or `assets/` resources.

## Layout

```text
my-skills/
├── .codex-plugin/plugin.json
├── .claude-plugin/plugin.json
├── claude-marketplace/.claude-plugin/marketplace.json
├── claude-marketplace/plugins/my-skills -> ../..
├── skills/
│   ├── lieflat-visual-explainer/
│   ├── notetaker/
│   ├── paper/
│   └── prompt-generator/
└── assets/
```

Use lowercase hyphen-case names and keep each skill's supporting files inside its directory. Put a skill at `skills/<skill-name>/SKILL.md`. This flat layout is supported by both Codex's plugin validator and the `npx skills` catalog scanner.

## Add A Skill

```bash
npx skills init skills/<skill-name>
```

Then edit the generated `SKILL.md`. Add stable skills to `.claude-plugin/plugin.json`; Codex discovers all skills recursively below `./skills/`.

## Install With The Skills CLI

List available skills:

```bash
npx skills add rv64m/my-skills --list
```

Install `paper` globally for Codex and Claude Code. The CLI uses symlinks by default, so one canonical copy is shared by both agents:

```bash
npx skills add rv64m/my-skills --skill paper -g \
  -a codex -a claude-code -y
```

Install the whole collection:

```bash
npx skills add rv64m/my-skills --skill '*' -g \
  -a codex -a claude-code -y
```

Use `--copy` only when symlinks are unavailable or an independent copy is desired.

## Licensing

Most repository content remains unpublished under the top-level `UNLICENSED` plugin declaration. The vendored assets inside `skills/lieflat-visual-explainer/` retain their own licenses: Visual Explainer-derived material is MIT, while Lieflat Charts assets are PolyForm Noncommercial 1.0.0 and may only be used for noncommercial purposes. See that skill's `LICENSES/` and `THIRD_PARTY_NOTICES.md` before redistribution.

## Plugin Validation

Codex:

```bash
uv run --with PyYAML python /Users/a1/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py .
```

Claude Code:

```bash
claude --plugin-dir /Users/a1/Codes/my-skills
claude plugin validate /Users/a1/Codes/my-skills
```

Install the local Claude marketplace with:

```bash
claude plugin marketplace add /Users/a1/Codes/my-skills/claude-marketplace
claude plugin install my-skills@my-skills-local
```
