---
name: paperdown2md
description: >-
  将一篇或多篇学术论文（标题、arXiv/DOI/URL、微信公众号/小红书帖子链接等）下载为 PDF，并用 MinerU
  extract（需 Token）转为 full.md 与 images/，按论文在指定目录下建独立文件夹。
  只要用户提到论文下载转 Markdown、paperdown2md、批量拉论文 PDF、MinerU 解析论文、
  按标题/链接整理文献目录、公众号/小红书论文链接、或要把 arXiv/DOI 论文落成 full.md，就应使用本 skill——
  即使用户没有明确说「paperdown2md」。
compatibility: >-
  需要 mineru-open-api CLI 与 MinerU Token（~/.cursor/skills/mineru/key 或
  MINERU_TOKEN）。可选 lr（LightRead CLI）辅助检索。本 skill 的 Python **必须**
  在 skillsplace conda 环境中运行（macOS:
  /Users/jaycexu/anaconda3/envs/skillsplace；Windows: D:\Anaconda\envs\skillsplace；
  jumphost-inner: ~/xsjenv/miniconda3/envs/skillsplace）。禁止用系统 python3。
version: 1.2.0
---

# paperdown2md — 论文 PDF 下载 + MinerU 转 Markdown

把用户给出的**一篇或多篇**论文标识，在**指定输出目录**下落成标准结构：

```text
<output-dir>/
└── <论文文件夹名>/
    ├── <论文名>.pdf      # 与文件夹同名或用户指定的短名
    ├── full.md           # MinerU extract 全文 Markdown
    └── images/           # 文中图片资源
```

参考示例：`paperdown2md/example/CIDD: Collaborative Intelligence for Structure-Based Drug Design Empowered by LLMs/`（文件夹可用代表性短名 `CIDD`，也可用完整标题）。

## 何时触发

- 用户给出论文**标题**、**arXiv/DOI/链接**、**微信公众号/小红书帖子链接**、或直接 **PDF URL**（可多个）
- 用户指定**目标目录**（如 `paperdown2md/example/`、`~/papers/`）
- 需要 **PDF + full.md + images** 三件套，且解析要走 **MinerU `extract`（Token）**，不要用 `flash-extract` 代替大论文

## 核心流程（每篇论文）

### 1. 确认输出目录

- 用户必须给出 `--output-dir` / 目标路径；未指定时**先问**，不要猜。
- 路径不存在则创建；已有同名文件夹时先说明是否覆盖或跳过。

### 2. 决定文件夹名与 PDF 文件名

按优先级选择**文件夹名**（同时作为默认 PDF 基名，扩展名 `.pdf`）：

| 论文类型 | 命名建议 | 示例 |
|----------|----------|------|
| 提出新**模型/方法** | 模型/方法缩写或专名 | `CIDD`、`TargetDiff` |
| **Benchmark** 论文 | benchmark 名称 | `CrossDocked2020` |
| **数据集** 论文 | 数据集名称 | `ImageNet` |
| 其他 | 论文标题（可截断至 ~120 字符） | 与 PDF 原标题一致 |

规则：

- 去掉文件系统非法字符 `\ / : * ? " < > |`
- 用户若明确说「文件夹叫 CIDD」，**以用户为准**
- 多篇论文批量处理时，**每篇单独文件夹**；不要混在一个目录里

### 3. 解析标识并下载 PDF

**优先用 bundled 脚本**（解析 arXiv、DOI、直链 PDF、公众号/小红书帖子、OpenAlex/arXiv 标题检索）。

**Python 必须在 skillsplace 环境执行**——用 `scripts/run.sh`（自动定位 skillsplace 的 Python），不要直接 `python3`：

```bash
bash paperdown2md/scripts/run.sh \
  -o "<输出目录>" \
  --name "<文件夹名>" \
  "<标识>"
```

或显式指定解释器（macOS 本机）：

```bash
/Users/jaycexu/anaconda3/envs/skillsplace/bin/python paperdown2md/scripts/paperdown2md.py \
  -o "<输出目录>" --name "<文件夹名>" "<标识>"
```

| 环境 | skillsplace 路径 |
|------|------------------|
| macOS 本机 | `/Users/jaycexu/anaconda3/envs/skillsplace` |
| Windows 笔记本 | `D:\Anaconda\envs\skillsplace` |
| jumphost-inner | `~/xsjenv/miniconda3/envs/skillsplace` |

`标识` 可以是：

