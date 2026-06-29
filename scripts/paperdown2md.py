#!/usr/bin/env python3
"""
Download paper PDF(s) and convert to full.md + images/ via MinerU extract.

Stdlib only. 必须在 skillsplace conda 环境中运行；请用 scripts/run.sh 调用。
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
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
PMC_ID_RE = re.compile(r"(?:PMC)?(\d{5,})", re.I)
EUROPEPMC_RENDER_RE = re.compile(
    r"europepmc\.org/articles/(PMC\d+)(?:\?pdf=render)?",
    re.I,
)
PMC_ARTICLE_RE = re.compile(
    r"(?:ncbi\.nlm\.nih\.gov|pmc\.ncbi\.nlm\.nih\.gov)/pmc/articles/(?:PMC)?(\d+)",
    re.I,
)
PUBLISHER_PDF_HREF_RE = re.compile(
    r"""href=["']([^"']*(?:/pdf(?:direct)?/|/pdf/|\.pdf(?:\?|#|$)|downloadpdf|/epdf/|citation-pdf)[^"']*)["']""",
    re.I,
)
CITATION_PDF_META_RE = re.compile(
    r'name="citation_pdf_url"\s+content="([^"]+)"|content="([^"]+)"\s+name="citation_pdf_url"',
    re.I,
)
PUBLISHER_HOSTS = (
    "onlinelibrary.wiley.com",
    "link.springer.com",
    "nature.com",
    "sciencedirect.com",
    "cell.com",
    "acs.org",
    "tandfonline.com",
    "oup.com",
    "cambridge.org",
    "ieee.org",
    "mdpi.com",
    "frontiersin.org",
)


@dataclass
class ResolvedPaper:
    """Resolved download target for one paper."""

    title: str
    download_url: str | None = None
    landing_url: str | None = None
    pmc_fallback_url: str | None = None
    work: dict | None = None

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


def is_pdf_file(path: Path, min_size: int = 1024) -> bool:
    if not path.is_file() or path.stat().st_size < min_size:
        return False
    with path.open("rb") as f:
        return f.read(5) == b"%PDF-"


def extract_doi_from_work(work: dict) -> str | None:
    doi = work.get("doi")
    if isinstance(doi, str) and doi.startswith("https://doi.org/"):
        return doi.removeprefix("https://doi.org/")
    ids = work.get("ids") or {}
    doi = ids.get("doi")
    if isinstance(doi, str):
        return doi.removeprefix("https://doi.org/")
    return None


def normalize_pmcid(raw: str) -> str | None:
    m = PMC_ID_RE.search(raw)
    if not m:
        return None
    return f"PMC{m.group(1)}"


def extract_pmcid_from_work(work: dict) -> str | None:
    for loc in work.get("locations") or []:
        landing = loc.get("landing_page_url") or ""
        source_name = ((loc.get("source") or {}).get("display_name") or "").lower()
        if "pubmed central" in source_name or "pmc" in landing.lower():
            m = PMC_ARTICLE_RE.search(landing)
            if m:
                return f"PMC{m.group(1)}"
            pmcid = normalize_pmcid(landing)
            if pmcid:
                return pmcid
    return None


def lookup_pmcid_by_doi(doi: str) -> str | None:
    q = urllib.parse.quote(doi, safe="")
    try:
        xml = http_get_text(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
            f"?db=pubmed&term={q}[DOI]&retmode=json",
            timeout=30,
        )
        data = json.loads(xml)
        ids = (data.get("esearchresult") or {}).get("idlist") or []
        if not ids:
            return None
        pmid = ids[0]
        link_url = (
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi"
            f"?dbfrom=pubmed&id={pmid}&linkname=pubmed_pmc&retmode=json"
        )
        link_data = http_get_json(link_url, timeout=30)
        for linkset in link_data.get("linksets") or []:
            for ldb in linkset.get("linksetdbs") or []:
                if ldb.get("linkname") == "pubmed_pmc":
                    links = ldb.get("links") or []
                    if links:
                        return f"PMC{links[0]}"
    except (urllib.error.URLError, json.JSONDecodeError, KeyError, ValueError):
        return None
    return None


