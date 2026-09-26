"""Build the site and check the home page template against the rest.

The home page (docs/index.md) selects docs/overrides/home.html and hides the
navigation, toc and footer nav. Every other page — the blog, and the docs
section sync_docs.py builds from radiusred/gh-codecrew — keeps Zensical's
default layout. `zensical build` has no site-dir option, so the fixture copies
the site source into a temp dir, runs the sync there, and builds in strict mode
so any warning fails the build.

The build needs the upstream on disk, since the nav points into the synced
section. Without one the module skips on a machine that
never named a source, and fails when SYNC_SOURCE_BASE was set and points at
nothing: CI sets it and checks the hub out under it, so an absence there is
drift, and this strict build must not quietly stop running (see
upstream_guard.py).
"""

import html
import os
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import NamedTuple

import pytest

from sync_docs import HOME_ANCHORS
from upstream_guard import absent_upstream, find_upstream

ROOT = Path(__file__).resolve().parent.parent
CONFIGURED = os.environ.get("SYNC_SOURCE_BASE") or None
UPSTREAM = find_upstream(CONFIGURED, ROOT)
if UPSTREAM is None:
    pytestmark = pytest.mark.skip(reason=absent_upstream(CONFIGURED, ROOT))

# Measured in headless Chromium at a 420px viewport (root font 20px, code
# 12.8px JetBrains Mono, 16px of padding a side): the install block's code
# column holds 43 characters before it scrolls sideways. The longest command
# is 42. Longer lines scroll on a phone. Below 420px the terminals and the
# routing example step down to 11.2px (NARROW_CODE), which keeps 42 characters
# and the prompt inside the block at 375px (M19-R7).
INSTALL_LINE_MAX = 42
NARROW_CODE = ("(max-width: 26.1875em)", "font-size: 0.56rem")
# One rule for every code line on the page: the worked example's verbs (longest 23)
# and the YAML are held to the same 42. The crew section's `identity new` is the
# exception: with the `--name` protocol 2.1 requires it is 54, so it wraps (#44).
# Start now's copy of it sits in a terminal, which scrolls rather than wraps, so it
# splits at a shell continuation and keeps to the ceiling (#52).
STEP_CODE_MAX = 42
CREW_ROLES = ("implementer", "reviewer", "qa", "doc-synthesizer", "coordinator")
CREW_MEMBER_NAMES = ("cody", "checky", "testy", "wordy")  # Radius Red's crew, not the framework's
# The two the operator's approval of M19-R3 (2026-09-26) lets the worked example name, and only it.
EXAMPLE_CREW = ("cody", "checky")
# The crew section's example routing table, the only fenced block on the home page.
# Its identities are made-up, typed placeholders: the M8 rule keeps crew members off
# this page, and the page no longer points at the hub's real table (M19-R1, #44).
TABLE_BLOCK = r'<div class="language-yaml highlight">.*?</div>'
# The receipts: glyph, header, strapline, and the visible detail with its link target (M19-R4).
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
# The PR the proof's screenshots show, and the GitHub events its visible text links (#48).
PROOF_PR = "https://github.com/radiusred/snake/pull/6"
PROOF_LINKS = {
    "change request": PROOF_PR + "#pullrequestreview-5058697880",
    "fix commit": PROOF_PR + "/commits/c1c26e581b4843830c5c9ebd16f69648bf281865",
    "fix answer": PROOF_PR + "#issuecomment-5463789260",
    "approval": PROOF_PR + "#pullrequestreview-5058716626",
}
PROOF_AUTHOR, PROOF_REVIEWER = "radiusred-cody[bot]", "radiusred-checky[bot]"
# Character-exact from the change-request review.
PROOF_FINDING_QUOTE = "Two plan-level assertions are weakened in the shipped tests"
# The crew badges: what each role does, in visible text written for the engineer reading
# the page (M19-R5). They replaced pop-overs that quoted each contract's opening to the agent.
ROLE_SUMMARIES = {
    "implementer": "Plans the task on its issue, builds the change and opens the pull request.",
    "reviewer": "Reads the diff in a fresh session, then requests changes or approves.",
    "qa": "Runs what was built against each requirement and records a verdict.",
    "doc-synthesizer": "Turns the milestone's recorded decisions into its document.",
    "coordinator": "Opens the work and starts each role's session: you, or an orchestrator.",
}
# The contracts' openings speak to the agent that loads them; none of it is homepage copy now.
CONTRACT_VOICE = ("You implement one", "You review one", "You exercise what", "You write the milestone", "You run the delivery loop")
# Why: three benefits, in order (M19-R5). The second is the different-model reviewer, bounded.
WHY_HEADINGS = (
    "See who built it, and who checked it",
    "A second model, with other blind spots",
    "The record is the work",
)
# Character-exact from the reviewer contract's opening (hub .codecrew/roles/reviewer.md).
REVIEWER_REASON = "self-evaluation shares the blind spots of the work itself"
# Where the middle of the page sends a reader for principal types and topology (M19-R5).
IDENTITIES_DOC = "docs/identities/"
TOPOLOGY_DOC = "docs/spec/#3-topology-hub-and-spokes"
# The worked example's turns, in order: who speaks, and for the two agents the harness,
# the App and the crew artwork they wear. The loop is build, change request, fix,
# approval, finish (M19-R3).
EXAMPLE_SPEAKERS = ("you", "cody", "checky", "cody", "checky", "cody")
EXAMPLE_AGENTS = {
    "cody": ("Cody", "Claude Code", "radiusred-cody[bot]", "assets/images/crew/codecrew-code-t.png"),
    "checky": ("Checky", "Codex", "radiusred-checky[bot]", "assets/images/crew/codecrew-review-t.png"),
}
# Said once on the page, in the example's lead (M19-R3).
WHO_STARTS_SESSIONS = "the operator or an orchestrator starts every session"
FRESH_SESSION = "review runs in a fresh session"
# Start now's second step (M19-R6): the reviewer's App, minted with the name the crew
# section's example routes it to, split so each line keeps to STEP_CODE_MAX.
REVIEWER_COMMAND = ("gh codecrew identity new reviewer \\", "  --name myorg-checker")
# The plan-tier qualifier every required-review claim on the page carries, worded once
# (SPEC §5, platform requirements), in the proof's receipt and in Start now alike.
PAID_PLAN = "on a private repo, branch protection needs a paid GitHub plan"
START_STEPS = (("start-solo", "First, work solo"), ("add-a-reviewer", "Next, add an agent reviewer"))
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
    start = page.index('<div class="md-sidebar md-sidebar--primary')
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
    sidebar = re.search(r'<div class="md-sidebar md-sidebar--primary[^"]*"[^>]*>', home)
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


