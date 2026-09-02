"""Sync reference documentation from radiusred/gh-codecrew into docs/docs/.

Copies, from the upstream repo:
  README.md       -> docs/docs/index.md
  SPEC.md         -> docs/docs/spec.md
  CHANGELOG.md    -> docs/docs/changelog.md
  ROADMAP.md      -> docs/docs/roadmap.md
  CONTRIBUTING.md -> docs/docs/contributing.md
  SECURITY.md     -> docs/docs/security.md
  docs/**         -> docs/docs/**                (subtree preserved)

`exclude` paths (relative to the upstream docs/ dir, e.g. "milestones/")
are left out. Links into an excluded path are rewritten to GitHub URLs,
like any other non-synced file.

Markdown links and HTML <img src> in synced .md files are rewritten so:
  - links to other synced files resolve correctly under docs/docs/
  - links to non-synced files become absolute GitHub URLs (blob/ or raw/)
  - external URLs and in-page anchors are left alone

The Docs nav block in zensical.toml (between BEGIN_DOCS_NAV/END_DOCS_NAV)
is regenerated: Overview first, then pages in `order`, then the remaining
docs/ pages alphabetically, then the root reference files.

Source location resolution:
  Locally the upstream repo lives at ../gh-codecrew. CI checks it out under
  $SYNC_SOURCE_BASE/gh-codecrew. The env var overrides the default base.

Idempotent: the destination is wiped before re-sync.
"""

import os
import posixpath
import re
import shutil
from pathlib import Path

PROJECT = {
    "name": "gh-codecrew",
    "repo": "radiusred/gh-codecrew",
    "branch": "main",
    # Per-milestone records are internal project history, not site material.
    "exclude": ["milestones/"],
    # Reading order for the docs/ pages; anything not listed follows alphabetically.
    "order": [
        "introduction.md",
        "first-milestone.md",
        "identities.md",
        "platform-interop.md",
        "extensions.md",
        "founding-decisions.md",
        "gsd-vs-frontier-orchestration.md",
    ],
}

DEST = Path("docs/docs")
NAV_PREFIX = "docs"
DEFAULT_SOURCE_BASE = Path("..")
CONFIG = Path("zensical.toml")
NAV_BEGIN = "# BEGIN_DOCS_NAV"
NAV_END = "# END_DOCS_NAV"
NAV_INDENT = "    "

# Root-of-repo files promoted into the docs dir, with their nav labels.
# Order here is the order they appear at the end of the nav.
ROOT_FILES = [
    ("README.md", "index.md", "Overview"),
    ("SPEC.md", "spec.md", "Specification"),
    ("CHANGELOG.md", "changelog.md", "Changelog"),
    ("ROADMAP.md", "roadmap.md", "Roadmap"),
    ("CONTRIBUTING.md", "contributing.md", "Contributing"),
    ("SECURITY.md", "security.md", "Security"),
]
ROOT_FILE_MAP = {src: dest for src, dest, _ in ROOT_FILES}
ROOT_DEST_NAMES = set(ROOT_FILE_MAP.values())

# Image extensions get rewritten to raw.githubusercontent.com so they render.
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico"}

# Markdown link/image:  ![alt](url "title")  or  [text](url "title")
MD_LINK_RE = re.compile(r'(!?)\[([^\]]*)\]\(([^)\s]+)(\s+"[^"]*")?\)')
# HTML <img src="...">. Matches single or double quotes.
HTML_IMG_RE = re.compile(r'(<img\b[^>]*?\bsrc=)(["\'])([^"\']+)\2', re.IGNORECASE)


def source_for(project):
    base = Path(os.environ.get("SYNC_SOURCE_BASE", DEFAULT_SOURCE_BASE))
    return base / project["name"]


def is_external(url):
    return bool(re.match(r'^[a-z][a-z0-9+\-.]*://|^mailto:|^#', url, re.IGNORECASE))


def split_anchor(path):
    """Split 'foo.md#section' into ('foo.md', '#section')."""
    if "#" in path:
        p, _, frag = path.partition("#")
        return p, "#" + frag
    return path, ""


def is_excluded(docs_rel, project):
    """True if `docs_rel` (relative to the upstream docs/ dir) falls under one
    of the project's `exclude` entries. A trailing slash marks a subtree."""
    for pattern in project.get("exclude", ()):
        prefix = pattern.rstrip("/")
        if docs_rel == prefix or docs_rel.startswith(prefix + "/"):
            return True
    return False


def map_to_dest(repo_path, project):
    """Map a repo-root-relative path to (dest_relpath_or_None, repo_path).

    dest_relpath is relative to DEST (e.g. 'index.md', 'foo.md', 'sub/bar.md').
    When None, the path doesn't sync; the caller emits a GitHub URL instead.
    """
    if repo_path in ROOT_FILE_MAP:
        return ROOT_FILE_MAP[repo_path], repo_path
    if repo_path.startswith("docs/"):
        docs_rel = repo_path[len("docs/"):]
        if is_excluded(docs_rel, project):
            return None, repo_path
        return docs_rel, repo_path
    return None, repo_path


def github_url(repo_path, project, is_image):
    repo, branch = project["repo"], project["branch"]
    ext = posixpath.splitext(repo_path.split("#", 1)[0])[1].lower()
    if is_image or ext in IMAGE_EXTS:
        return f"https://raw.githubusercontent.com/{repo}/{branch}/{repo_path}"
    return f"https://github.com/{repo}/blob/{branch}/{repo_path}"


