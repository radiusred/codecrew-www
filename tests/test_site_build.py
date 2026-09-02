"""Build the site and check the home page template against the rest.

The home page (docs/index.md) selects docs/overrides/home.html and hides the
navigation, toc and footer nav. Every other page keeps Zensical's default
layout. `zensical build` has no site-dir option, so the fixture copies the
site source into a temp dir and builds there, in strict mode so any warning
fails the build.
"""

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


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


def section(html: str, name: str) -> str:
    """The markup of one home page section, by its `cc-*` class."""
    start = html.index(f'<section class="cc-section {name}')
    return html[start : html.index("</section>", start)]


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


def test_blog_keeps_the_default_layout(blog: str):
    assert "cc-home" not in blog
    assert "md-content__inner" in blog
    assert "md-sidebar--primary" in blog
    assert "md-sidebar--secondary" in blog
    assert "md-footer__inner" in blog