def front_matter(source: Path) -> dict[str, str]:
    """The plain `key: value` lines of a Markdown page's front matter, quotes stripped."""
    front = source.read_text().split("---\n")[1]
    return {k: v.strip().strip("\"'") for k, v in re.findall(r"^(\w+):[ \t]*(\S.*)$", front, re.M)}


def head_meta(page: str) -> dict[str, str]:
    """What a page's head tells a search engine or a link preview: title and description, three ways each."""
    found = {"title": html.unescape(re.search(r"<title>(.*?)</title>", page, re.S).group(1)).strip()}
    for attr, name in (
        ("name", "description"),
        ("property", "og:title"),
        ("property", "og:description"),
        ("name", "twitter:title"),
        ("name", "twitter:description"),
    ):
        found[name] = html.unescape(re.search(rf'<meta {attr}="{name}" content="([^"]*)"', page).group(1))
    return found


def test_home_metadata_carries_the_crew_pitch(home: str):
    """M19-R7: the home page's description and title say what the hero says (agents under
    their own GitHub App identities, different harnesses and models building and reviewing,
    the record in GitHub), not the receipts-led line it carried before M19."""
    front = front_matter(ROOT / "docs" / "index.md")
    meta = head_meta(home)
    description = front["description"]
    assert meta["description"] == meta["og:description"] == meta["twitter:description"] == description
    for pitch in ("GitHub App identity", "different harnesses and models", "build and review", "record"):
        assert pitch in description, pitch
    assert "receipts" not in description.lower()
    # The title's tagline is the hero's headline, set from the page's own front matter.
    hero = section(home, "cc-hero")
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", hero, re.S).group(1)
    headline = squash(text(re.sub(r'<a class="headerlink".*?</a>', "", h1, flags=re.S)))
    assert front["tagline"] == headline.removesuffix(".")
    assert meta["title"] == meta["og:title"] == meta["twitter:title"] == f"CodeCrew — {front['tagline']}"
    assert "receipts" not in " ".join(meta.values()).lower()


def test_the_home_metadata_stays_on_the_home_page(site: Path, post: "Post"):
    """M19-R7 sets the pitch for the home page only: the docs and the 404 keep the site's
    description and tagline, and a blog post keeps its own front matter's."""
    config = (site.parent / "zensical.toml").read_text()
    site_description = re.search(r'^site_description = "(.*)"$', config, re.M).group(1)
    home_front = front_matter(ROOT / "docs" / "index.md")
    for page in (site / "docs" / "identities" / "index.html", site / "404.html"):
        meta = head_meta(page.read_text())
        assert meta["description"] == meta["og:description"] == site_description, page
        assert home_front["tagline"] not in " ".join(meta.values()), page
    docs_title = head_meta((site / "docs" / "identities" / "index.html").read_text())["title"]
    assert docs_title.startswith("Identities") and docs_title.endswith(" - CodeCrew")  # its own title, as before
    main_template = (ROOT / "docs" / "overrides" / "main.html").read_text()
    tagline = re.search(r'{% set tagline = "(.*)" %}', main_template).group(1)
    assert head_meta((site / "404.html").read_text())["title"] == f"CodeCrew — {tagline}"

    source = sorted((ROOT / "docs" / "blog" / "posts").glob("*.md"))[-1]
    meta = head_meta(post.page)
    assert meta["description"] == meta["og:description"] == front_matter(source)["description"]
    assert meta["title"] == f"{post.title} - CodeCrew"


def test_home_has_the_product_page_flow(home: str):
    order = ("cc-hero", "cc-example", "cc-crew", "cc-why", "cc-proof", "cc-start")
    positions = [home.index(f"cc-section {name}") for name in order]
    assert positions == sorted(positions)  # the example sits where How it works did, the crew after it
    assert 'id="start-now"' in home
    assert 'id="the-example"' in section(home, "cc-example")  # the anchor the hero's second call to action needs (M19-R2)


