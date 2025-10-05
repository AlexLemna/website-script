#!/usr/bin/env python3

from __future__ import annotations

import argparse
import datetime as _dt
import logging
import tomllib
from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import List, Optional, Tuple

# ----------------------- Configuration and CLI -----------------------

DEFAULT_CONFIG_NAMES = ("alexsite.toml",)
ETC_CONFIG_PATH = Path("/etc/alexsite.toml")


@dataclass
class Config:
    site_title: str = "Site"
    base_url: str = "/"
    css_href: str = "/style.css"
    date_format: str = "%Y-%m-%d"
    src_root: Optional[Path] = None
    dst_root: Optional[Path] = None


def load_toml(path: Path) -> dict:
    with path.open("rb") as f:
        return tomllib.load(f)


def find_config() -> dict:
    # Prefer local config in CWD, then /etc
    cwd = Path.cwd()
    for name in DEFAULT_CONFIG_NAMES:
        p = cwd / name
        if p.exists():
            return load_toml(p)
    if ETC_CONFIG_PATH.exists():
        return load_toml(ETC_CONFIG_PATH)
    return {}


def merge_config(base: dict, override: dict) -> dict:
    out = dict(base)
    out.update({k: v for k, v in override.items() if v is not None})
    return out


def build_config(args: argparse.Namespace, per_domain: dict) -> Config:
    global_cfg = find_config()
    merged = {}
    merged = merge_config(merged, global_cfg)
    merged = merge_config(merged, per_domain)
    cli = {
        "site_title": args.site_title,
        "base_url": args.base_url,
        "css_href": args.css_href,
        "src_root": str(args.src_root) if args.src_root else None,
        "dst_root": str(args.dst_root) if args.dst_root else None,
        "date_format": args.date_format,
    }
    merged = merge_config(merged, {k: v for k, v in cli.items() if v is not None})
    cfg = Config(
        site_title=str(merged.get("site_title", "Site")),
        base_url=str(merged.get("base_url", "/")),
        css_href=str(merged.get("css_href", "/style.css")),
        date_format=str(merged.get("date_format", "%Y-%m-%d")),
        src_root=Path(merged["src_root"]) if merged.get("src_root") else None,
        dst_root=Path(merged["dst_root"]) if merged.get("dst_root") else None,
    )
    return cfg


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Minimal static site builder without third-party modules."
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--domain",
        required=True,
        help="Domain subtree to build, e.g., notes.alexanderlemna.com",
    )
    common.add_argument(
        "--src-root", type=Path, help="Root of source trees (e.g., /var/www/src)"
    )
    common.add_argument(
        "--dst-root",
        type=Path,
        help="Root of destination trees (e.g., /var/www/htdocs)",
    )
    common.add_argument("--site-title", help="Override site title")
    common.add_argument("--base-url", help="Base URL for canonical links")
    common.add_argument("--css-href", help="Href to a CSS file for all pages")
    common.add_argument(
        "--date-format", help="strftime format for dates, default %Y-%m-%d"
    )
    common.add_argument(
        "--dry-run", action="storeTrue", help="Log actions without writing files"
    )
    common.add_argument("--verbose", action="store_true", help="Verbose logging")

    b = sub.add_parser(
        "build", parents=[common], help="Build site for the specified domain"
    )
    b.add_argument(
        "--clean-first",
        action="store_true",
        help="Remove generated .html under domain before build",
    )

    c = sub.add_parser(
        "clean", parents=[common], help="Remove generated .html for the domain"
    )

    return p.parse_args()


def setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)-7s %(message)s",
        datefmt="%H:%M:%S",
    )


# ----------------------- Markdown to HTML (minimal) -----------------------


def _is_fenced_start(line: str) -> Optional[str]:
    line = line.rstrip("\n")
    if line.startswith("```"):
        lang = line[3:].strip()
        return lang or ""
    return None


def _render_inline(text: str) -> str:
    # Escape first, then apply minimal inline markdown.
    t = escape(text)
    # inline code
    t = _replace_delimited(t, "`", "<code>", "</code>")
    # strong and em (nested handling is simplistic)
    t = _replace_delimited(t, "**", "<strong>", "</strong>")
    t = _replace_delimited(t, "*", "<em>", "</em>")
    # links [text](url)
    t = _replace_links(t)
    return t


def _replace_delimited(s: str, delim: str, open_tag: str, close_tag: str) -> str:
    parts = s.split(delim)
    if len(parts) < 3:
        return s
    out = []
    toggle = False
    for part in parts:
        if toggle:
            out.append(open_tag + part + close_tag)
        else:
            out.append(part)
        toggle = not toggle
    # If odd number, last segment was not closed; rejoin with delimiter to avoid corruption.
    if toggle:
        return s
    return "".join(out)


