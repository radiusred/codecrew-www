import os
import re
import shutil
from datetime import date, timedelta
from pathlib import Path

import pytest

import main


@pytest.fixture
def site(tmp_path: Path, monkeypatch):
    """A minimal site tree in tmp_path, with main.py's paths pointed at it."""
    (tmp_path / "docs/blog/posts").mkdir(parents=True)
    (tmp_path / "_drafts").mkdir()
    (tmp_path / "zensical.toml").write_text(
        '[project]\nsite_url = "https://codecrew.works/"\nnav = [\n'
        "    # BEGIN_BLOG_POSTS\n    # END_BLOG_POSTS\n]\n"
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(main, "DOCS_BLOG", Path("docs/blog/posts"))
    monkeypatch.setattr(main, "DRAFTS_BLOG", Path("_drafts"))
    monkeypatch.setattr(main, "CONFIG", Path("zensical.toml"))
    monkeypatch.setattr(main, "ARCHIVE_PAGE", Path("docs/blog/archive.md"))
    monkeypatch.setattr(main, "ATOM_FEED", Path("docs/blog/atom.xml"))
    return tmp_path


def post(path: Path, title: str, d: date):
    path.write_text(
        f"---\nlayout: default\nauthor: Wordy\ntitle: {title}\ndate: {d.isoformat()}\n"
        f"description: About {title}.\n---\n\n## Body\n"
    )


def test_future_posts_are_demoted_and_due_drafts_promoted(site: Path):
    today = date.today()
    post(site / "docs/blog/posts/future.md", "Future", today + timedelta(days=3))
    post(site / "_drafts/due.md", "Due", today - timedelta(days=1))
    main.reconcile_drafts()
    assert (site / "_drafts/future.md").exists()
    assert (site / "docs/blog/posts/due.md").exists()


def test_a_notes_file_in_drafts_is_never_published(site: Path):
    """www#79: _drafts/ also holds working notes that are not posts, such as the
    list-submission drafts. With no front matter they carry no date, so they stay
    put, even when a line in the body looks like a date field."""
    notes = site / "_drafts/notes.md"
    notes.write_text(f"# Notes\n\ndate: {date.today().isoformat()}\n")
    main.reconcile_drafts()
    main.regenerate_nav()
    assert notes.exists()
    assert not (site / "docs/blog/posts/notes.md").exists()
    assert "notes.md" not in (site / "zensical.toml").read_text()


def test_the_committed_drafts_notes_carry_no_front_matter():
    """The real notes files in _drafts/ must never open with front matter, or a
    date in it would publish them as a blog post on the next build."""
    root = Path(__file__).resolve().parent.parent
    for notes in sorted((root / "_drafts").glob("m*-*.md")):
        assert not notes.read_text().startswith("---"), notes.name
        assert main._post_date(notes) is None, notes.name


def test_nav_archive_and_feed_reflect_published_posts(site: Path):
    today = date.today()
    post(site / "docs/blog/posts/2026-01-01-one.md", "One", today - timedelta(days=10))
    post(site / "docs/blog/posts/2026-02-01-two.md", "Two", today - timedelta(days=1))
    main.regenerate_nav()
    main.generate_archive()
    main.generate_atom_feed()
    cfg = (site / "zensical.toml").read_text()
    assert 'blog/posts/2026-02-01-two.md' in cfg and 'blog/posts/2026-01-01-one.md' in cfg
    archive = (site / "docs/blog/archive.md").read_text()
    assert archive.index("[Two]") < archive.index("[One]")
    feed = (site / "docs/blog/atom.xml").read_text()
    assert "<title>CodeCrew blog</title>" in feed
    assert "https://codecrew.works/blog/posts/2026-02-01-two/" in feed


def test_empty_blog_still_generates(site: Path):
    main.main()
    assert (site / "docs/blog/archive.md").exists()
    assert "<feed" in (site / "docs/blog/atom.xml").read_text()


def test_nav_label_is_the_plain_title_with_no_markup(site: Path):
    """A nav key becomes the page's <title> and <h1>, so it carries no HTML."""
    today = date.today()
    post(site / "docs/blog/posts/2026-03-01-plain.md", "A Plain Title", today)
    main.regenerate_nav()
    cfg = (site / "zensical.toml").read_text()
    label = re.search(r'\{ "(.*)" = "blog/posts/2026-03-01-plain\.md" \}', cfg).group(1)
    assert label == "A Plain Title"
    assert "<" not in label and "small" not in label
    assert today.isoformat() not in label


GENERATED = ("zensical.toml", "docs/blog/archive.md", "docs/blog/atom.xml")


def test_the_committed_blog_metadata_is_what_main_generates(tmp_path: Path, monkeypatch):
    """www#41: the deploy regenerates the blog nav, the archive and the feed, so a
    post committed without running main.py reached the live site while main
    disagreed with it. Regenerating from the committed posts must change nothing.

    Drafts are not reconciled here: the date a draft falls due is not a commit,
    and the scheduled build that promotes it must not turn main red overnight."""
    root = Path(__file__).resolve().parent.parent
    shutil.copytree(root / "docs" / "blog", tmp_path / "docs" / "blog")
    shutil.copy(root / "zensical.toml", tmp_path / "zensical.toml")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(main, "DOCS_BLOG", Path("docs/blog/posts"))
    monkeypatch.setattr(main, "CONFIG", Path("zensical.toml"))
    monkeypatch.setattr(main, "ARCHIVE_PAGE", Path("docs/blog/archive.md"))
    monkeypatch.setattr(main, "ATOM_FEED", Path("docs/blog/atom.xml"))
    main.regenerate_nav()
    main.generate_archive()
    main.generate_atom_feed()
    for rel in GENERATED:
        assert (tmp_path / rel).read_text() == (root / rel).read_text(), (
            f"{rel} is out of date: run `uv run python main.py` and commit what it writes"
        )
