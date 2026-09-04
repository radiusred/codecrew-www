"""The upstream docs sync: what lands where, what the links become, and the
nav block it writes.

Everything here runs against a synthetic upstream in `tmp_path`, so the suite
never depends on a radiusred/gh-codecrew checkout being on disk. The real
upstream is exercised by tests/test_site_build.py, which builds the site.
"""

import tomllib

import pytest

import sync_docs
from sync_docs import (
    DEST,
    github_url,
    main,
    nav_entries,
    rewrite_target,
    sync,
    toml_string,
    write_docs_nav,
)

GITHUB = "https://github.com/radiusred/gh-codecrew"
RAW = "https://raw.githubusercontent.com/radiusred/gh-codecrew/main"

UPSTREAM = {
    "README.md": "# CodeCrew\n",
    "AGENTS.md": "# Agents\n",
    "SPEC.md": (
        "# CodeCrew Protocol Specification\n\n"
        "See [founding decisions](docs/founding-decisions.md), the\n"
        "[coordinator contract](roles/coordinator.md) and\n"
        "[an agent](agent://<agent id>).\n"
    ),
    "CONTRIBUTING.md": "# Contributing\n",
    "SECURITY.md": "# Security\n",
    "LICENSE": "Apache 2.0\n",
    "docs/introduction.md": (
        "# CodeCrew, precisely\n\n"
        "The [landing page](../README.md), the [table](../README.md#the-routing-table),\n"
        "the [install](../README.md#start-now) and the [receipts](../README.md#the-receipts).\n"
        "Read [the spec](../SPEC.md#roles), [identities](identities.md) and the\n"
        "[records](milestones/) and [one record](milestones/1-first.md); the\n"
        "[changelog](../CHANGELOG.md), the [licence](../LICENSE) and the\n"
        "[logo](../assets/logo.webp) stay upstream.\n"
        "[gh](https://cli.github.com/) is external, [top](#top) is an anchor.\n"
        "[root-relative](/docs/identities.md) and [above root](../../README.md).\n"
    ),
    "docs/first-milestone.md": "# Your first milestone\n",
    "docs/identities.md": "# Identities: running solo, staffing a crew\n",
    "docs/extensions.md": "# Local extensions — `roles/<role>.local.md`\n",
    "docs/platform-interop.md": "# Platform interop: hosting a crew on a platform\n",
    "docs/founding-decisions.md": "# Founding decisions\n",
    "docs/gsd-vs-frontier-orchestration.md": (
        '# GSD vs. "just let the model orchestrate": an assessment\n'
    ),
    "docs/milestones/1-first.md": (
        "# M1: First\n\nBack to [the intro](../introduction.md) and the\n"
        "[landing page](../../README.md).\n"
    ),
    "docs/milestones/2-second.md": '# M2: Second\n\n<img src="../../assets/shot.png" alt="">\n',
    "docs/milestones/10-tenth.md": "# M10: Tenth\n",
    # A sibling whose name merely starts with an excluded prefix.
    "docs/milestones-archive/kept.md": "# Kept\n",
}

CONFIG_TEMPLATE = (
    'nav = [\n  { "Home" = "index.md" },\n'
    f"  {sync_docs.NAV_BEGIN}\n  {sync_docs.NAV_END}\n"
    '  { "Blog" = "blog/index.md" },\n]\n'
)


@pytest.fixture
def upstream(tmp_path, monkeypatch):
    """A synthetic gh-codecrew checkout under a scratch SYNC_SOURCE_BASE, with
    the sync's relative DEST and CONFIG rooted in the same scratch dir."""
    base = tmp_path / "_sources"
    repo = base / "gh-codecrew"
    for relpath, content in UPSTREAM.items():
        path = repo / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    (tmp_path / "zensical.toml").write_text(CONFIG_TEMPLATE, encoding="utf-8")
    monkeypatch.setenv("SYNC_SOURCE_BASE", str(base))
    monkeypatch.chdir(tmp_path)
    return tmp_path


