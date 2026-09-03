"""Sync radiusred/gh-codecrew's documentation into docs/docs/.

codecrew.works is CodeCrew's own site: the home page carries the product pitch
(the README's argument, in page form) and this sync gives the reference material
a web home beneath it at /docs/. The upstream repo stays the single source of
truth — nothing landed here is committed, the tree is rebuilt from scratch on
every build, and www.radiusred.uk no longer carries a copy of it.

What lands where (repo-root-relative source -> path under docs/docs/):

    docs/introduction.md   -> index.md          (/docs/)
    docs/**                -> **               (/docs/**, milestones included)
    SPEC.md                -> spec.md
    CONTRIBUTING.md        -> contributing.md
    SECURITY.md            -> security.md

README.md does not sync: the home page already is the README's argument, so
links to it resolve to the home page rather than to a second copy. Links to
anything else that did not sync — AGENTS.md, ROADMAP.md, CHANGELOG.md, LICENSE,
roles/, assets/ — become absolute GitHub URLs. External URLs and bare in-page
anchors are left alone.

One page is generated rather than copied: docs/milestones/index.md, so the
upstream's links to the bare `milestones/` directory land somewhere on-site
instead of bouncing to a GitHub tree view, and so the nav section has a landing
page (navigation.indexes is on).

The Docs nav tab is written between the sentinel markers in zensical.toml, the
same way main.py maintains the blog's. When no upstream checkout is on disk the
block is emptied and the destination removed, so a build without one still
succeeds — with no Docs tab and nothing dangling in the nav.

Source location: $SYNC_SOURCE_BASE/gh-codecrew, defaulting to ../gh-codecrew.
CI checks the upstream out under _sources/.
"""

import os
import posixpath
import re
import shutil
from pathlib import Path

NAME = "gh-codecrew"
REPO = "radiusred/gh-codecrew"
BRANCH = "main"

DOCS_ROOT = Path("docs")  # the site's docs_dir
SECTION = "docs"  # the section's URL segment: codecrew.works/docs/
DEST = DOCS_ROOT / SECTION
DEFAULT_SOURCE_BASE = Path("..")
CONFIG = Path("zensical.toml")

NAV_BEGIN = "# BEGIN_DOCS_NAV"
NAV_END = "# END_DOCS_NAV"
NAV_INDENT = "  "  # top-level nav entries in zensical.toml sit at two spaces

# The upstream's docs/ dir becomes the section root, so its introduction — the
# page that calls itself "the map" — becomes the section index.
DOCS_DIR = "docs"
SECTION_INDEX = "docs/introduction.md"
MILESTONES = "milestones"

# Root-of-repo files that sync alongside the docs/ tree.
ROOT_FILE_MAP = {
    "SPEC.md": "spec.md",
    "CONTRIBUTING.md": "contributing.md",
    "SECURITY.md": "security.md",
}
# The README is the exception: the home page already carries it.
HOME_SOURCE = "README.md"
# The home page is the README's argument in page form, not a copy of it, so its
# section ids are its own. README anchors cross over through this table; one it
# does not know is dropped — the link still lands on the home page — and
# reported, rather than left to dangle a --strict build breaks on.
HOME_ANCHORS = {
    "#why-youd-want-a-crew": "",  # the hero is this section
    "#how-it-works-in-four-beats": "#how-it-works",
    "#the-receipts": "#codecrew-works",
    "#start-now": "#start-now",
}

# Image extensions get rewritten to raw.githubusercontent.com so they render.
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico"}

# Markdown link/image:  ![alt](url "title")  or  [text](url "title")
MD_LINK_RE = re.compile(r'(!?)\[([^\]]*)\]\(([^)\s]+)(\s+"[^"]*")?\)')
# HTML <img src="...">. Matches single or double quotes.
HTML_IMG_RE = re.compile(r'(<img\b[^>]*?\bsrc=)(["\'])([^"\']+)\2', re.IGNORECASE)

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
# A title's subtitle: everything after the first ": " or " — ".
SUBTITLE_RE = re.compile(r"\s*(?::|\s—)\s.*$", re.DOTALL)
# The leading number of a milestone record's filename, for ordering.
LEADING_NUMBER_RE = re.compile(r"^(\d+)")

# The section's reading order, which is the order docs/introduction.md itself
# prescribes rather than the alphabetical one. Pages the upstream adds later are
# appended after these, alphabetically, and the trailing pair always comes last.
PAGE_ORDER = (
    "index.md",
    "first-milestone.md",
    "identities.md",
    "extensions.md",
    "platform-interop.md",
    "founding-decisions.md",
    "gsd-vs-frontier-orchestration.md",
    "spec.md",
)
TRAILING_PAGES = (("contributing.md", "Contributing"), ("security.md", "Security"))
# The index's own H1 ("CodeCrew, precisely") titles the page; the tab wants the
# word a reader scans for.
INDEX_LABEL = "Introduction"
MILESTONES_LABEL = "Milestones"

