#!/usr/bin/env python3
"""Builds the site pages from the files in _source/.

    python3 _source/build.py            # writes the live pages into the repository
    python3 _source/build.py --preview DIR   # writes a self-contained copy into DIR

Content lives in:
    _source/pages/*.html   page sections (research, teaching, experience ...)
    _source/work.yml       selected work
    _source/posts/*.md     blog posts; one file per post, named YYYY-MM-DD-short-title.md
"""
import datetime as dt
import html
import os
import re
import shutil
import sys
from email.utils import format_datetime

import markdown
import yaml

SITE = "https://stephenanti.com"
# projects kept in their own GitHub repositories; they are only on the GitHub address
PROJECTS = "https://stephenanti.github.io"
OTHER_REPOS = ("/citibike/", "/justice_project/", "/county_disaster/", "/election_webmap/")
NAME = "Stephen Mante Anti"
CV = "/resume/CVAntiSA.pdf"
DESC = ("Stephen Mante Anti (Stephen M. Anti) is a Ph.D. candidate in Communication and Media "
        "Studies at the University of Oregon studying news framing, stigma, and help-seeking in Ghana.")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "_source")

PREVIEW = "--preview" in sys.argv
OUT = sys.argv[sys.argv.index("--preview") + 1] if PREVIEW else ROOT
SHOW_DRAFTS = PREVIEW

# pages built by this script; any other path on the site is left alone
SITE_PAGES = ("/", "/research/", "/teaching/", "/work/", "/blog/")

LINKS = {
    "orcid": "https://orcid.org/0009-0009-2115-2912",
    "scholar": "https://scholar.google.com/citations?hl=en&amp;user=oBHctCIAAAAJ",
    "sojc": "https://journalism.uoregon.edu/directory/graduate-employees/all/smanti",
    "linkedin": "https://www.linkedin.com/in/stephenanti/",
    "x": "https://x.com/stephenanti",
}
EXT = 'target="_blank" rel="noopener"'


def read(path):
    with open(os.path.join(SRC, path), encoding="utf-8") as f:
        return f.read()


def esc(t):
    return html.escape(str(t), quote=True)


# ---------- links ----------
def is_site_page(path):
    return path in SITE_PAGES or path.startswith("/blog/")


def u(path, depth):
    """Address of a page or file on this site, as seen from a page `depth` folders deep."""
    if path.startswith(("http://", "https://", "mailto:", "#")):
        return path
    if path in OTHER_REPOS:
        return PROJECTS + path
    frag = ""
    if "#" in path:
        path, frag = path.split("#", 1)
        frag = "#" + frag
    if not PREVIEW:
        return path + frag
    if path.startswith("/") and not is_site_page(path) and not path.startswith(("/images/", "/assets/", "/resume/")):
        return SITE + path + frag  # other projects are read from the live site in previews
    rel = "../" * depth + path.lstrip("/")
    if rel.endswith("/") or rel == "":
        rel += "index.html"
    return rel + frag


def img_src(img, depth):
    if img.startswith("yt:"):
        return "https://i.ytimg.com/vi/%s/hqdefault.jpg" % img[3:]
    if img.startswith("http"):
        return img
    return u("/" + img.lstrip("/"), depth)


def target(url):
    return EXT if url.startswith("http") else ""


# ---------- posts ----------
def load_posts():
    posts = []
    folder = os.path.join(SRC, "posts")
    for fn in sorted(os.listdir(folder)):
        if not fn.endswith(".md"):
            continue
        raw = open(os.path.join(folder, fn), encoding="utf-8").read()
        m = re.match(r"^---\n(.*?)\n---\n(.*)$", raw, re.S)
        meta = yaml.safe_load(m.group(1)) if m else {}
        body = m.group(2) if m else raw
        if meta.get("draft") and not SHOW_DRAFTS:
            continue
        date = meta.get("date") or dt.date.fromisoformat(fn[:10])
        if isinstance(date, str):
            date = dt.date.fromisoformat(date)
        slug = meta.get("slug") or re.sub(r"^\d{4}-\d{2}-\d{2}-", "", fn[:-3])
        md = markdown.Markdown(extensions=["extra", "smarty", "sane_lists"])
        words = len(re.findall(r"\w+", body))
        posts.append({
            "title": meta["title"],
            "summary": meta.get("summary", ""),
            "tags": meta.get("tags", []) or [],
            "image": meta.get("image"),
            "date": date,
            "slug": slug,
            "path": "/blog/%s/" % slug,
            "html": md.convert(body),
            "minutes": max(1, round(words / 230)),
            "draft": bool(meta.get("draft")),
        })
    posts.sort(key=lambda p: p["date"], reverse=True)
    return posts


