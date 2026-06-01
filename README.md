# paperdown2md

**Agent Skill** ([`SKILL.md`](SKILL.md)) for downloading academic papers and converting them to Markdown — compatible with **Cursor**, **Claude Code**, Codex CLI, and any agent that auto-loads skills.

Resolve arXiv / DOI / PDF URL / English title → download PDF → MinerU `extract` (Token) → `full.md` + `images/` per paper folder.

Discoverable on [SkillsMP](https://skillsmp.com/search?q=paperdown2md) (indexed from this GitHub repo).

## Install

### Cursor (recommended)

```bash
git clone https://github.com/Iayce/paperdown2md.git ~/.cursor/skills/paperdown2md
```

Or symlink a local checkout:

```bash
ln -s /path/to/paperdown2md ~/.cursor/skills/paperdown2md
```

### Dependencies

| Requirement | Notes |
|-------------|-------|
| **skillsplace** conda env | Python for `paperdown2md.py` must run here |
| **mineru-open-api** CLI | MinerU Open API client |
| **MinerU Token** | `MINERU_TOKEN` env var or `~/.cursor/skills/mineru/key` — **never commit tokens** |

Optional: [LightRead CLI](https://github.com) (`lr`) for title search fallback.

## Quick start

```bash
bash ~/.cursor/skills/paperdown2md/scripts/run.sh \
  -o "./papers" \
  --name "CIDD" \
  "https://arxiv.org/abs/xxxx.xxxxx"
```

Output layout:

```text
<papers>/
└── <folder-name>/
    ├── <name>.pdf
    ├── full.md
    └── images/
```

PDF only (skip MinerU):

```bash
bash ~/.cursor/skills/paperdown2md/scripts/run.sh \
  -o "./papers" --skip-extract "10.1038/s41586-021-03824-4"
```

## When it triggers

Keywords: `paperdown2md`, paper download, PDF to Markdown, MinerU, arXiv, DOI, `full.md`, `Agent Skill`, `SKILL.md`, `Cursor`, `Claude Code`, `SkillsMP`.

See [`SKILL.md`](SKILL.md) for the full agent workflow.

## Repository layout

```text
SKILL.md                 # Agent entry point
scripts/
  run.sh                 # Recommended entry (skillsplace Python)
  paperdown2md.py        # Download + MinerU extract
example/                 # Sample CIDD output (full.md + images/)
evals/evals.json         # Eval prompts
```

## Security

- MinerU tokens live **only** on your machine (`MINERU_TOKEN` or `~/.cursor/skills/mineru/key`).
- This repo never stores API keys; `.gitignore` blocks `key`, `.env`, and similar files.

## License

MIT — see [LICENSE](LICENSE).

## 中文简介

paperdown2md 是一个 **Agent Skill**（根目录 `SKILL.md`），面向 **Cursor**、**Claude Code** 等 Agent：把 arXiv / DOI / PDF 链接 / 英文标题解析成 PDF，再用 MinerU Token 版 `extract` 生成 `full.md` 与 `images/`，每篇论文独立文件夹。Token 仅本地配置，勿提交到仓库。

安装：`git clone https://github.com/Iayce/paperdown2md.git ~/.cursor/skills/paperdown2md`
