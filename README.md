# paperdown2md

**Agent Skill** ([`SKILL.md`](SKILL.md)) for downloading academic papers and converting them to Markdown — compatible with **Cursor**, **Claude Code**, Codex CLI, and any agent that auto-loads skills.

Resolve arXiv / DOI / PDF URL / WeChat or Xiaohongshu post URL / English title → download PDF → MinerU `extract` (Token) → `full.md` + `images/` per paper folder.

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

Optional: [LightRead CLI](https://github.com) (`lr`) for title search fallback; [web-access](https://github.com/eze-is/web-access) CDP proxy for WeChat articles when HTTP is blocked.

### Social post URLs (WeChat / Xiaohongshu, v1.2+)

```bash
# WeChat
bash ~/.cursor/skills/paperdown2md/scripts/run.sh -o "./papers" \
  "https://mp.weixin.qq.com/s/jMW2lbgiHDka8CASFtQ81w"

# Xiaohongshu (keep full share URL with xsec_token)
bash ~/.cursor/skills/paperdown2md/scripts/run.sh -o "./papers" \
  "https://www.xiaohongshu.com/explore/6a1c2d75000000000603739b?xsec_token=..."
```

Flow: fetch post (HTTP → browser CDP fallback) → extract arXiv/DOI/PDF links → if none, search OpenAlex + arXiv API by title/keywords → download + MinerU.

### WeChat article URLs (v1.1+)

```bash
bash ~/.cursor/skills/paperdown2md/scripts/run.sh \
  -o "./papers" \
  "https://mp.weixin.qq.com/s/jMW2lbgiHDka8CASFtQ81w"
```

The script fetches the article, extracts arXiv/DOI/PDF links from the body, then downloads. If HTTP hits anti-bot (e.g. 环境异常), it falls back to Chrome CDP via web-access (`node ~/.cursor/skills/web-access/scripts/check-deps.mjs`). See **Social post URLs** above for Xiaohongshu and literature-search fallback.

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

paperdown2md 是一个 **Agent Skill**（根目录 `SKILL.md`），面向 **Cursor**、**Claude Code** 等 Agent：把 arXiv / DOI / PDF 链接 / 微信公众号 / 小红书帖子 / 英文标题解析成 PDF，再用 MinerU Token 版 `extract` 生成 `full.md` 与 `images/`，每篇论文独立文件夹。社交媒体帖子在 HTTP 被拦时会自动尝试 Chrome CDP；无直链时会用 OpenAlex + arXiv API 检索论文。Token 仅本地配置，勿提交到仓库。

安装：`git clone https://github.com/Iayce/paperdown2md.git ~/.cursor/skills/paperdown2md`