def lookup_pmcid_from_europepmc(doi: str) -> str | None:
    q = urllib.parse.quote(doi, safe="")
    try:
        data = http_get_json(
            "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
            f"?query=DOI:{q}&format=json&pageSize=1",
            timeout=30,
        )
        results = (data.get("resultList") or {}).get("result") or []
        if not results:
            return None
        pmcid = results[0].get("pmcid")
        if isinstance(pmcid, str) and pmcid:
            return pmcid if pmcid.upper().startswith("PMC") else f"PMC{pmcid}"
    except (urllib.error.URLError, json.JSONDecodeError):
        return None
    return None


def europepmc_render_url(pmcid: str) -> str:
    pmcid = normalize_pmcid(pmcid) or pmcid
    return f"https://europepmc.org/articles/{pmcid}?pdf=render"


def resolve_pmc_fallback(work: dict) -> str | None:
    pmcid = extract_pmcid_from_work(work)
    doi = extract_doi_from_work(work)
    if not pmcid and doi:
        pmcid = lookup_pmcid_from_europepmc(doi) or lookup_pmcid_by_doi(doi)
    if not pmcid:
        return None
    return europepmc_render_url(pmcid)


def pick_publisher_landing(work: dict) -> str | None:
    oa = (work.get("open_access") or {}).get("oa_url")
    if isinstance(oa, str) and oa.startswith("http"):
        return oa
    loc = work.get("primary_location") or {}
    landing = loc.get("landing_page_url")
    if isinstance(landing, str) and landing.startswith("http"):
        return landing
    doi = extract_doi_from_work(work)
    if doi:
        return f"https://doi.org/{doi}"
    return None


def is_publisher_landing_url(url: str) -> bool:
    host = urllib.parse.urlparse(url).netloc.lower()
    return any(p in host for p in PUBLISHER_HOSTS) or "doi.org" in host


def is_known_pdf_endpoint(url: str) -> bool:
    lower = url.lower()
    if lower.endswith(".pdf"):
        return True
    if "europepmc.org" in lower and "pdf=render" in lower:
        return True
    if "arxiv.org/pdf/" in lower:
        return True
    return False


def absolutize_url(base: str, href: str) -> str:
    return urllib.parse.urljoin(base, href)


def score_publisher_pdf_url(url: str) -> int:
    lower = url.lower()
    score = 0
    if lower.endswith(".pdf"):
        score += 10
    if "/pdfdirect/" in lower or "/pdf/" in lower:
        score += 8
    if "download" in lower:
        score += 4
    if "supp" in lower or "supporting" in lower:
        score -= 6
    return score


def extract_pdf_urls_from_html(html: str, base_url: str) -> list[str]:
    seen: set[str] = set()
    urls: list[tuple[int, str]] = []

    def add(raw: str) -> None:
        url = absolutize_url(base_url, raw.strip())
        if url in seen:
            return
        seen.add(url)
        if not re.search(r"pdf|download", url, re.I):
            return
        urls.append((score_publisher_pdf_url(url), url))

    for m in CITATION_PDF_META_RE.finditer(html):
        add(m.group(1) or m.group(2) or "")
    for m in PUBLISHER_PDF_HREF_RE.finditer(html):
        add(m.group(1))
    for m in re.finditer(r'href="([^"]+\.pdf[^"]*)"', html, re.I):
        add(m.group(1))

    urls.sort(key=lambda item: item[0], reverse=True)
    return [u for _, u in urls]


def try_http_pdf(
    url: str,
    dest: Path,
    *,
    timeout: int = 300,
    referer: str | None = None,
) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    headers = {"User-Agent": BROWSER_UA}
    if referer:
        headers["Referer"] = referer
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp, dest.open("wb") as f:
            shutil.copyfileobj(resp, f)
    except urllib.error.URLError:
        return False
    if is_pdf_file(dest):
        return True
    if dest.exists():
        dest.unlink()
    return False


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
) -> ResolvedPaper:
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
                        return ResolvedPaper(
                            title=display_title or title or q,
                            download_url=pdf,
                        )
            else:
                print(f"[paperdown2md] Literature search (OpenAlex): {q!r}")
                for work in openalex_search_works(q):
                    try:
                        resolved = resolve_from_openalex_work(work, display_title or q)
                    except ValueError:
                        continue
                    if is_relevant_match(q, resolved.title):
                        print(f"[paperdown2md] Matched paper: {resolved.title}")
                        return resolved

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

        def read_page() -> tuple[str, str | None, str | None]:
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

        html, page_title, body_text = read_page()
        if len(html) < 500:
            time.sleep(3)
            html, page_title, body_text = read_page()
        return html, page_title, body_text
    finally:
        try:
            urllib.request.urlopen(f"{base}/close?target={target_id}", timeout=5)
        except (urllib.error.URLError, TimeoutError, OSError):
            pass


