"""Build the site and check the home page template against the rest.

The home page (docs/index.md) selects docs/overrides/home.html and hides the
navigation, toc and footer nav. Every other page keeps Zensical's default
layout. `zensical build` has no site-dir option, so the fixture copies the
site source into a temp dir and builds there, in strict mode so any warning
fails the build.
"""

import html
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

# Measured in headless Chromium at a 420px viewport (root font 20px, code
# 12.8px JetBrains Mono, 16px of padding a side): the install block's code
# column holds 43 characters before it scrolls sideways. The longest command
# is 42. Longer lines scroll on a phone.
INSTALL_LINE_MAX = 42
# The same measurement for an inline code element inside a How-it-works
# step: about 46 characters at 420px. The longest verb line is 44.
STEP_CODE_MAX = 44
INSTALL_COMMANDS = (
    "gh extension install radiusred/gh-codecrew",
    "cd my-project",
    "gh codecrew init",
    "claude",
)


@pytest.fixture(scope="module")
def site(tmp_path_factory) -> Path:
    src = tmp_path_factory.mktemp("codecrew-www")
    shutil.copytree(ROOT / "docs", src / "docs")
    shutil.copy(ROOT / "zensical.toml", src / "zensical.toml")
    result = subprocess.run(
        [sys.executable, "-m", "zensical", "build", "--clean", "--strict"],
        cwd=src,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return src / "site"


@pytest.fixture(scope="module")
def home(site: Path) -> str:
    return (site / "index.html").read_text()


@pytest.fixture(scope="module")
def blog(site: Path) -> str:
    return (site / "blog" / "index.html").read_text()


def section(page: str, name: str) -> str:
    """The markup of one home page section, by its `cc-*` class."""
    start = page.index(f'<section class="cc-section {name}')
    return page[start : page.index("</section>", start)]


def code_lines(block: str) -> list[str]:
    """The text lines of the first highlighted code block in `block`."""
    code = re.search(r"<pre>.*?<code>(.*?)</code>", block, re.S).group(1)
    lines = [html.unescape(re.sub(r"<[^>]+>", "", line)) for line in code.split("\n")]
    return [line for line in lines if line.strip()]


def test_home_uses_the_home_template(home: str):
    assert 'class="md-content cc-home"' in home
    assert "md-content__inner" not in home  # no reading column
    assert "rr-page-meta" not in home  # the "published on" override is bypassed


def test_home_has_no_sidebars_or_footer_nav(home: str):
    assert "md-sidebar--primary" not in home
    assert "md-sidebar--secondary" not in home
    assert "md-footer__inner" not in home  # prev/next navigation
    assert "md-footer-meta" in home  # copyright + social strip stays
    assert "md-social" in home


def test_home_keeps_the_header(home: str):
    assert 'data-md-component="header"' in home
    assert 'data-md-component="search"' in home
    assert 'data-md-component="palette"' in home
    assert 'class="md-tabs"' in home


def test_home_has_the_product_page_flow(home: str):
    for name in ("cc-hero", "cc-how", "cc-why", "cc-proof", "cc-start"):
        assert f"cc-section {name}" in home, name
    assert 'id="start-now"' in home


def test_hero_carries_the_logo_and_both_calls_to_action(home: str):
    hero = section(home, "cc-hero")
    assert 'class="cc-hero__logo"' in hero
    assert 'class="cc-logo"' in hero
    assert 'class="cc-hero__body"' in hero
    assert "cc-hero__headline" in hero
    assert "Agent-driven software delivery" in hero
    assert "CodeCrew is an engineering process framework, and a small one" in hero
    assert 'href="#start-now"' in hero  # primary call to action
    assert 'href="https://github.com/radiusred/gh-codecrew#readme"' in hero


def test_home_has_exactly_one_install_block(home: str):
    assert home.count("language-sh highlight") == 1
    assert "cc-install" not in section(home, "cc-hero")
    assert "cc-install" in section(home, "cc-start")


def test_install_block_fits_a_phone_and_keeps_the_commands(home: str):
    lines = code_lines(section(home, "cc-start"))
    assert [line for line in lines if not line.startswith("#")] == list(INSTALL_COMMANDS)
    too_long = [line for line in lines if len(line) > INSTALL_LINE_MAX]
    assert not too_long, too_long


def test_how_it_works_leads_with_the_three_moments_and_names_a_verb_per_step(home: str):
    how = section(home, "cc-how")
    lead = "You do not run the verbs. Your agent does."
    assert lead in how
    assert how.index('class="cc-how__lead"') < how.index('class="cc-steps"')
    assert lead not in section(home, "cc-start")
    steps = how.split('<div class="cc-step">')[1:]
    assert len(steps) == 4
    for step in steps:
        snippets = [html.unescape(m) for m in re.findall(r"<code>(.*?)</code>", step)]
        assert snippets and snippets[0].startswith("gh codecrew "), step
        too_long = [snippet for snippet in snippets if len(snippet) > STEP_CODE_MAX]
        assert not too_long, too_long


def test_blog_keeps_the_default_layout(blog: str):
    assert "cc-home" not in blog
    assert "md-content__inner" in blog
    assert "md-sidebar--primary" in blog
    assert "md-sidebar--secondary" in blog
    assert "md-footer__inner" in blog
    assert "cc-button" not in blog
    assert "cc-section" not in blog
