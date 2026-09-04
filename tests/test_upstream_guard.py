"""The strict site-build module's guard: found through SYNC_SOURCE_BASE or the
sibling directory; absent, it skips only when no source was named, and fails
when one was. Exercised against scratch trees, so these run — and mean the
same thing — whether or not this machine has a gh-codecrew checkout."""

from pathlib import Path

import pytest

from upstream_guard import SKIP_REASON, UPSTREAM_NAME, absent_upstream, find_upstream


@pytest.fixture
def root(tmp_path: Path) -> Path:
    """This repo, as a directory with no gh-codecrew beside it."""
    repo = tmp_path / "www" / "codecrew-www"
    repo.mkdir(parents=True)
    return repo


def test_the_variable_names_the_directory_holding_the_checkout(root: Path, tmp_path: Path) -> None:
    (tmp_path / "_sources" / UPSTREAM_NAME).mkdir(parents=True)
    assert find_upstream(str(tmp_path / "_sources"), root) == tmp_path / "_sources"


def test_a_relative_variable_resolves_against_the_repo(root: Path) -> None:
    (root / "_sources" / UPSTREAM_NAME).mkdir(parents=True)
    assert find_upstream("_sources", root) == root / "_sources"


def test_without_the_variable_a_sibling_clone_is_found(root: Path) -> None:
    (root.parent / UPSTREAM_NAME).mkdir()
    assert find_upstream(None, root) == root.parent


def test_a_missing_checkout_is_none_either_way(root: Path, tmp_path: Path) -> None:
    (tmp_path / "empty").mkdir()
    assert find_upstream(str(tmp_path / "empty"), root) is None
    assert find_upstream(None, root) is None


def test_absent_and_unnamed_skips_with_the_reason(root: Path) -> None:
    assert absent_upstream(None, root) == SKIP_REASON
    assert UPSTREAM_NAME in SKIP_REASON and "SYNC_SOURCE_BASE" in SKIP_REASON


def test_absent_but_named_fails_and_says_where_it_looked(root: Path, tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(pytest.fail.Exception) as failure:
        absent_upstream(str(empty), root)
    message = str(failure.value)
    assert f"SYNC_SOURCE_BASE={str(empty)!r}" in message
    assert str(empty.resolve()) in message
    assert UPSTREAM_NAME in message
    assert not failure.value.pytrace, "the failure is a message, not a traceback"