- arXiv：`https://arxiv.org/abs/xxxx.xxxxx` 或 `xxxx.xxxxx`
- DOI：`10.1038/...` 或 `https://doi.org/...`
- 直接 PDF：`https://....pdf`
- **微信公众号文章**：`https://mp.weixin.qq.com/s/...`
- **小红书帖子**：`https://www.xiaohongshu.com/explore/...`（建议保留分享链接中的 `xsec_token` 等参数）
- 英文标题：脚本经 OpenAlex 搜索并取最佳开放获取 PDF

#### 社交媒体帖子（公众号 / 小红书，v1.1+）

以公众号或小红书帖子为起点时，脚本会：

1. **公众号**：先用 HTTP 拉 HTML；**小红书**：默认走浏览器 CDP（内容多为 JS 渲染）
2. **若 HTTP 失败或被反爬**（如「环境异常」、笔记无法浏览）→ **自动切浏览器 CDP**（[web-access](~/.cursor/skills/web-access/SKILL.md) 的 Chrome Proxy，`localhost:3456`）
3. 从正文提取 arXiv / DOI / PDF 直链；**若无直链** → 用帖子标题与正文关键词做 **OpenAlex + arXiv API** 文献检索（含相关性过滤）
4. 用帖子标题作文件夹名（可用 `--name` 覆盖），再按既有流程下载 PDF + MinerU

```bash
# 公众号
bash paperdown2md/scripts/run.sh -o "<输出目录>" \
  "https://mp.weixin.qq.com/s/jMW2lbgiHDka8CASFtQ81w"

# 小红书（保留完整分享 URL）
bash paperdown2md/scripts/run.sh -o "<输出目录>" \
  "https://www.xiaohongshu.com/explore/6a1c2d75000000000603739b?xsec_token=..."
```

浏览器兜底前提：Chrome 已开启远程调试（`chrome://inspect/#remote-debugging`），且可运行：

```bash
node ~/.cursor/skills/web-access/scripts/check-deps.mjs
```

检索仍无结果时，Agent 可再用 `lr search`、[web-access](~/.cursor/skills/web-access/SKILL.md) 或 WebSearch 定位论文，把 arXiv/DOI 链接传给 `run.sh`。

脚本搞不定时，再：

1. 用 `lr search arxiv "<english title>" --format json` 或 `lr search "<title>" --format json` 找 `url`，取 arXiv PDF
2. 按 [web-access](~/.cursor/skills/web-access/SKILL.md) 查出版方页面（注意版权；优先 OA / arXiv）
3. 仍无 PDF → **告知用户**需手动放入文件夹，再只对已有 PDF 跑 MinerU

下载后 PDF 命名：`--name CIDD` → `CIDD.pdf`；未指定 `--name` 时用解析到的标题。

### 4. MinerU extract → full.md + images/

**一律使用 Token 版 `extract`**（表格/公式/大文件）。操作前：

```bash
export MINERU_TOKEN="$(tr -d '\n' < "$HOME/.cursor/skills/mineru/key")"
mineru-open-api auth --verify
```

- Token 缺失：**明确告诉用户**配置 `~/.cursor/skills/mineru/key` 或 `MINERU_TOKEN`，不要改用 `flash-extract` 糊弄大 PDF。
- PDF **>10MB 或页数多**：`--model vlm`，`--timeout 3600`（学术论文默认）
- 扫描件：加 `--ocr`

脚本已包含 extract 与整理步骤；手动执行时：

```bash
mineru-open-api extract "<paper-dir>/<name>.pdf" \
  -o "<paper-dir>/_mineru_out" -f md --model vlm --timeout 3600

# 将 _mineru_out/*.md → full.md，_mineru_out/images → images/，删除 _mineru_out
```

整理后检查：`full.md` 中 `![](images/...)` 路径在本地存在。

### 5. 批量多篇

对每个标识重复步骤 2–4。可一次传多个 source（仅当**共用同一 `--name` 不适用**时分开跑）：

```bash
bash paperdown2md/scripts/run.sh -o "<输出目录>" \
  "https://arxiv.org/abs/2301.00001" \
  "10.1038/s41586-020-00000" \
  "Another Paper Title In English"
```

批量时**每篇单独 `--name`**：多次调用脚本，或先由你根据标题决定短名再执行。

## 完成标准（向用户汇报）

每篇论文汇报：

- 文件夹路径
- PDF 文件名与大小
- `full.md` 行数/大小、`images/` 图片数量
- 若某篇失败：原因（无 OA PDF、无 Token、MinerU 超时等）与建议下一步