def test_hero_carries_the_logo_and_both_calls_to_action(home: str):
    hero = section(home, "cc-hero")
    assert 'class="cc-hero__logo"' in hero
    assert 'class="cc-logo"' in hero
    assert 'class="cc-hero__body"' in hero
    assert "cc-hero__headline" in hero
    assert "Decisions and deviations" not in hero  # said once, in the Why panel
    assert "the record is the work" not in text(hero).lower()  # the Why panel's heading carries it
    assert "github.com" not in hero
    # Two buttons, in order: setup first, the worked example second (M19-R2). The docs
    # stay one click away in the header's Docs tab and the drawer, not in the hero.
    buttons = [
        (re.search(r'href="([^"]*)"', a).group(1), re.search(r'class="([^"]*)"', a).group(1))
        for a in re.findall(r"<a [^>]*cc-button[^>]*>", hero)
    ]
    assert buttons == [("#start-now", "cc-button cc-button--primary"), ("#the-example", "cc-button")]
    assert 'id="start-now"' in section(home, "cc-start")
    assert 'id="the-example"' in section(home, "cc-example")
    assert 'href="docs/"' not in hero


def test_the_logo_steps_down_on_a_phone(css: str):
    """At 375px a 13rem logo pushed the pitch halfway down the first screen; below 45em it
    is 7rem, so the headline and the first paragraph land above the fold (M19-R7)."""
    assert "max-width: 13rem" in rule(css, ".md-typeset .cc-logo")
    narrow = media_block(css, "screen and (max-width: 44.9375em)")
    assert re.search(r"\.md-typeset \.cc-logo \{\s*max-width: 7rem;", narrow)
    assert "max-width: 19rem" in media_block(css, "screen and (min-width: 60em)")  # the desktop logo is unchanged


def test_hero_leads_with_the_crew(home: str):
    """M19-R2: the hero's visible text names GitHub App identities and says that
    different harnesses and models build and review, before any section below it."""
    hero = section(home, "cc-hero")
    headline = squash(text(re.search(r"<h1[^>]*>(.*?)</h1>", hero, re.S).group(1)))
    assert "crew" in headline.lower()
    subs = [squash(text(p)) for p in re.findall(r'<p class="cc-hero__sub">(.*?)</p>', hero, re.S)]
    lead = subs[0]
    assert "GitHub App identity" in lead
    assert "different harnesses and models" in lead and "build and review" in lead
    # Apps are optional (user:, team:, operator-held seats): the attribution claim is
    # conditional on the agent acting under its App, not said of every commit (#54's review).
    assert "Anything an agent does under its App — a commit, a review, a recorded decision — carries that App's name." in lead
    assert "Every commit, review and recorded decision carries" not in lead
    # The worked example says, once, who starts the sessions and that review runs fresh;
    # the hero does not repeat it, and names no crew member (R3's example does).
    visible = squash(text(hero))
    for claim in (WHO_STARTS_SESSIONS, FRESH_SESSION):
        assert claim not in visible, claim
    for name in CREW_MEMBER_NAMES:
        assert not re.search(rf"\b{name}\b", visible.lower()), name


def test_hero_keeps_the_commodity_line_aimed_at_separation_of_duties(home: str):
    """M17-R2's sentence survives M19-R2, re-aimed: distinct identities make separation
    of duties real, and that is the point the coordinator's commodity status leaves."""
    hero = section(home, "cc-hero")
    sentence = next(
        p for p in re.findall(r'<p class="cc-hero__sub">(.*?)</p>', hero, re.S) if "commodity" in p
    )
    link = '<a href="blog/posts/2026-09-19-the-coordinator-is-a-commodity-now/">a commodity now</a>'
    assert link in sentence  # on-site, on the words the M17 record names
    words = squash(text(sentence))
    assert "The coordinator running your agents is a commodity now" in words
    assert "separation of duties is not" in words
    assert "distinct identities" in words
    # Bounded to the tier where it holds: a routed reviewer App (SPEC §4, NO_HOLDER_REVIEW).
    # An operator-held reviewer seat or pure solo counts other things (#54's review).
    assert "route the reviewer to its own App, and CodeCrew merges only on that App's approval, never the author's" in words


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


