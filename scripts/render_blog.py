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
    table{{width:100%;border-collapse:collapse;margin:14px 0;font-size:15px}}
    th,td{{border:1px solid var(--line);padding:8px 10px;vertical-align:top;text-align:left}}
    thead th{{background:#f7f7f4;font-weight:700}}
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


def render_inline(text: str) -> str:
    t = html.escape(text)
    # links: [label](url)
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', t)
    # inline code
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    # bold
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    # italics
    t = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", t)
    return t


def _is_table_separator(line: str) -> bool:
    x = line.strip()
    if "|" not in x:
        return False
    x = x.strip("|")
    parts = [p.strip() for p in x.split("|")]
    if not parts:
        return False
    for p in parts:
        if not p:
            return False
        if not re.fullmatch(r":?-{3,}:?", p):
            return False
    return True


def _split_table_row(line: str):
    x = line.strip().strip("|")
    return [c.strip() for c in x.split("|")]


def md_to_html(md: str) -> str:
    # lightweight markdown renderer (safe, dependency-free)
    lines = md.replace("\r\n", "\n").split("\n")
    out = []
    in_ul = False
    i = 0

    def close_ul():
        nonlocal in_ul
        if in_ul:
            out.append("</ul>")
            in_ul = False

    while i < len(lines):
        raw = lines[i]
        s = raw.strip()

        if not s:
            close_ul()
            i += 1
            continue

        # table block: header row + separator + rows
        if "|" in s and i + 1 < len(lines) and _is_table_separator(lines[i + 1]):
            close_ul()
            header = _split_table_row(lines[i])
            i += 2
            rows = []
            while i < len(lines):
                r = lines[i].strip()
                if not r or "|" not in r:
                    break
                rows.append(_split_table_row(lines[i]))
                i += 1

            out.append("<table><thead><tr>" + "".join(f"<th>{render_inline(c)}</th>" for c in header) + "</tr></thead><tbody>")
            for row in rows:
                out.append("<tr>" + "".join(f"<td>{render_inline(c)}</td>" for c in row) + "</tr>")
            out.append("</tbody></table>")
            continue

        if s.startswith("### "):
            close_ul()
            out.append(f"<h3>{render_inline(s[4:])}</h3>")
        elif s.startswith("## "):
            close_ul()
            out.append(f"<h2>{render_inline(s[3:])}</h2>")
        elif s.startswith("# "):
            close_ul()
            out.append(f"<h1>{render_inline(s[2:])}</h1>")
        elif s.startswith("- "):
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            out.append(f"<li>{render_inline(s[2:])}</li>")
        else:
            close_ul()
            out.append(f"<p>{render_inline(s)}</p>")

        i += 1

    close_ul()
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
