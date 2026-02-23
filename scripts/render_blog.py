#!/usr/bin/env python3
from __future__ import annotations
import re
from pathlib import Path
from datetime import datetime
import html

ROOT = Path(__file__).resolve().parents[1]
POSTS_DIR = ROOT / "blog" / "posts"
BLOG_DIR = ROOT / "blog"

SITE_TITLE = "HUXLEY"

BASE_TEMPLATE = """<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width,initial-scale=1\" />
  <title>{title} | HUXLEY</title>
  <style>
    :root{{--bg:#f4f4f0;--text:#222;--card:#fff;--muted:#666;--line:#e4e4e0;--accent:#0b69ff;}}
    body{{font-family:system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;margin:0;background:var(--bg);color:var(--text);}}
    .wrap{{max-width:900px;margin:0 auto;padding:28px 20px;}}
    .nav{{display:flex;gap:16px;font-size:14px;margin:8px 0 22px;}}
    .nav a{{color:#444;text-decoration:none}}
    h1,h2,h3{{margin:0 0 12px;line-height:1.2}}
    .meta{{color:var(--muted);font-size:14px;margin-bottom:20px}}
    article{{background:var(--card);border:1px solid var(--line);padding:24px;border-radius:12px}}
    .grid{{display:grid;gap:14px}}
    .card{{background:var(--card);border:1px solid var(--line);padding:16px;border-radius:10px}}
    a{{color:var(--accent);text-decoration:none}}
    ul{{padding-left:20px}}
    code{{background:#eee;padding:1px 4px;border-radius:4px}}
  </style>
</head>
<body>
<div class=\"wrap\">
  <h1>{header}</h1>
  <div class=\"nav\"><a href=\"/index.html\">Home</a><a href=\"/blog/index.html\">Blog</a></div>
  {content}
</div>
</body>
</html>
"""


def parse_frontmatter(raw: str):
    raw = raw.replace("\r\n", "\n")
    if not raw.startswith("---\n"):
        return {}, raw
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", raw, flags=re.S)
    if not m:
        return {}, raw
    fm_txt, body = m.groups()
    meta = {}
    for ln in fm_txt.split("\n"):
        if ":" not in ln:
            continue
        k, v = ln.split(":", 1)
        meta[k.strip()] = v.strip().strip('"')
    return meta, body


def md_to_html(md: str) -> str:
    # very small markdown renderer (safe, dependency-free)
    lines = md.split("\n")
    out = []
    in_ul = False
    for ln in lines:
        s = ln.strip()
        if not s:
            if in_ul:
                out.append("</ul>")
                in_ul = False
            continue
        if s.startswith("### "):
            if in_ul:
                out.append("</ul>"); in_ul = False
            out.append(f"<h3>{html.escape(s[4:])}</h3>")
        elif s.startswith("## "):
            if in_ul:
                out.append("</ul>"); in_ul = False
            out.append(f"<h2>{html.escape(s[3:])}</h2>")
        elif s.startswith("# "):
            if in_ul:
                out.append("</ul>"); in_ul = False
            out.append(f"<h1>{html.escape(s[2:])}</h1>")
        elif s.startswith("- "):
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            out.append(f"<li>{html.escape(s[2:])}</li>")
        else:
            if in_ul:
                out.append("</ul>")
                in_ul = False
            out.append(f"<p>{html.escape(s)}</p>")
    if in_ul:
        out.append("</ul>")
    return "\n".join(out)


def render():
    BLOG_DIR.mkdir(parents=True, exist_ok=True)
    POSTS_DIR.mkdir(parents=True, exist_ok=True)

    posts = []
    for md_file in sorted(POSTS_DIR.glob("*.md")):
        if md_file.name.lower() == "readme.md" or md_file.name.startswith("_"):
            continue
        raw = md_file.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(raw)
        title = meta.get("title") or md_file.stem.replace("-", " ").title()
        date = meta.get("date", "")
        summary = meta.get("summary", "")
        slug = md_file.stem
        out_html = BLOG_DIR / f"{slug}.html"

        article = (
            f"<article>"
            f"<h1>{html.escape(title)}</h1>"
            f"<div class='meta'>{html.escape(date)}</div>"
            f"{md_to_html(body)}"
            f"</article>"
        )
        page = BASE_TEMPLATE.format(title=html.escape(title), header=SITE_TITLE, content=article)
        out_html.write_text(page, encoding="utf-8")

        posts.append({"title": title, "date": date, "summary": summary, "slug": slug})

    # Newest-first by date string fallback filename
    posts.sort(key=lambda p: (p.get("date") or "", p["slug"]), reverse=True)

    cards = ["<div class='grid'>"]
    for p in posts:
        cards.append(
            "<div class='card'>"
            f"<h3><a href='/blog/{p['slug']}.html'>{html.escape(p['title'])}</a></h3>"
            f"<div class='meta'>{html.escape(p.get('date',''))}</div>"
            f"<p>{html.escape(p.get('summary',''))}</p>"
            f"<a href='/blog/{p['slug']}.html'>Read →</a>"
            "</div>"
        )
    cards.append("</div>")

    index = BASE_TEMPLATE.format(
        title="Blog",
        header="HUXLEY — Blog",
        content="\n".join(cards)
    )
    (BLOG_DIR / "index.html").write_text(index, encoding="utf-8")
    print(f"rendered {len(posts)} post(s)")


if __name__ == "__main__":
    render()
