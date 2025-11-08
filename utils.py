import os, pathlib, datetime, hashlib, requests, re
from slugify import slugify
from urllib.parse import urlparse
from markdown import markdown

def ensure_dir(path: str):
    pathlib.Path(path).mkdir(parents=True, exist_ok=True)

def to_slug(s: str) -> str:
    return slugify(s or "", lowercase=True)

def iso8601(dt):
    if isinstance(dt, (int, float)):
        return datetime.datetime.utcfromtimestamp(dt).isoformat() + "Z"
    if isinstance(dt, datetime.datetime):
        if dt.tzinfo is None:
            return dt.isoformat() + "Z"
        return dt.astimezone(datetime.timezone.utc).isoformat()
    return str(dt)

def hash_str(s: str) -> str:
    return hashlib.sha1((s or "").encode("utf-8")).hexdigest()[:10]

def download_image(url: str, dest_folder: str) -> str:
    if not url:
        return ""
    try:
        ensure_dir(dest_folder)
        name = hash_str(url) + os.path.splitext(urlparse(url).path)[-1]
        dest = os.path.join(dest_folder, name)
        if not os.path.exists(dest):
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            with open(dest, "wb") as f:
                f.write(r.content)
        return name
    except Exception:
        return ""

def md_to_html(md_text: str) -> str:
    return markdown(md_text or "", extensions=['extra','sane_lists','smarty'])
