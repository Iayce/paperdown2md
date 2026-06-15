#!/usr/bin/env python3
"""
Download paper PDF(s) and convert to full.md + images/ via MinerU extract.

Stdlib only. 必须在 skillsplace conda 环境中运行；请用 scripts/run.sh 调用。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ARXIV_ID_RE = re.compile(
    r"(?:arxiv\.org/(?:abs|pdf)/|arxiv:)(\d{4}\.\d{4,5}(?:v\d+)?)",
    re.I,
)
DOI_RE = re.compile(r"\b(10\.\d{4,9}/[^\s\]]+)\b", re.I)
WEIXIN_URL_RE = re.compile(r"https?://mp\.weixin\.qq\.com/s/", re.I)
XHS_URL_RE = re.compile(
    r"https?://(?:www\.)?xiaohongshu\.com/(?:explore|discovery/item)/",
    re.I,
)
OG_TITLE_RE = re.compile(
    r'property="og:title"\s+content="([^"]+)"|content="([^"]+)"\s+property="og:title"',
    re.I,
)
PAPER_HOST_RE = re.compile(
    r"(arxiv\.org|doi\.org|biorxiv\.org|medrxiv\.org)",
    re.I,
)
DIRECT_PDF_HOST_RE = re.compile(
    r"(arxiv\.org|doi\.org|biorxiv\.org|medrxiv\.org|\.pdf(?:\?|#|$))",
    re.I,
)
EXCLUDED_PAPER_HOSTS = (
    "beian.cac.gov.cn",
    "xhscdn.com",
    "fe-video-qc.xhscdn.com",
    "dc.xhscdn.com",
)
SOCIAL_TITLE_PREFIX_RE = re.compile(
    r"^(?:bioRxiv|arXiv|medRxiv|Nature|Science|Cell)\s*[｜|:]\s*",
    re.I,
)
INVALID_FS_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# skillsplace 环境路径（与用户规则一致）
SKILLSPLACE_MARKERS = (
    "/envs/skillsplace/",
    "\\envs\\skillsplace\\",
)


def require_skillsplace_env() -> None:
    """本 skill 的 Python 只能在 skillsplace conda 环境中执行。"""
    if os.environ.get("PAPERDOWN2MD_SKIP_ENV_CHECK"):
        return
    if os.environ.get("CONDA_DEFAULT_ENV") == "skillsplace":
        return
    exe = Path(sys.executable).as_posix().lower()
    if any(m.lower() in exe for m in SKILLSPLACE_MARKERS):
        return
    print(
        "error: paperdown2md 必须在 skillsplace conda 环境中运行。\n"
        "  推荐: bash paperdown2md/scripts/run.sh ...\n"
        "  macOS:  /Users/jaycexu/anaconda3/envs/skillsplace/bin/python ...\n"
        "  Windows: D:\\Anaconda\\envs\\skillsplace\\python.exe ...\n"
        "  inner:   ~/xsjenv/miniconda3/envs/skillsplace/bin/python ...\n"
        f"  当前解释器: {sys.executable}",
        file=sys.stderr,
    )
    sys.exit(1)


def sanitize_name(name: str, max_len: int = 120) -> str:
    name = INVALID_FS_CHARS.sub("_", name.strip())
    name = re.sub(r"\s+", " ", name)
    return name[:max_len].rstrip(" ._") or "paper"


def http_get_json(url: str, timeout: int = 60) -> dict:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "paperdown2md/1.0 (academic; +https://github.com/Iayce/paperdown2md)"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def http_get_text(url: str, timeout: int = 120, user_agent: str | None = None) -> str:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": user_agent or "paperdown2md/1.0"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def download_file(url: str, dest: Path, timeout: int = 300) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "paperdown2md/1.0"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp, dest.open("wb") as f:
        shutil.copyfileobj(resp, f)


def parse_arxiv_id(source: str) -> str | None:
    m = ARXIV_ID_RE.search(source)
    return m.group(1) if m else None


def arxiv_pdf_url(arxiv_id: str) -> str:
    base = arxiv_id.split("v")[0]
    return f"https://arxiv.org/pdf/{base}.pdf"


def openalex_work(source: str) -> dict | None:
    if source.startswith("http"):
        if "doi.org" in source or "openalex.org" in source:
            url = source if "openalex.org" in source else f"https://api.openalex.org/works/{urllib.parse.quote(source, safe='')}"
        else:
            url = None
    else:
        doi_m = DOI_RE.search(source)
        if doi_m:
            url = f"https://api.openalex.org/works/https://doi.org/{doi_m.group(1)}"
        else:
            url = None

    if url:
        try:
            return http_get_json(url)
        except (urllib.error.URLError, json.JSONDecodeError, KeyError):
            return None

    q = urllib.parse.quote(source)
    try:
        data = http_get_json(
            f"https://api.openalex.org/works?search={q}&per_page=5"
        )
        results = data.get("results") or []
        return results[0] if results else None
    except (urllib.error.URLError, json.JSONDecodeError):
        return None


def pick_pdf_url(work: dict) -> tuple[str | None, str | None]:
    """Return (pdf_url, title)."""
    title = (work.get("title") or work.get("display_name") or "").strip()
    loc = work.get("best_oa_location") or {}
    pdf = loc.get("pdf_url")
    if pdf:
        return pdf, title
    oa = (work.get("open_access") or {}).get("oa_url")
    if oa and oa.lower().endswith(".pdf"):
        return oa, title
    for loc in work.get("locations") or []:
        pdf = loc.get("pdf_url")
        if pdf:
            return pdf, title
    return None, title


def openalex_search_works(query: str, per_page: int = 5) -> list[dict]:
    q = urllib.parse.quote(query)
    try:
        data = http_get_json(
            f"https://api.openalex.org/works?search={q}&per_page={per_page}"
        )
        return data.get("results") or []
    except (urllib.error.URLError, json.JSONDecodeError):
        return []


def is_weixin_url(source: str) -> bool:
    return bool(WEIXIN_URL_RE.search(source)) or (
        "mp.weixin.qq.com" in source and "/s/" in source
    )


def is_xhs_url(source: str) -> bool:
    return bool(XHS_URL_RE.search(source)) or (
        "xiaohongshu.com" in source
        and ("/explore/" in source or "/discovery/item/" in source)
    )


def is_social_url(source: str) -> bool:
    return is_weixin_url(source) or is_xhs_url(source)


def social_platform(source: str) -> str:
    if is_xhs_url(source):
        return "xhs"
    if is_weixin_url(source):
        return "weixin"
    return "unknown"


def normalize_social_html(html: str) -> str:
    return (
        html.replace("\\x3c", "<")
        .replace("\\x3e", ">")
        .replace("\\x26", "&")
        .replace("\\x22", '"')
    )


def is_excluded_paper_url(url: str) -> bool:
    host = urllib.parse.urlparse(url).netloc.lower()
    return any(excl in host for excl in EXCLUDED_PAPER_HOSTS)


def extract_og_title(html: str) -> str | None:
    m = OG_TITLE_RE.search(html)
    if not m:
        return None
    return (m.group(1) or m.group(2) or "").strip() or None


def clean_social_title(title: str) -> str:
    title = re.sub(r"\s*-\s*小红书\s*$", "", title.strip())
    title = SOCIAL_TITLE_PREFIX_RE.sub("", title)
    return title.strip()


def is_footer_line(text: str) -> bool:
    markers = (
        "有限公司",
        "沪ICP",
        "ICP备",
        "举报电话",
        "营业执照",
        "地址：",
        "电话：",
        "关于我们",
        "行吟信息",
        "个性化推荐算法",
        "医疗器械",
    )
    return any(m in text for m in markers)


def extract_title_from_xhs_body(body: str) -> str | None:
    candidates: list[tuple[int, int, str]] = []
    for line in body.splitlines():
        line = line.strip()
        if len(line) < 8 or is_footer_line(line):
            continue
        if line in {"关注", "首页", "消息", "我", "更多", "关于我们", "推荐", "直播", "发布"}:
            continue
        score = 0
        if re.search(r"bioRxiv|arXiv|medRxiv|论文|微调|预测|design|affinity", line, re.I):
            score += 10
        if "｜" in line or "|" in line:
            score += 5
        candidates.append((score, len(line), line))
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return clean_social_title(candidates[0][2])


def extract_social_title(
    html: str,
    body: str | None = None,
    page_title: str | None = None,
) -> str | None:
    for candidate in (page_title, extract_og_title(html)):
        if not candidate or candidate in ("小红书", "小红书 - 你的生活兴趣社区"):
            continue
        cleaned = clean_social_title(candidate)
        if cleaned and "页面不见了" not in cleaned and not is_footer_line(cleaned):
            if len(cleaned) >= 8 or re.search(r"bioRxiv|arXiv|论文", cleaned, re.I):
                return cleaned
    if body:
        xhs_title = extract_title_from_xhs_body(body)
        if xhs_title:
            return xhs_title
    return None


def extract_paper_urls_from_html(html: str) -> list[str]:
    html = normalize_social_html(html)
    raw_urls = re.findall(r"https?://[^\s\"'<>\\]+", html)
    seen: set[str] = set()
    paper_urls: list[str] = []
    for raw in raw_urls:
        url = raw.rstrip(".,;)]}>\"'\\")
        if is_excluded_paper_url(url):
            continue
        if not DIRECT_PDF_HOST_RE.search(url):
            continue
        if url in seen:
            continue
        seen.add(url)
        paper_urls.append(url)
    return paper_urls


def extract_paper_refs_from_text(text: str) -> list[str]:
    refs: list[str] = []
    seen: set[str] = set()

    def add(ref: str) -> None:
        if ref not in seen:
            seen.add(ref)
            refs.append(ref)

    for m in ARXIV_ID_RE.finditer(text):
        add(arxiv_pdf_url(m.group(1)))
    for m in DOI_RE.finditer(text):
        add(f"https://doi.org/{m.group(1)}")
    for m in re.finditer(
        r"https?://(?:www\.)?(?:arxiv\.org/\S+|doi\.org/\S+|biorxiv\.org/\S+|medrxiv\.org/\S+)",
        text,
        re.I,
    ):
        url = m.group(0).rstrip(".,;)]}>\"'")
        if not is_excluded_paper_url(url):
            add(url)
    return refs


def collect_paper_refs(html: str, body: str | None = None) -> list[str]:
    refs = extract_paper_urls_from_html(html)
    refs.extend(extract_paper_refs_from_text(body or ""))
    refs.extend(extract_paper_refs_from_text(html))
    seen: set[str] = set()
    unique: list[str] = []
    for ref in refs:
        if ref not in seen:
            seen.add(ref)
            unique.append(ref)
    return unique


def build_literature_search_queries(title: str | None, body: str | None) -> list[str]:
    queries: list[str] = []
    seen: set[str] = set()

    def add(q: str) -> None:
        q = re.sub(r"\s+", " ", q.strip(" -|｜:"))
        if len(q) < 8 or q in seen or is_footer_line(q):
            return
        seen.add(q)
        queries.append(q)

    text = body or ""
    if text:
        for m in re.finditer(r"\b([A-Z][A-Za-z0-9]*-\d+[A-Za-z0-9]*)\b", text):
            name = m.group(1)
            if re.search(r"affinity|fine[- ]?tun", text, re.I):
                add(f"{name} affinity fine-tuning")
            add(name)

    if title and not is_footer_line(title):
        add(clean_social_title(title))

    return queries[:6]


def arxiv_search_works(query: str, max_results: int = 5) -> list[tuple[str, str]]:
    q = urllib.parse.quote_plus(query)
    url = (
        f"http://export.arxiv.org/api/query?search_query=all:{q}"
        f"&start=0&max_results={max_results}"
    )
    try:
        xml = http_get_text(url, timeout=60)
    except urllib.error.URLError:
        return []

    works: list[tuple[str, str]] = []
    for block in re.split(r"(?=<entry>)", xml):
        if "<entry>" not in block:
            continue
        title_m = re.search(r"<title>\s*([^<]+?)\s*</title>", block)
        id_m = re.search(r"<id>https?://arxiv\.org/abs/([^<]+)</id>", block)
        if not title_m or not id_m:
            continue
        arxiv_id = id_m.group(1).strip()
        title = re.sub(r"\s+", " ", title_m.group(1).strip())
        works.append((arxiv_pdf_url(arxiv_id), title))
    return works


def is_relevant_match(query: str, title: str) -> bool:
    title_l = title.lower()
    required = [
        t
        for t in re.findall(r"[A-Za-z0-9][A-Za-z0-9-]*", query)
        if re.search(r"[-\d]", t) and len(t) >= 3
    ]
    if required:
        return any(t.lower() in title_l for t in required)
    words = [w for w in re.findall(r"[A-Za-z]{4,}", query)]
    if not words:
        return True
    return sum(1 for w in words if w.lower() in title_l) >= max(1, len(words) // 2)


def resolve_via_literature_search(
    queries: list[str],
    display_title: str | None,
) -> tuple[str, str]:
    if not queries:
        raise ValueError("No search queries built from social post content")

    for q in queries:
        prefer_arxiv = bool(re.search(r"[A-Za-z]+-\d+", q))
        engines: tuple[str, ...] = ("arxiv", "openalex") if prefer_arxiv else ("openalex", "arxiv")

        for engine in engines:
            if engine == "arxiv":
                print(f"[paperdown2md] Literature search (arXiv): {q!r}")
                for pdf, title in arxiv_search_works(q):
                    if is_relevant_match(q, title):
                        print(f"[paperdown2md] Matched paper: {title}")
                        return pdf, display_title or title or q
            else:
                print(f"[paperdown2md] Literature search (OpenAlex): {q!r}")
                for work in openalex_search_works(q):
                    pdf, title = pick_pdf_url(work)
                    if pdf and is_relevant_match(q, title or ""):
                        print(f"[paperdown2md] Matched paper: {title}")
                        return pdf, display_title or title or q

    joined = "; ".join(queries[:3])
    raise ValueError(
        f"Literature search found no open PDF for queries: {joined}. "
        "Try passing arXiv/DOI directly, or use lr search / web-access."
    )


def weixin_page_blocked(html: str) -> bool:
    return "环境异常" in html and len(html) < 100_000


def xhs_page_blocked(html: str, page_title: str | None = None) -> bool:
    markers = ("页面不见了", "暂时无法浏览", "当前笔记暂时无法浏览")
    if page_title and any(m in page_title for m in markers):
        return True
    return any(m in html for m in markers) and len(html) < 200_000


def social_page_usable(
    html: str,
    *,
    platform: str,
    body: str | None = None,
    page_title: str | None = None,
) -> bool:
    if platform == "weixin" and weixin_page_blocked(html):
        return False
    if platform == "xhs" and xhs_page_blocked(html, page_title):
        return False
    if collect_paper_refs(html, body):
        return True
    if platform == "xhs":
        title = extract_social_title(html, body, page_title)
        return bool(title and body and len(body) > 200)
    return False


def cdp_proxy_base() -> str:
    return os.environ.get("CDP_PROXY_URL", "http://127.0.0.1:3456").rstrip("/")


def cdp_proxy_ready(base: str, timeout: int = 3) -> bool:
    try:
        with urllib.request.urlopen(f"{base}/health", timeout=timeout) as resp:
            return resp.status == 200
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def ensure_cdp_proxy() -> str | None:
    """Ensure web-access CDP proxy is running; return base URL or None."""
    base = cdp_proxy_base()
    if cdp_proxy_ready(base):
        return base

    check_deps = Path.home() / ".cursor/skills/web-access/scripts/check-deps.mjs"
    if not check_deps.is_file():
        return None

    print("[paperdown2md] Starting CDP proxy via web-access check-deps…")
    try:
        subprocess.run(
            ["node", str(check_deps)],
            check=True,
            timeout=45,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        return None

    return base if cdp_proxy_ready(base, timeout=8) else None


def cdp_request_json(
    url: str,
    *,
    data: bytes | None = None,
    method: str = "GET",
    timeout: int = 90,
) -> dict:
    req = urllib.request.Request(url, data=data, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_page_browser(url: str, *, need_body: bool = False) -> tuple[str, str | None, str | None]:
    """Fetch page via Chrome CDP. Returns (html, page_title, body_text)."""
    base = ensure_cdp_proxy()
    if not base:
        raise ValueError(
            "Browser fallback unavailable: CDP proxy not running. "
            "Enable Chrome remote debugging (chrome://inspect/#remote-debugging), "
            "run `node ~/.cursor/skills/web-access/scripts/check-deps.mjs`, "
            "or pass the arXiv/DOI link directly."
        )

    encoded = urllib.parse.quote(url, safe="")
    tab = cdp_request_json(f"{base}/new?url={encoded}", timeout=120)
    target_id = tab.get("targetId")
    if not target_id:
        raise ValueError(f"CDP /new returned no targetId: {tab}")

    try:
        try:
            urllib.request.urlopen(
                f"{base}/scroll?target={target_id}&direction=bottom",
                timeout=20,
            )
        except (urllib.error.URLError, TimeoutError, OSError):
            pass

        title_result = cdp_request_json(
            f"{base}/eval?target={target_id}",
            data=b"document.title",
            method="POST",
            timeout=60,
        )
        page_title = title_result.get("value")
        page_title = page_title if isinstance(page_title, str) else None

        body_text: str | None = None
        if need_body:
            body_result = cdp_request_json(
                f"{base}/eval?target={target_id}",
                data=b"document.body.innerText",
                method="POST",
                timeout=60,
            )
            body_val = body_result.get("value")
            body_text = body_val if isinstance(body_val, str) else None

        result = cdp_request_json(
            f"{base}/eval?target={target_id}",
            data=b"document.documentElement.outerHTML",
            method="POST",
            timeout=120,
        )
        html = result.get("value") or ""
        if not isinstance(html, str) or not html.strip():
            raise ValueError("Browser returned empty HTML")
        return html, page_title, body_text
    finally:
        try:
            urllib.request.urlopen(f"{base}/close?target={target_id}", timeout=5)
        except (urllib.error.URLError, TimeoutError, OSError):
            pass


def fetch_social_page(url: str, platform: str) -> tuple[str, str | None, str | None]:
    """HTTP first (WeChat); XHS prefers browser. Returns (html, page_title, body_text)."""
    html: str | None = None
    page_title: str | None = None
    body_text: str | None = None
    curl_error: Exception | None = None

    if platform != "xhs":
        try:
            html = http_get_text(url, timeout=120, user_agent=BROWSER_UA)
        except urllib.error.URLError as e:
            curl_error = e

        if html and social_page_usable(html, platform=platform):
            print(f"[paperdown2md] {platform} post fetched via HTTP")
            return html, extract_og_title(html), None

    if html and platform == "weixin" and weixin_page_blocked(html):
        reason = "verification required (环境异常)"
    elif html and platform == "weixin":
        reason = "no paper links in HTTP response"
    elif platform == "xhs":
        reason = "XHS requires browser for note content"
    elif html:
        reason = "content insufficient in HTTP response"
    else:
        reason = f"HTTP failed ({curl_error})"

    print(f"[paperdown2md] HTTP insufficient ({reason}); trying browser (CDP)…")
    html, page_title, body_text = fetch_page_browser(
        url,
        need_body=(platform == "xhs"),
    )

    if platform == "weixin" and weixin_page_blocked(html):
        raise ValueError(
            "WeChat page still blocked after browser fetch. "
            "Complete verification in Chrome, or pass the arXiv/DOI link directly."
        )
    if platform == "xhs" and xhs_page_blocked(html, page_title):
        raise ValueError(
            "XHS note unavailable (missing xsec_token or login required). "
            "Use the full share link from the app, or pass arXiv/DOI directly."
        )
    if not social_page_usable(
        html,
        platform=platform,
        body=body_text,
        page_title=page_title,
    ):
        title = extract_social_title(html, body_text, page_title)
        hint = f" Title: {title!r}." if title else ""
        raise ValueError(
            f"Could not extract usable content from {platform} post via browser.{hint}"
        )

    print(f"[paperdown2md] {platform} post fetched via browser (CDP)")
    return html, page_title, body_text


def resolve_social_article(url: str) -> tuple[str, str]:
    """Resolve WeChat / XHS post → (pdf_url, folder_title)."""
    platform = social_platform(url)
    label = "WeChat" if platform == "weixin" else "XHS"
    print(f"[paperdown2md] Resolving {label} post: {url}")

    html, page_title, body_text = fetch_social_page(url, platform)
    title = extract_social_title(html, body_text, page_title)
    paper_refs = collect_paper_refs(html, body_text)

    if paper_refs:
        print(f"[paperdown2md] Found {len(paper_refs)} paper ref(s); using: {paper_refs[0]}")
        pdf_url, resolved_title = resolve_paper_source(paper_refs[0])
        return pdf_url, title or resolved_title

    queries = build_literature_search_queries(title, body_text)
    if not queries and title:
        queries = [title]
    print(
        f"[paperdown2md] No direct paper link in {label} post; "
        "searching literature by title/keywords…"
    )
    return resolve_via_literature_search(queries, title)


def resolve_paper_source(source: str) -> tuple[str, str]:
    """Resolve arXiv / DOI / PDF / OpenAlex title → (pdf_url, suggested_title)."""
    source = source.strip()
    if not source:
        raise ValueError("empty source")

    if source.lower().endswith(".pdf") and (
        source.startswith("http://") or source.startswith("https://")
    ):
        return source, Path(urllib.parse.urlparse(source).path).stem

    arxiv_id = parse_arxiv_id(source)
    if arxiv_id:
        return arxiv_pdf_url(arxiv_id), arxiv_id

    if source.startswith("http") and "arxiv.org" in source:
        arxiv_id = parse_arxiv_id(source)
        if arxiv_id:
            return arxiv_pdf_url(arxiv_id), arxiv_id

    work = openalex_work(source)
    if work:
        pdf, title = pick_pdf_url(work)
        if pdf:
            return pdf, title or source
        raise ValueError(
            f"OpenAlex found '{title or source}' but no open PDF URL; "
            "try arXiv link, direct PDF URL, or manual download."
        )

    raise ValueError(
        f"Cannot resolve PDF for: {source!r}. "
        "Use arXiv URL/ID, DOI, direct .pdf URL, or English title for OpenAlex search."
    )


def resolve_source(source: str) -> tuple[str, str]:
    """Return (pdf_url, suggested_title). Supports social post URLs as entry points."""
    source = source.strip()
    if is_social_url(source):
        return resolve_social_article(source)
    return resolve_paper_source(source)


def load_mineru_token() -> str | None:
    if os.environ.get("MINERU_TOKEN"):
        return os.environ["MINERU_TOKEN"].strip()
    key_paths = [
        Path.home() / ".cursor/skills/mineru/key",
        Path.home() / ".cursor/skills/mineru/KEY",
    ]
    for p in key_paths:
        if p.is_file():
            return p.read_text().strip()
    return None


def run_mineru_extract(pdf_path: Path, paper_dir: Path, model: str, timeout: int) -> None:
    token = load_mineru_token()
    if not token:
        raise RuntimeError(
            "MinerU token not found. Set MINERU_TOKEN or create ~/.cursor/skills/mineru/key"
        )

    tmp = paper_dir / "_mineru_out"
    if tmp.exists():
        shutil.rmtree(tmp)

    env = os.environ.copy()
    env["MINERU_TOKEN"] = token

    cmd = [
        "mineru-open-api",
        "extract",
        str(pdf_path),
        "-o",
        str(tmp),
        "-f",
        "md",
        "--model",
        model,
        "--timeout",
        str(timeout),
    ]
    subprocess.run(cmd, check=True, env=env)

    md_files = list(tmp.glob("*.md"))
    if not md_files:
        raise RuntimeError(f"MinerU produced no .md in {tmp}")

    src_md = md_files[0]
    dest_md = paper_dir / "full.md"
    if dest_md.exists():
        dest_md.unlink()
    shutil.move(str(src_md), str(dest_md))

    src_images = tmp / "images"
    dest_images = paper_dir / "images"
    if dest_images.exists():
        shutil.rmtree(dest_images)
    if src_images.is_dir():
        shutil.move(str(src_images), str(dest_images))

    shutil.rmtree(tmp, ignore_errors=True)


def process_one(
    source: str,
    output_dir: Path,
    folder_name: str | None,
    pdf_name: str | None,
    skip_extract: bool,
    model: str,
    timeout: int,
) -> Path:
    pdf_url, suggested_title = resolve_source(source)
    name = sanitize_name(folder_name or suggested_title)
    paper_dir = output_dir / name
    paper_dir.mkdir(parents=True, exist_ok=True)

    pdf_basename = sanitize_name(pdf_name or name) + ".pdf"
    pdf_path = paper_dir / pdf_basename

    print(f"[paperdown2md] Downloading → {pdf_path}")
    download_file(pdf_url, pdf_path)

    size_mb = pdf_path.stat().st_size / (1024 * 1024)
    print(f"[paperdown2md] PDF saved ({size_mb:.1f} MB)")

    if skip_extract:
        return paper_dir

    print(f"[paperdown2md] MinerU extract (model={model})…")
    run_mineru_extract(pdf_path, paper_dir, model=model, timeout=timeout)
    print(f"[paperdown2md] Done: {paper_dir}/full.md + images/")
    return paper_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="Download papers and convert to Markdown via MinerU.")
    parser.add_argument(
        "sources",
        nargs="+",
        help="arXiv/DOI/PDF URL, WeChat/XHS post URL, or paper title (OpenAlex)",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        required=True,
        type=Path,
        help="Parent directory for per-paper folders",
    )
    parser.add_argument(
        "--name",
        help="Folder and default PDF base name (e.g. CIDD). Overrides auto-detected title.",
    )
    parser.add_argument(
        "--pdf-name",
        help="PDF filename base only (default: same as --name or detected title)",
    )
    parser.add_argument(
        "--skip-extract",
        action="store_true",
        help="Only download PDF; do not run MinerU",
    )
    parser.add_argument(
        "--model",
        default="vlm",
        choices=["vlm", "pipeline", "html"],
        help="MinerU model (default: vlm for academic papers)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=3600,
        help="MinerU extract timeout seconds (default: 3600)",
    )
    args = parser.parse_args()
    require_skillsplace_env()

    if not shutil.which("mineru-open-api") and not args.skip_extract:
        print("error: mineru-open-api not in PATH", file=sys.stderr)
        return 1

    args.output_dir.mkdir(parents=True, exist_ok=True)
    results: list[Path] = []
    errors: list[str] = []

    for i, src in enumerate(args.sources):
        name = args.name if len(args.sources) == 1 else None
        pdf_name = args.pdf_name if len(args.sources) == 1 else None
        try:
            results.append(
                process_one(
                    src,
                    args.output_dir,
                    name,
                    pdf_name,
                    args.skip_extract,
                    args.model,
                    args.timeout,
                )
            )
        except Exception as e:
            errors.append(f"{src}: {e}")

    for p in results:
        print(f"OK {p}")
    for err in errors:
        print(f"FAIL {err}", file=sys.stderr)

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
