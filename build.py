#!/usr/bin/env python3
"""Regenerate index.html from template.html using the current public gists of GITHUB_USER."""
import json, os, sys, urllib.request

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

if "--md" in sys.argv:  # markdown is only built on request; the workflow doesn't pass this
    def slug(t):
        return "".join(c if c.isalnum() else "-" for c in t.lower()).strip("-")

    md = ["# HOL 2026 - Code Snippets", "",
          "Copy-and-paste snippets for the hands-on lab, collected from the gists in one place.", "",
          "## Contents", ""]
    for g in data:
        md.append(f"- [{g['group']}](#{slug(g['group'])})")
        md += [f"  - [`{f['name']}`](#{slug(f['name'])})" for f in g["files"]]
    md += ["", "---", ""]
    for g in data:
        md += [f'## <a id="{slug(g["group"])}"></a>{g["group"]}', ""]
        for f in g["files"]:
            lang = "yaml" if f["name"].endswith((".yml", ".yaml")) else "sql"
            md += [f'### <a id="{slug(f["name"])}"></a>`{f["name"]}`', "",
                   f"```{lang}", f["content"].rstrip("\n"), "```", ""]
        md += ["---", ""]
    open("code-snippets.md", "w").write("\n".join(md))
print(f"Wrote index.html{' and code-snippets.md' if '--md' in sys.argv else ''} with {len(files)} files")