MILESTONES_INDEX = """# Milestones

One record per milestone, compiled at close from the decisions and deviations
recorded while the work happened — the "why", as it was written down at the
time.

"""


def source_dir():
    base = Path(os.environ.get("SYNC_SOURCE_BASE") or DEFAULT_SOURCE_BASE)
    return base / NAME


def is_external(url):
    return bool(re.match(r"^[a-z][a-z0-9+\-.]*://|^mailto:|^#", url, re.IGNORECASE))


def split_anchor(path):
    """Split 'foo.md#section' into ('foo.md', '#section')."""
    if "#" in path:
        p, _, frag = path.partition("#")
        return p, "#" + frag
    return path, ""


def map_to_dest(repo_path):
    """Map a repo-root-relative path to its path under DEST, or None if it
    does not sync (the caller then emits a GitHub URL)."""
    if repo_path in ROOT_FILE_MAP:
        return ROOT_FILE_MAP[repo_path]
    if repo_path == SECTION_INDEX or repo_path == DOCS_DIR:
        return "index.md"
    if repo_path.startswith(DOCS_DIR + "/"):
        rel = repo_path[len(DOCS_DIR) + 1 :]
        # The bare milestones/ directory resolves to the index this sync writes.
        return f"{MILESTONES}/index.md" if rel == MILESTONES else rel
    return None


def github_url(repo_path, is_image):
    ext = posixpath.splitext(repo_path.split("#", 1)[0])[1].lower()
    if is_image or ext in IMAGE_EXTS:
        return f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/{repo_path}"
    return f"https://github.com/{REPO}/blob/{BRANCH}/{repo_path}"


def home_url(source_dest_dir):
    """A relative link from a synced page to the site's home page, which sits
    one level above DEST in the docs tree."""
    depth = len(source_dest_dir.split("/")) if source_dest_dir else 0
    return "../" * (depth + 1) + "index.md"


def home_anchor(anchor, source_repo_path):
    """Translate a README anchor to the home page's, or drop it."""
    if not anchor:
        return ""
    mapped = HOME_ANCHORS.get(anchor)
    if mapped is None:
        print(
            f"  note: {source_repo_path} links README{anchor}, which the home "
            "page has no section for — anchor dropped"
        )
        return ""
    return mapped


def rewrite_target(url, source_repo_path, is_image):
    """Rewrite a single link/image target. `source_repo_path` is the original
    file's location in the upstream repo (used to resolve relative paths)."""
    if is_external(url):
        return url
    path, anchor = split_anchor(url)
    if not path:
        # Pure anchor like "#foo".
        return url

    source_dir_ = posixpath.dirname(source_repo_path)
    resolved = (
        posixpath.normpath(posixpath.join(source_dir_, path))
        if source_dir_
        else posixpath.normpath(path)
    )
    if resolved.startswith("../") or resolved == "..":
        # Escapes repo root — leave the original alone.
        return url

    source_dest = map_to_dest(source_repo_path) or ""
    source_dest_dir = posixpath.dirname(source_dest)

    if resolved == HOME_SOURCE:
        return home_url(source_dest_dir) + home_anchor(anchor, source_repo_path)

    dest_relpath = map_to_dest(resolved)
    if dest_relpath is None:
        return github_url(resolved, is_image) + anchor

    rel = posixpath.relpath(dest_relpath, source_dest_dir or ".")
    return rel + anchor


def rewrite_links(content, source_repo_path):
    def md_replace(m):
        bang, text, url, title = m.group(1), m.group(2), m.group(3), m.group(4) or ""
        new_url = rewrite_target(url, source_repo_path, is_image=(bang == "!"))
        return f"{bang}[{text}]({new_url}{title})"

    def html_replace(m):
        prefix, quote, url = m.group(1), m.group(2), m.group(3)
        new_url = rewrite_target(url, source_repo_path, is_image=True)
        return f"{prefix}{quote}{new_url}{quote}"

    content = MD_LINK_RE.sub(md_replace, content)
    return HTML_IMG_RE.sub(html_replace, content)


def humanize(stem):
    return stem.replace("_", " ").replace("-", " ").strip().title()


def extract_title(md_path, default):
    """A page's title, from frontmatter, its first H1, or its filename."""
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
                    return value.strip().strip("\"'")
        content = content[m.end() :]

    h1 = H1_RE.search(content)
    if h1:
        title = HTML_COMMENT_RE.sub("", h1.group(1)).strip()
        if title:
            return title

    return default


def nav_label(title):
    """A page's nav label: its title without the subtitle a colon or dash
    introduces, so the sidebar stays scannable."""
    return SUBTITLE_RE.sub("", title).strip() or title


def milestone_sort_key(path):
    """Milestone records order by the number their filename leads with, behind
    the section index."""
    if path.name == "index.md":
        return (-1, 0, "")
    m = LEADING_NUMBER_RE.match(path.name)
    return (0, int(m.group(1)), path.name) if m else (1, 0, path.name)