def synced(dest=DEST):
    return sorted(p.relative_to(dest).as_posix() for p in dest.rglob("*") if p.is_file())


def page(relpath):
    return (DEST / relpath).read_text(encoding="utf-8")


def nav_block(root):
    text = (root / "zensical.toml").read_text(encoding="utf-8")
    start = text.index(sync_docs.NAV_BEGIN)
    return text[start : text.index(sync_docs.NAV_END, start)].rstrip()


def test_the_docs_tree_and_the_three_root_files_land_the_readme_does_not(upstream):
    assert sync() is True
    assert synced() == [
        "contributing.md",
        "extensions.md",
        "first-milestone.md",
        "founding-decisions.md",
        "gsd-vs-frontier-orchestration.md",
        "identities.md",
        "index.md",
        "milestones-archive/kept.md",  # excluded prefixes stop at a path boundary
        "platform-interop.md",
        "security.md",
        "spec.md",
    ]
    # introduction.md became the section index; README and AGENTS never synced.
    assert page("index.md").startswith("# CodeCrew, precisely")
    assert not (DEST / "introduction.md").exists()
    assert not (DEST / "readme.md").exists()
    assert not (DEST / "agents.md").exists()
    assert not (DEST / "milestones").exists()  # EXCLUDE: the engineering trail


def test_links_between_synced_pages_resolve_on_site(upstream):
    sync()
    index = page("index.md")
    assert "[the spec](spec.md#roles)" in index  # ../SPEC.md from docs/
    assert "[identities](identities.md)" in index
    # SPEC.md sits at the repo root, so its docs/ links flatten into the section.
    assert "[founding decisions](founding-decisions.md)" in page("spec.md")


def test_a_page_in_a_subdirectory_reaches_the_index_and_the_home_page(upstream):
    # Nothing in the current upstream syncs into a subdirectory, so this holds
    # rewrite_target to the depth arithmetic directly: a page one level down
    # reaches the section index at ../ and the site's home page at ../../.
    deep = "docs/guides/deep.md"
    assert rewrite_target("../introduction.md", deep, is_image=False) == "../index.md"
    assert rewrite_target("../../README.md", deep, is_image=False) == "../../index.md"
    assert rewrite_target("../identities.md", deep, is_image=False) == "../identities.md"


def test_readme_links_land_on_the_home_page_with_its_own_anchors(upstream, capsys):
    sync()
    index = page("index.md")
    assert "[landing page](../index.md)" in index  # the site's home page, not a copy
    assert "[table](../index.md#the-crew)" in index  # README anchor translated to the home page's id
    assert "[install](../index.md#start-now)" in index  # the one anchor both pages share
    # A heading the README no longer has (gh-codecrew#235 cut the receipts) has
    # no row: the anchor is dropped, the link lands on the home page, and the
    # sync says so rather than redirecting a link that is dead upstream.
    assert "[receipts](../index.md)" in index
    assert "links README#the-receipts, which the home page has no section for" in capsys.readouterr().out
    assert "](../README.md" not in index  # no link to the file survives the move


def test_links_to_files_that_did_not_sync_become_github_urls(upstream):
    sync()
    index = page("index.md")
    assert f"[changelog]({GITHUB}/blob/main/CHANGELOG.md)" in index
    assert f"[logo]({RAW}/assets/logo.webp)" in index  # an image extension goes to raw
    assert f"[coordinator contract]({GITHUB}/blob/main/roles/coordinator.md)" in page("spec.md")
    assert f"[licence]({GITHUB}/blob/main/LICENSE)" in index  # no extension, still a file


def test_a_root_relative_link_resolves_against_the_repo_root(upstream):
    sync()
    # "/docs/identities.md" means the repo's docs/identities.md, as it does on
    # GitHub — not a URL path, and never a doubled slash in a blob link.
    assert "[root-relative](identities.md)" in page("index.md")