## 依赖与排障

| 问题 | 处理 |
|------|------|
| `no API token found` | 配置 MinerU Token，见 [mineru](~/.cursor/skills/mineru/SKILL.md) |
| `mineru-open-api: command not found` | 安装 MinerU CLI（mineru skill 安装脚本） |
| OpenAlex 无 PDF | 换 arXiv 链接、`lr search`、或请用户提供 PDF |
| 公众号「环境异常」 | 脚本会自动尝试 CDP 浏览器；仍失败则请用户完成验证或直传 arXiv/DOI |
| 小红书笔记无法浏览 | 使用 App 分享的完整 URL（含 `xsec_token`）；或直传 arXiv/DOI |
| 帖子无论文直链 | 脚本会用标题/关键词检索 OpenAlex + arXiv；仍失败再用 `lr search` / web-access |
| extract 超时 | 增大 `--timeout` 或向用户说明重试 |
| 用户只要 PDF 不要 Markdown | `paperdown2md.py --skip-extract` |

## 示例

**单篇（CIDD，代表性文件夹名）：**

```bash
bash paperdown2md/scripts/run.sh \
  -o "paperdown2md/example" \
  --name "CIDD: Collaborative Intelligence for Structure-Based Drug Design Empowered by LLMs" \
  "CIDD Collaborative Intelligence Structure-Based Drug Design LLMs"
```

**从微信公众号文章起步（HTTP 失败时自动走浏览器 CDP）：**

```bash
bash paperdown2md/scripts/run.sh \
  -o "paperdown2md/example" \
  "https://mp.weixin.qq.com/s/jMW2lbgiHDka8CASFtQ81w"
```

**从小红书帖子起步（无直链时自动检索 arXiv/OpenAlex）：**

```bash
bash paperdown2md/scripts/run.sh \
  -o "paperdown2md/example" \
  "https://www.xiaohongshu.com/explore/6a1c2d75000000000603739b?xsec_token=..."
```

或使用已有 PDF 仅做 MinerU（需 PDF 已在文件夹内）：

```bash
export MINERU_TOKEN="$(tr -d '\n' < "$HOME/.cursor/skills/mineru/key")"
mineru-open-api extract "paperdown2md/example/CIDD.../CIDD....pdf" \
  -o "paperdown2md/example/CIDD.../_mineru_out" -f md --model vlm --timeout 3600
# 再整理为 full.md + images/
```

## 与其他 skill 的分工

- **mineru**：只转已有 PDF/文件 → 读 mineru skill
- **lightread-cli**：LightRead 资料库、笔记、综述 → 不是本地 paperdown2md 目录结构
- **web-access**：网页检索、非结构化下载
- **paperdown2md（本 skill）**：本地目录 + PDF + full.md + images 一条龙
- **aiforbio-paper-reading**（下游）：在 `full.md` + `images/` 就绪后，于**同一论文目录**写 `{ModelName}record.md` 生物医学精读（公式逐元素推导 + 样本数据流）。见 [aiforbio-paper-reading](https://github.com/Iayce/aiforbio-paper-reading)

## 与 aiforbio-paper-reading 联动（推荐流水线）

本 skill 负责**获取与转换**；精读记录交给 **aiforbio-paper-reading**：

```text
paperdown2md  -o <文献目录> "<标识>"
    →  <文献目录>/<论文名>/{pdf, full.md, images/}
aiforbio-paper-reading
    →  <文献目录>/<论文名>/{ModelName}record.md
```

`full.md` + `images/` 生成后，若用户要「读论文 / 写 record / 精读 / 公式推导 / 数据流示例」，**提醒并衔接 aiforbio-paper-reading**，勿在本 skill 内写长篇阅读笔记。

## 脚本说明

- `scripts/run.sh`：**唯一推荐的入口**；自动选用 skillsplace 里的 Python。
- `scripts/paperdown2md.py`：stdlib only；启动时校验是否在 skillsplace；`resolve` → 下载 → `mineru-open-api extract` → `full.md` / `images/`。

Agent 执行本 skill 时：**先 `run.sh`，不要** `python3 paperdown2md.py`。

安装到 Cursor 全局 skills：

```bash
git clone https://github.com/Iayce/paperdown2md.git ~/.cursor/skills/paperdown2md
```

或 symlink 本地 checkout：`ln -s /path/to/paperdown2md ~/.cursor/skills/paperdown2md`
