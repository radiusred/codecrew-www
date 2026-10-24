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
CREW_ROLES = ("implementer", "reviewer", "qa", "doc-synthesizer", "coordinator")  # the routing table's order
# The badges are an org chart (M22, #71): the coordinator heads it, first in the markup so the
# reading and Tab order match what the eye sees, and the other four roles follow, in table order.
CREW_CHART = ("coordinator",) + CREW_ROLES[:-1]
CREW_MEMBER_NAMES = ("cody", "checky", "testy", "wordy")  # Radius Red's crew, not the framework's
# The two the operator's approval of M19-R3 (2026-09-26) lets the worked example name, and only it.
EXAMPLE_CREW = ("cody", "checky")
# The crew section's example routing table, the only fenced block on the home page.
# Its identities are made-up, typed placeholders: the M8 rule keeps crew members off
# this page, and the page no longer points at the hub's real table (M19-R1, #44).
TABLE_BLOCK = r'<div class="language-yaml highlight">.*?</div>'
# The receipts: glyph, header, strapline, and the visible detail with its link target (M19-R4).
# The first is M22-R1's point (e), merged into the milestones receipt it duplicated (M22-R3).
HUB = "https://github.com/radiusred/gh-codecrew"
RECEIPTS = (
    ("package-check", "It is working software, not a set of prompts.", "Tests, CI and releases, in public.",
     "vets, builds and tests it on every pull request", HUB + "/actions"),
    ("megaphone", "The first spoke published its own announcement.", "Driven from the hub, in public.",
     "delivered by the protocol it describes", "https://www.radiusred.uk/blog/posts/2026-08-20-this-post-was-delivered-by-the-framework-it-introduces/"),
    ("bot", "This project is agent-staffed, and you can check.", "Four seats, four App identities.",
     "gh codecrew task finish merges a task here only once the reviewer App has approved", "https://github.com/radiusred/codecrew-www/pull/3"),
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
# Why: M22-R1's ideas (a) to (d) with M19-R5's bounded different-model reviewer, in the
# order a first-time reader meets them straight after the hero (the operator's review of
# PR #70): identities, the review they make possible, the gates, the state, the record.
# (e) is the proof section's first receipt.
WHY_HEADINGS = (
    "One App per role, with that role's permissions",
    "A second model, with other blind spots",
    "Gates in code, not instructions",
    "GitHub is the only state store",
    "Decisions, recorded as they are made",
)
# M22-R1's five ideas, each by a phrase only its own copy uses, and the section that carries
# it. M22-R3: a first-time reader meets each one once.
IDEAS = {
    "gates in code": ("cc-why", "easier to trust than an agent's own report"),
    "GitHub the only state store": ("cc-why", "no workflow database drifts"),
    "an App per role": ("cc-why", "not one shared, privileged token"),
    "decisions as they happen": ("cc-why", "at the moment of choice"),
    "working software": ("cc-proof", "working software, not a set of prompts"),
}
# What the gates panel says each verb checks, keyed by the refusal code (hub SPEC §10) that
# backs it: M22-R2's gate lists match the refusal table, and claim nothing it does not hold.
# The panel names a few, in a few words, and links the table for the rest.
FINISH_CHECKS = {
    "CHECKS_FAILING": "green CI",
    # The approval depends on routing (the routed holder's, or a non-author's when the seat is
    # operator-held), so the panel names the routing's, never "the reviewer's" (PR #72 review).
    "NO_HOLDER_REVIEW": "the approval your routing requires",
    "NO_NONDOER_APPROVAL": "the approval your routing requires",
    "GATED": "every question raised for a human answered",
    "GATE_UNRECORDED": "every question raised for a human answered",
}
CLOSE_CHECKS = {
    # A verdict can be unsatisfied: what close needs is each latest verdict `satisfied`.
    "VERDICT_MISSING": "refuses until every requirement's latest QA verdict is satisfied",
    "VERDICT_UNSATISFIED": "refuses until every requirement's latest QA verdict is satisfied",
}
REFUSAL_TABLE_DOC = "docs/spec/#10-the-cli"
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
# The plan-tier qualifier the required-review claim carries (SPEC §5, platform requirements).
# The claim and the qualifier live in Start now alone (M22-R3, QA's finding on #71).
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
    # The operator's review of PR #70: Why comes straight after the hero, so a first-time
    # reader meets the ideas first; then the crew, so the roles are known before the worked
    # example tells its story through them; then the proof of it, and how to start.
    order = ("cc-hero", "cc-why", "cc-crew", "cc-example", "cc-proof", "cc-start")
    positions = [home.index(f"cc-section {name}") for name in order]
    assert positions == sorted(positions)
    assert tuple(re.findall(r'<section class="cc-section (cc-[\w-]+)', home)) == order
    assert 'id="start-now"' in home
    assert 'id="the-example"' in section(home, "cc-example")  # the anchor the hero's second call to action needs (M19-R2)


def test_the_bands_below_the_hero_alternate(home: str):
    """Under the dark hero the sections alternate between the glowing band and the page
    ground, starting with the band, whatever order they come in."""
    classes = re.findall(r'<section class="cc-section (cc-[\w-]+)([^"]*)"', home)
    below = [(name, "cc-section--alt" in rest) for name, rest in classes[1:]]
    assert [alt for _, alt in below] == [i % 2 == 0 for i in range(len(below))], below


def test_the_moved_sections_stand_on_their_own(home: str):
    """Why comes before the crew and the example, so it explains its own terms: the roles
    are glossed, the reviewer's reason is not credited to a "contract" the page has not yet
    introduced, and human gates are put in plain words. The example's finish note points
    back at the gates instead of listing them again (M22-R3)."""
    why = squash(text(section(home, "cc-why")))
    assert "(implementer, reviewer, QA and the rest)" in why
    assert "contract" not in why.lower() and "human gate" not in why.lower()
    assert "as the reviewer's instructions put it" in why
    example = squash(text(section(home, "cc-example")))
    assert "The gates run here: if one fails, it refuses with its reason." in example
    assert "It checks CI" not in example


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
    assert "distinct identities are what make it real." in words
    # M22-R3: the line leads into the identities and the gates and no longer restates them.
    # The merge rule it carried is the gates panel's, said once there (NO_HOLDER_REVIEW).
    assert "approval" not in words and "merges" not in words
    assert "the approval your routing requires" in squash(text(section(home, "cc-why")))


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
    # Point (e) is checkable from its links (M22-R1), and names no version or date (M22-R2).
    software = cards[0]
    for href in (HUB, HUB + "/actions", HUB + "/releases", HUB + "/tree/main/docs/milestones"):
        assert f'href="{href}"' in software, href
    words = squash(text(software))
    assert "unit tests" in words and "fake tracker" in words and "every pull request" in words
    assert "Every milestone shipped this way." not in proof  # merged into this receipt
    staffed = squash(text(cards[2]))
    # The project's own fact, not the general rule: the required-review trade and its
    # plan-tier qualifier are Start now's alone (M22-R3, QA's finding on #71).
    assert PAID_PLAN not in staffed and "write access" not in staffed
    # About the gate (routing plus NO_HOLDER_REVIEW), never the history: the bootstrap PR
    # merged with no review, so no claim about every merge (PR #74 review).
    assert "each merge" not in staffed and "every merge" not in staffed
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
    for figure, role in zip(figures, CREW_CHART):
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


def test_the_crew_is_an_org_chart_headed_by_the_coordinator(home: str, css: str):
    """M22 (#71): the coordinator's badge sits centred on top, first in the DOM, and the four
    roles sit beneath it: two by two on a phone, one row from 45em, joined there by connector
    lines drawn in CSS, which put nothing in the markup or the accessibility tree."""
    crew = section(home, "cc-crew")
    roles = re.findall(r'<strong class="cc-crew__role">([^<]+)</strong>', crew)
    assert tuple(roles) == CREW_CHART
    assert "display: grid" in rule(css, ".cc-crew__badges")
    assert "repeat(2, minmax(0, 7.5rem))" in rule(css, ".cc-crew__badges")  # 2x2 on a phone
    head = rule(css, ".md-typeset .cc-crew__badge:first-child")
    assert "grid-column: 1 / -1" in head and "justify-self: center" in head
    opens = "@media screen and (min-width: 45em) {\n  .cc-crew__badges {"
    wide = media_block(css[css.index(opens):], "screen and (min-width: 45em)")
    assert "repeat(4, minmax(0, 7.5rem))" in wide  # one row of four beneath the head
    for line in ("cc-crew__badge:first-child::after", "cc-crew__badge:not(:first-child)::before",
                 "cc-crew__badge:not(:first-child)::after"):
        assert line in wide and css.count(line) == wide.count(line), line  # none on a phone
    assert css.count("border-left: 0.05rem solid var(--md-default-fg-color--lighter)") == 2  # stem and ticks
    assert "border-top: 0.05rem solid var(--md-default-fg-color--lighter)" in css  # the bar
    assert "::before" not in rule(css, ".md-typeset .cc-crew__badge")
    assert "aria-hidden" not in crew and "cc-crew__line" not in crew  # no markup for the lines


def test_crew_section_names_the_seats_and_no_crew_member(home: str, css: str):
    crew = section(home, "cc-crew")
    badges = re.findall(r'<img src="assets/images/crew/[^"]+"[^>]*>\s*<figcaption><strong class="cc-crew__role">([^<]+)</strong>', crew)
    assert tuple(badges) == CREW_CHART
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
    assert tuple(seats) == CREW_ROLES  # a row per badge above: the four in the chart's order, then its head
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
    panels = why[: why.index('<div class="cc-newhere">')].split('<div class="cc-panel">')[1:]
    assert len(panels) == len(WHY_HEADINGS)
    for panel in panels:
        glyphs = re.findall(r'<p class="cc-panel__glyph">(.*?)</p>', panel, re.S)
        assert len(glyphs) == 1 and glyphs[0].count('<span class="twemoji">') == 1, panel[:80]
        assert panel.index("cc-panel__glyph") < panel.index("<h3")  # the glyph tops the panel


def why_panels(home: str) -> dict[str, str]:
    """The Why section's panels, by heading, as visible text."""
    why = section(home, "cc-why")
    panels = why[: why.index('<div class="cc-newhere">')].split('<div class="cc-panel">')[1:]  # the row under them is not a panel
    heading = lambda p: squash(text(re.search(r"<h3[^>]*>(.*?)<a class=\"headerlink\"", p, re.S).group(1)))
    return {heading(p): squash(text(p)) for p in panels}


def test_why_is_the_five_ideas_and_a_bounded_second_model(home: str):
    """M22-R1: the panels explain (a) to (d), each with the reason it matters; M19-R5's
    bounded second-model panel stays. Bounded: fresh context is the other half of the
    independence (hub docs/identities.md), a bot name proves an App and not a model, and no
    review catches everything."""
    panels = why_panels(home)
    assert tuple(panels) == WHY_HEADINGS
    apps, second, gates, state, record = panels.values()
    assert "Checks in code" in gates and "easier to trust than an agent's own report" in gates
    assert "no workflow database drifts" in state
    # A failed session loses no task context, bounded: what was never pushed is not on GitHub.
    assert "A session that fails loses no task context, only work it never pushed" in state
    assert "its own GitHub App and permissions" in apps
    for heading, words in panels.items():
        assert len(words.split()) <= 60, heading  # one idea and its reason, in a few short sentences
    assert f"\u201c{REVIEWER_REASON}\u201d" in second  # the contract's reason, quoted exactly
    assert "different model or harness" in second
    assert "clean session" in second  # fresh context, not only a fresh identity
    assert "its own" in second and "every bug" in second  # it has blind spots of its own; no promise of catching all
    assert "guarantee" not in squash(text(section(home, "cc-why"))).lower()
    assert "Decisions and deviations" in record  # said once, here (the hero test pins its absence there)
    assert "synthesized" in record and "planning document" in record  # the reason it matters


def test_each_of_the_five_ideas_is_on_the_page_once(home: str):
    """M22-R3: nothing on the home page says the same thing twice. Each idea has one home,
    and the copy it replaced (the attribution panel, the record panel, the milestones
    receipt, the hero's merge rule) is gone."""
    page = squash(text("".join(section(home, name) for name in re.findall(r'<section class="cc-section (cc-[\w-]+)', home))))
    for idea, (home_section, phrase) in IDEAS.items():
        assert page.lower().count(phrase.lower()) == 1, idea
        assert phrase.lower() in squash(text(section(home, home_section))).lower(), idea
    for gone in ("See who built it, and who checked it", "The record is the work",
                 "Every milestone shipped this way.", "merges only on that App's approval"):
        assert gone not in page, gone
    assert "No server, no dashboard" not in page  # cut for length in the operator's review of PR #70
    assert page.count("Decisions and deviations") == 1
    assert page.count("Anything an agent does under its App") == 1  # attribution: the hero's, alone
    assert page.count(WHO_STARTS_SESSIONS) == 1


def refusal_table() -> dict[str, str]:
    """The hub SPEC §10 refusal table: each code and the verbs that raise it."""
    spec = (UPSTREAM / "gh-codecrew" / "SPEC.md").read_text()
    return dict(re.findall(r"^\| `([A-Z_]+)` \| ([^|]+) \|", spec, re.M))


def test_the_gates_claim_only_what_the_refusal_table_backs(home: str, site: Path):
    """M22-R2: every check the gates panel names for task finish and milestone close is a
    refusal that verb raises in the hub's SPEC §10 table. The plan is task start's check
    (NO_PLAN), not task finish's, and the worked example already says so."""
    gates = why_panels(home)["Gates in code, not instructions"]
    table = refusal_table()
    finish, close = gates.split("milestone close")
    assert "task finish merges only with" in finish
    for code, claim in FINISH_CHECKS.items():
        assert "`task finish`" in table[code], code
        assert claim in finish, code
    for code, claim in CLOSE_CHECKS.items():
        assert "`milestone close`" in table[code], code
        assert claim in close, code
    assert "`task start`" in table["NO_PLAN"] and "`task finish`" not in table["NO_PLAN"]
    assert "plan" not in gates.lower()
    assert "the reviewer's approval" not in gates and "has verified" not in gates  # PR #72 review
    assert f'href="{REFUSAL_TABLE_DOC}"' in section(home, "cc-why")  # the full list is the table's
    page, anchor = REFUSAL_TABLE_DOC.split("#")
    assert f'id="{anchor}"' in (site / page / "index.html").read_text()


def test_the_required_review_caveat_lives_only_in_start_now(home: str):
    """M22-R3, QA's finding on #71: the required-review trade is said once, under Start now.
    Elsewhere the page may say a reviewer can be given write access, but not why: no required
    review in any casing or hyphenation, no approval that counts, no paid-plan qualifier. This
    rejects the repeated claim however it is worded, not only the phrases it used before."""
    repeat = re.compile(r"required[\s-]+review|approvals?\s+(?:can\s+)?counts?|count(?:s|ed)?\s+toward"
                        r"|paid(?:\s+GitHub)?\s+plan|branch\s+protection", re.I)
    names = re.findall(r'<section class="cc-section (cc-[\w-]+)', home)
    for name in names:
        words = squash(text(section(home, name)))
        found = repeat.findall(words)
        if name == "cc-start":
            assert found  # its one home keeps the whole trade
        else:
            assert not found, (name, found)


def test_the_identity_claim_carries_the_approval_opt_in(home: str, site: Path):
    """M22-R2: review and qa cannot change code by default only. --with-approval-permission
    can give the reviewer write access (hub docs/identities.md). M22-R3: the panel says so and
    links Start now's account of the trade, without saying why (QA's finding on #71)."""
    why = section(home, "cc-why")
    apps = why_panels(home)["One App per role, with that role's permissions"]
    assert "Reviewer and QA Apps can't push code by default" in apps
    assert "--with-approval-permission can give the reviewer write access" in apps
    assert "the trade" in apps
    assert "required review" not in apps.lower() and "count" not in apps
    assert PAID_PLAN not in apps  # Start now carries the plan-tier qualifier
    assert 'href="#add-a-reviewer"' in why and 'id="add-a-reviewer"' in section(home, "cc-start")


def test_the_new_copy_names_no_version_no_date_and_no_source(home: str):
    """M22-R1 and R2: the copy is the site's own, in no first person, attributed to nothing,
    and it carries no version number or release date that would go stale."""
    proof = section(home, "cc-proof")
    software = re.split(r'<div class="cc-receipt">', proof)[1]
    new_copy = squash(text(section(home, "cc-why") + software))
    assert not re.search(r"\bv?\d+\.\d+", new_copy), new_copy
    assert not re.search(r"\b20\d\d\b", new_copy)
    months = r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\b"
    assert not re.search(months, new_copy)
    assert not re.search(r"\b(I|I'm|I've|my|me)\b", new_copy)
    page = text(home).lower()
    for source in ("chatgpt", "openai", "appraisal"):
        assert source not in page, source


def test_why_panels_fill_their_rows(css: str):
    """Five panels: one column on a phone, two from 45em with the fifth across both, and from
    60em three over two on a six-track grid, so the odd count leaves no hole."""
    assert ".cc-panels {\n    grid-template-columns: repeat(2, 1fr);" in css
    assert ".cc-panel:last-child:nth-child(odd) {\n    grid-column: 1 / -1;" in css
    assert ".cc-panels {\n    grid-template-columns: repeat(6, 1fr);" in css
    assert ".cc-panel:nth-child(n+4),\n  .cc-panel:last-child:nth-child(odd) {\n    grid-column: span 3;" in css
    assert "grid-template-columns: 1fr" in rule(css, ".cc-panels")  # one column on a phone


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


def test_the_tabs_run_home_why_docs_blog(home: str):
    """M23-R2's introductory pages have a tab of their own, before the reference docs."""
    tabs = [
        " ".join(text(label).split())
        for _, label in re.findall(
            r'<a href="([^"]*)" class="md-tabs__link[^"]*">(.*?)</a>', home, re.S
        )
    ]
    assert tabs == ["Home", "Why CodeCrew", "Docs", "Blog"]


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
    assert {f"./why/{slug}/" for slug in INTRO_PAGES} <= targets, sorted(targets)  # the Why CodeCrew tab's pages


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


def test_the_home_burger_is_a_keyboard_control(home: str, blog: str, docs_index: str):
    """Below the breakpoint the theme's burger is a <label for="__drawer"> with no Tab stop,
    so a keyboard could not open the drawer. On the home page a script makes it a button
    that controls the drawer and keeps its expanded state (M19-R7); the other pages keep
    the theme's burger (#58). Without JavaScript the markup is the theme's, unchanged."""
    assert 'id="cc-drawer"' in re.search(r'<div class="md-sidebar md-sidebar--primary[^>]*>', home).group(0)
    burger = re.search(r'<label class="md-header__button md-icon" for="__drawer"[^>]*>', home).group(0)
    assert 'aria-label="' in burger  # the theme's accessible name stays
    assert "tabindex" not in burger and "role=" not in burger  # added at runtime, so no-JS is as before
    footer = home[home.index('<footer class="md-footer cc-footer">') :]
    script = re.search(r"<script>(.*?)</script>", footer, re.S).group(1)
    for hook in (
        'label.md-header__button[for="__drawer"]',  # the theme's burger
        'getElementById("__drawer")',  # the theme's toggle
        'setAttribute("role", "button")',
        'setAttribute("tabindex", "0")',
        'setAttribute("aria-controls", "cc-drawer")',
        '"aria-expanded"',
        '"change"',  # kept in step however the toggle moves (burger, overlay)
        'event.key === "Enter" || event.key === " "',
        'event.key === "Escape"',
        "p.burger.focus()",  # Escape hands focus back to the burger
        "window.document$",  # re-run on instant navigation, and undone off the home page
        "removeAttribute",
    ):
        assert hook in script, hook
    # Inside the container, whose scripts the theme re-runs on instant navigation.
    assert home.index("<script>", home.index('class="md-footer cc-footer"')) < home.index('<div class="md-dialog"')
    for page in (blog, docs_index):
        assert "cc-drawer" not in page and 'aria-controls="cc-drawer"' not in page


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


# The theme's search panel classes, shut: the panel and its filter pane (M19-R7).
SEARCH_SHUT_CLASSES = (".l.d", ".a.d")


def home_script(home: str) -> str:
    footer = home[home.index('<footer class="md-footer cc-footer">') :]
    return re.search(r"<script>(.*?)</script>", footer, re.S).group(1)


def shut_search_rules(script: str) -> dict[str, str]:
    """The rules the home page's script adds inside the search's shadow root, by selector."""
    sheet = "".join(re.findall(r'"([^"]*)"', re.search(r"var SEARCH_SHUT =(.*?);\n", script, re.S).group(1)))
    return dict(re.findall(r"([^{}]+)\{([^}]*)\}", sheet))


def test_the_shut_search_panel_is_out_of_the_tab_order(home: str, blog: str, docs_index: str):
    """The theme's search is a shadow-root panel that, shut, is only faded out, so Tab
    walked through three of its controls at 1280px and four at 375px. On the home page a
    script puts a rule in that shadow root hiding the shut panel and filter pane once
    their fade is over (M19-R7); off the home page it takes the rule out again."""
    script = home_script(home)
    rules = shut_search_rules(script)
    assert tuple(rules) == SEARCH_SHUT_CLASSES
    for selector, body in rules.items():
        assert "visibility:hidden" in body, selector
        assert re.search(r"visibility 0s \.\d+s\b", body), selector  # hidden only after the fade
    for hook in (
        ".shadowRoot",  # the theme's search host
        'mine.id = "cc-search-shut"',
        "root.appendChild(mine)",
        "mine.remove()",  # undone on a page reached by instant navigation
        "quietSearch(!!p.drawer)",  # the drawer's id marks the home page
        "new MutationObserver",  # the theme may mount search after this runs
    ):
        assert hook in script, hook
    for page in (blog, docs_index):
        assert "cc-search-shut" not in page


def test_the_shut_search_rules_follow_the_theme_they_key_off(site: Path, home: str):
    """The rules name the theme's minified class names and repeat its transitions, with a
    delayed visibility change added. If a theme upgrade renames the classes or changes the
    fade, this fails rather than letting the invisible Tab stops quietly come back."""
    bundles = list((site / "assets/javascripts").glob("bundle.*.min.js"))
    assert len(bundles) == 1, bundles
    theme = bundles[0].read_text()
    for selector, ours in shut_search_rules(home_script(home)).items():
        match = re.search(re.escape(selector) + r"\{([^}]*)\}", theme)
        assert match, f"the theme no longer ships {selector}"
        declared = dict(d.split(":", 1) for d in match.group(1).split(";"))
        assert "pointer-events" in declared or "width" in declared, selector  # the shut state
        assert declared["opacity"] == "0", selector
        transition = dict(d.split(":", 1) for d in ours.split(";"))["transition"]
        assert transition.startswith(declared["transition"] + ",visibility 0s "), selector


# The palette toggle's ring on the home page (M19-R7): whichever radio has keyboard
# focus, the label on show carries the theme's own focus ring.
PALETTE_RING = (
    "body:has(.cc-home) .md-header__option:has(> .md-option:is(:focus-visible, .focus-visible))"
    " > label:not([hidden])"
)
THEME_OPTION_RING = ".md-option.focus-visible+label{"


def palette_form(page: str) -> str:
    start = page.index('<form class="md-header__option" data-md-component="palette">')
    return page[start : page.index("</form>", start)]


def test_the_palette_toggle_shows_keyboard_focus_on_the_home_page(css: str, home: str, blog: str, docs_index: str):
    """The theme rings the label straight after the focused radio. It never checks a radio
    on load, only un-hides one label, so Tab lands on the first radio and Shift+Tab on the
    last, whose next label is often the hidden one: in a fresh OS-dark visit Tab reached
    the palette with no ring at all (QA on #61). On the home page the label on show takes
    the ring whichever radio has focus (M19-R7)."""
    ring = rule(css, PALETTE_RING)
    assert "outline-style: auto" in ring
    assert "outline-color: var(--md-accent-fg-color)" in ring
    # The markup the rule rests on, the same on every page: two radios in the header's
    # palette form, each followed by the label that switches to the other, one hidden.
    for name, page in (("home", home), ("blog", blog), ("docs", docs_index)):
        pairs = re.findall(r'<input class="md-option"[^>]*id="(__palette_\d)">\s*<label ([^>]*)>', palette_form(page))
        assert [radio for radio, _ in pairs] == ["__palette_0", "__palette_1"], name
        assert [re.search(r'for="([^"]*)"', label).group(1) for _, label in pairs] == ["__palette_1", "__palette_0"]
        assert all(label.endswith(" hidden") for _, label in pairs), name  # the theme's script un-hides one
    # Scoped by the home page's container: the docs and the blog have none.
    assert "cc-home" in home
    for page in (blog, docs_index):
        assert "cc-home" not in page


def test_the_palette_ring_follows_the_theme_it_keys_off(site: Path, css: str):
    """The ring is the theme's own, and the theme still shows the palette by un-hiding the
    label after the chosen radio rather than checking it. If an upgrade changes either,
    this fails rather than letting the rule drift from what it mends."""
    bundled = [p for p in (site / "assets/stylesheets/modern").glob("*.css") if "palette" not in p.name]
    assert len(bundled) == 1, bundled
    theme_css = bundled[0].read_text()
    assert ".md-option{position:absolute;width:0;height:0;opacity:0}" in theme_css  # the radios are invisible
    start = theme_css.index(THEME_OPTION_RING) + len(THEME_OPTION_RING)
    theirs = theme_css[start : theme_css.index("}", start)].split(";")
    ours = [d.strip().rstrip(";").replace(": ", ":") for d in rule(css, PALETTE_RING).strip().splitlines()]
    assert ours == theirs, (ours, theirs)
    bundles = list((site / "assets/javascripts").glob("bundle.*.min.js"))
    assert len(bundles) == 1, bundles
    theme = bundles[0].read_text()
    assert re.search(r"nextElementSibling;(\w+) instanceof HTMLElement&&\(\1\.hidden=", theme)
    assert 'b(e,"keydown").pipe(O(a=>a.key==="Enter")' in theme  # Enter toggles and refocuses


# M23-R2: four introductory pages, written for the site (not synced from the hub), one per
# problem a stranger searches before they know the name. Each carries its search phrase in its
# title, H1, meta description and opening paragraph (the Decision on www#76 records the phrases).
INTRO_PAGES = {
    "second-model-review": ("AI code review by a second model", "AI code review by a second model"),
    "github-app-per-agent": ("GitHub App for AI coding agents", "GitHub App for AI coding agents: one per agent"),
    "gates-in-code": ("enforce review gates for AI coding agents", "Enforce review gates for AI coding agents"),
    "compared": ("Spec Kit, BMAD, OpenSpec and GSD", "CodeCrew compared with Spec Kit, BMAD, OpenSpec and GSD"),
}
# M23-R5: the hub's feedback category, which every introductory page and the homepage link.
TRIED_IT = "https://github.com/radiusred/gh-codecrew/discussions/categories/i-tried-it"
INTRO_WORDS_MAX = 650  # "a few hundred words at most", the table and the closing links included
# The M15 record's `milestone close --dry-run`: the gates page quotes it character-exact.
DRY_RUN_RECORD = "docs/milestones/15-v2-0-1-what-the-fleet-migration-taught.md"
# What the gates page says each verb checks, keyed by the SPEC §10 refusal codes that back it.
INTRO_FINISH_CHECKS = {
    "its CI checks have run, and every one is green": ("NO_CHECKS", "CHECKS_PENDING", "CHECKS_FAILING"),
    "the approval your setup requires": ("NO_HOLDER_REVIEW", "NO_NONDOER_APPROVAL"),
    "every question raised for a human has an answer on record": ("GATED", "GATE_UNRECORDED"),
    "it is run by whoever started the task": ("NOT_OWNER",),
}
INTRO_CLOSE_CHECKS = {
    "every task under it is closed": ("OPEN_TASKS",),
    "every requirement's latest QA verdict is satisfied": ("VERDICT_MISSING", "VERDICT_UNSATISFIED"),
    "the milestone's write-up is on the default branch": ("DOC_MISSING",),
}
# Every claim the comparison makes about another tool links that tool's own repository or docs.
TOOL_SOURCES = {
    "Spec Kit": ("https://github.com/github/spec-kit", "https://github.github.io/spec-kit/quickstart.html"),
    "BMAD Method": ("https://github.com/bmad-code-org/BMAD-METHOD", "https://docs.bmad-method.org/start/build-your-first-change/"),
    "OpenSpec": ("https://github.com/Fission-AI/OpenSpec", "https://openspec.dev/"),
    "GSD": ("https://github.com/open-gsd/gsd-core",),
}


class IntroPage(NamedTuple):
    slug: str
    phrase: str
    title: str
    page: str     # the built HTML
    article: str  # the page's own content, heading anchors dropped


@pytest.fixture(scope="module")
def intro_pages(site: Path) -> list[IntroPage]:
    pages = []
    for slug, (phrase, title) in INTRO_PAGES.items():
        built = (site / "why" / slug / "index.html").read_text()
        article = built[built.index("<article") : built.index("</article>")]
        article = re.sub(r'<a class="headerlink".*?</a>', "", article, flags=re.S)
        pages.append(IntroPage(slug, phrase, title, built, article))
    return pages


def test_each_intro_page_has_its_own_title_and_description(intro_pages: list[IntroPage], site: Path):
    """M23-R8: a title and a description of its own, not the site's, so search engines and
    link previews have something to show for the page."""
    config = (site.parent / "zensical.toml").read_text()
    site_description = re.search(r'^site_description = "(.*)"$', config, re.M).group(1)
    descriptions = set()
    for intro in intro_pages:
        front = front_matter(ROOT / "docs" / "why" / f"{intro.slug}.md")
        meta = head_meta(intro.page)
        assert front["title"] == intro.title, intro.slug
        assert meta["title"] == meta["og:title"] == meta["twitter:title"] == f"{intro.title} - CodeCrew", intro.slug
        assert meta["description"] == meta["og:description"] == meta["twitter:description"] == front["description"]
        assert meta["description"] != site_description, intro.slug
        descriptions.add(meta["description"])
        assert f'<link rel="canonical" href="https://codecrew.works/why/{intro.slug}/">' in intro.page
    assert len(descriptions) == len(INTRO_PAGES)


def test_each_intro_page_carries_its_search_phrase_four_times(intro_pages: list[IntroPage]):
    """M23-R2: the phrase a stranger types before they know the name is in the title, the H1,
    the meta description and the opening paragraph."""
    for intro in intro_pages:
        h1 = squash(text(re.search(r"<h1[^>]*>(.*?)</h1>", intro.article, re.S).group(1)))
        opening = squash(text(re.search(r"</h1>\s*<p>(.*?)</p>", intro.article, re.S).group(1)))
        meta = head_meta(intro.page)
        for where, words in (("title", meta["title"]), ("h1", h1), ("description", meta["description"]), ("opening", opening)):
            assert intro.phrase.lower() in words.lower(), (intro.slug, where)
        assert h1 == intro.title


def test_each_intro_page_is_short_and_ends_with_a_next_step_and_the_invitation(intro_pages: list[IntroPage]):
    """M23-R2 and R5: short, one idea, then a next step, then a plain invitation to the "I tried
    it" category, then the other three pages (R8)."""
    for intro in intro_pages:
        words = squash(text(intro.article)).split()
        assert len(words) <= INTRO_WORDS_MAX, (intro.slug, len(words))
        next_step = intro.article.index('<h2 id="next-step">')
        invite = intro.article.index(f'href="{TRIED_IT}"')
        more = intro.article.index('<h2 id="more-for-newcomers">')
        assert next_step < invite < more, intro.slug
        step = intro.article[next_step:invite]
        assert re.search(r'href="\.\./\.\./docs/[\w-]+/(#[\w-]+)?"', step), intro.slug  # the guide or a reference doc
        box = re.search(r'<div class="admonition question">(.*?)</div>', intro.article, re.S).group(1)
        assert "Tried it? Tell us how it went" in text(box) and f'href="{TRIED_IT}"' in box, intro.slug
        assert intro.article.count(f'href="{TRIED_IT}"') == 1, intro.slug
        others = re.findall(r'href="\.\./([\w-]+)/"', intro.article[more:])
        assert sorted(others) == sorted(set(INTRO_PAGES) - {intro.slug}), intro.slug


def test_each_intro_page_links_land_on_built_pages(intro_pages: list[IntroPage], site: Path):
    for intro in intro_pages:
        for href in re.findall(r'href="(\.\./[^"#]*)(?:#([\w-]+))?"', intro.article):
            path, anchor = href
            target = (site / "why" / intro.slug / path / "index.html").resolve()
            assert target.is_file(), (intro.slug, path)
            if anchor:
                assert f'id="{anchor}"' in target.read_text(), (intro.slug, path, anchor)


def test_the_intro_pages_are_in_the_sitemap(site: Path):
    """M23-R8: Google finds them through the sitemap as well as the homepage."""
    sitemap = (site / "sitemap.xml").read_text()
    for slug in INTRO_PAGES:
        assert f"<loc>https://codecrew.works/why/{slug}/</loc>" in sitemap, slug


def test_the_homepage_links_each_intro_page_and_the_invitation(home: str):
    """M23-R8 and R5: a compact "New here?" row under the Why panels links each page, and one
    line invites a reader who tried it. It adds no section: the M22 order is pinned above."""
    why = section(home, "cc-why")
    row = why[why.index('<div class="cc-newhere">') :]
    assert why.index('<div class="cc-panels">') < why.index('<div class="cc-newhere">')
    links = re.findall(r'<li><a href="why/([\w-]+)/">(.*?)</a></li>', row)
    assert [slug for slug, _ in links] == list(INTRO_PAGES)
    for slug, label in links:
        assert INTRO_PAGES[slug][0].lower() in label.lower(), slug  # the page's own search phrase, as anchor text
    invite = re.search(r'<p class="cc-newhere__invite">(.*?)</p>', row, re.S).group(1)
    assert f'href="{TRIED_IT}"' in invite and "Tell us how it went" in invite
    assert section(home, "cc-why").count(f'href="{TRIED_IT}"') == 1  # once, in the row
    assert "<h2" not in row and "<h3" not in row  # a row, not another section or panel


def test_the_intro_pages_name_no_crew_member(intro_pages: list[IntroPage]):
    """The M8 rule: crew member names stay off product pages; bot logins only in link targets
    or screen-grabs. And topos is no one's example."""
    for intro in intro_pages:
        words = text(intro.article).lower()
        for name in CREW_MEMBER_NAMES + ("topos",):
            assert not re.search(rf"\b{name}\b", words), (intro.slug, name)
        assert "[bot]" not in re.sub(r"<code>\[bot\]</code>", "", intro.article)  # the suffix, never a login


def test_the_required_review_caveat_is_stated_once_across_the_intro_pages(intro_pages: list[IntroPage]):
    """The write-permission opt-in and the paid plan private repos need, on the identity page
    alone; the gates page links it."""
    homes = [intro.slug for intro in intro_pages if PAID_PLAN in squash(text(intro.article))]
    assert homes == ["github-app-per-agent"]
    identity = next(intro for intro in intro_pages if intro.slug == "github-app-per-agent")
    words = squash(text(identity.article))
    assert "--with-approval-permission" in words and "write access" in words
    assert "task finish refuses until the reviewer App has approved" in words
    gates = next(intro for intro in intro_pages if intro.slug == "gates-in-code")
    assert 'href="../github-app-per-agent/#one-caveat-about-required-reviews"' in gates.article
    assert 'id="one-caveat-about-required-reviews"' in identity.article


def test_the_second_model_page_keeps_its_claims_bounded(intro_pages: list[IntroPage]):
    """A fresh session as well as a distinct identity; a bot name proves an App, not a model;
    the operator or an orchestrator starts the sessions; no review catches everything."""
    page = next(intro for intro in intro_pages if intro.slug == "second-model-review")
    words = squash(text(page.article))
    assert f"“{REVIEWER_REASON}”" in words  # quoted exactly from the reviewer contract
    assert "It runs in a new session, with none of the builder's conversation" in words
    assert "a different bot name proves a different App, not a different model" in words
    assert "CodeCrew does not start agents or choose models: you do, or an orchestrator does" in words
    assert "No review catches every bug" in words
    lines = code_lines(page.article)
    assert [line.strip() for line in lines if "harness:" in line] == ["harness: claude-code", "harness: codex"]
    assert all(re.fullmatch(r"identity: app:myorg-[a-z]+", line.strip()) for line in lines if "identity:" in line)


def test_the_gates_page_claims_only_what_the_refusal_table_backs(intro_pages: list[IntroPage]):
    """M23-R2 (c): every check named for task finish and milestone close is a refusal that
    verb raises in the hub's SPEC §10 table, and task start's plan check is task start's."""
    page = next(intro for intro in intro_pages if intro.slug == "gates-in-code")
    words = squash(text(page.article))
    table = refusal_table()
    finish = words[words.index("gh codecrew task finish merges") : words.index("gh codecrew milestone close closes")]
    close = words[words.index("gh codecrew milestone close closes") : words.index("Earlier still")]
    for claims, verb, part in ((INTRO_FINISH_CHECKS, "task finish", finish), (INTRO_CLOSE_CHECKS, "milestone close", close)):
        for claim, codes in claims.items():
            assert claim in part, claim
            for code in codes:
                assert f"`{verb}`" in table[code], (claim, code)
    assert "task start refuses a task with no plan" in words and "`task start`" in table["NO_PLAN"]
    assert "plan" not in finish.lower() and "plan" not in close.lower()


def test_the_gates_page_quotes_a_real_refusal_exactly(intro_pages: list[IntroPage]):
    """One example refusal, in SPEC §6's `refused[CODE]: detail` shape, quoted character-exact
    from the hub's M15 record, which the page links at the commit it was read from."""
    page = next(intro for intro in intro_pages if intro.slug == "gates-in-code")
    record = (UPSTREAM / "gh-codecrew" / DRY_RUN_RECORD).read_text()
    lines = code_lines(page.article[page.article.index('<h2 id="what-a-refusal-looks-like">') :])
    quoted = "\n".join(lines)
    assert quoted in record
    refusals = [line for line in lines if "refused[" in line]
    assert len(refusals) == 1
    code = re.search(r"refused\[([A-Z_]+)\]: \S", refusals[0]).group(1)
    assert "`milestone close`" in refusal_table()[code]
    spec = (UPSTREAM / "gh-codecrew" / "SPEC.md").read_text()
    assert "codecrew: refused[CODE]: detail" in spec and "refused[CODE]: detail" in squash(text(page.article))
    assert f"/blob/149bd78a32d7180b9a06705c796bb0772b9ccd74/{DRY_RUN_RECORD}#L89-L97" in page.article


def test_the_comparison_links_each_tool_at_its_own_source(intro_pages: list[IntroPage]):
    """M23-R2 (d): describes, never disparages; every claim about another tool links that
    tool's own repository or docs; GSD appears as the origin story, linking the essay."""
    page = next(intro for intro in intro_pages if intro.slug == "compared")
    for tool, sources in TOOL_SOURCES.items():
        part = re.search(rf'<h2 id="[\w-]+">{tool}</h2>(.*?)<h2', page.article, re.S).group(1)
        for href in sources:
            assert f'href="{href}"' in part, (tool, href)
    gsd = re.search(r'<h2 id="gsd">GSD</h2>(.*?)<h2', page.article, re.S).group(1)
    assert "GSD is where CodeCrew began" in squash(text(gsd))
    assert 'href="../../docs/gsd-vs-frontier-orchestration/"' in gsd
    words = squash(text(page.article)).lower()
    for slight in ("ceremony", "bloat", "worse", "better than", "unlike", "outdated", "obsolete"):
        assert slight not in words, slight
    rows = re.findall(r"<tr>\s*<td>(.*?)</td>", page.article, re.S)
    assert [text(r).strip() for r in rows] == ["Spec Kit", "BMAD Method", "OpenSpec", "GSD", "CodeCrew"]


def test_the_intro_pages_commands_fit_a_phone(intro_pages: list[IntroPage]):
    """Every code line a reader might copy keeps to the homepage's ceiling, so it does not
    scroll at 375px; the quoted dry run is a record, character-exact, and is the exception."""
    for intro in intro_pages:
        blocks = re.findall(r"<pre>.*?</pre>", intro.article, re.S)
        for block in blocks:
            lines = code_lines(block)
            if any("refused[" in line for line in lines):
                continue
            too_long = [line for line in lines if len(line) > STEP_CODE_MAX]
            assert not too_long, (intro.slug, too_long)
