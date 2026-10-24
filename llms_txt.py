"""Write docs/llms.txt: the site's index for language models (https://llmstxt.org).

The file is generated, never committed, from the same two things the site is
built from: the nav in zensical.toml and each page's front matter. So it stays
correct as pages come and go, with no list of its own to keep in step. It runs
after sync_docs.py (the docs section and its descriptions) and main.py (the blog
nav), and before the build, which copies it to /llms.txt.

The shape, in the format's order:

    # CodeCrew
    > SUMMARY
    DETAILS
    ## Start here       the nav's top-level pages, the homepage first
    ## <group>          one section per nav group, in nav order
    ## Source           SPEC.md, CLI.md and the repository, at source on GitHub
    ## Optional         the groups in OPTIONAL_GROUPS (the blog)

A page joins the file by joining the nav: a new top-level page lands under
"Start here", and a new nav group (the introductory pages, say) becomes a
section of its own, in nav order. Each link is the page's canonical URL, its
front-matter title or else its nav label, and its front-matter description.
"""

import json
import re
import tomllib
from pathlib import Path

CONFIG = Path("zensical.toml")
DOCS_ROOT = Path("docs")  # the site's docs_dir
OUT = DOCS_ROOT / "llms.txt"

HUB = "https://github.com/radiusred/gh-codecrew"
SUMMARY = (
    "CodeCrew is a protocol and a GitHub CLI extension (`gh codecrew`) for software "
    "delivery with AI coding agents on GitHub. Each agent can work under a GitHub App "
    "identity of its own, so different harnesses and models can build and review each "
    "other's work, and the plan, the decisions, the reviews and the verdicts are kept "
    "in GitHub issues and pull requests."
)
DETAILS = (
    "CodeCrew does not run agents. You, or an orchestration platform, start each agent "
    "session; CodeCrew gives it a role contract to work under, an identity to act as, "
    "and gates that its CLI enforces by refusing a command until the gate is met. It "
    "runs solo on one person's GitHub login, or with a separate identity for each role. "
    "It is open source under the Apache 2.0 licence."
)
START_SECTION = "Start here"
OPTIONAL_GROUPS = ("Blog",)
SOURCE_LINKS = (
    ("SPEC.md", f"{HUB}/blob/main/SPEC.md", "The CodeCrew protocol specification, at source."),
    ("CLI.md", f"{HUB}/blob/main/CLI.md", "The reference for every gh codecrew command, at source."),
    ("radiusred/gh-codecrew", HUB, "The repository: the CLI's code, its releases, and its issues."),
)

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def front_matter(page):
    """The plain `key: value` lines of a page's front matter, quotes removed. A
    JSON-quoted value (what sync_docs.py writes) is decoded as JSON."""
    try:
        text = page.read_text(encoding="utf-8")
    except OSError:
        return {}
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}
    data = {}
    for line in match.group(1).splitlines():
        key, sep, value = line.partition(":")
        if not sep or line[:1].isspace():
            continue
        value = value.strip()
        if value.startswith('"'):
            try:
                value = json.loads(value)
            except ValueError:
                value = value.strip('"')
        else:
            value = value.strip("'")
        data[key.strip()] = value
    return data


def page_url(site_url, target):
    """The canonical URL Zensical gives the page built from `target`."""
    path = target.removesuffix(".md")
    if path == "index" or path.endswith("/index"):
        path = path.removesuffix("index")
    else:
        path += "/"
    return site_url + path


def link(site_url, label, target):
    meta = front_matter(DOCS_ROOT / target)
    title = meta.get("title") or label
    line = f"- [{title}]({page_url(site_url, target)})"
    description = meta.get("description")
    return f"{line}: {description}" if description else line


def sections(config):
    """[(section title, [link lines])] from the nav, in the file's order."""
    project = config.get("project", config)
    site_url = project["site_url"].rstrip("/") + "/"
    start, groups, optional = [], [], []

    def pages(entries):
        for entry in entries:
            for label, target in entry.items():
                if isinstance(target, list):
                    yield from pages(target)
                else:
                    yield label, target

    for entry in project.get("nav", []):
        for label, target in entry.items():
            if isinstance(target, list):
                lines = [link(site_url, *page) for page in pages(target)]
                (optional if label in OPTIONAL_GROUPS else groups).append((label, lines))
            else:
                start.append(link(site_url, label, target))

    source = [f"- [{title}]({url}): {about}" for title, url, about in SOURCE_LINKS]
    out = [(START_SECTION, start)] + groups + [("Source", source)]
    if optional:
        out.append(("Optional", [line for _, lines in optional for line in lines]))
    return out


def render(config):
    parts = ["# CodeCrew", "", f"> {SUMMARY}", "", DETAILS, ""]
    for title, lines in sections(config):
        if lines:
            parts += [f"## {title}", "", *lines, ""]
    return "\n".join(parts)


def main():
    with open(CONFIG, "rb") as f:
        config = tomllib.load(f)
    OUT.write_text(render(config), encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
