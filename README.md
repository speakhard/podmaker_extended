# Podmaker — Multi-Podcast Static Site Generator (Flask + Jinja)

Self-hosted Podpage-alike. Reads one or more podcast RSS feeds and generates static websites per show.

## Quickstart
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python build.py
python app.py  # http://localhost:5050
```

## Extensions Included
- **Analytics**: Plausible or custom head HTML (`analytics:` in `config/shows.yaml`).
- **Reviews**: Drop JSON at `data/reviews/<slug>.json` (list of `{date,rating,author,title,text,link}`) → renders **/reviews/**.
- **Transcripts**: If your feed includes Podcasting 2.0 `<podcast:transcript>`, it's linked on episodes. Manual transcripts: place HTML at `content/transcripts/<slug>/<episode-slug>.html` and link from show notes.
- **Blog/News**: Markdown under `content/posts/<slug>/*.md` with optional front matter → renders **/blog/** and per-post pages.
- **CNAME**: If `domain` is set, writes a `CNAME` file for custom domains on GitHub Pages/Netlify.

## Hosting Options (Which one and why)

### 1) GitHub Actions + GitHub Pages
**What it is:** CI builds your site on each push and publishes to Pages for free.  
**Pros:** Free, versioned, automated. Great for multi-site monorepos.  
**Cons:** Custom build matrix is DIY; no server-side forms.  
**How:** This repo includes `.github/workflows/build.yml`. Pages serves the `public/` folder it uploads.

### 2) Netlify
**What it is:** Static host with CI, previews, CDN, and form handling.  
**Pros:** Fast global CDN, branch previews, simple Forms (no backend), redirects, environment vars.  
**Cons:** Paid tiers for heavy usage or teams.  
**How:** Set build command `python build.py`, publish dir `public/`. Optional `netlify.toml` for headers/redirects.

### 3) Cloudflare Pages
**What it is:** Cloudflare’s static hosting with global edge CDN.  
**Pros:** Excellent caching, cheap/free bandwidth, easy custom domains, great for multiple subdomains.  
**Cons:** Fewer niceties than Netlify Forms (unless you add Workers).  
**How:** Configure build command `python build.py`, output `public/` in the Pages dashboard.

### 4) Bluehost (or cPanel shared hosting)
**What it is:** Traditional hosting. Upload files via FTP/SFTP.  
**Pros:** Familiar, works with existing domains/email.  
**Cons:** No CI by default, manual deploys, less edge caching.  
**How:** Build locally, upload `public/<slug>/` to your web root or subdirectory; repeat per show.

## Multi-Show
Add entries to `config/shows.yaml`. Each show builds to `public/<slug>/`. Map a domain/subdomain per folder (GitHub Pages with custom domains via `CNAME`, Netlify sites, or Cloudflare Pages projects).

## Reviews Sources
There’s no official Apple reviews API. Copy/export into JSON locally (same fields as above). If using Podchaser’s API, write a small script to output the same JSON format.

## Customization
- Add analytics or extra tags in `analytics.custom_head_html`.
- Modify `templates/*.html` and `static/styles.css` for theme tweaks.
- Add pages by creating templates and rendering them in `build.py`.