def cdp_eval_on_page(
    url: str,
    expression: str,
    *,
    timeout: int = 120,
    keep_open: bool = False,
) -> tuple[dict, str | None]:
    """Open URL in CDP tab, eval JS, optionally keep tab open. Returns (result, target_id)."""
    base = ensure_cdp_proxy()
    if not base:
        raise ValueError("CDP proxy not available")

    encoded = urllib.parse.quote(url, safe="")
    tab = cdp_request_json(f"{base}/new?url={encoded}", timeout=timeout)
    target_id = tab.get("targetId")
    if not target_id:
        raise ValueError(f"CDP /new returned no targetId: {tab}")

    try:
        result = cdp_request_json(
            f"{base}/eval?target={target_id}",
            data=expression.encode("utf-8"),
            method="POST",
            timeout=timeout,
        )
        value = result.get("value")
        if isinstance(value, dict):
            payload = value
        elif result.get("error"):
            raise ValueError(str(result.get("error")))
        else:
            payload = {"value": value}
        if keep_open:
            return payload, target_id
        return payload, None
    finally:
        if not keep_open:
            try:
                urllib.request.urlopen(f"{base}/close?target={target_id}", timeout=5)
            except (urllib.error.URLError, TimeoutError, OSError):
                pass


def cdp_eval_on_target(target_id: str, expression: str, *, timeout: int = 120) -> dict:
    base = ensure_cdp_proxy()
    if not base:
        raise ValueError("CDP proxy not available")
    result = cdp_request_json(
        f"{base}/eval?target={target_id}",
        data=expression.encode("utf-8"),
        method="POST",
        timeout=timeout,
    )
    value = result.get("value")
    if isinstance(value, dict):
        return value
    if result.get("error"):
        raise ValueError(str(result.get("error")))
    return {"value": value}


def cdp_close_target(target_id: str) -> None:
    base = cdp_proxy_base()
    try:
        urllib.request.urlopen(f"{base}/close?target={target_id}", timeout=5)
    except (urllib.error.URLError, TimeoutError, OSError):
        pass


def find_pdf_url_via_browser(landing_url: str) -> str | None:
    print(f"[paperdown2md] Browser: resolving PDF link from {landing_url}")
    html, _, _ = fetch_page_browser(landing_url)
    candidates = extract_pdf_urls_from_html(html, landing_url)
    if candidates:
        print(f"[paperdown2md] Browser found PDF candidate: {candidates[0]}")
        return candidates[0]
    return None


def browser_fetch_pdf(url: str, dest: Path, *, referer: str | None = None) -> None:
    """Download PDF via in-page fetch (uses Chrome login cookies / institutional access)."""
    context_url = referer or url
    url_json = json.dumps(url)
    init_js = f"""
(async () => {{
  const url = {url_json};
  const r = await fetch(url, {{credentials: 'include', redirect: 'follow'}});
  const ct = (r.headers.get('content-type') || '').toLowerCase();
  if (!r.ok) return {{error: 'HTTP ' + r.status, status: r.status}};
  const buf = await r.arrayBuffer();
  const bytes = new Uint8Array(buf);
  const head = Array.from(bytes.slice(0, 5)).map(b => String.fromCharCode(b)).join('');
  if (head !== '%PDF-') {{
    return {{error: 'not a PDF', contentType: ct, head: head, size: bytes.length}};
  }}
  window.__paperdown2mdPdf = bytes;
  window.__paperdown2mdPdfOffset = 0;
  return {{ok: true, size: bytes.length, contentType: ct}};
}})()
"""
    chunk_js = """
(() => {
  const data = window.__paperdown2mdPdf;
  if (!data) return {error: 'no pdf buffer'};
  const chunkSize = 524288;
  const start = window.__paperdown2mdPdfOffset;
  const end = Math.min(start + chunkSize, data.length);
  const chunk = data.slice(start, end);
  let s = '';
  for (let i = 0; i < chunk.length; i++) s += String.fromCharCode(chunk[i]);
  window.__paperdown2mdPdfOffset = end;
  return {done: end >= data.length, offset: end, total: data.length, b64: btoa(s)};
})()
"""

    print(f"[paperdown2md] Browser fetch (session cookies): {url}")
    init_result, target_id = cdp_eval_on_page(context_url, init_js, timeout=180, keep_open=True)
    if not target_id:
        raise RuntimeError("Browser fetch failed to open CDP tab")

    try:
        if init_result.get("error"):
            raise RuntimeError(f"Browser fetch failed: {init_result['error']}")

        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open("wb") as out:
            while True:
                chunk = cdp_eval_on_target(target_id, chunk_js, timeout=180)
                if chunk.get("error"):
                    raise RuntimeError(chunk["error"])
                out.write(base64.b64decode(chunk["b64"]))
                if chunk.get("done"):
                    break
    finally:
        cdp_close_target(target_id)


