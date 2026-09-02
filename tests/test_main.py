import os
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
    assert "<title>CodeCrew Blog</title>" in feed
    assert "https://codecrew.works/blog/posts/2026-02-01-two/" in feed


def test_empty_blog_still_generates(site: Path):
    main.main()
    assert (site / "docs/blog/archive.md").exists()
    assert "<feed" in (site / "docs/blog/atom.xml").read_text()
