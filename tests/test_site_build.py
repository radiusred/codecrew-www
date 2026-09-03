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
# One rule for every code line on the page: the step lines (longest 33,
# the crew section's `identity new`) are held to the same 42.
STEP_CODE_MAX = 42
CREW_ROLES = ("implementer", "reviewer", "qa", "doc-synthesizer", "coordinator")
# One grab per How-it-works step, in order, with the anchor (a share of the
# image's height) that puts its distinguishing feature in the strip above
# the fade: the Requirements list, the Plan heading, the Merged badge and
# merged-by line, the document title.
STEP_IMAGES = (("milestone", "62%"), ("task", "64%"), ("pr", "21%"), ("record", "0%"))
CREW_MEMBER_NAMES = ("cody", "checky", "testy", "wordy")  # Radius Red's crew, not the framework's
INSTALL_COMMANDS = (
    "gh --version",
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


@pytest.fixture(scope="module")
def css(site: Path) -> str:
    return (site / "stylesheets" / "extra.css").read_text()


def rule(css: str, selector: str) -> str:
    """The declarations of the first rule whose selector line is exactly `selector`."""
    match = re.search(r"^" + re.escape(selector) + r"\s*\{([^}]*)\}", css, re.M)
    assert match, selector
    return match.group(1)


def section(page: str, name: str) -> str:
    """The markup of one home page section, by its `cc-*` class."""
    start = page.index(f'<section class="cc-section {name}')
    return page[start : page.index("</section>", start)]


def text(markup: str) -> str:
    """The visible text of a fragment: tags stripped, entities unescaped."""
    return html.unescape(re.sub(r"<[^>]+>", " ", markup))


def code_lines(block: str) -> list[str]:
    """The text lines of the first code block in `block`: what a copy of it yields."""
    code = re.search(r"<pre>.*?<code[^>]*>(.*?)</code>", block, re.S).group(1)
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
    assert 'class="md-footer cc-footer"' in home  # its own ground, apart from Start now
    assert "md-social" in home


def test_home_keeps_the_header(home: str):
    assert 'data-md-component="header"' in home
    assert 'data-md-component="search"' in home
    assert 'data-md-component="palette"' in home
    assert 'class="md-tabs"' in home


def test_home_has_the_product_page_flow(home: str):
    order = ("cc-hero", "cc-how", "cc-crew", "cc-why", "cc-proof", "cc-start")
    positions = [home.index(f"cc-section {name}") for name in order]
    assert positions == sorted(positions)  # the crew sits between How it works and Why
    assert 'id="start-now"' in home


def test_hero_carries_the_logo_and_both_calls_to_action(home: str):
    hero = section(home, "cc-hero")
    assert 'class="cc-hero__logo"' in hero
    assert 'class="cc-logo"' in hero
    assert 'class="cc-hero__body"' in hero
    assert "cc-hero__headline" in hero
    assert "Agent-driven software delivery" in hero
    assert "CodeCrew is an engineering process framework, and a small one" in hero
    assert "the answer is in a chat transcript nobody saved" in hero  # the antecedent
    assert "Decisions and deviations" not in hero  # said once, in the Why panel
    assert 'href="#start-now"' in hero  # primary call to action
    assert 'href="https://github.com/radiusred/gh-codecrew#readme"' in hero


def test_home_has_exactly_one_install_block(home: str):
    assert home.count('class="cc-install cc-term"') == 1
    assert "cc-install" not in section(home, "cc-hero")
    assert "cc-install" in section(home, "cc-start")
    assert "language-sh highlight" not in home  # the terminal window replaced the fenced block


def test_install_block_is_a_terminal_window_that_copies_clean(home: str):
    start = section(home, "cc-start")
    term = start[start.index('<div class="cc-install cc-term">') : start.index("</pre>")]
    assert 'class="cc-term__bar"' in term and term.count('class="cc-term__dot"') == 3
    assert 'class="cc-term__title">~/my-project<' in term
    assert term.count('<span class="cc-term__line"') == 5
    outputs = [html.unescape(o) for o in re.findall(r'data-out="([^"]+)"', term)]
    assert outputs == [
        ">= 2.50.0 required",
        "any repo on GitHub, new or years old",
        "writes and commits the CodeCrew files",
        "or codex, or whichever agent you run",
    ]
    lines = code_lines(start)  # the DOM text: what the copy button yields
    assert lines == list(INSTALL_COMMANDS)  # five runnable lines, the version check first
    assert "Two things to have first" not in start  # the prerequisites paragraph is gone
    assert "$" not in "".join(lines)  # the prompt is CSS, never typed
    too_long = [line for line in lines if len(line) > INSTALL_LINE_MAX]
    assert not too_long, too_long
    assert term.index("</code>") > term.index(INSTALL_COMMANDS[-1])
    assert 'class="cc-term__line"' in term and "\n" in term  # one command per line


def test_terminal_prompt_and_output_are_generated_content(css: str):
    assert 'content: "$"' in rule(css, ".cc-term__line::before")
    assert "attr(data-out)" in rule(css, ".cc-term__line[data-out]::after")
    window = rule(css, ".cc-term")
    assert "width: fit-content" in window and "max-width: 100%" in window and "margin: 0 auto" in window


def test_how_it_works_leads_with_the_three_moments_and_marks_each_speaker(home: str):
    how = section(home, "cc-how")
    lead = "You are needed at three moments"
    assert lead in how
    assert how.index('class="cc-how__lead"') < how.index('class="cc-steps"')
    assert lead not in section(home, "cc-start")
    steps = re.split(r'<div class="cc-step(?: [^"]*)?"[^>]*>', how)[1:]  # not .cc-steps
    assert len(steps) == 4
    for step in steps:
        heading = re.search(r"<h3[^>]*>(.*?)</h3>", step, re.S).group(1)
        assert '<span class="twemoji">' in heading  # the Lucide glyph before the step's name
        agent = re.search(r'<p class="cc-step__line cc-step__agent">(.*?)</p>', step, re.S).group(1)
        you = re.search(r'<p class="cc-step__line cc-step__you">(.*?)</p>', step, re.S).group(1)
        assert '<span class="twemoji">' in agent and "<title>Claude</title>" in agent  # the Claude glyph
        assert '<span class="twemoji">' in you and "<title>" not in you  # the lucide person glyph
        snippets = [html.unescape(m) for m in re.findall(r"<code>(.*?)</code>", agent)]
        assert len(snippets) == 1 and snippets[0].startswith("gh codecrew "), step
        too_long = [snippet for snippet in snippets if len(snippet) > STEP_CODE_MAX]
        assert not too_long, too_long


def test_each_step_carries_its_muted_screen_grab(css: str, home: str, site: Path):
    image = rule(css, ".cc-step--bg::before")
    assert "aspect-ratio: var(--cc-step-bg-ratio" in image and "translateY(calc(-1 * var(--cc-step-bg-y" in image
    assert "filter: saturate(0.7) contrast(0.9) brightness(0.9)" in image  # eased so the grab is recognisable
    fade = rule(css, ".cc-step--bg::after")
    assert "linear-gradient(180deg, #0a001226 0" in fade and "var(--cc-ink) 8.8rem" in fade  # clear at the top, solid before the description
    assert "padding: 7.2rem" in rule(css, ".cc-step--bg")  # the heading sits over the tail of the fade
    openings = re.findall(
        r'<div class="cc-step cc-step--bg" style="--cc-step-bg: url\(([^)]+)\); --cc-step-bg-ratio: \d+ / \d+; --cc-step-bg-y: (\d+%)">',
        section(home, "cc-how"),
    )
    assert openings == [(f"../assets/images/steps/{name}.webp", anchor) for name, anchor in STEP_IMAGES]
    for url, _ in openings:
        # Chromium resolves a url() in a custom property from the stylesheet that uses it.
        assert (site / "stylesheets" / url).resolve().is_file(), url
    strays = [p.name for p in (site / "assets" / "images").glob("*.png") if p.stem in [n for n, _ in STEP_IMAGES] + ["docs"]]
    assert not strays, strays  # the grabs live under steps/ only


def test_crew_section_names_the_seats_and_no_crew_member(home: str, css: str):
    crew = section(home, "cc-crew")
    badges = re.findall(r'<img src="assets/images/crew/[^"]+"[^>]*>\s*<figcaption>([^<]+)</figcaption>', crew)
    assert tuple(badges) == CREW_ROLES
    assert "identity new reviewer" in crew
    assert "background: var(--cc-purple)" in rule(css, ".md-typeset .cc-crew__badge img")  # white marks need a ground
    lower = text(home).lower()
    for name in CREW_MEMBER_NAMES:
        assert not re.search(rf"\b{name}\b", lower), name  # bot logins may live in link targets only


def test_why_panels_carry_one_glyph_each_and_no_picture(home: str, site: Path):
    why = section(home, "cc-why")
    assert "<img" not in why
    assert not (site / "assets" / "images" / "hub-and-spokes.svg").exists()
    panels = why.split('<div class="cc-panel">')[1:]
    assert len(panels) == 3
    for panel in panels:
        glyphs = re.findall(r'<p class="cc-panel__glyph">(.*?)</p>', panel, re.S)
        assert len(glyphs) == 1 and glyphs[0].count('<span class="twemoji">') == 1, panel[:80]
        assert panel.index("cc-panel__glyph") < panel.index("<h3")  # the glyph tops the panel
    assert "One repo is the hub" in why


def test_alternate_bands_carry_the_glow_in_both_schemes(css: str):
    assert "radial-gradient" in rule(css, ".cc-section--alt")
    slate = rule(css, '[data-md-color-scheme="slate"] .cc-section--alt')
    assert "radial-gradient" in slate and "var(--cc-ink)" in slate


def test_home_footer_has_its_own_ground(css: str):
    footer = rule(css, ".cc-footer")
    assert "--md-default-bg-color: var(--cc-purple)" in footer  # what .md-footer is painted with
    assert "--md-default-fg-color: #ffffff" in footer
    assert "border-top" in footer


def test_home_links_take_the_pink_and_buttons_keep_the_cyan(css: str):
    assert "--cc-pink: #ce5ae9;" in rule(css, ":root")
    assert "--cc-pink-deep:" in rule(css, ":root")
    assert "--md-typeset-a-color: var(--cc-pink-deep)" in rule(css, ".cc-home")
    assert "--md-typeset-a-color: var(--cc-pink)" in rule(css, '[data-md-color-scheme="slate"] .cc-home')
    assert "--md-typeset-a-color: var(--cc-pink)" in rule(css, ".cc-section.cc-hero")
    assert "--cc-pink" not in rule(css, ".md-typeset .cc-button")
    assert "var(--cc-cyan-tint)" in rule(css, ".md-typeset .cc-button--primary")


def test_blog_keeps_the_default_layout(blog: str):
    assert "cc-home" not in blog
    assert "md-content__inner" in blog
    assert "md-sidebar--primary" in blog
    assert "md-sidebar--secondary" in blog
    assert "md-footer__inner" in blog
    assert "cc-button" not in blog
    assert "cc-section" not in blog
    assert "cc-footer" not in blog
