"""Build the site and check the home page template against the rest.

The home page (docs/index.md) selects docs/overrides/home.html and hides the
navigation, toc and footer nav. Every other page — the blog, and the docs
section sync_docs.py builds from radiusred/gh-codecrew — keeps Zensical's
default layout. `zensical build` has no site-dir option, so the fixture copies
the site source into a temp dir, runs the sync there, and builds in strict mode
so any warning fails the build.

The build needs the upstream on disk, since the nav and the hero's button both
point into the synced section: the module skips without one. CI checks it out,
so it never skips there.
"""

import html
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
UPSTREAM_NAME = "gh-codecrew"


def upstream_base() -> Path | None:
    """The directory holding a radiusred/gh-codecrew checkout: what CI points
    SYNC_SOURCE_BASE at, else the sibling directory a local clone sits in."""
    configured = os.environ.get("SYNC_SOURCE_BASE")
    candidate = Path(configured) if configured else ROOT.parent
    if not candidate.is_absolute():
        candidate = ROOT / candidate
    return candidate.resolve() if (candidate / UPSTREAM_NAME).is_dir() else None


UPSTREAM = upstream_base()
pytestmark = pytest.mark.skipif(
    UPSTREAM is None,
    reason=(
        "needs a radiusred/gh-codecrew checkout beside this repo (or "
        "SYNC_SOURCE_BASE pointing at one): the docs section is synced from it"
    ),
)

# Measured in headless Chromium at a 420px viewport (root font 20px, code
# 12.8px JetBrains Mono, 16px of padding a side): the install block's code
# column holds 43 characters before it scrolls sideways. The longest command
# is 42. Longer lines scroll on a phone.
INSTALL_LINE_MAX = 42
# One rule for every code line on the page: the step lines (longest 33,
# the crew section's `identity new`) are held to the same 42.
STEP_CODE_MAX = 42
CREW_ROLES = ("implementer", "reviewer", "qa", "doc-synthesizer", "coordinator")
CREW_MEMBER_NAMES = ("cody", "checky", "testy", "wordy")  # Radius Red's crew, not the framework's
# The receipts: glyph, header, strapline, and the popover's detail with its link target.
RECEIPTS = (
    ("milestone", "Every milestone shipped this way.", "Agent-authored, independently reviewed.",
     "deterministic CI gates, QA verdicts enforced at close, and a synthesized document for each", "https://github.com/radiusred/gh-codecrew/tree/main/docs/milestones"),
    ("megaphone", "The first spoke published its own announcement.", "Driven from the hub, in public.",
     "delivered by the protocol it describes", "https://www.radiusred.uk/blog/posts/2026-08-20-this-post-was-delivered-by-the-framework-it-introduces/"),
    ("bot", "This project is agent-staffed, and you can check.", "Four seats, four App identities.",
     "A reviewer App minted with write access satisfies GitHub's own required-review rule", "https://github.com/radiusred/codecrew-www/pull/3"),
    ("network", "It scales from solo, to a team, to an orchestration platform.", "Same protocol, any routing table.",
     "with a dedicated coordinator agent from the first event", "https://github.com/radiusred/gh-codecrew/issues/164"),
)
# The crew popovers: the opening of each contract in radiusred/gh-codecrew's roles/<role>.md,
# reused verbatim (copied at the hub's main of 2026-09-03; the hub is not on CI's disk).
ROLE_OPENINGS = {
    "implementer": "You implement one CodeCrew task. Your work is judged by someone else — build for the reviewer, the QA agent, and the person reading the audit trail in three weeks.",
    "reviewer": "You review one CodeCrew PR. You exist because self-evaluation shares the blind spots of the work itself — your value is independence, so form your own view before reading the implementer's narrative.",
    "qa": "You exercise what was built against what was promised. The reviewer judges the diff; you judge the behaviour. Run the thing.",
    "doc-synthesizer": "You write the milestone document — the record that lets someone in three months understand why the system is the way it is. You compile what was recorded; you do not invent what wasn't.",
    "coordinator": "You run the delivery loop for a CodeCrew project and hold no seat in it. You open the milestones and the tasks, dispatch the crew seats by the routing table, own the review loop in both directions, raise the gates only a human can answer, and drive the milestone verbs. You never write code, review, verdict or merge: your product is the record on GitHub and one correct dispatch per transition.",
}
# The conversation under each step: the human's line and the verb the agent runs.
STEP_CHAT = (
    ("Let's add a new feature.", "gh codecrew milestone new"),
    ("Plan it and get started.", "gh codecrew task start"),
    ("Reviewed and approved.", "gh codecrew task finish"),
    ("That's everything. Close it.", "gh codecrew milestone close"),
)
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
    # The synced tree is generated, never committed: drop any local copy and
    # rebuild it here, so this exercises the sync the deploy actually runs.
    shutil.copytree(ROOT / "docs", src / "docs", ignore=shutil.ignore_patterns("docs"))
    shutil.copy(ROOT / "zensical.toml", src / "zensical.toml")
    shutil.copy(ROOT / "sync_docs.py", src / "sync_docs.py")
    synced = subprocess.run(
        [sys.executable, "sync_docs.py"],
        cwd=src,
        env={**os.environ, "SYNC_SOURCE_BASE": str(UPSTREAM)},
        capture_output=True,
        text=True,
    )
    assert synced.returncode == 0, synced.stdout + synced.stderr
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


