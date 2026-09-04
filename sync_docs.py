"""Sync radiusred/gh-codecrew's documentation into docs/docs/.

codecrew.works is CodeCrew's own site: the home page carries the product pitch
(the README's argument, in page form) and this sync gives the reference material
a web home beneath it at /docs/. The upstream repo stays the single source of
truth — nothing landed here is committed, the tree is rebuilt from scratch on
every build, and www.radiusred.uk no longer carries a copy of it.

What lands where (repo-root-relative source -> path under docs/docs/):

    docs/introduction.md   -> index.md          (/docs/)
    docs/**                -> **                (/docs/**, minus EXCLUDE)
    SPEC.md                -> spec.md
    CONTRIBUTING.md        -> contributing.md
    SECURITY.md            -> security.md

docs/milestones/ is excluded: the per-milestone records are an internal
engineering artefact, and this is the product's marketing site. Links into an
excluded path go to GitHub like any other path that did not sync.

README.md does not sync: the home page already is the README's argument, so
links to it resolve to the home page rather than to a second copy. Links to
anything else that did not sync — AGENTS.md, ROADMAP.md, CHANGELOG.md, LICENSE,
roles/, assets/ — become absolute GitHub URLs. External URLs and bare in-page
anchors are left alone.

The Docs nav tab is written between the sentinel markers in zensical.toml, the
same way main.py maintains the blog's.

An absent upstream checkout is an error, not a quiet degrade: the nav block is
emptied and the destination removed so the config is left consistent, and then
the sync exits nonzero naming what to clone. The site cannot build without it —
the home page's "Read the docs" button targets docs/index.md, so a build with no
synced section fails on a dangling link, and failing here says why.

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

# Subtrees of the upstream docs/ dir that do not belong on the marketing site.
# A trailing slash marks a subtree; the directory itself is excluded too, so a
# link to it becomes a GitHub URL rather than resolving to nothing. The
# milestone records are the engineering trail, not product documentation.
EXCLUDE = ("milestones/",)

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
# reported, rather than left to dangle a --strict build breaks on. A row per
# heading the README has and the home page answers: a heading the README lost
# loses its row too, so a page still linking it is reported rather than quietly
# redirected (gh-codecrew#235 cut the README to a landing page; #read-next has
# no home-page counterpart and stays unmapped).
HOME_ANCHORS = {
    "#the-routing-table": "#the-crew",  # the home page's own annotated table
    "#start-now": "#start-now",
}

# Image extensions get rewritten to raw.githubusercontent.com so they render.
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico"}

# Markdown link/image:  ![alt](url "title")  or  [text](url "title")
MD_LINK_RE = re.compile(r'(!?)\[([^\]]*)\]\(([^)\s]+)(\s+"[^"]*")?\)')
# HTML <img src="...">. Matches single or double quotes.
HTML_IMG_RE = re.compile(r'(<img\b[^>]*?\bsrc=)(["\'])([^"\']+)\2', re.IGNORECASE)

# TOML basic-string escapes. Anything else below 0x20 (and DEL) goes to \uXXXX,
# so a title carrying a backslash or a control character cannot produce a config
# that fails to parse — or one that parses into a different label.
TOML_ESCAPES = {
    "\\": "\\\\",
    '"': '\\"',
    "\b": "\\b",
    "\t": "\\t",
    "\n": "\\n",
    "\f": "\\f",
    "\r": "\\r",
}

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
# A title's subtitle: everything after the first ": " or " — ".
SUBTITLE_RE = re.compile(r"\s*(?::|\s—)\s.*$", re.DOTALL)
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


def is_excluded(docs_rel):
    """True if `docs_rel` (relative to the upstream docs/ dir) is one of the
    EXCLUDE subtrees, or sits inside one."""
    for pattern in EXCLUDE:
        prefix = pattern.rstrip("/")
        if docs_rel == prefix or docs_rel.startswith(prefix + "/"):
            return True
    return False


def map_to_dest(repo_path):
    """Map a repo-root-relative path to its path under DEST, or None if it
    does not sync (the caller then emits a GitHub URL)."""
    if repo_path in ROOT_FILE_MAP:
        return ROOT_FILE_MAP[repo_path]
    if repo_path == SECTION_INDEX or repo_path == DOCS_DIR:
        return "index.md"
    if repo_path.startswith(DOCS_DIR + "/"):
        rel = repo_path[len(DOCS_DIR) + 1 :]
        return None if is_excluded(rel) else rel
    return None


def github_url(repo_path, is_image):
    path = repo_path.split("#", 1)[0]
    if is_image or posixpath.splitext(path)[1].lower() in IMAGE_EXTS:
        return f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/{repo_path}"
    # GitHub 301s /blob/ to /tree/ for a directory, so link the directory
    # directly. Asked of the checkout rather than guessed from the absence of an
    # extension: LICENSE has none and is a file. The fragment is stripped first —
    # rewrite_target already splits it off, but a direct caller may not have.
    view = "tree" if (source_dir() / path).is_dir() else "blob"
    return f"https://github.com/{REPO}/{view}/{BRANCH}/{repo_path}"


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

    if path.startswith("/"):
        # Root-relative in a repo-relative document: resolve against the repo
        # root, which is what such a link means on GitHub.
        resolved = posixpath.normpath(path).lstrip("/")
    else:
        source_dir_ = posixpath.dirname(source_repo_path)
        resolved = (
            posixpath.normpath(posixpath.join(source_dir_, path))
            if source_dir_
            else posixpath.normpath(path)
        )
    if resolved.startswith("../") or resolved == "..":
        # Escapes the repo root: already broken upstream, and there is no
        # target to point at. Left alone and reported — once the page is under
        # docs/docs/ the link resolves against the site instead of the repo, so
        # a --strict build fails on it rather than shipping a wrong URL.
        print(
            f"  note: {source_repo_path} links {url}, which escapes the repo "
            "root — left as written"
        )
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


def nav_entries(dest):
    """Build the [(label, target)] nav entries for the synced section."""
    pages = {p.relative_to(dest).as_posix() for p in dest.rglob("*.md")}

    def entry(rel, label=None):
        title = extract_title(dest / rel, default=humanize(Path(rel).stem))
        return (label or nav_label(title), f"{SECTION}/{rel}")

    trailing_names = {name for name, _ in TRAILING_PAGES}
    ordered = [rel for rel in PAGE_ORDER if rel in pages]
    extra = sorted(
        rel for rel in pages if rel not in PAGE_ORDER and rel not in trailing_names
    )

    entries = [entry(rel, INDEX_LABEL if rel == "index.md" else None) for rel in ordered + extra]

    for name, label in TRAILING_PAGES:
        if name in pages:
            entries.append(entry(name, label))

    return entries


def toml_string(value):
    """`value` as a quoted TOML basic string."""
    out = []
    for char in value:
        if char in TOML_ESCAPES:
            out.append(TOML_ESCAPES[char])
        elif char < "\x20" or char == "\x7f":
            out.append(f"\\u{ord(char):04x}")
        else:
            out.append(char)
    return '"' + "".join(out) + '"'


def _nav_lines(entries, indent):
    lines = []
    for label, target in entries:
        if isinstance(target, list):
            lines.append(f"{indent}{{ {toml_string(label)} = [")
            lines += _nav_lines(target, indent + "  ")
            lines.append(f"{indent}] }},")
        else:
            lines.append(f"{indent}{{ {toml_string(label)} = {toml_string(target)} }},")
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
            if is_excluded(rel.as_posix()):
                continue
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

    print(f"  {NAME}: synced {copied} files into {DEST}")
    return True


def main():
    print(f"Syncing {REPO} docs into {DEST}/")
    if sync():
        write_docs_nav(nav_entries(DEST))
        return
    # Leave the config consistent with the (now absent) tree, then say why the
    # build that follows would have failed on the home page's docs button.
    write_docs_nav([])
    raise SystemExit(
        f"error: no {NAME} checkout at {source_dir()}. The docs section and the "
        "home page's 'Read the docs' button both need it: clone "
        f"https://github.com/{REPO} beside this repo, or point "
        "SYNC_SOURCE_BASE at the directory holding it."
    )


if __name__ == "__main__":
    main()
