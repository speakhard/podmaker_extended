import os, datetime
from flask import Flask, send_from_directory
from jinja2 import Environment, FileSystemLoader, select_autoescape

BASE_DIR = os.path.dirname(__file__)
PUBLIC_DIR = os.path.join(BASE_DIR, "public")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

app = Flask(__name__, static_folder=None)
env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(["html", "xml"]),
    trim_blocks=True,
    lstrip_blocks=True,
)
env.globals["now"] = lambda: datetime.datetime.utcnow()

@app.route("/")
def root():
    entries = []
    if os.path.isdir(PUBLIC_DIR):
        for name in sorted(os.listdir(PUBLIC_DIR)):
            path = os.path.join(PUBLIC_DIR, name)
            if os.path.isdir(path):
                entries.append({"slug": name, "url": f"/site/{name}/"})
    return env.get_template("portal.html").render(sites=entries)

@app.route("/site/<slug>/")
@app.route("/site/<slug>/<path:path>")
def serve_site(slug, path="index.html"):
    site_root = os.path.join(PUBLIC_DIR, slug)
    full = os.path.join(site_root, path)
    if os.path.isdir(full):
        full = os.path.join(full, "index.html")
    rel_dir = os.path.dirname(os.path.relpath(full, site_root))
    return send_from_directory(os.path.join(site_root, rel_dir), os.path.basename(full))

@app.route("/static/<path:path>")
def static_files(path):
    return send_from_directory(os.path.join(BASE_DIR, "static"), path)

@app.route("/healthz")
def health():
    return {"ok": True}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)
