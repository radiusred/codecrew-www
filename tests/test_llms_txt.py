"""llms_txt.py: /llms.txt from the nav and each page's front matter (M23-R3).

Runs against a synthetic site in tmp_path; tests/test_site_build.py checks the
file the real build publishes.
"""

from pathlib import Path

import pytest

import llms_txt

CONFIG = """[project]
site_url = "https://codecrew.works/"
nav = [
  { "Home" = "index.md" },
  { "Docs" = [
    { "Introduction" = "docs/index.md" },
    { "Your first milestone" = "docs/first-milestone.md" },
  ] },
  { "Blog" = [
    { "Latest" = "blog/index.md" },
    { "A post" = "blog/posts/2026-01-01-a-post.md" },
  ] },
]
"""

PAGES = {
    "index.md": "---\ntitle: CodeCrew\ndescription: The homepage's own line.\n---\n\n# Hi\n",
    "docs/index.md": '---\ndescription: "The map, with \\"quotes\\"."\n---\n# CodeCrew, precisely\n',
    "docs/first-milestone.md": '---\ndescription: "Getting started."\n---\n# Your first milestone\n',
    "blog/index.md": "---\nlayout: default\ntitle: Blog\ndescription: Release notes.\n---\n# Blog\n",
    "blog/posts/2026-01-01-a-post.md": "---\ntitle: A post\ndescription: 'About it.'\n---\n",
}


@pytest.fixture
def site(tmp_path: Path, monkeypatch) -> Path:
    for rel, text in PAGES.items():
        (tmp_path / "docs" / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / "docs" / rel).write_text(text, encoding="utf-8")
    (tmp_path / "zensical.toml").write_text(CONFIG, encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    return tmp_path


def written(site: Path) -> str:
    llms_txt.main()
    return (site / "docs" / "llms.txt").read_text(encoding="utf-8")


def headings(text: str) -> list[str]:
    return [line for line in text.splitlines() if line.startswith("#")]


def test_the_file_takes_the_llmstxt_shape(site: Path):
    """An H1 with the project's name, a blockquote summary, then H2 sections of links."""
    text = written(site)
    lines = text.splitlines()
    assert lines[0] == "# CodeCrew"
    assert lines[2].startswith("> CodeCrew is ")
    assert headings(text) == ["# CodeCrew", "## Start here", "## Docs", "## Source", "## Optional"]


def test_each_page_is_its_canonical_url_title_and_description(site: Path):
    text = written(site)
    assert "- [CodeCrew](https://codecrew.works/): The homepage's own line." in text
    # A JSON-quoted description (what sync_docs.py writes) is decoded, not shown raw.
    assert '- [Introduction](https://codecrew.works/docs/): The map, with "quotes".' in text
    assert "- [Your first milestone](https://codecrew.works/docs/first-milestone/): Getting started." in text
    # The front matter's title beats a nav label like "Latest".
    assert "- [Blog](https://codecrew.works/blog/): Release notes." in text
    assert "(https://codecrew.works/blog/posts/2026-01-01-a-post/): About it." in text


def test_spec_and_cli_are_linked_at_source(site: Path):
    text = written(site)
    source = text[text.index("## Source") : text.index("## Optional")]
    assert "[SPEC.md](https://github.com/radiusred/gh-codecrew/blob/main/SPEC.md)" in source
    assert "[CLI.md](https://github.com/radiusred/gh-codecrew/blob/main/CLI.md)" in source


def test_the_blog_is_optional_reading(site: Path):
    text = written(site)
    optional = text[text.index("## Optional") :]
    assert "blog/posts/2026-01-01-a-post/" in optional
    assert "blog/" not in text[: text.index("## Optional")]


def test_a_new_nav_group_becomes_its_own_section_in_nav_order(site: Path):
    """Where the introductory pages land when they join the nav (codecrew-www#76): a
    group of their own is a section of its own, placed where the nav puts it."""
    config = (site / "zensical.toml").read_text(encoding="utf-8")
    config = config.replace(
        '  { "Docs" = [',
        '  { "Start" = [\n    { "Reviews" = "start/reviews.md" },\n  ] },\n  { "Docs" = [',
    )
    (site / "zensical.toml").write_text(config, encoding="utf-8")
    (site / "docs/start").mkdir()
    (site / "docs/start/reviews.md").write_text("---\ndescription: Reviewed.\n---\n", encoding="utf-8")
    text = written(site)
    assert headings(text)[1:4] == ["## Start here", "## Start", "## Docs"]
    assert "- [Reviews](https://codecrew.works/start/reviews/): Reviewed." in text


def test_a_new_top_level_page_joins_start_here(site: Path):
    config = (site / "zensical.toml").read_text(encoding="utf-8")
    config = config.replace('  { "Home" = "index.md" },', '  { "Home" = "index.md" },\n  { "Why" = "why.md" },')
    (site / "zensical.toml").write_text(config, encoding="utf-8")
    (site / "docs/why.md").write_text("# Why\n", encoding="utf-8")
    text = written(site)
    start = text[text.index("## Start here") : text.index("## Docs")]
    assert "- [Why](https://codecrew.works/why/)\n" in start  # no description, no colon
