"""Rewrites the Featured Projects table in README.md.

Ordering comes from the curated project list maintained in the portfolio
repo (dbishal13.github.io/assets/projects-curated.json) — flagship tier
first, then shipped — so featuring is a deliberate editorial choice, not
whatever repo happened to get pushed to most recently. Private ("working"
tier) entries are never shown here.

Any public, non-fork, non-archived, described repo not yet added to the
curated list is appended after the curated rows (most-recently-pushed
first) as a self-healing fallback, so brand-new repos aren't invisible
while waiting to be curated.
"""

import json
import os
import re
import urllib.request

USERNAME = "DBishal13"
EXCLUDE = {"dbishal13", "dbishal13.github.io", "pywmp_documentation"}
COUNT = 6
DESC_MAX_LEN = 200
README_PATH = "README.md"
START_MARKER = "<!-- FEATURED-PROJECTS:START -->"
END_MARKER = "<!-- FEATURED-PROJECTS:END -->"
CURATED_URL = (
    "https://raw.githubusercontent.com/DBishal13/dbishal13.github.io/"
    "main/assets/projects-curated.json"
)
TIER_ORDER = {"flagship": 0, "shipped": 1}


def fetch_json(url):
    request = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request) as response:
        return json.load(response)


def fetch_repos():
    return fetch_json(f"https://api.github.com/users/{USERNAME}/repos?per_page=100&sort=pushed")


def fetch_curated():
    try:
        data = fetch_json(CURATED_URL)
    except Exception:
        return []
    return [
        p for p in data.get("projects", [])
        if p.get("visibility") == "public" and p.get("tier") in TIER_ORDER
    ]


def truncate(text, max_len):
    text = text.strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


def build_table(curated, repos):
    rows = ["| Project | Description |", "|---|---|"]

    curated_sorted = sorted(curated, key=lambda p: TIER_ORDER[p["tier"]])[:COUNT]
    curated_names = {
        (p.get("repo", "").split("/")[-1] or p["name"]).lower() for p in curated_sorted
    }
    for p in curated_sorted:
        repo_slug = p.get("repo", "")
        url = f"https://github.com/{repo_slug}" if repo_slug else ""
        description = truncate(p["description"].replace("|", "-"), DESC_MAX_LEN)
        rows.append(f"| [**{p['name']}**]({url}) | {description} |")

    picked = 0
    for repo in repos:
        if picked >= max(0, COUNT - len(curated_sorted)):
            break
        if repo["fork"] or repo["archived"] or repo["name"].lower() in EXCLUDE:
            continue
        if repo["name"].lower() in curated_names:
            continue
        if not repo["description"]:
            continue
        description = truncate(repo["description"].replace("|", "-"), DESC_MAX_LEN)
        rows.append(f"| [**{repo['name']}**]({repo['html_url']}) | {description} |")
        picked += 1

    return "\n".join(rows)


def main():
    with open(README_PATH, encoding="utf-8") as f:
        content = f.read()

    pattern = re.compile(re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER), re.DOTALL)
    if not pattern.search(content):
        raise SystemExit(f"Markers {START_MARKER} / {END_MARKER} not found in {README_PATH}")

    table = build_table(fetch_curated(), fetch_repos())
    new_content = pattern.sub(f"{START_MARKER}\n{table}\n{END_MARKER}", content)

    if new_content == content:
        print("No changes")
        return

    with open(README_PATH, "w", encoding="utf-8", newline="\n") as f:
        f.write(new_content)
    print("README.md updated")


if __name__ == "__main__":
    main()