def _replace_links(s: str) -> str:
    # Very simple link parser: [text](url) without nesting.
    out = []
    i = 0
    L = len(s)
    while i < L:
        if s[i] == "[":
            j = s.find("]", i + 1)
            if j != -1 and j + 1 < L and s[j + 1] == "(":
                k = s.find(")", j + 2)
                if k != -1:
                    text = s[i + 1 : j]
                    url = s[j + 2 : k]
                    out.append(f'<a href="{url}">{text}</a>')
                    i = k + 1
                    continue
        out.append(s[i])
        i += 1
    return "".join(out)


def markdown_to_html(md: str) -> str:
    """Very small Markdown subset renderer producing semantic HTML."""
    lines = md.splitlines()
    html_lines: List[str] = []
    in_code = False
    code_buf: List[str] = []
    list_open = False
    ol_open = False

    def close_lists():
        nonlocal list_open, ol_open
        if list_open:
            html_lines.append("</ul>")
            list_open = False
        if ol_open:
            html_lines.append("</ol>")
            ol_open = False

    i = 0
    while i < len(lines):
        raw = lines[i]
        line = raw.rstrip("\n")

        # Fenced code blocks
        fence = _is_fenced_start(line)
        if fence is not None:
            if in_code:
                # closing fence
                html_lines.append("<pre><code>")
                html_lines.extend(escape("\n".join(code_buf)).splitlines())
                html_lines.append("</code></pre>")
                code_buf.clear()
                in_code = False
            else:
                in_code = True
            i += 1
            continue

        if in_code:
            code_buf.append(raw)
            i += 1
            continue

        # Headings
        if line.startswith("#"):
            close_lists()
            level = len(line) - len(line.lstrip("#"))
            level = max(1, min(6, level))
            text = line[level:].strip()
            html_lines.append(f"<h{level}>" + _render_inline(text) + f"</h{level}>")
            i += 1
            continue

        # Ordered list "1. " pattern
        if _list_numbered := _starts_with_numbered_item(line):
            close_tag_to_use = "ol"
            if not ol_open:
                close_lists()
                html_lines.append("<ol>")
                ol_open = True
            html_lines.append("<li>" + _render_inline(_list_numbered) + "</li>")
            i += 1
            continue

        # Unordered list "- " pattern
        if line.strip().startswith("- "):
            if not list_open:
                close_lists()
                html_lines.append("<ul>")
                list_open = True
            html_lines.append(
                "<li>" + _render_inline(line.strip()[2:].strip()) + "</li>"
            )
            i += 1
            continue

        # Blank lines separate paragraphs
        if not line.strip():
            close_lists()
            html_lines.append("")
            i += 1
            continue

        # Indented code (4 spaces or a tab)
        if line.startswith("    ") or line.startswith("\t"):
            close_lists()
            code_block, advance = _collect_indented_code(lines, i)
            html_lines.append("<pre><code>")
            html_lines.append(escape("\n".join(code_block)))
            html_lines.append("</code></pre>")
            i += advance
            continue

        # Paragraph
        close_lists()
        html_lines.append("<p>" + _render_inline(line.strip()) + "</p>")
        i += 1

    # Close any open list
    if list_open:
        html_lines.append("</ul>")
    if ol_open:
        html_lines.append("</ol>")

    return "\n".join(html_lines)


def _starts_with_numbered_item(line: str) -> Optional[str]:
    s = line.lstrip()
    # minimal detection: "1. ", "2. ", etc.
    if len(s) >= 3 and s[0].isdigit():
        # find dot
        j = 1
        while j < len(s) and s[j].isdigit():
            j += 1
        if j < len(s) and s[j] == "." and j + 1 < len(s) and s[j + 1] == " ":
            return s[j + 2 :].strip()
    return None


def _collect_indented_code(lines: List[str], start: int) -> Tuple[List[str], int]:
    buf: List[str] = []
    i = start
    while i < len(lines):
        l = lines[i]
        if l.startswith("    ") or l.startswith("\t"):
            buf.append(l[4:] if l.startswith("    ") else l[1:])
            i += 1
        else:
            break
    return buf, i - start


# ----------------------- Site building -----------------------

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="canonical" href="{canonical}">
<link rel="stylesheet" href="{css_href}">
</head>
<body>
<header>
  <h1><a href="{base_url}">{site_title}</a></h1>
</header>
<main>
{content}
</main>
<footer>
  <p>Built {built} UTC</p>