def drawer(page: str) -> str:
    """The markup of the primary sidebar: what the header's burger opens."""
    start = page.index('<div class="md-sidebar md-sidebar--primary"')
    return page[start : page.index("</main>", start)]


def section(page: str, name: str) -> str:
    """The markup of one home page section, by its `cc-*` class."""
    start = page.index(f'<section class="cc-section {name}')
    return page[start : page.index("</section>", start)]


def text(markup: str) -> str:
    """The visible text of a fragment: glyphs (whose SVG carries a title) dropped, tags stripped, entities unescaped."""
    markup = re.sub(r'<span class="twemoji">.*?</svg></span>', " ", markup, flags=re.S)
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


def test_home_drops_the_desktop_sidebars_and_the_footer_nav(home: str):
    # The primary sidebar is present but `hidden`, which is not the same as
    # absent: Zensical gives .md-sidebar--primary display:block below the
    # tab-collapse breakpoint, so this one element is both the desktop sidebar
    # M8-R1 drops and the drawer its retained tabs collapse into. It used to be
    # removed outright, which left the burger opening an empty overlay (#9).
    sidebar = re.search(r'<div class="md-sidebar md-sidebar--primary"[^>]*>', home)
    assert sidebar and "hidden" in sidebar.group(0)
    assert "md-sidebar--secondary" not in home  # no "on this page" panel
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
    assert 'href="docs/"' in hero  # the docs on this site, not the README on GitHub
    assert "github.com" not in hero


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


def test_payoff_line_sits_beside_the_terminal(home: str, css: str):
    start = section(home, "cc-start")
    pair = re.search(r'<div class="cc-start__pair">(.*?)\n</div>\n</div>\n', start, re.S).group(1)
    assert pair.index('class="cc-install cc-term"') < pair.index('class="cc-start__payoff"')  # terminal, then the line, as siblings
    payoff = re.search(r'<p class="cc-start__payoff">(.*?)</p>', pair, re.S).group(1)
    assert '<span class="cc-start__lead">Then one sentence to your agent:</span>' in payoff
    assert "“Let's build this project!”" in html.unescape(payoff)  # double quotes carry the emphasis
    assert "<em>" not in payoff  # the italic went
    assert "Then one sentence" not in start.replace(payoff, "")  # said once
    assert "grid-template-columns: 1fr" in rule(css, ".cc-start__pair")  # stacked on phones
    # The indented form lives only inside a media block; the 60em block for this pair is the stylesheet's last one.
    assert "@media screen and (min-width: 60em) {\n  .cc-start__pair {\n    grid-template-columns: auto 1fr;" in css  # beside it from 60em
    assert "font-size: 1.8rem" in rule(css, ".md-typeset .cc-start .cc-start__payoff")


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
    assert "the bubble on the right is the one it runs" in how  # the lead describes the bubbles
    steps = re.split(r'<div class="cc-step(?: [^"]*)?"[^>]*>', how)[1:]  # not .cc-steps
    assert len(steps) == 4
    for step, (line, verb) in zip(steps, STEP_CHAT):
        heading = re.search(r"<h3[^>]*>(.*?)</h3>", step, re.S).group(1)
        assert '<span class="twemoji">' in heading  # the Lucide glyph before the step's name
        chat = re.search(r'<div class="cc-chat">(.*?)</div>', step, re.S).group(1)
        you = re.search(r'<p class="cc-bubble cc-bubble--you">(.*?)</p>', chat, re.S).group(1)
        agent = re.search(r'<p class="cc-bubble cc-bubble--agent">(.*?)</p>', chat, re.S).group(1)
        assert chat.index("cc-bubble--you") < chat.index("cc-bubble--agent")  # the human speaks first
        assert '<span class="twemoji">' in you and "<title>" not in you  # the lucide person glyph
        assert text(you).strip() == line  # one short line of speech
        assert '<span class="twemoji">' in agent and "<title>Claude</title>" in agent  # the Claude glyph
        snippets = [html.unescape(m) for m in re.findall(r"<code>(.*?)</code>", agent)]
        assert snippets == [verb]  # exactly one code line, the verb unchanged
        assert len(verb) <= STEP_CODE_MAX
        assert text(agent).strip() == verb  # nothing in the agent's bubble but the verb