def test_a_link_above_the_repo_root_is_left_alone_and_reported(upstream, capsys):
    sync()
    # docs/introduction.md's "../../README.md" escapes the repo: there is no
    # target to rewrite to, and the strict build is what catches it.
    assert "[above root](../../README.md)" in page("index.md")
    assert "escapes the repo root" in capsys.readouterr().out


def test_external_urls_and_bare_anchors_are_left_alone(upstream):
    sync()
    assert "[gh](https://cli.github.com/)" in page("index.md")
    assert "[top](#top)" in page("index.md")
    assert "[an agent](agent://<agent id>)" in page("spec.md")  # SPEC's own scheme


def test_links_into_an_excluded_subtree_go_to_github(upstream):
    # The upstream fixture still has milestone records: the exclusion is proved
    # against a tree that has them, not one that happens not to.
    sync()
    index = page("index.md")
    assert f"[records]({GITHUB}/tree/main/docs/milestones)" in index  # the directory
    assert f"[one record]({GITHUB}/blob/main/docs/milestones/1-first.md)" in index
    assert "milestones/index.md" not in index  # no on-site landing page any more


def test_an_excluded_prefix_stops_at_a_path_boundary(upstream):
    # "milestones/" must not swallow a sibling called "milestones-archive/".
    sync()
    assert (DEST / "milestones-archive" / "kept.md").is_file()
    assert not (DEST / "milestones").exists()
    assert "Kept" in {label for label, _ in nav_entries(DEST)}


def test_github_url_picks_tree_for_a_directory_and_blob_for_a_file(upstream):
    # Asked of the checkout, not guessed from the absence of an extension.
    assert github_url("docs/milestones", is_image=False) == f"{GITHUB}/tree/main/docs/milestones"
    assert github_url("LICENSE", is_image=False) == f"{GITHUB}/blob/main/LICENSE"
    assert github_url("AGENTS.md", is_image=False) == f"{GITHUB}/blob/main/AGENTS.md"
    # A path that is not in the checkout at all cannot be a directory.
    assert github_url("ROADMAP.md", is_image=False) == f"{GITHUB}/blob/main/ROADMAP.md"
    # A fragment does not turn a directory into a file.
    assert (
        github_url("docs/milestones#m1", is_image=False)
        == f"{GITHUB}/tree/main/docs/milestones#m1"
    )


def test_the_nav_block_holds_the_whole_section_in_order(upstream):
    main()
    assert nav_block(upstream).splitlines()[1:] == [
        '  { "Docs" = [',
        '    { "Introduction" = "docs/index.md" },',
        '    { "Your first milestone" = "docs/first-milestone.md" },',
        '    { "Identities" = "docs/identities.md" },',
        '    { "Local extensions" = "docs/extensions.md" },',
        '    { "Platform interop" = "docs/platform-interop.md" },',
        '    { "Founding decisions" = "docs/founding-decisions.md" },',
        '    { "GSD vs. \\"just let the model orchestrate\\"" = "docs/gsd-vs-frontier-orchestration.md" },',
        '    { "CodeCrew Protocol Specification" = "docs/spec.md" },',
        '    { "Kept" = "docs/milestones-archive/kept.md" },',
        '    { "Contributing" = "docs/contributing.md" },',
        '    { "Security" = "docs/security.md" },',
        '  ] },',
    ]
    # No record reaches the nav; the similarly-named sibling still does.
    assert "docs/milestones/" not in nav_block(upstream)
    # The Docs tab sits between Home and Blog, and nothing outside the markers moved.
    config = (upstream / "zensical.toml").read_text(encoding="utf-8")
    assert config.index('"Home"') < config.index('"Docs"') < config.index('"Blog"')


