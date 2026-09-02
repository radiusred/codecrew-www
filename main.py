import re
import shutil
import tomllib
from datetime import date, datetime
from pathlib import Path

DOCS_BLOG = Path("docs/blog/posts")
DRAFTS_BLOG = Path("_drafts")
CONFIG = Path("zensical.toml")
ARCHIVE_PAGE = Path("docs/blog/archive.md")
ATOM_FEED = Path("docs/blog/atom.xml")


def _load_site_url():
    """Read site_url from zensical.toml so this script and the site stay in sync."""
    with open(CONFIG, "rb") as f:
        cfg = tomllib.load(f)
    url = cfg.get("project", {}).get("site_url") or cfg.get("site_url")
    if not url:
        raise RuntimeError(f"site_url not found in {CONFIG}")
    return url.rstrip("/")


SITE_URL = _load_site_url()
BLOG_PATH = "blog/posts"
NAV_LIMIT = 10
NAV_INDENT = "    "
NAV_BEGIN = "# BEGIN_BLOG_POSTS"
NAV_END = "# END_BLOG_POSTS"


def parse_frontmatter(content):
    """Extract YAML frontmatter from markdown file."""
    match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
    if not match:
        return {}, content

    frontmatter_text = match.group(1)
    body = content[match.end() :]

    data = {}
    for line in frontmatter_text.split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            data[key.strip()] = value.strip().strip("\"'")

    return data, body


def _post_date(post_file):
    """Return the post's frontmatter date as a date, or None if missing/invalid."""
    fm, _ = parse_frontmatter(post_file.read_text())
    raw = fm.get("date")
    if not raw:
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return None


def reconcile_drafts():
    """Move future-dated posts out of docs/blog/posts/, promote due drafts back in."""
    DRAFTS_BLOG.mkdir(parents=True, exist_ok=True)
    today = date.today()

    demoted = []
    for post in DOCS_BLOG.glob("*.md"):
        d = _post_date(post)
        if d and d > today:
            shutil.move(str(post), str(DRAFTS_BLOG / post.name))
            demoted.append(post.name)

    promoted = []
    for draft in DRAFTS_BLOG.glob("*.md"):
        d = _post_date(draft)
        if d and d <= today:
            shutil.move(str(draft), str(DOCS_BLOG / draft.name))
            promoted.append(draft.name)

    if demoted:
        print(f"Hidden as drafts ({len(demoted)}): {', '.join(sorted(demoted))}")
    if promoted:
        print(f"Promoted to published ({len(promoted)}): {', '.join(sorted(promoted))}")


def _published_posts():
    """Return [(date, title, filename)] for all published posts, newest first."""
    posts = []
    for post in DOCS_BLOG.glob("*.md"):
        fm, _ = parse_frontmatter(post.read_text())
        d = _post_date(post)
        title = fm.get("title")
        if d and title:
            posts.append((d, title, post.name))
    posts.sort(key=lambda p: p[0], reverse=True)
    return posts


def regenerate_nav():
    """Rewrite the blog-posts block in zensical.toml between sentinel markers."""
    posts = _published_posts()
    visible = list(reversed(posts[:NAV_LIMIT]))

    new_lines = [f"{NAV_INDENT}{NAV_BEGIN}"]
    for d, title, fname in visible:
        safe_title = title.replace('"', '\\"')
        label = f'{safe_title} <small class=\\"muted\\">({d.isoformat()})</small>'
        new_lines.append(
            f'{NAV_INDENT}{{ "{label}" = "blog/posts/{fname}" }},'
        )
    new_lines.append(f"{NAV_INDENT}{NAV_END}")

    text = CONFIG.read_text()
    lines = text.split("\n")
    start = end = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if start is None and stripped == NAV_BEGIN:
            start = i
        elif start is not None and stripped == NAV_END:
            end = i
            break
    if start is None or end is None:
        raise RuntimeError(
            f"Could not find {NAV_BEGIN}/{NAV_END} markers in zensical.toml"
        )

    lines[start : end + 1] = new_lines
    new_text = "\n".join(lines)
    if new_text != text:
        CONFIG.write_text(new_text)
        print(f"Updated blog nav with {len(visible)} visible posts")


def generate_archive():
    """Write docs/blog/archive.md grouping all published posts by year and month, newest first."""
    posts = _published_posts()
    lines = [
        "---",
        "title: All Posts",
        "description: A complete index of every post on the CodeCrew blog.",
        "---",
        "",
        "# All Posts",
        "",
    ]
    last_year = last_month = None
    for d, title, fname in posts:
        if d.year != last_year:
            if last_year is not None:
                lines.append("")
            lines += [f"## {d.year}", ""]
            last_year, last_month = d.year, None
        if d.month != last_month:
            if last_month is not None:
                lines.append("")
            lines += [f"### {d.strftime('%B')}", ""]
            last_month = d.month
        slug = fname.removesuffix(".md")
        lines.append(f"- **{d.isoformat()}** — [{title}](posts/{slug}.md)")
    lines.append("")

    ARCHIVE_PAGE.write_text("\n".join(lines))
    print(f"Generated archive page with {len(posts)} posts.")


def generate_atom_feed():
    """Generate Atom 1.0 feed from blog posts."""
    posts = []

    for post_file in sorted(DOCS_BLOG.glob("*.md"), reverse=True):
        with open(post_file, "r") as f:
            content = f.read()

        fm, body = parse_frontmatter(content)

        if not all(k in fm for k in ["title", "date", "description"]):
            continue

        post_date = datetime.fromisoformat(fm["date"])
        if post_date > datetime.now():
            continue

        posts.append(
            {
                "title": fm["title"],
                "date": fm["date"],
                "description": fm["description"],
                "slug": post_file.stem,
                "filename": post_file.name,
            }
        )

    now = datetime.now().isoformat() + "Z"
    latest_date = posts[0]["date"] + "T00:00:00Z" if posts else now
    feed_url = f"{SITE_URL}/{BLOG_PATH.rsplit('/', 1)[0]}/atom.xml"
    blog_url = f"{SITE_URL}/{BLOG_PATH.rsplit('/', 1)[0]}/"

    feed = f"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>CodeCrew Blog</title>
  <subtitle>Release notes, design decisions and field reports from building and running CodeCrew.</subtitle>
  <link href="{feed_url}" rel="self" />
  <link href="{blog_url}" rel="alternate" />
  <id>{blog_url}</id>
  <updated>{latest_date}</updated>
  <author>
    <name>Radius Red Ltd.</name>
  </author>
"""

    for post in posts:
        post_url = f"{SITE_URL}/{BLOG_PATH}/{post['slug']}/"
        entry_date = post["date"] + "T00:00:00Z"
        feed += f"""  <entry>
    <title>{post['title']}</title>
    <link href="{post_url}" rel="alternate" />
    <id>{post_url}</id>
    <updated>{entry_date}</updated>
    <summary>{post['description']}</summary>
  </entry>
"""

    feed += "</feed>\n"

    ATOM_FEED.write_text(feed)
    print(f"Generated Atom feed with {len(posts)} posts")


def main():
    reconcile_drafts()
    regenerate_nav()
    generate_archive()
    generate_atom_feed()


if __name__ == "__main__":
    main()