def test_start_goes_from_solo_to_an_agent_reviewer(home: str, site: Path):
    """M19-R6: install, init and work solo, then the next step: the reviewer seat gets an App
    of its own. Installing it is per account, and the required-review claim carries both of
    its qualifiers: the write-permission opt-in and the paid plan private repos need."""
    start = section(home, "cc-start")
    assert re.search(r'<h2 id="start-now">Start now<a class="headerlink"', start)  # the hero's primary button lands here
    steps = tuple(re.findall(r'<h3 id="([\w-]+)">(.*?)<a class="headerlink"', start))
    assert steps == START_STEPS  # solo first, the reviewer next
    solo, reviewer = start.split(f'<h3 id="{START_STEPS[1][0]}">')
    # Solo is real on day one: the install terminal and the one sentence stay in it.
    assert 'class="cc-install cc-term"' in solo and "cc-install" not in reviewer
    assert "Then one sentence to your agent" in solo
    lead = squash(text(re.search(r'<p class="cc-start__step-lead">(.*?)</p>', solo, re.S).group(1)))
    assert "gh codecrew init routes every seat to you" in lead
    assert "not a cut-down CodeCrew" in lead
    assert "approve your own pull request" in lead and "task finish" in lead and "confirmation" in lead  # the one thing solo changes
    # ...and the flag that does it: without it the gate refuses NO_NONDOER_APPROVAL (hub CLI.md, SPEC §4).
    assert "task finish --operator-confirm" in lead
    assert "<code>task finish --operator-confirm</code>" in solo  # readable as a command, not prose
    # The reviewer's App: one command, in a terminal of its own, copied as one shell command.
    assert 'class="cc-reviewer cc-term"' in reviewer
    lines = code_lines(reviewer)
    assert lines == list(REVIEWER_COMMAND)
    assert " ".join(line.removesuffix("\\").strip() for line in lines) == "gh codecrew identity new reviewer --name myorg-checker"
    too_long = [line for line in lines if len(line) > STEP_CODE_MAX]
    assert not too_long, too_long
    assert '<span class="cc-term__line cc-term__line--cont" data-out=' in reviewer  # no prompt on the continuation
    assert "a name of your own" in squash(text(reviewer))  # the App name is the reader's, not the example's
    # Then what the verb leaves to you, in order.
    follow_ups = re.search(r'<ol class="cc-start__next">(.*?)</ol>', reviewer, re.S).group(1)
    install, route, begin = (squash(text(li)) for li in re.findall(r"<li>(.*?)</li>", follow_ups, re.S))
    assert install.startswith("Install it on each account it must reach.")
    assert "per account" in install and "personal account" in install and "public-installable" in install
    assert "app:myorg-checker" in route and ".codecrew/config.yml" in route and "uncommitted" in route
    assert "gh codecrew roles show reviewer" in begin
    assert "CodeCrew does not start it" in begin and "orchestrator" in begin  # the boundary, without restating the example's sentence
    # Every required-review claim in the section carries both qualifiers, and the CLI's own gate.
    claims = [squash(text(block)) for block in re.findall(r"<(?:p|li)[^>]*>(.*?)</(?:p|li)>", start, re.S) if "required review" in text(block)]
    assert claims
    for claim in claims:
        assert "--with-approval-permission" in claim and "write access" in claim, claim
        assert PAID_PLAN in claim, claim
        assert "task finish refuses until the reviewer App has approved" in claim, claim
    # The rest is the identities guide's, and its anchors exist in the built page.
    links = re.findall(r'href="(docs/identities/[^"]*)"', start)
    assert {"docs/identities/#minting-a-crew-member", "docs/identities/#dispatching-a-role-session"} <= set(links)
    for href in links:
        page, _, anchor = href.partition("#")
        assert f'id="{anchor}"' in (site / page / "index.html").read_text(), href
    for name in CREW_MEMBER_NAMES:  # the M8 rule holds here: the command uses the example's placeholder
        assert not re.search(rf"\b{name}\b", text(start).lower()), name


def test_terminal_prompt_and_output_are_generated_content(css: str):
    assert 'content: "$"' in rule(css, ".cc-term__line::before")
    assert 'content: ""' in rule(css, ".cc-term__line--cont::before")  # a continuation line takes no prompt
    assert "attr(data-out)" in rule(css, ".cc-term__line[data-out]::after")
    window = rule(css, ".cc-term")
    assert "width: fit-content" in window and "max-width: 100%" in window and "margin: 0 auto" in window


def test_the_worked_example_is_two_agents_in_a_review_loop(home: str):
    """M19-R3: a build, change request, fix and approval loop, told through CodeCrew's own
    crew and labelled as an example. It replaced the single-agent "How it works" tour."""
    example = section(home, "cc-example")
    assert "cc-how" not in home and "How it works" not in text(home)  # the tour is gone
    assert "cc-step" not in home and "cc-bubble--agent" not in home  # and its bubbles with it
    label = example.index('<p class="cc-example__label">A worked example</p>')
    heading = re.search(r'<h2 id="the-example">(.*?)<a class="headerlink"', example).group(1)
    assert heading == "One agent builds. Another checks the work."
    assert label < example.index("<h2")  # labelled before it starts
    lead = squash(text(re.search(r'<p class="cc-example__lead">(.*?)</p>', example, re.S).group(1)))
    assert "Cody, on Claude Code, writes the code, and Checky, on Codex, reviews it" in lead
    assert "each acting on GitHub as its own App" in lead
    assert "The change is made up" in lead  # an example, not a transcript
    page = squash(text(home))
    for claim in (WHO_STARTS_SESSIONS, FRESH_SESSION):
        assert claim in lead and page.count(claim) == 1, claim  # stated once, in the lead

    turns = re.findall(r'<li class="cc-turn cc-turn--(\w+)">(.*?)</li>', example, re.S)
    assert tuple(speaker for speaker, _ in turns) == EXAMPLE_SPEAKERS
    assert "<title>Claude</title>" not in example  # no one icon standing for every agent
    bubbles = []
    for speaker, turn in turns:
        who = squash(text(re.search(r'<p class="cc-turn__who">(.*?)</p>', turn, re.S).group(1)))
        avatar = re.search(r'<\w+ class="cc-turn__avatar"[^>]*>', turn).group(0)
        if speaker == "you":
            assert who.startswith("You")
            assert "<img" not in turn and "lucide-user" in turn  # the person glyph, as in the tour
        else:
            name, harness, app, art = EXAMPLE_AGENTS[speaker]
            assert who == f"{name} · {harness} · {app}"  # the agent, its harness and its App
            assert f'<span class="cc-turn__app">{app}</span>' in turn  # kept whole when the line wraps
            assert avatar.startswith("<img") and f'src="{art}"' in avatar  # its own crew artwork
        bubbles.append(re.search(r'<p class="cc-bubble">(.*?)</p>', turn, re.S).group(1))
    goal, build, request, fix, approval, finish = (squash(text(b)) for b in bubbles)
    assert "Requirement:" in goal
    assert "PR is open" in build
    assert request.startswith("Changes requested.")
    assert fix.startswith("Fixed in a new commit")
    assert approval.endswith("Approved.")
    assert [html.unescape(c) for c in re.findall(r"<code>(.*?)</code>", bubbles[-1])] == ["gh codecrew task finish"]
    assert finish == "gh codecrew task finish"  # the owner merges through the gatekeeper
    verbs = [html.unescape(c) for c in re.findall(r"<code>(.*?)</code>", example)]
    too_long = [verb for verb in verbs if len(verb) > STEP_CODE_MAX]
    assert not too_long, too_long

    close = re.findall(r'<p class="cc-example__close">(.*?)</p>', example, re.S)
    assert len(close) == 1 and example.index("cc-example__close") > example.index("</ol>")  # one line, after the loop
    close = squash(text(close[0]))
    assert "QA checks what was built against each requirement" in close
    assert "the recorded decisions become the milestone's document" in close
    assert "any question only you can answer" in close  # the human's gate stays in view