def test_steps_are_plain_cards_with_no_grab(css: str, home: str, site: Path):
    assert "content: counter(cc-step)" in rule(css, ".md-typeset .cc-step h3::before")  # the accent number
    assert "var(--md-accent-fg-color)" in rule(css, ".md-typeset .cc-step h3 .twemoji")  # the accent glyph
    assert "cc-step--bg" not in home
    assert "steps/" not in home  # no step image referenced
    assert not (site / "assets" / "images" / "steps").exists()
    assert "cc-step--bg" not in css  # the rules went with the images


def media_block(css: str, query: str) -> str:
    """The body of the first `@media <query>` block."""
    start = css.index(f"@media {query} {{")
    depth, i = 0, start
    while True:
        if css[i] == "{":
            depth += 1
        elif css[i] == "}":
            depth -= 1
            if depth == 0:
                return css[start:i]
        i += 1


def test_proof_captures_are_two_halves_of_one_review(css: str, home: str, site: Path):
    proof = section(home, "cc-proof")
    assert proof.index('class="cc-captures"') < proof.index('class="cc-receipts"')  # under the heading, above the receipts
    images = re.findall(r'<figure class="cc-capture"><img src="(assets/images/proof/[^"]+)"[^>]*alt="[^"]+"[^>]*></figure>', proof)
    assert images == ["assets/images/proof/pr-review-top.webp", "assets/images/proof/pr-review-bottom.webp"]  # top, then bottom
    for url in images:
        assert (site / url).is_file(), url
    assert not (site / "assets" / "images" / "proof" / "pr-review.webp").exists()  # the single tall capture is gone
    assert "perspective: 60rem" in rule(css, ".cc-captures")
    card = rule(css, ".md-typeset .cc-capture")
    assert "flex: 0 1 26.5rem" in card and "position: relative" in card  # readable size; positioned for z-order
    first, second = rule(css, ".md-typeset .cc-capture:nth-child(1)"), rule(css, ".md-typeset .cc-capture:nth-child(2)")
    assert "rotateY(8deg)" in first and "rotateY(-8deg)" in second
    assert "margin-left: -4rem" in second and "z-index: 1" in second  # the second overlaps the first's right edge, above it
    for prefix in ("-webkit-mask-image", "mask-image"):  # the fades, on the whole card
        assert f"{prefix}: linear-gradient(180deg, #000 86%, transparent 100%)" in first
        assert f"{prefix}: linear-gradient(180deg, transparent 0, #000 14%)" in second
    assert ":empty" not in css  # both cards always render
    phone = media_block(css, "screen and (max-width: 44.9375em)")
    assert "perspective: none" in phone and "rotateY" not in phone and "mask" not in phone  # flat, fades kept
    assert ".md-typeset .cc-capture:nth-child(n) {\n    margin-left: 0;\n    transform: none;" in phone  # no overlap, no tilt on phones
    assert "cc-proof--bg" not in css and "cc-proof--bg" not in home


def squash(s: str) -> str:
    """Collapse whitespace, including the space `text()` leaves where a tag closed before punctuation."""
    return re.sub(r" ([.,;:])", r"\1", " ".join(s.split()))


def test_proof_caption_heading_and_uniform_receipt_cards(home: str):
    proof = section(home, "cc-proof")
    assert re.search(r'<h2 id="codecrew-works">CodeCrew Works<a class="headerlink"', proof)  # nothing linked the old id
    caption = re.search(r'<p class="cc-captures__caption">(.*?)</p>', proof, re.S).group(1)
    assert squash(text(caption)) == "A pull request merged after a change request. Author and reviewer are CodeCrew App identities."
    assert '<a href="#the-crew">CodeCrew App identities</a>' in caption
    assert 'id="the-crew"' in section(home, "cc-crew")
    cards = re.split(r'<div class="cc-receipt cc-pop" tabindex="0">', proof)[1:]
    assert len(cards) == 4 and proof.count('class="cc-receipt ') == 4 and 'class="cc-receipt"' not in proof  # every receipt is a trigger
    for card, (glyph, header, strap, detail, href) in zip(cards, RECEIPTS):
        glyph_p = re.search(r'<p class="cc-receipt__glyph">(.*?)</p>', card, re.S).group(1)
        assert glyph_p.count('<span class="twemoji">') == 1
        assert f"<p><strong>{header}</strong></p>" in card
        assert f'<p class="cc-receipt__strap">{strap}</p>' in card
        panel = re.search(r'<div class="cc-pop__panel">(.*?)</div>', card, re.S).group(1)
        assert detail in squash(text(panel)) and f'href="{href}"' in panel
        assert card.index("cc-receipt__glyph") < card.index("<strong>") < card.index("cc-receipt__strap") < card.index("cc-pop__panel")
    assert "cody" not in text(proof).lower() and "checky" not in text(proof).lower()  # role names only