def nice_date(d):
    return d.strftime("%B %-d, %Y")


# ---------- shared pieces ----------
def head(title, desc, path, depth, image="images/portrait.jpg", kind="website", extra=""):
    url = SITE + path
    img = SITE + "/" + image.lstrip("/")
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="{kind}">
<meta property="og:site_name" content="{NAME}">
<meta property="og:url" content="{url}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:image" content="{img}">
<meta name="twitter:card" content="summary">
<link rel="icon" type="image/png" href="{u('/images/favicon.png', depth)}">
<link rel="apple-touch-icon" href="{u('/images/apple-touch-icon.png', depth)}">
<link rel="stylesheet" href="{u('/assets/site.css', depth)}">
<link rel="alternate" type="application/rss+xml" title="{NAME}: Blog" href="{SITE}/blog/feed.xml">
{extra}</head>
<body>
"""


def nav(active, depth, has_posts):
    items = [("Research", "/research/"), ("Teaching", "/teaching/"), ("Work", "/work/")]
    if has_posts:
        items.append(("Blog", "/blog/"))
    links = []
    for label, path in items:
        on = ' class="on" aria-current="page"' if active == path else ""
        links.append(f'<a href="{u(path, depth)}"{on}>{label}</a>')
    links.append(f'<a href="{u(CV, depth)}" {EXT}>CV</a>')
    contact = "#contact" if active == "/" else u("/#contact", depth)
    links.append(f'<a href="{contact}">Contact</a>')
    home_on = ' class="home on js-top" aria-current="page"' if active == "/" else ' class="home"'
    return f"""<nav class="top">
  <div class="page"><div class="bar">
    <div class="home-slot"><a class="logo" href="{u('/', depth)}" aria-label="Home"><img src="{u('/images/logo.png', depth)}" alt="SMA, Stephen Mante Anti" width="128" height="66"></a><a{home_on} href="{u('/', depth)}">Home</a></div>
    <div class="links">
      {chr(10).join('      ' + l for l in links).strip()}
    </div>
  </div></div>
</nav>
"""


def social(depth):
    return f"""<p class="social">
    <a href="{LINKS['linkedin']}" {EXT} title="LinkedIn"><img src="{u('/images/icons/linkedin.svg', depth)}" alt="LinkedIn"></a>
    <a href="mailto:sma2263@columbia.edu" title="Email"><img src="{u('/images/icons/email.svg', depth)}" alt="Email"></a>
    <a href="{LINKS['x']}" {EXT} title="X"><img src="{u('/images/icons/x.svg', depth)}" alt="X"></a>
  </p>"""


def footer(depth):
    return f"""
<footer><div class="page"><p class="to-top-row"><a class="js-top to-top" href="#">Back to top ↑</a></p><div class="bar"><span class="copy">© <span id="yr">{dt.date.today().year}</span> {NAME}</span></div></div></footer>
<script src="{u('/assets/site.js', depth)}"></script>
</body>
</html>
"""


def pagehead(title, lede=""):
    lede = f'\n    <p class="lede">{lede}</p>' if lede else ""
    return f"""<header class="pagehead">
  <div class="page">
    <h1>{title}</h1>{lede}
  </div>