def test_the_example_wears_the_crew_artwork_and_tints_each_speaker(css: str, home: str, site: Path):
    assert "white-space: nowrap" in rule(css, ".md-typeset .cc-turn__app")
    avatar = rule(css, ".md-typeset .cc-example .cc-turn__avatar")
    assert "background: var(--cc-purple)" in avatar and "border-radius: 50%" in avatar  # white marks need a ground
    for art in ("codecrew-code-t.png", "codecrew-review-t.png"):
        assert (site / "assets" / "images" / "crew" / art).is_file()
    assert "var(--cc-cyan-tint)" in rule(css, ".md-typeset .cc-turn--cody .cc-bubble")
    assert "var(--cc-pink)" in rule(css, ".md-typeset .cc-turn--checky .cc-bubble")  # the review seat's colour
    assert "var(--md-default-fg-color--lightest)" in rule(css, ".md-typeset .cc-turn--you .cc-bubble")
    assert ".cc-step" not in css and "cc-how" not in css  # the tour's rules went with it
    assert "steps/" not in home  # no step image referenced
    assert not (site / "assets" / "images" / "steps").exists()


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


def test_code_blocks_step_down_below_420px_so_42_characters_fit_at_375(css: str, home: str):
    """At 375px the install terminal's longest line and the routing example's last row
    scrolled sideways at 12.8px, and a block that scrolls takes a Tab stop (M19-R7)."""
    query, size = NARROW_CODE
    block = media_block(css, f"screen and {query}")
    for selector in (".md-typeset .cc-term pre > code", ".md-typeset .cc-crew .highlight pre > code"):
        assert selector in block, selector
    assert size in block
    assert 'class="cc-term__code"' in section(home, "cc-start")  # the selectors still find their blocks
    assert re.search(TABLE_BLOCK, section(home, "cc-crew"), re.S)


def test_the_routing_example_line_anchors_take_no_tab_stop(css: str, home: str):
    """The site-wide `anchor_linenums` gives each YAML row an empty link, a Tab stop
    nobody can see; the home page hides them from the keyboard (M19-R7)."""
    table = re.search(TABLE_BLOCK, section(home, "cc-crew"), re.S).group(0)
    assert re.search(r'<a id="__codelineno-[\d-]+"[^>]*href="#__codelineno-[\d-]+"></a>', table)  # still emitted
    assert "visibility: hidden" in rule(css, '.md-typeset .cc-crew .highlight a[id^="__codelineno-"]')


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


def test_proof_names_the_pr_its_apps_the_finding_and_the_fix(home: str):
    """M19-R4: the proof can be checked without hovering. Visible text under the screenshots
    names the PR, its author App and reviewer App, the finding and the fix, and links the review."""
    proof = section(home, "cc-proof")
    assert re.search(r'<h2 id="codecrew-works">CodeCrew Works<a class="headerlink"', proof)  # nothing linked the old id
    assert "cc-captures__caption" not in proof  # the generic caption is gone
    case = proof_case(proof)
    assert proof.index('class="cc-captures"') < proof.index('class="cc-proof__case"') < proof.index('class="cc-receipts"')
    words = squash(text(case))
    assert f'href="{PROOF_PR}"' in case and "radiusred/snake#6" in words  # the PR, named and linked
    assert f"written by the App {PROOF_AUTHOR}" in words
    assert f"reviewed by the App {PROOF_REVIEWER}" in words
    for what, href in PROOF_LINKS.items():
        assert f'href="{href}"' in case, what  # straight to each event on GitHub
    finding = squash(text(re.search(r'<li class="cc-proof__finding">(.*?)</li>', case, re.S).group(1)))
    assert f"\u201c{PROOF_FINDING_QUOTE}\u201d" in finding  # quoted exactly
    assert "Score: 1" in finding and "moved up" in finding  # both findings, in words
    fix = squash(text(re.search(r'<li class="cc-proof__fix">(.*?)</li>', case, re.S).group(1)))
    assert "Score: 1" in fix and "(10,10) to (10,9)" in fix
    approval = squash(text(re.search(r'<li class="cc-proof__approval">(.*?)</li>', case, re.S).group(1)))
    assert "c1c26e5" in approval and "approved" in approval
    assert '<a href="#the-example">' in case and 'id="the-example"' in section(home, "cc-example")  # what it proves
    for model in ("Claude", "Codex", "GPT", "Opus", "Sonnet"):
        assert model not in words, model  # no harness or model claimed for a PR that does not record one