def test_crew_badges_open_popovers_quoting_the_contracts(home: str):
    crew = section(home, "cc-crew")
    figures = re.findall(r'<figure class="cc-crew__badge cc-pop" tabindex="0">(.*?)</figure>', crew, re.S)
    assert len(figures) == 5
    for figure, role in zip(figures, CREW_ROLES):
        assert re.search(rf"<figcaption>{role}</figcaption>", figure)
        panel = re.search(r'<div class="cc-pop__panel">(.*?)</div>', figure, re.S).group(1)
        assert squash(text(panel)) == ROLE_OPENINGS[role]  # verbatim from the contract's opening


def test_popovers_are_css_only_hidden_at_rest_and_lift_their_triggers(css: str, home: str):
    panel = rule(css, ".md-typeset .cc-pop .cc-pop__panel")
    assert "visibility: hidden" in panel and "opacity: 0" in panel
    shown = rule(css, ".cc-pop:hover .cc-pop__panel, .cc-pop:focus-within .cc-pop__panel")
    assert "visibility: visible" in shown and "opacity: 1" in shown
    rest = rule(css, ".cc-pop")
    assert "outline: 0.08rem solid transparent" in rest  # resting outline: only the colour transitions, from nothing
    assert "z-index" not in rest  # siblings rest at auto...
    lift = rule(css, ".cc-pop:hover, .cc-pop:focus-within")
    assert "z-index: 5" in lift  # ...and the open trigger, a stacking context, ranks above them all
    assert "outline-color: color-mix(in srgb, var(--cc-cyan) 45%, transparent)" in lift  # the crew badges' ring, unchanged
    receipts_lift = rule(css, ".cc-receipts .cc-pop:hover, .cc-receipts .cc-pop:focus-within")
    assert receipts_lift.strip() == "outline-color: transparent;"  # the receipts lose the ring and keep the lift
    assert "background: #ffffff" in panel and "box-shadow: 0 0.8rem 2rem #0a001259" in panel  # raised: white, firmer shadow
    assert "background: var(--cc-purple-light)" in rule(css, '[data-md-color-scheme="slate"] .md-typeset .cc-pop .cc-pop__panel')
    assert "font-size: 0.95rem" in panel
    assert "top: calc(100% - 1.5rem)" in panel  # overlaps the card's bottom rather than gapping below it
    assert "top: calc(100% - 0.5rem)" in rule(css, ".md-typeset .cc-crew__badge .cc-pop__panel")  # the tile's padding only
    assert "translateY(-2px)" in lift and "outline-color: color-mix(in srgb, var(--cc-cyan) 45%, transparent)" in lift
    assert ".cc-pop:focus-visible" not in css  # no state brighter than the sustained one
    assert css.count("translateY(-2px)") == 1  # nothing without a popover lifts
    phone = media_block(css, "screen and (max-width: 44.9375em)")
    assert "position: fixed" in phone and "bottom: 1rem" in phone  # the sheet
    for name in ("cc-crew", "cc-proof"):  # no JavaScript and no title tooltips for any of it
        markup = re.sub(r'<a class="headerlink"[^>]*>', "", section(home, name))  # Zensical's own heading anchors carry a title
        assert "<script" not in markup
        assert 'title="' not in markup


def test_crew_section_names_the_seats_and_no_crew_member(home: str, css: str):
    crew = section(home, "cc-crew")
    badges = re.findall(r'<img src="assets/images/crew/[^"]+"[^>]*>(?:</p>)?\s*<figcaption>([^<]+)</figcaption>', crew)
    assert tuple(badges) == CREW_ROLES
    assert "identity new reviewer" in crew
    badge = rule(css, ".md-typeset .cc-crew__badge img")
    assert "background: var(--cc-purple)" in badge  # white marks need a ground
    assert "width: 6rem" in badge and "height: 6rem" in badge and "padding: 0.5rem" in badge  # doubled from 3rem
    assert "top: calc(100% - 0.5rem)" in rule(css, ".md-typeset .cc-crew__badge .cc-pop__panel")  # the overlap stays at the tile's padding
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


