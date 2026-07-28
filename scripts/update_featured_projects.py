"""Rewrites the Featured Projects table in README.md from live repo data.

Picks the N most recently-pushed, non-fork repos (excluding this profile
repo and the GitHub Pages site) and replaces the content between the
FEATURED-PROJECTS markers in README.md.
"""

import json
import os
import re
import urllib.request

USERNAME = "DBishal13"
EXCLUDE = {"dbishal13", "dbishal13.github.io"}
COUNT = 6
DESC_MAX_LEN = 200
README_PATH = "README.md"
START_MARKER = "<!-- FEATURED-PROJECTS:START -->"
END_MARKER = "<!-- FEATURED-PROJECTS:END -->"


def fetch_repos():
    url = f"https://api.github.com/users/{USERNAME}/repos?per_page=100&sort=pushed"
    request = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request) as response:
        return json.load(response)


def truncate(text, max_len):
    text = text.strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


def build_table(repos):
    rows = ["| Project | Description |", "|---|---|"]
    picked = 0
    for repo in repos:
        if repo["fork"] or repo["archived"] or repo["name"].lower() in EXCLUDE:
            continue
        if not repo["description"]:
            continue
        description = truncate(repo["description"].replace("|", "-"), DESC_MAX_LEN)
        rows.append(f"| [**{repo['name']}**]({repo['html_url']}) | {description} |")
        picked += 1
        if picked >= COUNT:
            break
    return "\n".join(rows)


def main():
    with open(README_PATH, encoding="utf-8") as f:
        content = f.read()

    pattern = re.compile(re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER), re.DOTALL)
    if not pattern.search(content):
        raise SystemExit(f"Markers {START_MARKER} / {END_MARKER} not found in {README_PATH}")

    table = build_table(fetch_repos())
    new_content = pattern.sub(f"{START_MARKER}\n{table}\n{END_MARKER}", content)

    if new_content == content:
        print("No changes")
        return

    with open(README_PATH, "w", encoding="utf-8", newline="\n") as f:
        f.write(new_content)
    print("README.md updated")


if __name__ == "__main__":
    main()
