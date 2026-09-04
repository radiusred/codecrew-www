"""Where the strict site-build test finds radiusred/gh-codecrew, and what an
absent checkout means.

CI sets SYNC_SOURCE_BASE and checks the hub out under it; a local run usually
has a clone beside this repo instead. The two absences differ: a run that
named no source may skip the module on a machine without a clone, but a run
that set the variable and found nothing there has drifted — a renamed checkout
path, a variable dropped from a job — and the strict build, the only check that
the synced docs still link up, must fail rather than quietly stop running.
"""

from pathlib import Path

import pytest

UPSTREAM_NAME = "gh-codecrew"
SKIP_REASON = (
    f"needs a radiusred/{UPSTREAM_NAME} checkout beside this repo (or "
    "SYNC_SOURCE_BASE pointing at one): the docs section is synced from it"
)


def find_upstream(configured: str | None, root: Path) -> Path | None:
    """The directory holding a gh-codecrew checkout: SYNC_SOURCE_BASE's value
    (relative paths resolve against the repo root) when set, else the directory
    the repo sits in. None when no checkout is there."""
    candidate = Path(configured) if configured else root.parent
    if not candidate.is_absolute():
        candidate = root / candidate
    return candidate.resolve() if (candidate / UPSTREAM_NAME).is_dir() else None


def absent_upstream(configured: str | None, root: Path) -> str:
    """The reason to skip when no checkout was found and none was named. When
    SYNC_SOURCE_BASE was set, fail instead — loudly, since CI always sets it."""
    if configured:
        looked_in = (root / configured).resolve()
        pytest.fail(
            f"SYNC_SOURCE_BASE={configured!r} holds no {UPSTREAM_NAME} checkout "
            f"(looked in {looked_in}), so the strict site build cannot run. Check "
            f"radiusred/{UPSTREAM_NAME} out there, or unset the variable to skip this "
            "module on a machine without a clone.",
            pytrace=False,
        )
    return SKIP_REASON
