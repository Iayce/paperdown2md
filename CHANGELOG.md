# Changelog

## [1.1.0] — 2026-06-15

### Added

- **WeChat article URLs** (`https://mp.weixin.qq.com/s/...`) as download entry points
- Parse `og:title` and arXiv / DOI / PDF links from公众号正文
- **Browser fallback**: when HTTP/curl is blocked (e.g. 环境异常) or finds no paper links, auto-retry via Chrome CDP (web-access proxy on `localhost:3456`)

## [1.0.0] — 2026-06-02

### Added

- Initial public release on GitHub
- `SKILL.md` — Agent workflow for PDF download + MinerU extract → `full.md` + `images/`
- `scripts/paperdown2md.py` — arXiv / DOI / direct PDF / OpenAlex title resolution; stdlib only
- `scripts/run.sh` — skillsplace conda environment wrapper
- Example output: CIDD paper folder under `example/`
- Eval prompts under `evals/evals.json`