def test_guide_labels_drop_a_subtitle(upstream):
    sync()
    labels = {label for label, _ in nav_entries(DEST)}
    assert "Identities" in labels  # "Identities: running solo, staffing a crew"
    assert "Local extensions" in labels  # "Local extensions — `roles/<role>.local.md`"
    assert 'GSD vs. "just let the model orchestrate"' in labels
    assert "CodeCrew Protocol Specification" in labels  # no subtitle to drop


def test_a_page_the_order_does_not_know_is_appended_before_the_trailing_pair(upstream):
    (upstream / "_sources/gh-codecrew/docs/zeta.md").write_text("# Zeta\n", encoding="utf-8")
    (upstream / "_sources/gh-codecrew/docs/alpha.md").write_text("# Alpha\n", encoding="utf-8")
    sync()
    labels = [label for label, _ in nav_entries(DEST)]
    assert labels.index("CodeCrew Protocol Specification") < labels.index("Alpha")
    assert labels.index("Alpha") < labels.index("Zeta")
    assert labels[-2:] == ["Contributing", "Security"]


def test_the_generated_config_parses_whatever_a_title_carries(upstream):
    hostile = {
        "docs/backslash.md": "# Path C:\\users\n",
        "docs/control.md": "# Bell \x07 and tab\n",
        "docs/quoted.md": '# He said "hello"\n',
    }
    for relpath, content in hostile.items():
        (upstream / "_sources/gh-codecrew" / relpath).write_text(content, encoding="utf-8")
    main()
    config = tomllib.loads((upstream / "zensical.toml").read_text(encoding="utf-8"))
    docs = next(entry["Docs"] for entry in config["nav"] if "Docs" in entry)
    labels = {label for entry in docs for label in entry}
    # Round-trips exactly: the backslash is a backslash, not an escape.
    assert "Path C:\\users" in labels
    assert 'He said "hello"' in labels
    assert "Bell \x07 and tab" in labels


def test_toml_string_escapes_what_toml_requires():
    assert toml_string("plain") == '"plain"'
    assert toml_string("back\\slash") == '"back\\\\slash"'
    assert toml_string('say "hi"') == '"say \\"hi\\""'
    assert toml_string("line\nbreak") == '"line\\nbreak"'
    assert toml_string("bell\x07") == '"bell\\u0007"'
    for value in ("back\\slash", 'say "hi"', "line\nbreak", "bell\x07"):
        assert tomllib.loads(f"x = {toml_string(value)}")["x"] == value


def test_the_sync_is_idempotent(upstream):
    main()
    first_tree, first_config = synced(), (upstream / "zensical.toml").read_text()
    main()
    assert synced() == first_tree
    assert (upstream / "zensical.toml").read_text() == first_config


def test_a_removed_upstream_page_does_not_survive_the_next_sync(upstream):
    sync()
    (upstream / "_sources/gh-codecrew/docs/extensions.md").unlink()
    sync()
    assert "extensions.md" not in synced()


def test_without_an_upstream_the_sync_fails_loudly_and_leaves_no_nav_entries(
    upstream, monkeypatch
):
    main()
    assert DEST.exists() and '"Docs"' in nav_block(upstream)

    monkeypatch.setenv("SYNC_SOURCE_BASE", str(upstream / "nowhere"))
    with pytest.raises(SystemExit) as exit_info:
        main()
    # The site cannot build without the upstream — the home page's docs button
    # targets the section index — so this is an error, not a quiet degrade.
    assert "no gh-codecrew checkout" in str(exit_info.value)
    assert "SYNC_SOURCE_BASE" in str(exit_info.value)
    assert not DEST.exists()
    assert nav_block(upstream).strip() == sync_docs.NAV_BEGIN  # no dangling nav entries


def test_missing_markers_are_an_error_not_a_silent_no_op(upstream):
    (upstream / "zensical.toml").write_text("nav = []\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="BEGIN_DOCS_NAV"):
        write_docs_nav([("Docs", "docs/index.md")])