</header>
"""


def card(it, depth):
    url = u(it["url"], depth)
    t = target(url)
    text = f'<p>{it["text"]}</p>' if it.get("text") else ""
    if url.startswith("http") and "youtube.com" not in url:
        text += f'<p class="open"><a href="{url}" {t}>Open project ↗</a></p>'
    elif "youtube.com" in url:
        text += f'<p class="open"><a href="{url}" {t}>Watch on YouTube ↗</a></p>'
    else:
        text += f'<p class="open"><a href="{url}">Open project →</a></p>'
    return (f'<div class="item"><a class="thumb" href="{url}" {t}><span class="alt">{esc(it["title"])}</span>'
            f'<img loading="lazy" src="{img_src(it["img"], depth)}" alt=""></a>'
            f'<h4><a href="{url}" {t}>{esc(it["title"])}</a></h4>{text}</div>')


def featured(f, depth):
    url = u(f["url"], depth)
    return f"""<div class="featured">
    <a class="thumb" href="{url}"><img src="{img_src(f['img'], depth)}" alt="Chart from the story"></a>
    <div>
      <p class="kicker">{esc(f['kicker'])}</p>
      <h4><a href="{url}">{esc(f['title'])}</a></h4>
      <p>{f['text']}</p>
      <a class="arrow" href="{url}">{esc(f.get('link_text', 'Read more'))} →</a>
    </div>
  </div>"""


def post_list(posts, depth, limit=None):
    out = []
    for p in posts[:limit] if limit else posts:
        url = u(p["path"], depth)
        tags = "".join(f'<span class="tag">{esc(t)}</span>' for t in p["tags"])
        thumb = (f'<a class="pthumb" href="{url}"><img loading="lazy" src="{img_src(p["image"], depth)}" alt=""></a>'
                 if p["image"] else "")
        draft = ' <span class="tag">Draft</span>' if p["draft"] else ""
        out.append(f"""<article class="post-row{' has-thumb' if thumb else ''}">
    {thumb}<div>
      <p class="meta">{nice_date(p['date'])} · {p['minutes']} min read{draft}</p>
      <h3><a href="{url}">{esc(p['title'])}</a></h3>
      <p>{esc(p['summary'])}</p>
      <p class="tags">{tags}</p>
    </div>
  </article>""")
    return "\n  ".join(out)


def write(path, text):
    full = os.path.join(OUT, path.lstrip("/"), "index.html") if path.endswith("/") else os.path.join(OUT, path.lstrip("/"))
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(text)


def fix_links(fragment, depth):
    """Rewrite site paths (href="/..." and src="/...") inside hand-written page fragments."""
    return re.sub(r'(href|src)="(/[^"]*)"', lambda m: f'{m.group(1)}="{u(m.group(2), depth)}"', fragment)


# ---------- pages ----------
def build():
    work = yaml.safe_load(read("work.yml"))
    posts = load_posts()
    has_posts = bool(posts)

    # Home
    d = 0
    picks = [it for s in work["sections"] for it in s["items"] if it.get("home")]
    f = work["featured"]
    home_cards = [card({"title": f["title"], "url": f["url"], "img": f["img"], "text": f["kicker"].replace(" · ", ", ")}, d)]
    home_cards += [card({**it, "text": it.get("text", "") if len(it.get("text", "")) < 90 else it["text"].split(":")[0] + "."}, d) for it in picks]
    writing = ""
    if has_posts:
        writing = f"""
<section id="blog">
  <h2>Blog</h2>
  {post_list(posts, d, 3)}
  <p class="all"><a class="arrow" href="{u('/blog/', d)}">All posts →</a></p>
</section>
"""
    jsonld = f"""<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"Person","name":"{NAME}","alternateName":["Stephen M. Anti","Stephen Anti"],"url":"{SITE}/","image":"{SITE}/images/portrait.jpg","jobTitle":"Ph.D. Candidate, Communication and Media Studies","affiliation":{{"@type":"CollegeOrUniversity","name":"University of Oregon","department":{{"@type":"Organization","name":"School of Journalism and Communication"}}}},"alumniOf":[{{"@type":"CollegeOrUniversity","name":"Columbia University"}},{{"@type":"CollegeOrUniversity","name":"Cardiff University"}}],"knowsAbout":["health communication","media effects","news framing","mental illness stigma","help-seeking","Ghana","data journalism","broadcast journalism"],"sameAs":["{LINKS['linkedin']}","{LINKS['orcid']}","https://scholar.google.com/citations?user=oBHctCIAAAAJ","{LINKS['sojc']}","{LINKS['x']}"]}}
</script>
"""
    home = head(f"{NAME} | University of Oregon", DESC, "/", d, kind="profile", extra=jsonld) + nav("/", d, has_posts) + f"""
<header class="intro" id="top">
  <div class="page">
    <img class="photo" id="photo" src="{u('/images/portrait.jpg', d)}" alt="{NAME}">
    <div>
      <h1>{NAME}</h1>
      <p class="position">Ph.D. Candidate, Communication and Media Studies<br>School of Journalism and Communication, University of Oregon</p>
{read('pages/intro.html').rstrip()}
      <p class="btns"><a href="{u('/research/', d)}">Explore my research</a> <a href="{u('/research/#publications', d)}">See publications</a></p>
      <p class="contact-line"><a href="{u(CV, d)}" {EXT}>CV (PDF)</a> <span>|</span> <a href="mailto:smanti@uoregon.edu">smanti@uoregon.edu</a> <span>|</span> <a href="mailto:sma2263@columbia.edu">sma2263@columbia.edu</a><br><a href="{LINKS['orcid']}" {EXT}>ORCID</a> <span>|</span> <a href="{LINKS['scholar']}" {EXT}>Google Scholar</a> <span>|</span> <a href="{LINKS['sojc']}" {EXT}>SOJC profile</a></p>
      {social(d)}
    </div>
  </div>