def download_pdf_resolved(resolved: ResolvedPaper, dest: Path, *, no_browser: bool = False) -> None:
    """Download PDF using HTTP, Europe PMC mirror, then browser CDP fallbacks."""
    attempts: list[str] = []

    if resolved.download_url:
        timeout = 600 if "europepmc.org" in resolved.download_url else 300
        if try_http_pdf(
            resolved.download_url,
            dest,
            timeout=timeout,
            referer=resolved.landing_url,
        ):
            return
        attempts.append(f"HTTP: {resolved.download_url}")

    if resolved.pmc_fallback_url:
        print(f"[paperdown2md] Trying Europe PMC mirror: {resolved.pmc_fallback_url}")
        if try_http_pdf(resolved.pmc_fallback_url, dest, timeout=600):
            return
        attempts.append(f"Europe PMC: {resolved.pmc_fallback_url}")

    if no_browser:
        joined = "; ".join(attempts) or "no download URL resolved"
        raise RuntimeError(
            f"PDF download failed ({joined}). Browser fallback disabled (--no-browser)."
        )

    print("[paperdown2md] HTTP insufficient; trying browser (CDP)…")

    browser_pdf_url: str | None = None
    landing = resolved.landing_url
    if landing and not is_known_pdf_endpoint(landing):
        browser_pdf_url = find_pdf_url_via_browser(landing)

    for candidate in (
        browser_pdf_url,
        resolved.download_url,
        resolved.pmc_fallback_url,
    ):
        if not candidate:
            continue
        if try_http_pdf(candidate, dest, timeout=600, referer=landing or candidate):
            return

    fetch_url = browser_pdf_url or resolved.download_url or resolved.pmc_fallback_url or landing
    if not fetch_url:
        raise RuntimeError("No URL available for browser PDF fetch")

    browser_fetch_pdf(fetch_url, dest, referer=landing or fetch_url)
    if not is_pdf_file(dest):
        raise RuntimeError(
            f"Browser fetch did not produce a valid PDF for {fetch_url!r}. "
            "If this is paywalled, log in to your institution in Chrome first."
        )


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


def resolve_from_openalex_work(work: dict, fallback_title: str) -> ResolvedPaper:
    pdf, title = pick_pdf_url(work)
    title = title or fallback_title
    pmc_url = resolve_pmc_fallback(work)
    landing = pick_publisher_landing(work)

    if pdf:
        return ResolvedPaper(
            title=title,
            download_url=pdf,
            landing_url=landing,
            pmc_fallback_url=pmc_url,
            work=work,
        )

    if pmc_url:
        print(f"[paperdown2md] OpenAlex has no direct PDF; using PMC mirror: {pmc_url}")
        return ResolvedPaper(
            title=title,
            download_url=pmc_url,
            landing_url=landing,
            pmc_fallback_url=pmc_url,
            work=work,
        )

    if landing:
        print(
            f"[paperdown2md] OpenAlex has no direct PDF; will try publisher page via browser: {landing}"
        )
        return ResolvedPaper(
            title=title,
            landing_url=landing,
            pmc_fallback_url=pmc_url,
            work=work,
        )

    raise ValueError(
        f"OpenAlex found '{title}' but no open PDF URL or PMC mirror; "
        "try arXiv link, direct PDF URL, or manual download."
    )


