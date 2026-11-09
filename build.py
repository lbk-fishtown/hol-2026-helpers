#!/usr/bin/env python3
"""Regenerate index.html from template.html using the current public gists of GITHUB_USER."""
import json, os, urllib.request

USER = "paulandrewfield"
GROUPS = [
    ("Project setup", ["dbt_project.yml", "sources.yml"]),
    ("Staging models", ["stg_nations.sql", "stg_regions.sql"]),
    ("Marts", ["dim_customers.sql", "monthly_sales.sql", "monthly_sales.yml"]),
    ("Tests", ["assert_net_item_sales_amount_positive.sql", "all_models_have_descriptions.sql"]),
]
FALLBACK_GROUP = "Other"  # any file not listed above lands here

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "hol-2026-helpers-build"})
    tok = os.environ.get("GITHUB_TOKEN")
    if tok and "api.github.com" in url:
        req.add_header("Authorization", f"Bearer {tok}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode()

files = {}
for gist in json.loads(get(f"https://api.github.com/users/{USER}/gists?per_page=100")):
    for name, f in gist["files"].items():
        files[name] = {"name": name, "url": gist["html_url"], "content": get(f["raw_url"])}
if not files:
    raise SystemExit("No gists found; refusing to overwrite index.html")

listed = {n for _, ns in GROUPS for n in ns}
groups = [(g, [n for n in ns if n in files]) for g, ns in GROUPS]
groups.append((FALLBACK_GROUP, sorted(n for n in files if n not in listed)))
data = [{"group": g, "files": [files[n] for n in ns]} for g, ns in groups if ns]

js = json.dumps(data).replace("</", "<\\/")
html = open("template.html").read().replace("/*DATA*/[]", js)
open("index.html", "w").write(html)
print(f"Wrote index.html with {len(files)} files")