@pytest.fixture(scope="module")
def docs_index(site: Path) -> str:
    return (site / "docs" / "index.html").read_text()


def test_docs_tab_sits_between_home_and_blog(home: str):
    tabs = [
        " ".join(text(label).split())
        for _, label in re.findall(
            r'<a href="([^"]*)" class="md-tabs__link[^"]*">(.*?)</a>', home, re.S
        )
    ]
    assert tabs == ["Home", "Docs", "Blog"]


def test_the_hero_button_lands_on_the_docs_index(site: Path, home: str):
    assert 'href="docs/"' in section(home, "cc-hero")
    assert (site / "docs" / "index.html").is_file()  # what that href resolves to


def test_docs_section_keeps_the_default_layout(docs_index: str):
    assert "cc-home" not in docs_index
    assert "md-content__inner" in docs_index  # the reading column the home page drops
    assert "md-sidebar--primary" in docs_index
    assert "md-sidebar--secondary" in docs_index
    assert "md-footer__inner" in docs_index  # prev/next navigation
    assert "cc-section" not in docs_index
    assert "cc-footer" not in docs_index


def test_every_docs_nav_target_has_a_built_page(site: Path):
    config = (site.parent / "zensical.toml").read_text()
    block = config[config.index("BEGIN_DOCS_NAV") : config.index("END_DOCS_NAV")]
    targets = re.findall(r'"(docs/[^"]+\.md)"', block)
    assert len(targets) >= 10, targets  # the whole section, not a stub
    assert "docs/spec.md" in targets and "docs/contributing.md" in targets
    assert not any("milestones" in target for target in targets)  # excluded
    for target in targets:
        rel = target.removesuffix(".md").removesuffix("/index")
        assert (site / rel / "index.html").is_file(), target


def test_the_synced_links_resolve_on_site(docs_index: str):
    # ../README.md is the home page, which carries the README's argument.
    assert '<a href="../">' in docs_index
    assert '<a href="../#codecrew-works">' in docs_index  # by the home page's own id
    assert '<a href="spec/">' in docs_index  # ../SPEC.md, now on-site
    # A file that did not sync still points at the repo.
    assert "github.com/radiusred/gh-codecrew/blob/main/CHANGELOG.md" in docs_index
    assert "README.md" not in docs_index


def test_the_milestone_records_are_not_on_the_site(site: Path, docs_index: str):
    # They are the engineering trail, not product documentation (M9-R1, as
    # amended 2026-09-04). The upstream still has them; the site must not.
    assert not (site / "docs" / "milestones").exists()
    assert not list(site.rglob("*-role-contracts-and-cli-skeleton*"))
    # The introduction's two links to them leave for GitHub, as a directory.
    assert "github.com/radiusred/gh-codecrew/tree/main/docs/milestones" in docs_index


def test_the_home_drawer_reaches_every_tab(home: str):
    # Below 76.234375em the tabs are gone and the drawer is the only navigation,
    # so it must carry what the tabs carried.
    panel = drawer(home)
    assert "md-nav--primary" in panel
    targets = set(re.findall(r'<a href="([^"]*)" class="md-nav__link', panel))
    assert {"", "./docs/", "./blog/"} <= targets, sorted(targets)


def test_no_page_offers_a_burger_with_nothing_behind_it(home: str, blog: str, docs_index: str):
    # The bug in #9 was exactly this pair coming apart on one page: the header
    # renders the toggle unconditionally, the template decided the panel.
    for name, page in (("home", home), ("blog", blog), ("docs", docs_index)):
        assert 'data-md-toggle="drawer"' in page, name
        assert "md-nav--primary" in drawer(page), name


def test_the_hidden_drawer_rests_on_a_stylesheet_rule_that_still_exists(site: Path):
    # `hidden` only means "desktop only" because the theme overrides it below
    # the breakpoint. If an upgrade drops that, the home page loses its drawer
    # silently on phones — so assert the rule rather than trust it.
    bundled = [p for p in (site / "assets/stylesheets/modern").glob("*.css") if "palette" not in p.name]
    assert len(bundled) == 1, bundled
    css = bundled[0].read_text()
    start = css.index(".md-sidebar--primary{position:fixed")
    rule = css[start : css.index("}", start)]
    assert "display:block" in rule
    query = css[css.rindex("@media", 0, start) :][: css[css.rindex("@media", 0, start) :].index("{")]
    assert query == "@media screen and (max-width:76.234375em)", query
