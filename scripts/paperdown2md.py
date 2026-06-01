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
INVALID_FS_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')

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


def resolve_source(source: str) -> tuple[str, str]:
    """Return (pdf_url, suggested_title)."""
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
        help="arXiv URL/ID, DOI, direct PDF URL, or paper title (OpenAlex search)",
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