def test_proof_receipts_are_visible_text(home: str):
    """M19-R4: every receipt's substance is on the page, not in a pop-over."""
    proof = section(home, "cc-proof")
    assert "cc-pop" not in proof and "tabindex" not in proof  # nothing in the proof hides behind hover or focus
    cards = re.split(r'<div class="cc-receipt">', proof)[1:]
    assert len(cards) == 4 and proof.count('class="cc-receipt"') == 4
    for card, (glyph, header, strap, detail, href) in zip(cards, RECEIPTS):
        glyph_p = re.search(r'<p class="cc-receipt__glyph">(.*?)</p>', card, re.S).group(1)
        assert glyph_p.count('<span class="twemoji">') == 1
        assert f"<p><strong>{header}</strong></p>" in card
        assert f'<p class="cc-receipt__strap">{strap}</p>' in card
        body = re.search(r'<div class="cc-receipt__detail">(.*?)</div>', card, re.S).group(1)
        assert detail in squash(text(body)) and f'href="{href}"' in body
        assert card.index("cc-receipt__glyph") < card.index("<strong>") < card.index("cc-receipt__strap") < card.index("cc-receipt__detail")
    staffed = squash(text(cards[2]))
    assert PAID_PLAN in staffed  # the claim's plan-tier qualifier
    orchestrator = cards[3]
    for href in ("https://github.com/radiusred/numberguess", "https://github.com/radiusred/snake",
                 "https://github.com/radiusred/gh-codecrew/issues/119", "https://github.com/radiusred/gh-codecrew/issues/164"):
        assert f'href="{href}"' in orchestrator, href  # the orchestrator receipt, visible with its links
    assert "radiusred/numberguess" in text(orchestrator) and "radiusred/snake" in text(orchestrator)
    words = text(re.sub(r'<div class="cc-proof__case">.*?</div>', "", proof, flags=re.S)).lower()
    assert "cody" not in words and "checky" not in words  # the receipts keep to role names
    not_yet = re.search(r'<p class="cc-proof__not-yet">(.*?)</p>', proof, re.S).group(1)
    assert squash(text(not_yet)) == "Not yet: any backend other than GitHub, or GitHub Enterprise Server."
    assert proof.index("cc-receipts") < proof.index("cc-proof__not-yet")


def proof_case(proof: str) -> str:
    """The proof's case block: the visible account of the PR the screenshots show."""
    match = re.search(r'<div class="cc-proof__case">(.*?)</div>', proof, re.S)
    assert match, "cc-proof__case"
    return match.group(1)


def test_crew_badges_say_what_each_role_does(home: str):
    """M19-R5: each badge carries its role and a visible summary, written for the reader."""
    crew = section(home, "cc-crew")
    figures = re.findall(r'<figure class="cc-crew__badge">(.*?)</figure>', crew, re.S)
    assert len(figures) == 5
    for figure, role in zip(figures, CREW_ROLES):
        caption = re.search(r"<figcaption>(.*?)</figcaption>", figure, re.S).group(1)
        assert re.search(rf'<strong class="cc-crew__role">{role}</strong>', caption)
        summary = squash(text(re.search(r'<span class="cc-crew__summary">(.*?)</span>', caption, re.S).group(1)))
        assert summary == ROLE_SUMMARIES[role]
    for summary in ROLE_SUMMARIES.values():
        assert not summary.startswith("You"), summary  # about the role, to the reader, not to the agent
        assert len(summary) <= 80, summary  # one line's worth under a badge
    page = squash(text(home))
    for opening in CONTRACT_VOICE:
        assert opening not in page, opening  # the contracts' own voice stays in the contracts


def test_nothing_on_the_home_page_hides_behind_hover(css: str, home: str):
    """M19-R4 put the receipts on the page; M19-R5 does the same for the crew. The pop-over
    mechanism, and every rule it needed, is gone."""
    sections = "".join(section(home, name) for name in re.findall(r'<section class="cc-section (cc-[\w-]+)', home))
    for marker in ("cc-pop", "tabindex", "cc-pop__panel"):  # the theme's own nav keeps its tabindex
        assert marker not in sections, marker
    assert ".cc-pop" not in css
    assert "translateY(-2px)" not in css  # the lift only a pop-over trigger had
    phone = media_block(css, "screen and (max-width: 44.9375em)")
    assert "position: fixed" not in phone  # the pop-over's bottom sheet on phones
    for name in ("cc-crew", "cc-why", "cc-proof"):  # no JavaScript and no title tooltips for any of it
        markup = re.sub(r'<a class="headerlink"[^>]*>', "", section(home, name))  # Zensical's own heading anchors carry a title
        assert "<script" not in markup
        assert 'title="' not in markup


def test_crew_section_names_the_seats_and_no_crew_member(home: str, css: str):
    crew = section(home, "cc-crew")
    badges = re.findall(r'<img src="assets/images/crew/[^"]+"[^>]*>\s*<figcaption><strong class="cc-crew__role">([^<]+)</strong>', crew)
    assert tuple(badges) == CREW_ROLES
    assert "identity new reviewer" in crew
    badge = rule(css, ".md-typeset .cc-crew__badge img")
    assert "background: var(--cc-purple)" in badge  # white marks need a ground
    assert "width: 6rem" in badge and "height: 6rem" in badge and "padding: 0.5rem" in badge  # doubled from 3rem
    # The M8 rule keeps crew members off the product page, bot logins in link targets only.
    # The operator's approval of M19-R3 lifts it for Cody and Checky in the worked example
    # alone (#46), and for their two Apps in the proof's case block, which names the PR's
    # author and reviewer (M19-R4, #48); everywhere else, and for the other two everywhere,
    # it stands.
    case = proof_case(section(home, "cc-proof"))
    elsewhere = text(home.replace(section(home, "cc-example"), "").replace(case, "")).lower()
    for name in CREW_MEMBER_NAMES:
        assert not re.search(rf"\b{name}\b", elsewhere), name
    example = text(section(home, "cc-example")).lower()
    for name in CREW_MEMBER_NAMES:
        assert bool(re.search(rf"\b{name}\b", example)) == (name in EXAMPLE_CREW), name
    apps = re.findall(r"\bradiusred-(\w+)\[bot\]", text(case))
    assert set(apps) == set(EXAMPLE_CREW)  # the case block names the two Apps, by login
    assert not re.search(r"\b(testy|wordy)\b", text(case).lower())