def write_milestones_index(dest):
    """Write the milestones landing page: the section's records, in order."""
    records = sorted(
        (p for p in (dest / MILESTONES).glob("*.md") if p.name != "index.md"),
        key=milestone_sort_key,
    )
    lines = [MILESTONES_INDEX.rstrip("\n"), ""]
    for record in records:
        title = extract_title(record, default=humanize(record.stem))
        lines.append(f"- [{title}]({record.name})")
    lines.append("")
    (dest / MILESTONES / "index.md").write_text("\n".join(lines), encoding="utf-8")


def nav_entries(dest):
    """Build the [(label, target)] nav entries for the synced section, with the
    milestone records nested under their index as ('Milestones', [entries])."""
    pages = {p.relative_to(dest).as_posix() for p in dest.rglob("*.md")}

    def entry(rel, label=None, trim=True):
        title = extract_title(dest / rel, default=humanize(Path(rel).stem))
        if label is None:
            label = nav_label(title) if trim else title
        return (label, f"{SECTION}/{rel}")

    trailing_names = {name for name, _ in TRAILING_PAGES}
    ordered = [rel for rel in PAGE_ORDER if rel in pages]
    extra = sorted(
        rel
        for rel in pages
        if rel not in PAGE_ORDER
        and rel not in trailing_names
        and not rel.startswith(MILESTONES + "/")
    )

    entries = [entry(rel, INDEX_LABEL if rel == "index.md" else None) for rel in ordered + extra]

    records = sorted((dest / MILESTONES).glob("*.md"), key=milestone_sort_key)
    if records:
        # The index leads, so navigation.indexes makes the section header it.
        # Records keep their full titles: "M1:" is the label, not a subtitle.
        nested = [
            entry(
                f"{MILESTONES}/{p.name}",
                label=MILESTONES_LABEL if p.name == "index.md" else None,
                trim=False,
            )
            for p in records
        ]
        entries.append((MILESTONES_LABEL, nested))

    for name, label in TRAILING_PAGES:
        if name in pages:
            entries.append(entry(name, label))

    return entries


def _nav_lines(entries, indent):
    lines = []
    for label, target in entries:
        safe = label.replace('"', '\\"')
        if isinstance(target, list):
            lines.append(f'{indent}{{ "{safe}" = [')
            lines += _nav_lines(target, indent + "  ")
            lines.append(f"{indent}] }},")
        else:
            lines.append(f'{indent}{{ "{safe}" = "{target}" }},')
    return lines


def write_docs_nav(entries):
    """Rewrite the BEGIN_DOCS_NAV/END_DOCS_NAV block in zensical.toml. With no
    entries the block holds only its markers, so no Docs tab is rendered."""
    lines = [f"{NAV_INDENT}{NAV_BEGIN}"]
    if entries:
        lines.append(f'{NAV_INDENT}{{ "Docs" = [')
        lines += _nav_lines(entries, NAV_INDENT + "  ")
        lines.append(f"{NAV_INDENT}] }},")
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


def sync():
    """Copy the upstream docs into DEST, rewriting links. Returns True when
    anything landed."""
    src = source_dir()
    if DEST.exists():
        shutil.rmtree(DEST)

    if not src.is_dir():
        print(f"  skip {NAME}: source not found at {src}")
        return False

    DEST.mkdir(parents=True, exist_ok=True)
    copied = 0

    for src_name, dest_name in ROOT_FILE_MAP.items():
        src_path = src / src_name
        if src_path.is_file():
            content = rewrite_links(src_path.read_text(encoding="utf-8"), src_name)
            (DEST / dest_name).write_text(content, encoding="utf-8")
            copied += 1

    docs_src = src / DOCS_DIR
    if docs_src.is_dir():
        for path in sorted(docs_src.rglob("*")):
            rel = path.relative_to(docs_src)
            if path.is_dir():
                (DEST / rel).mkdir(parents=True, exist_ok=True)
                continue
            repo_relpath = f"{DOCS_DIR}/{rel.as_posix()}"
            target = DEST / map_to_dest(repo_relpath)
            target.parent.mkdir(parents=True, exist_ok=True)
            if path.suffix == ".md":
                content = rewrite_links(path.read_text(encoding="utf-8"), repo_relpath)
                target.write_text(content, encoding="utf-8")
            else:
                shutil.copy2(path, target)
            copied += 1

    if copied == 0:
        shutil.rmtree(DEST)
        print(f"  {NAME}: nothing to sync")
        return False

    if (DEST / MILESTONES).is_dir():
        write_milestones_index(DEST)
        copied += 1

    print(f"  {NAME}: synced {copied} files into {DEST}")
    return True


def main():
    print(f"Syncing {REPO} docs into {DEST}/")
    write_docs_nav(nav_entries(DEST) if sync() else [])


if __name__ == "__main__":
    main()