</header>

<main class="page">

<section id="research">
  <h2>Research</h2>
{fix_links(read('pages/home-research.html'), d).rstrip()}
  <p class="all"><a class="arrow" href="{u('/research/', d)}">Dissertation, publications and presentations →</a></p>
</section>

<section id="work">
  <h2>Selected work</h2>
  <div class="grid">
    {(chr(10) + '    ').join(home_cards)}
  </div>
  <p class="all"><a class="arrow" href="{u('/work/', d)}">All work: maps, data stories and broadcast →</a></p>
</section>
{writing}
<section id="practice">
  <h2>Professional experience</h2>
{fix_links(read('pages/experience.html'), d).rstrip()}
</section>

<section id="contact">
  <h2>Contact</h2>
  <p>Email: <a href="mailto:smanti@uoregon.edu">smanti@uoregon.edu</a> or <a href="mailto:sma2263@columbia.edu">sma2263@columbia.edu</a><br>
  <a href="{LINKS['orcid']}" {EXT}>ORCID</a> · <a href="{LINKS['scholar']}" {EXT}>Google Scholar</a> · <a href="{LINKS['sojc']}" {EXT}>SOJC profile</a> · <a href="{u(CV, d)}" {EXT}>CV (PDF)</a></p>
  {social(d)}
</section>

</main>
""" + footer(d)
    write("/", home)

    # Research
    d = 1
    page = head(f"Research | {NAME}", "Research by Stephen Mante Anti on news framing, stigma, and help-seeking for mental illness in Ghana, with publications and conference presentations.", "/research/", d) + nav("/research/", d, has_posts) + pagehead(
        "Research", "How news media frame mental illness, and how those frames move audiences toward or away from seeking help.") + f"""
<main class="page">
{fix_links(read('pages/research.html'), d).rstrip()}

<section id="publications">
  <h2>Publications and presentations</h2>
{fix_links(read('pages/publications.html'), d).rstrip()}
</section>
</main>
""" + footer(d)
    write("/research/", page)

    # Teaching
    page = head(f"Teaching | {NAME}", "Courses taught by Stephen Mante Anti at the University of Oregon and Jayee University College, Accra.", "/teaching/", d) + nav("/teaching/", d, has_posts) + pagehead(
        "Teaching") + f"""
<main class="page">
{fix_links(read('pages/teaching.html'), d).rstrip()}
</main>
""" + footer(d)
    write("/teaching/", page)

    # Work
    sections = work["sections"]
    filters = ['<button type="button" class="on" data-show="all" aria-pressed="true">All</button>'] + [
        f'<button type="button" data-show="{s["id"]}" aria-pressed="false">{esc(s["title"])}</button>' for s in sections]
    body = []
    for s in sections:
        cols = " two" if s.get("columns") == 2 else ""
        more = f'\n  <p class="more">{s["more"]}</p>' if s.get("more") else ""
        body.append(f"""<section class="work-group" id="{s['id']}">
  <h2>{esc(s['title'])}</h2>
  <p class="note">{s.get('note', '')}</p>
  <div class="grid{cols}">
    {(chr(10) + '    ').join(card(it, d) for it in s['items'])}
  </div>{more}
</section>""")
    page = head(f"Work | {NAME}", "Selected work by Stephen Mante Anti: interactive maps, data stories, and broadcast journalism from Ghana and the United States.", "/work/", d) + nav("/work/", d, has_posts) + pagehead(
        "Work", "Data stories, interactive maps, and more than a decade of broadcast journalism.") + f"""
<main class="page">
  {featured(work['featured'], d)}
  <div class="filters" role="group" aria-label="Show work by type">
    {' '.join(filters)}
  </div>
{chr(10).join(body)}
</main>
""" + footer(d)
    write("/work/", page)

    # Blog
    if has_posts:
        page = head(f"Blog | {NAME}", "Essays and notes by Stephen Mante Anti on health communication, journalism, data, and Ghana.", "/blog/", d) + nav("/blog/", d, has_posts) + pagehead(
            "Blog", "Essays, notes, and commentary.") + f"""
<main class="page">
  {post_list(posts, d)}
  <p class="feed"><a href="{SITE}/blog/feed.xml">Subscribe by RSS</a></p>