def test_crew_section_shows_the_example_routing_table(home: str):
    """M10-R7: a concrete table where the seats are introduced.

    It is an example, not a mirror — what a routing table looks like, not
    what any project runs (the M10-R6 amendment on radiusred/gh-codecrew#207,
    and the operator's Decision on #19). Nothing here compares it to a
    .codecrew.yml, and its identities are placeholders.
    """
    crew = section(home, "cc-crew")
    assert len(re.findall(TABLE_BLOCK, home, re.S)) == 1  # the page's only fenced block, and it is here
    assert len(re.findall(TABLE_BLOCK, crew, re.S)) == 1
    lead, _, rest = crew.partition('<div class="language-yaml highlight">')
    assert "routing table" in text(lead)  # it lands under the sentence that names one
    assert "illustrative" in text(lead)  # the gloss says it is an example (M19-R1)
    gloss = squash(text(lead.split("<p>")[-1]))
    assert "app:" in gloss and "~" in gloss  # the two forms the example uses...
    assert "user:" not in gloss and "team:" not in gloss  # ...and not the ones it does not (M19-R5)
    # ...and no longer sends the reader to the hub's real table to read it against.
    assert "gh-codecrew#the-routing-table" not in home
    assert "2-four-seats" not in home
    assert "identity new reviewer" in rest  # and before the verb that mints a seat's holder
    lines = code_lines(crew)
    assert lines[0] == "roles:"
    seats = [line.strip(" :") for line in lines if re.fullmatch(r"  [\w-]+:", line)]
    assert tuple(seats) == CREW_ROLES  # a row per badge above, in the same order
    keys = {line.split(":")[0].strip() for line in lines[1:]}
    assert {"harness", "model", "identity"} <= keys  # what a row routes
    identities = [line.strip().removeprefix("identity: ").split("  ")[0] for line in lines if line.strip().startswith("identity:")]
    assert identities == ["app:myorg-coder", "app:myorg-checker", "app:myorg-tester", "app:myorg-writer", "~"]  # placeholders, and a seat a person holds
    assert "    identity: ~   # a human: the operator" in lines  # the comment says so in the block
    too_long = [line for line in lines if len(line) > STEP_CODE_MAX]
    assert not too_long, too_long  # the page's one ceiling for every code line


def test_home_configuration_is_valid_under_protocol_2_1(home: str):
    """M19-R1: a reader who copies the homepage's configuration gets one the CLI accepts.

    Protocol 2.1 refuses an untyped routing identity with IDENTITY_UNTYPED (hub
    SPEC §5, §10): the grammar is `~`, `app:`, `user:` or `team:`. And
    `gh codecrew identity new` exits 1 without `--name` (hub CLI.md).
    """
    lines = code_lines(section(home, "cc-crew"))
    identities = [line.split("identity:", 1)[1].split("#")[0].strip() for line in lines if line.strip().startswith("identity:")]
    assert identities  # the example still routes its seats
    untyped = [value for value in identities if value != "~" and not re.match(r"(app|user|team):\S+$", value)]
    assert not untyped, untyped
    joined = re.sub(r"\\(?:<[^>]+>)*\n(?:<[^>]+>)*", " ", home)  # a shell continuation joins its lines, as the shell does
    commands = [html.unescape(re.sub(r"<[^>]+>", "", m)) for m in re.findall(r"gh codecrew identity new.*?(?=</code>|\n)", joined)]
    assert commands  # the page still shows the verb that mints a seat's holder
    nameless = [command for command in commands if not re.search(r"\s--name\s+\S", command)]
    assert not nameless, nameless


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


def test_why_is_three_benefits_one_of_them_a_bounded_second_model(home: str):
    """M19-R5: three benefits, including a bounded claim that a reviewer on a different model
    does not share the author's blind spots. Bounded: fresh context is the other half of the
    independence (hub docs/identities.md), a bot name proves an App and not a model, and no
    review catches everything."""
    why = section(home, "cc-why")
    panels = why.split('<div class="cc-panel">')[1:]
    headings = tuple(squash(text(re.search(r"<h3[^>]*>(.*?)<a class=\"headerlink\"", p, re.S).group(1))) for p in panels)
    assert headings == WHY_HEADINGS
    who, second, record = (squash(text(p)) for p in panels)
    assert "own GitHub App" in who and "not which model" in who  # attribution, and what it does not prove
    assert f"\u201c{REVIEWER_REASON}\u201d" in second  # the contract's reason, quoted exactly
    assert "different model or harness" in second
    assert "clean session" in second  # fresh context, not only a fresh identity
    assert "its own" in second and "every bug" in second  # it has blind spots of its own; no promise of catching all
    assert "guarantee" not in squash(text(why)).lower()
    assert "Decisions and deviations" in record  # said once, here (the hero test pins its absence there)
    assert "refuses" in record and "gh codecrew task finish" in record  # the gates, enforced by the CLI
    assert "No server, no dashboard" in record  # the fact survives, the topology does not


