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
OG_TITLE_RE = re.compile(
    r'property="og:title"\s+content="([^"]+)"|content="([^"]+)"\s+property="og:title"',
    re.I,
)
PAPER_HOST_RE = re.compile(
    r"(arxiv\.org|doi\.org|biorxiv\.org|medrxiv\.org|\.pdf(?:\?|#|$))",
    re.I,
)
INVALID_FS_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
WEIXIN_UA = (
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


def is_weixin_url(source: str) -> bool:
    return bool(WEIXIN_URL_RE.search(source)) or (
        "mp.weixin.qq.com" in source and "/s/" in source
    )


def normalize_weixin_html(html: str) -> str:
    return (
        html.replace("\\x3c", "<")
        .replace("\\x3e", ">")
        .replace("\\x26", "&")
        .replace("\\x22", '"')
    )


def extract_weixin_title(html: str) -> str | None:
    m = OG_TITLE_RE.search(html)
    if not m:
        return None
    return (m.group(1) or m.group(2) or "").strip() or None


def extract_paper_urls_from_html(html: str) -> list[str]:
    html = normalize_weixin_html(html)
    raw_urls = re.findall(r"https?://[^\s\"'<>\\]+", html)
    seen: set[str] = set()
    paper_urls: list[str] = []
    for raw in raw_urls:
        url = raw.rstrip(".,;)]}>\"'\\")
        if not PAPER_HOST_RE.search(url):
            continue
        if url in seen:
            continue
        seen.add(url)
        paper_urls.append(url)
    return paper_urls


def weixin_page_blocked(html: str) -> bool:
    return "环境异常" in html and len(html) < 100_000


def weixin_page_usable(html: str) -> bool:
    if weixin_page_blocked(html):
        return False
    return bool(extract_paper_urls_from_html(html))


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


def fetch_weixin_html_browser(url: str) -> str:
    """Fetch WeChat article HTML via Chrome CDP (web-access proxy)."""
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

        result = cdp_request_json(
            f"{base}/eval?target={target_id}",
            data=b"document.documentElement.outerHTML",
            method="POST",
            timeout=120,
        )
        html = result.get("value") or ""
        if not isinstance(html, str) or not html.strip():
            raise ValueError("Browser returned empty HTML from WeChat page")
        return html
    finally:
        try:
            urllib.request.urlopen(f"{base}/close?target={target_id}", timeout=5)
        except (urllib.error.URLError, TimeoutError, OSError):
            pass


def fetch_weixin_html(url: str) -> str:
    """HTTP first; fall back to browser CDP when blocked or missing paper links."""
    html: str | None = None
    curl_error: Exception | None = None

    try:
        html = http_get_text(url, timeout=120, user_agent=WEIXIN_UA)
    except urllib.error.URLError as e:
        curl_error = e

    if html and weixin_page_usable(html):
        print("[paperdown2md] WeChat article fetched via HTTP")
        return html

    if html and weixin_page_blocked(html):
        reason = "verification required (环境异常)"
    elif html:
        reason = "no arXiv/DOI/PDF links in HTTP response"
    else:
        reason = f"HTTP failed ({curl_error})"

    print(f"[paperdown2md] HTTP insufficient ({reason}); trying browser (CDP)…")
    browser_html = fetch_weixin_html_browser(url)

    if weixin_page_blocked(browser_html):
        raise ValueError(
            "WeChat page still blocked after browser fetch. "
            "Complete verification in Chrome, or pass the arXiv/DOI link directly."
        )
    if not weixin_page_usable(browser_html):
        title = extract_weixin_title(browser_html)
        hint = f" Title: {title!r}." if title else ""
        raise ValueError(
            f"No arXiv/DOI/PDF link found in WeChat article via browser.{hint} "
            "Paste the paper link directly if the article only links GitHub or a project page."
        )

    print("[paperdown2md] WeChat article fetched via browser (CDP)")
    return browser_html


def resolve_weixin_article(url: str) -> tuple[str, str]:
    """Fetch WeChat article, extract first arXiv/DOI/PDF link, return (pdf_url, title)."""
    print(f"[paperdown2md] Resolving WeChat article: {url}")
    html = fetch_weixin_html(url)

    title = extract_weixin_title(html)
    paper_urls = extract_paper_urls_from_html(html)
    if not paper_urls:
        hint = f" Title: {title!r}." if title else ""
        raise ValueError(
            f"No arXiv/DOI/PDF link found in WeChat article.{hint} "
            "Paste the paper link directly if the article only links GitHub or a project page."
        )

    print(f"[paperdown2md] Found {len(paper_urls)} paper link(s); using: {paper_urls[0]}")
    pdf_url, _ = resolve_paper_source(paper_urls[0])
    return pdf_url, title or _


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
    """Return (pdf_url, suggested_title). Supports WeChat article URLs as entry points."""
    source = source.strip()
    if is_weixin_url(source):
        return resolve_weixin_article(source)
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
        help="arXiv URL/ID, DOI, direct PDF URL, WeChat article URL, or paper title (OpenAlex)",
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