def resolve_paper_source(source: str) -> ResolvedPaper:
    """Resolve arXiv / DOI / PDF / OpenAlex title → ResolvedPaper."""
    source = source.strip()
    if not source:
        raise ValueError("empty source")

    m = EUROPEPMC_RENDER_RE.search(source)
    if m:
        pmcid = normalize_pmcid(m.group(1)) or m.group(1)
        return ResolvedPaper(
            title=pmcid,
            download_url=europepmc_render_url(pmcid),
            pmc_fallback_url=europepmc_render_url(pmcid),
        )

    m = PMC_ARTICLE_RE.search(source)
    if m:
        pmcid = f"PMC{m.group(1)}"
        return ResolvedPaper(
            title=pmcid,
            download_url=europepmc_render_url(pmcid),
            pmc_fallback_url=europepmc_render_url(pmcid),
            landing_url=source if source.startswith("http") else None,
        )

    if is_known_pdf_endpoint(source) and (
        source.startswith("http://") or source.startswith("https://")
    ):
        return ResolvedPaper(
            title=Path(urllib.parse.urlparse(source).path).stem,
            download_url=source,
        )

    arxiv_id = parse_arxiv_id(source)
    if arxiv_id:
        return ResolvedPaper(title=arxiv_id, download_url=arxiv_pdf_url(arxiv_id))

    if source.startswith("http") and "arxiv.org" in source:
        arxiv_id = parse_arxiv_id(source)
        if arxiv_id:
            return ResolvedPaper(title=arxiv_id, download_url=arxiv_pdf_url(arxiv_id))

    if source.startswith("http") and is_publisher_landing_url(source):
        return ResolvedPaper(title=source, landing_url=source)

    work = openalex_work(source)
    if work:
        return resolve_from_openalex_work(work, source)

    raise ValueError(
        f"Cannot resolve PDF for: {source!r}. "
        "Use arXiv URL/ID, DOI, direct .pdf URL, or English title for OpenAlex search."
    )


def resolve_social_article(url: str) -> ResolvedPaper:
    """Resolve WeChat / XHS post → ResolvedPaper."""
    platform = social_platform(url)
    label = "WeChat" if platform == "weixin" else "XHS"
    print(f"[paperdown2md] Resolving {label} post: {url}")

    html, page_title, body_text = fetch_social_page(url, platform)
    title = extract_social_title(html, body_text, page_title)
    paper_refs = collect_paper_refs(html, body_text)

    if paper_refs:
        print(f"[paperdown2md] Found {len(paper_refs)} paper ref(s); using: {paper_refs[0]}")
        resolved = resolve_paper_source(paper_refs[0])
        if title:
            return ResolvedPaper(
                title=title,
                download_url=resolved.download_url,
                landing_url=resolved.landing_url,
                pmc_fallback_url=resolved.pmc_fallback_url,
                work=resolved.work,
            )
        return resolved

    queries = build_literature_search_queries(title, body_text)
    if not queries and title:
        queries = [title]
    print(
        f"[paperdown2md] No direct paper link in {label} post; "
        "searching literature by title/keywords…"
    )
    return resolve_via_literature_search(queries, title)


def resolve_source(source: str) -> ResolvedPaper:
    """Return ResolvedPaper. Supports social post URLs as entry points."""
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
    no_browser: bool = False,
) -> Path:
    resolved = resolve_source(source)
    name = sanitize_name(folder_name or resolved.title)
    paper_dir = output_dir / name
    paper_dir.mkdir(parents=True, exist_ok=True)

    pdf_basename = sanitize_name(pdf_name or name) + ".pdf"
    pdf_path = paper_dir / pdf_basename

    print(f"[paperdown2md] Downloading → {pdf_path}")
    download_pdf_resolved(resolved, pdf_path, no_browser=no_browser)

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
        "--no-browser",
        action="store_true",
        help="Disable Chrome CDP browser fallback for PDF download",
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

    no_browser = args.no_browser or bool(os.environ.get("PAPERDOWN2MD_NO_BROWSER"))

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
                    no_browser=no_browser,
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