def rewrite_target(url, source_repo_path, project, is_image):
    """Rewrite a single link/image target. `source_repo_path` is the original
    file's location in the upstream repo (used to resolve relative paths)."""
    if is_external(url):
        return url
    path, anchor = split_anchor(url)
    if not path:
        return url

    source_dir = posixpath.dirname(source_repo_path)
    resolved = posixpath.normpath(posixpath.join(source_dir, path)) if source_dir else posixpath.normpath(path)
    if resolved.startswith("../") or resolved == "..":
        return url

    dest_relpath, repo_path = map_to_dest(resolved, project)
    if dest_relpath is None:
        return github_url(repo_path, project, is_image) + anchor

    source_dest, _ = map_to_dest(source_repo_path, project)
    source_dest_dir = posixpath.dirname(source_dest) if source_dest else ""
    rel = posixpath.relpath(dest_relpath, source_dest_dir or ".")
    return rel + anchor


def rewrite_links(content, source_repo_path, project):
    def md_replace(m):
        bang, text, url, title = m.group(1), m.group(2), m.group(3), m.group(4) or ""
        new_url = rewrite_target(url, source_repo_path, project, is_image=(bang == "!"))
        return f"{bang}[{text}]({new_url}{title})"

    def html_replace(m):
        prefix, quote, url = m.group(1), m.group(2), m.group(3)
        new_url = rewrite_target(url, source_repo_path, project, is_image=True)
        return f"{prefix}{quote}{new_url}{quote}"

    content = MD_LINK_RE.sub(md_replace, content)
    content = HTML_IMG_RE.sub(html_replace, content)
    return content


FRONTMATTER_RE = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)
H1_RE = re.compile(r'^#\s+(.+?)\s*$', re.MULTILINE)
HTML_COMMENT_RE = re.compile(r'<!--.*?-->', re.DOTALL)


def humanize(stem):
    return stem.replace("_", " ").replace("-", " ").strip().title()


def extract_title(md_path, default):
    """Return a title from frontmatter, first H1, or a humanized filename."""
    try:
        content = md_path.read_text(encoding="utf-8")
    except OSError:
        return default

    m = FRONTMATTER_RE.match(content)
    if m:
        for line in m.group(1).split("\n"):
            if ":" in line:
                key, _, value = line.partition(":")
                if key.strip() == "title":
                    return value.strip().strip('"\'')
        content = content[m.end():]

    h1 = H1_RE.search(content)
    if h1:
        title = HTML_COMMENT_RE.sub("", h1.group(1)).strip()
        if title:
            return title

    return default


def nav_entries(project, dest):
    """Build [(label, target)] for the Docs nav.

    Order: Overview, then `order` pages, then remaining docs/ pages
    alphabetically, then the other root files in ROOT_FILES order."""
    entries = []
    if (dest / "index.md").exists():
        entries.append(("Overview", f"{NAV_PREFIX}/index.md"))

    pages = {}
    for path in sorted(dest.rglob("*.md")):
        rel = path.relative_to(dest).as_posix()
        if rel in ROOT_DEST_NAMES:
            continue
        pages[rel] = (extract_title(path, default=humanize(path.stem)), f"{NAV_PREFIX}/{rel}")

    for rel in project.get("order", ()):
        if rel in pages:
            entries.append(pages.pop(rel))
    entries.extend(pages[rel] for rel in sorted(pages))

    for _, dest_name, label in ROOT_FILES:
        if dest_name != "index.md" and (dest / dest_name).exists():
            entries.append((label, f"{NAV_PREFIX}/{dest_name}"))
    return entries


def write_nav(entries):
    """Rewrite the BEGIN_DOCS_NAV/END_DOCS_NAV block in zensical.toml."""
    lines = [f"{NAV_INDENT}{NAV_BEGIN}"]
    for label, target in entries:
        safe = label.replace('"', '\\"')
        lines.append(f'{NAV_INDENT}{{ "{safe}" = "{target}" }},')
    lines.append(f"{NAV_INDENT}{NAV_END}")

    text = CONFIG.read_text(encoding="utf-8")
    src_lines = text.split("\n")
    start = end = None
    for i, line in enumerate(src_lines):
        stripped = line.strip()
        if start is None and stripped == NAV_BEGIN:
            start = i
        elif start is not None and stripped == NAV_END:
            end = i
            break
    if start is None or end is None:
        raise RuntimeError(f"Could not find {NAV_BEGIN}/{NAV_END} markers in {CONFIG}")
    src_lines[start : end + 1] = lines
    new_text = "\n".join(src_lines)
    if new_text != text:
        CONFIG.write_text(new_text, encoding="utf-8")
        print(f"Updated docs nav with {len(entries)} pages")


def sync(project, dest):
    src = source_for(project)
    if not src.exists():
        raise SystemExit(f"source not found at {src}; set SYNC_SOURCE_BASE or clone it alongside")

    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)

    copied = 0
    for src_name, dest_name in ROOT_FILE_MAP.items():
        src_path = src / src_name
        if src_path.is_file():
            content = rewrite_links(src_path.read_text(encoding="utf-8"), src_name, project)
            (dest / dest_name).write_text(content, encoding="utf-8")
            copied += 1

    docs_src = src / "docs"
    if docs_src.is_dir():
        for path in sorted(docs_src.rglob("*")):
            rel = path.relative_to(docs_src)
            if is_excluded(rel.as_posix(), project):
                continue
            target = dest / rel
            if path.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            if path.suffix == ".md":
                content = rewrite_links(path.read_text(encoding="utf-8"), "docs/" + rel.as_posix(), project)
                target.write_text(content, encoding="utf-8")
            else:
                shutil.copy2(path, target)
            copied += 1

    print(f"  {project['name']}: synced {copied} files into {dest}/")
    return copied


def main():
    sync(PROJECT, DEST)
    write_nav(nav_entries(PROJECT, DEST))


if __name__ == "__main__":
    main()
