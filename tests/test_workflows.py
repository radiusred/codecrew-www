"""The two workflows do what M9-R5 says: check radiusred/gh-codecrew out where
the sync reads it, run the sync before the build, and build strict.

Read as text rather than parsed: the repo declares no YAML dependency, and the
steps are flat enough that each `- uses:`/`- run:` line, with the `with:` and
`env:` lines under it, is the unit these tests care about.
"""

import re
from pathlib import Path

import pytest

WORKFLOWS = Path(__file__).resolve().parent.parent / ".github" / "workflows"
HUB_CHECKOUT = "repository: radiusred/gh-codecrew"
STRICT_BUILD = "- run: zensical build --clean --strict"


def steps(workflow: str) -> list[str]:
    """Every step of the workflow as its own block, in file order."""
    text = (WORKFLOWS / workflow).read_text(encoding="utf-8")
    return [block.strip() for block in re.split(r"\n(?=\s+- (?:uses|run): )", text)[1:]]


def the_step(blocks: list[str], *marks: str) -> int:
    """The index of the one step whose block carries every mark."""
    found = [i for i, block in enumerate(blocks) if all(mark in block for mark in marks)]
    assert len(found) == 1, f"expected one step matching {marks}, found {len(found)}"
    return found[0]


@pytest.mark.parametrize(
    ("workflow", "consumer"),
    [("site.yml", "- run: python3 sync_docs.py"), ("ci.yml", "- run: uv run pytest")],
)
def test_the_hub_is_checked_out_where_the_sync_reads_it(workflow: str, consumer: str) -> None:
    blocks = steps(workflow)
    checkout = the_step(blocks, "- uses: actions/checkout@", HUB_CHECKOUT)
    assert "path: _sources/gh-codecrew" in blocks[checkout]
    reader = the_step(blocks, consumer)
    assert checkout < reader
    assert "SYNC_SOURCE_BASE: _sources" in blocks[reader]


def test_the_deploy_syncs_then_builds_strict() -> None:
    blocks = steps("site.yml")
    order = [
        the_step(blocks, HUB_CHECKOUT),
        the_step(blocks, "- run: python3 sync_docs.py"),
        the_step(blocks, "- run: python3 main.py"),
        the_step(blocks, "- run: zensical build"),
    ]
    assert order == sorted(order)
    assert blocks[order[-1]].splitlines()[0] == STRICT_BUILD


def test_the_lint_check_calls_the_shared_action_under_the_required_context() -> None:
    """The commitlint job is the thin caller radiusred/.github documents: a depth-0
    checkout, then the shared action, from a job named exactly as the org ruleset
    require-lint requires, with no commitlint config of this repo's own."""
    text = (WORKFLOWS / "ci.yml").read_text(encoding="utf-8")
    job = re.search(r"\n  commitlint:\n(.*?)(?=\n  \w|\Z)", text, re.S)
    assert job is not None, "ci.yml has no commitlint job"
    assert "    name: Lint commit messages\n" in job.group(1)
    assert "      pull-requests: read\n" in job.group(1)
    blocks = steps("ci.yml")
    checkout = the_step(blocks, "- uses: actions/checkout@", "fetch-depth: 0")
    lint = the_step(blocks, "- uses: radiusred/.github/.github/actions/commitlint@")
    assert checkout + 1 == lint
    assert not list(WORKFLOWS.parent.parent.glob("commitlint.config.*"))