def test_the_middle_leaves_topology_and_principal_types_to_the_docs(home: str, site: Path):
    """M19-R5: hub/spoke and the four kinds of seat-holder are the docs' to explain; the
    crew and Why sections link there, in context, and the links land on built pages."""
    crew, why = section(home, "cc-crew"), section(home, "cc-why")
    middle = squash(text(crew + why))
    for topology in ("spoke", "One repo is the hub", "two-line pointer"):
        assert topology not in middle, topology
    for principal in ("GitHub team", "username", "colleague", "principal", "user:", "team:"):
        assert principal not in middle, principal
    assert f'href="{IDENTITIES_DOC}"' in crew
    assert (site / IDENTITIES_DOC / "index.html").is_file()
    assert f'href="{TOPOLOGY_DOC}"' in why
    page, anchor = TOPOLOGY_DOC.split("#")
    assert f'id="{anchor}"' in (site / page / "index.html").read_text()


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


class Post(NamedTuple):
    title: str  # as the front matter declares it
    date: date  # likewise
    page: str   # the built HTML


@pytest.fixture(scope="module")
def post(site: Path) -> Post:
    """The newest published blog post: its front matter, and the page built from it."""
    sources = sorted((ROOT / "docs" / "blog" / "posts").glob("*.md"))
    assert sources, "no published post to render"
    source = sources[-1]
    front = source.read_text()
    title = re.search(r"^title:\s*(.+?)\s*$", front, re.M).group(1).strip("\"'")
    published = date.fromisoformat(re.search(r"^date:\s*(\S+)\s*$", front, re.M).group(1))
    built = site / "blog" / "posts" / source.stem / "index.html"
    return Post(title, published, built.read_text())


def test_a_post_titles_itself_from_its_front_matter_and_carries_no_nav_markup(post: Post):
    """The nav key is the page's title, so HTML in it lands in the tab, the
    heading and the social card as literal text. main.py keeps the key plain;
    the date is the rr-page-meta block's alone. Whether the theme prefers the
    key or the front matter varies by zensical version, so the page-wide
    <small check is what holds this whichever version resolves."""
    title, page = post.title, post.page
    assert "<small" not in page

    doc_title = html.unescape(re.search(r"<title>(.*?)</title>", page, re.S).group(1)).strip()
    assert doc_title == f"{title} - CodeCrew"

    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", page, re.S).group(1)
    assert text(re.sub(r'<a class="headerlink".*?</a>', "", h1, flags=re.S)).strip() == title

    for attr, name in (("property", "og:title"), ("name", "twitter:title")):
        content = re.search(rf'{attr}="{name}" content="([^"]*)"', page).group(1)
        assert html.unescape(content) == f"{title} - CodeCrew"


def test_the_post_still_shows_its_date_once_in_the_meta_block(post: Post):
    """Dropping the date from the nav loses nothing: the theme still prints it."""
    meta = text(re.search(r'<div class="rr-page-meta">(.*?)</div>', post.page, re.S).group(1))
    assert "published on:" in meta
    assert post.date.strftime("%B") in meta and str(post.date.year) in meta


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


def test_the_docs_tab_lands_on_the_docs_index(site: Path, home: str):
    # The hero's docs button went in M19-R2; the header tab is the way in from the home page.
    assert re.search(r'<a href="(\./)?docs/" class="md-tabs__link', home)
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
    # The reading order docs/introduction.md prescribes: M16-R2 put the
    # reference before the SPEC, M16-R4 the offline page between the two.
    assert targets.index("docs/cli.md") + 1 == targets.index("docs/working-offline.md")
    assert targets.index("docs/working-offline.md") + 1 == targets.index("docs/spec.md")
    assert not any("milestones" in target for target in targets)  # excluded
    for target in targets:
        rel = target.removesuffix(".md").removesuffix("/index")
        assert (site / rel / "index.html").is_file(), target


def test_the_synced_links_resolve_on_site(docs_index: str, home: str):
    # ../README.md is the home page, which carries the README's argument. Which
    # README anchors the introduction links depends on the hub checkout — before
    # gh-codecrew#238 the receipts, after it the routing table — so the check is
    # the invariant: every fragment that crossed over is one HOME_ANCHORS knows
    # and an id the built home page has, and no README anchor rode through raw.
    home_links = re.findall(r'<a href="\.\./(#[\w-]*)?">', docs_index)
    assert home_links, "the introduction links the README"
    for fragment in filter(None, home_links):
        assert fragment in HOME_ANCHORS.values(), fragment
        assert f'id="{fragment[1:]}"' in home, fragment
    assert '<a href="spec/">' in docs_index  # ../SPEC.md, now on-site
    assert '<a href="cli/">' in docs_index  # ../CLI.md, likewise
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


def test_the_shut_home_drawer_is_out_of_the_tab_order(home: str, blog: str, docs_index: str, css: str):
    """Below the breakpoint the theme parks the shut drawer off-canvas but leaves its links
    in the tab order, focus rings off-screen. On the home page it is hidden until the
    drawer toggle is checked (M19-R7); the other pages keep the theme's drawer (#58)."""
    sidebar = re.search(r'<div class="(md-sidebar md-sidebar--primary[^"]*)"', home).group(1)
    assert sidebar.split() == ["md-sidebar", "md-sidebar--primary", "cc-drawer"]
    for page in (blog, docs_index):
        assert "cc-drawer" not in page
    block = media_block(css, "screen and (max-width: 76.234375em)")  # the theme's drawer breakpoint
    shut = rule(block, '  [data-md-toggle="drawer"]:not(:checked) ~ .md-container .md-sidebar--primary.cc-drawer')
    assert "visibility: hidden" in shut
    assert "visibility 0s 0.2s" in shut  # hidden only once it has slid out


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
