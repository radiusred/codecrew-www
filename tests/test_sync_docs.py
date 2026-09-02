from pathlib import Path

import sync_docs
from sync_docs import PROJECT, extract_title, nav_entries, rewrite_links, rewrite_target


def test_readme_links_into_docs_become_relative():
    # README.md -> index.md, so docs/foo.md is reachable as foo.md.
    assert rewrite_target("docs/first-milestone.md#5-finish-the-task", "README.md", PROJECT, False) == (
        "first-milestone.md#5-finish-the-task"
    )


def test_root_reference_files_are_synced_not_linked_out():
    assert rewrite_target("SPEC.md", "README.md", PROJECT, False) == "spec.md"
    assert rewrite_target("../CHANGELOG.md", "docs/introduction.md", PROJECT, False) == "changelog.md"


def test_excluded_milestones_link_to_github():
    url = rewrite_target("milestones/3-first-spoke.md", "docs/introduction.md", PROJECT, False)
    assert url == "https://github.com/radiusred/gh-codecrew/blob/main/docs/milestones/3-first-spoke.md"


def test_non_synced_files_and_images_link_to_github():
    assert rewrite_target("AGENTS.md", "README.md", PROJECT, False) == (
        "https://github.com/radiusred/gh-codecrew/blob/main/AGENTS.md"
    )
    content = '<img src="assets/svg/four-seats.svg" alt="x" width="720">'
    assert rewrite_links(content, "README.md", PROJECT) == (
        '<img src="https://raw.githubusercontent.com/radiusred/gh-codecrew/main/assets/svg/four-seats.svg" alt="x" width="720">'
    )


def test_external_and_anchor_links_untouched():
    assert rewrite_target("https://example.com/x", "README.md", PROJECT, False) == "https://example.com/x"
    assert rewrite_target("#refusal-codes", "docs/introduction.md", PROJECT, False) == "#refusal-codes"


def test_nav_order_overview_then_ordered_then_alpha_then_root(tmp_path: Path):
    for name, title in {
        "index.md": "# CodeCrew",
        "introduction.md": "# CodeCrew, precisely",
        "first-milestone.md": "# Your first milestone",
        "aardvark.md": "# Aardvark",
        "zebra.md": "# Zebra",
        "spec.md": "# Spec",
        "contributing.md": "# Contributing",
    }.items():
        (tmp_path / name).write_text(title + "\n")
    project = {**PROJECT, "order": ["introduction.md", "first-milestone.md"]}
    labels = [label for label, _ in nav_entries(project, tmp_path)]
    assert labels == [
        "Overview",
        "CodeCrew, precisely",
        "Your first milestone",
        "Aardvark",
        "Zebra",
        "Specification",
        "Contributing",
    ]


def test_extract_title_prefers_frontmatter_then_h1(tmp_path: Path):
    fm = tmp_path / "fm.md"
    fm.write_text("---\ntitle: From Frontmatter\n---\n\n# Not this\n")
    assert extract_title(fm, "fallback") == "From Frontmatter"
    h1 = tmp_path / "h1.md"
    h1.write_text("# The H1 <!-- comment -->\n")
    assert extract_title(h1, "fallback") == "The H1"
    assert extract_title(tmp_path / "missing.md", "fallback") == "fallback"