</main>
""" + footer(d)
        write("/blog/", page)
        for i, p in enumerate(posts):
            d = 2
            newer = posts[i - 1] if i > 0 else None
            older = posts[i + 1] if i + 1 < len(posts) else None
            pn = ""
            if newer or older:
                pn = '<nav class="prevnext">' + (
                    f'<a class="older" href="{u(older["path"], d)}"><span>Older</span>{esc(older["title"])}</a>' if older else "<span></span>") + (
                    f'<a class="newer" href="{u(newer["path"], d)}"><span>Newer</span>{esc(newer["title"])}</a>' if newer else "") + "</nav>"
            share_url = SITE + p["path"]
            from urllib.parse import quote
            share = (f'<a href="https://www.linkedin.com/sharing/share-offsite/?url={quote(share_url, safe="")}" {EXT}>LinkedIn</a> · '
                     f'<a href="https://x.com/intent/post?url={quote(share_url, safe="")}&amp;text={quote(p["title"])}" {EXT}>X</a> · '
                     f'<a href="mailto:?subject={quote(p["title"])}&amp;body={quote(share_url, safe="")}">Email</a>')
            tags = "".join(f'<span class="tag">{esc(t)}</span>' for t in p["tags"])
            ld = ('<script type="application/ld+json">{"@context":"https://schema.org","@type":"BlogPosting",'
                  f'"headline":{yaml_json(p["title"])},"datePublished":"{p["date"].isoformat()}",'
                  f'"author":{{"@type":"Person","name":"{NAME}","url":"{SITE}/"}},"url":"{share_url}"}}</script>\n')
            body_html = fix_links(p["html"], d)
            page = head(f"{p['title']} | {NAME}", p["summary"] or DESC, p["path"], d, image=p["image"] or "images/portrait.jpg", kind="article", extra=ld) + nav("/blog/", d, has_posts) + f"""
<main class="page">
<article class="post">
  <p class="meta"><a href="{u('/blog/', d)}">Blog</a> · {nice_date(p['date'])} · {p['minutes']} min read</p>
  <h1>{esc(p['title'])}</h1>
  {f'<p class="standfirst">{esc(p["summary"])}</p>' if p['summary'] else ''}
  <div class="byline"><img src="{u('/images/portrait.jpg', d)}" alt=""><span>{NAME}</span></div>
  <div class="body">
{body_html}
  </div>
  <footer class="post-foot">
    <p class="tags">{tags}</p>
    <p class="share">Share: {share}</p>
  </footer>
  {pn}
</article>
</main>
""" + footer(d)
            write(p["path"], page)
        write("/blog/feed.xml", feed(posts))
    elif not PREVIEW:
        shutil.rmtree(os.path.join(OUT, "blog"), ignore_errors=True)

    if not PREVIEW:
        write("/sitemap.xml", sitemap(posts))
        open(os.path.join(OUT, ".nojekyll"), "w").close()

    # assets
    os.makedirs(os.path.join(OUT, "assets"), exist_ok=True)
    for fn in ("site.css", "site.js"):
        shutil.copy(os.path.join(SRC, "assets", fn), os.path.join(OUT, "assets", fn))
    return posts


def yaml_json(s):
    import json
    return json.dumps(s, ensure_ascii=False)


def feed(posts):
    items = []
    for p in posts[:20]:
        when = dt.datetime.combine(p["date"], dt.time(12), tzinfo=dt.timezone.utc)
        items.append(f"""  <item>
    <title>{esc(p['title'])}</title>
    <link>{SITE}{p['path']}</link>
    <guid>{SITE}{p['path']}</guid>
    <pubDate>{format_datetime(when)}</pubDate>
    <description>{esc(p['summary'])}</description>
  </item>""")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>{NAME}: Blog</title>
  <link>{SITE}/blog/</link>
  <description>Essays and notes by {NAME}.</description>
{chr(10).join(items)}
</channel>
</rss>
"""


def sitemap(posts):
    today = dt.date.today().isoformat()
    urls = [("/", "1.0"), ("/research/", "0.9"), ("/work/", "0.9"), ("/teaching/", "0.8")]
    if posts:
        urls.append(("/blog/", "0.8"))
        urls += [(p["path"], "0.7") for p in posts]
    urls += [("/nj-schools/", "0.8"), (CV, "0.7")]
    urls += [(p, "0.4") for p in ("/fancy/", "/brooklyn/", "/yam/", "/scrolly/")]
    rows = "\n".join(f"  <url><loc>{SITE}{p}</loc><lastmod>{today}</lastmod><priority>{pr}</priority></url>" for p, pr in urls)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{rows}
</urlset>
"""


if __name__ == "__main__":
    posts = build()
    print("Built %d blog post(s) into %s" % (len(posts), OUT))
