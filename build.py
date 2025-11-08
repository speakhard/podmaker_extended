import os, sys, time, shutil, yaml, feedparser, datetime, glob, json, re
from jinja2 import Environment, FileSystemLoader, select_autoescape
from utils import ensure_dir, to_slug, iso8601, download_image, md_to_html

BASE_DIR = os.path.dirname(__file__)
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")
PUBLIC_DIR = os.path.join(BASE_DIR, "public")

env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(["html", "xml"]),
    trim_blocks=True,
    lstrip_blocks=True,
)
env.globals["now"] = lambda: datetime.datetime.utcnow()
env.filters["date"] = lambda dt, fmt="%b %d, %Y": datetime.datetime.fromtimestamp(dt).strftime(fmt) if isinstance(dt, (int, float)) else str(dt)

def parse_feed(url):
    fp = feedparser.parse(url)
    return fp

def render(template, context, out_path):
    html = env.get_template(template).render(**context)
    ensure_dir(os.path.dirname(out_path))
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

def copy_static(dest):
    shutil.copytree(STATIC_DIR, os.path.join(dest, "static"), dirs_exist_ok=True)

def load_reviews(slug):
    path = os.path.join(BASE_DIR, "data", "reviews", f"{slug}.json")
    if os.path.exists(path):
        try:
            with open(path,"r",encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception:
            return []
    return []

def load_posts(slug):
    posts_root = os.path.join(BASE_DIR, "content", "posts", slug)
    items = []
    if os.path.isdir(posts_root):
        for p in sorted(glob.glob(os.path.join(posts_root, "*.md")), reverse=True):
            with open(p, "r", encoding="utf-8") as f:
                raw = f.read()
            title = os.path.splitext(os.path.basename(p))[0].replace("-", " ").title()
            date_display = ""
            m = re.match(r"^---\n(.*?)\n---\n(.*)$", raw, flags=re.S)
            body = raw
            if m:
                fm, body = m.groups()
                for line in fm.splitlines():
                    if ":" in line:
                        k,v = line.split(":",1)
                        k=k.strip().lower(); v=v.strip()
                        if k=="title": title=v
                        if k=="date": date_display=v
            html = md_to_html(body)
            excerpt = re.sub("<[^<]+?>","", html)[:180] + ("…" if len(html)>180 else "")
            items.append({
                "slug": to_slug(os.path.splitext(os.path.basename(p))[0]),
                "title": title, "html": html, "date_display": date_display, "excerpt": excerpt
            })
    return items

def build_show(show, out_root):
    print(f"==> Building {show.get('title')}")
    fp = parse_feed(show["feed"])

    site = {
        "title": show.get("title") or fp.feed.get("title", "Podcast"),
        "tagline": show.get("description") or fp.feed.get("subtitle") or fp.feed.get("description", ""),
        "link": show.get("domain") or fp.feed.get("link", ""),
        "color": show.get("color") or "#111827",
        "subscribe": show.get("subscribe", {}),
        "social": show.get("social", {}),
        "image": "",
        "analytics_head": ""
    }

    # Artwork
    img_url = ""
    if hasattr(fp.feed, "image"):
        img = getattr(fp.feed, "image")
        if isinstance(img, dict):
            img_url = img.get("href","")
    img_url = show.get("image") or img_url
    images_dir = os.path.join(out_root, "images")
    if img_url:
        saved = download_image(img_url, images_dir)
        site["image"] = f"/images/{saved}" if saved else ""

    # Analytics
    analytics = show.get("analytics", {}) or {}
    if analytics.get("plausible_domain"):
        dom = analytics["plausible_domain"]
        site["analytics_head"] += f'<script defer data-domain="{dom}" src="https://plausible.io/js/script.js"></script>\n'
    site["analytics_head"] += analytics.get("custom_head_html","")

    # CNAME for custom domains
    if show.get("domain"):
        ensure_dir(out_root)
        with open(os.path.join(out_root, "CNAME"), "w") as f:
            f.write(show["domain"].strip())

    # Episodes
    episodes = []
    for e in fp.entries:
        published = None
        if hasattr(e, "published_parsed") and e.published_parsed:
            published = time.mktime(e.published_parsed)
        elif hasattr(e, "updated_parsed") and e.updated_parsed:
            published = time.mktime(e.updated_parsed)
        else:
            published = time.time()

        audio_url = ""
        if hasattr(e, "enclosures") and e.enclosures:
            audio_url = e.enclosures[0].get("url", "")
        elif hasattr(e, "links"):
            for L in e.links:
                if L.get("type", "").startswith("audio"):
                    audio_url = L.get("href", "")
                    break

        ep = {
            "id": e.get("id") or e.get("guid") or e.get("link") or str(published),
            "title": e.get("title", "Untitled Episode"),
            "link": e.get("link", ""),
            "published": published,
            "summary": e.get("summary", ""),
            "content": (getattr(e, "content", [{}])[0].get("value", "") if hasattr(e, "content") else e.get("summary", "")),
            "audio": audio_url,
            "slug": to_slug(e.get("title") or str(published)),
            "transcript_url": getattr(e, "podcast_transcript", None) or ""
        }
        episodes.append(ep)

    episodes.sort(key=lambda x: x["published"], reverse=True)

    # Reviews + posts
    slug = show.get("slug") or to_slug(site["title"])
    reviews = load_reviews(slug)
    posts = load_posts(slug)

    context = {
        "site": site,
        "episodes": episodes,
        "show": show,
        "build_time": datetime.datetime.utcnow(),
    }

    copy_static(out_root)

    render("home.html", context, os.path.join(out_root, "index.html"))
    render("about.html", context, os.path.join(out_root, "about", "index.html"))
    render("reviews.html", {**context, "reviews": reviews}, os.path.join(out_root, "reviews", "index.html"))
    render("blog/index.html", {**context, "posts": posts}, os.path.join(out_root, "blog", "index.html"))
    for ep in episodes:
        render("episode.html", {**context, "ep": ep}, os.path.join(out_root, "episodes", ep["slug"], "index.html"))
    for p in posts:
        render("blog/post.html", {**context, "post": p}, os.path.join(out_root, "blog", p["slug"], "index.html"))

    render("sitemap.xml", context, os.path.join(out_root, "sitemap.xml"))
    with open(os.path.join(out_root, "robots.txt"), "w") as f:
        f.write("User-agent: *\nAllow: /\n")

def main():
    with open(os.path.join(BASE_DIR, "config", "shows.yaml"), "r") as f:
        config = yaml.safe_load(f)
    ensure_dir(PUBLIC_DIR)
    for show in config.get("shows", []):
        slug = show.get("slug") or to_slug(show.get("title") or "podcast")
        out_root = os.path.join(PUBLIC_DIR, slug)
        build_show(show, out_root)
    print(f"\nAll done. Static sites generated in: {PUBLIC_DIR}")

if __name__ == "__main__":
    main()