</footer>
</body>
</html>
"""


def render_page(
    config: Config, title: str, content_html: str, canonical_path: str
) -> str:
    built = _dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    canonical = config.base_url.rstrip("/") + "/" + canonical_path.lstrip("/")
    return HTML_TEMPLATE.format(
        title=escape(title),
        canonical=canonical,
        css_href=config.css_href,
        base_url=config.base_url.rstrip("/"),
        site_title=escape(config.site_title),
        content=content_html,
        built=built,
    )


def write_text(path: Path, text: str, dry_run: bool) -> None:
    logging.info("write %s", path)
    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def md_to_html_file(
    md_path: Path, rel_root: Path, out_root: Path, cfg: Config, dry_run: bool
) -> Optional[Path]:
    if md_path.name.startswith("__") and md_path.suffix == ".md":
        return None
    rel = md_path.relative_to(rel_root).with_suffix(".html")
    dst = out_root / rel
    logging.debug("convert %s -> %s", md_path, dst)
    html_body = markdown_to_html(md_path.read_text(encoding="utf-8"))
    title = md_title(md_path) or md_path.stem.replace("-", " ")
    canonical_path = str(rel)
    page = render_page(cfg, title, html_body, canonical_path)
    write_text(dst, page, dry_run)
    return dst


def md_title(md_path: Path) -> Optional[str]:
    # First ATX heading or fallback None
    for line in md_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("#"):
            return line.lstrip("#").strip()
    return None


def collect_md_files(root: Path) -> List[Path]:
    return [p for p in root.rglob("*.md")]


def clean_domain(dst_domain_root: Path, dry_run: bool) -> None:
    if not dst_domain_root.exists():
        logging.info("nothing to clean at %s", dst_domain_root)
        return
    for p in dst_domain_root.rglob("*.html"):
        # Avoid removing non-generated assets like index.html you may hand-maintain.
        logging.info("remove %s", p)
        if not dry_run:
            try:
                p.unlink()
            except FileNotFoundError:
                pass


def build_index(
    domain_src_root: Path, domain_dst_root: Path, cfg: Config, dry_run: bool
) -> None:
    index_md = domain_src_root / "__index__.md"
    if index_md.exists():
        body = markdown_to_html(index_md.read_text(encoding="utf-8"))
    else:
        body = "<h2>Index</h2>"

    # Add a generated listing of Markdown-derived pages
    entries: List[Tuple[str, str]] = []
    for p in domain_src_root.rglob("*.md"):
        if p.name.startswith("__"):
            continue
        rel_html = p.relative_to(domain_src_root).with_suffix(".html")
        title = md_title(p) or p.stem.replace("-", " ")
        entries.append((str(rel_html).replace("\\", "/"), title))
    entries.sort()

    listing = ["<h2>Posts</h2>", "<ul>"]
    for href, title in entries:
        listing.append(f'<li><a href="{href}">{escape(title)}</a></li>')
    listing.append("</ul>")

    content = body + "\n" + "\n".join(listing)
    page = render_page(cfg, f"{cfg.site_title} — Index", content, "index.html")
    write_text(domain_dst_root / "index.html", page, dry_run)


def load_domain_settings(domain_src_root: Path) -> dict:
    p = domain_src_root / "__settings__.toml"
    if p.exists():
        logging.info("domain settings: %s", p)
        return load_toml(p)
    return {}


def assert_path(path: Optional[Path], name: str) -> Path:
    if path is None:
        logging.error("%s not set via CLI or config", name)
        raise SystemExit(2)
    return path


def run_build(args: argparse.Namespace) -> None:
    cfg = build_config(
        args,
        per_domain=load_domain_settings(
            assert_path(args.src_root, "src_root") / args.domain
        ),
    )
    src_root = assert_path(cfg.src_root, "src_root")
    dst_root = assert_path(cfg.dst_root, "dst_root")

    domain_src = src_root / args.domain
    domain_dst = dst_root / args.domain

    if not domain_src.exists():
        logging.error("domain source path does not exist: %s", domain_src)
        raise SystemExit(2)

    if args.clean_first:
        clean_domain(domain_dst, args.dry_run)

    # Convert Markdown files
    md_files = collect_md_files(domain_src)
    logging.info("found %d markdown files", len(md_files))
    for md in md_files:
        md_to_html_file(md, domain_src, domain_dst, cfg, args.dry_run)

    # Build index
    build_index(domain_src, domain_dst, cfg, args.dry_run)

    logging.info("build complete for %s", args.domain)


def run_clean(args: argparse.Namespace) -> None:
    cfg = build_config(args, per_domain={})
    dst_root = assert_path(cfg.dst_root or args.dst_root, "dst_root")
    domain_dst = dst_root / args.domain
    clean_domain(domain_dst, args.dry_run)
    logging.info("clean complete for %s", args.domain)


def main() -> None:
    args = parse_args()
    setup_logging(getattr(args, "verbose", False))
    logging.debug("args: %r", args)
    try:
        if args.cmd == "build":
            run_build(args)
        elif args.cmd == "clean":
            run_clean(args)
        else:
            raise SystemExit(2)
    except KeyboardInterrupt:
        logging.warning("interrupted by user")
        raise SystemExit(130)


if __name__ == "__main__":
    main()
