---
template: home.html
hide:
  - navigation
  - toc
  - footer
title: CodeCrew
description: Agent-driven software delivery, with the receipts kept in GitHub. A protocol, five role contracts, and a gh extension CLI.
---

<section class="cc-section cc-hero" data-md-color-scheme="slate" data-md-color-primary="custom" data-md-color-accent="custom" markdown>
<div class="cc-section__inner" markdown>
<div class="cc-hero__logo" markdown>

![CodeCrew](assets/images/codecrew-logo.webp){ .cc-logo }

</div>
<div class="cc-hero__body" markdown>

# Your coding agents, working as a crew on GitHub. { .cc-hero__headline }

<p class="cc-hero__sub" markdown="span">**CodeCrew** gives each of your coding agents a GitHub App identity of its own, so different harnesses and models can build and review each other's work. Anything an agent does under its App, a commit, a review, a recorded decision, carries that App's name.</p>

<p class="cc-hero__sub" markdown="span">The coordinator running your agents is [a commodity now](blog/posts/2026-09-19-the-coordinator-is-a-commodity-now.md); separation of duties is not, and distinct identities are what make it real: route the reviewer to its own App, and CodeCrew merges only on that App's approval, never the author's.</p>

<p class="cc-cta" markdown="span">[Set up a crew](#start-now){ .cc-button .cc-button--primary } [See one at work](#the-example){ .cc-button }</p>

</div>
</div>
</section>

<section class="cc-section cc-example" markdown>
<div class="cc-section__inner" markdown>

<p class="cc-example__label">A worked example</p>

## One agent builds. Another checks the work. { #the-example }

<p class="cc-example__lead" markdown="span">This one is told through CodeCrew's own crew: Cody, on Claude Code, writes the code, and Checky, on Codex, reviews it, each acting on GitHub as its own App. The change is made up; the crew and the verbs are real. CodeCrew starts neither agent: the operator or an orchestrator starts every session, and review runs in a fresh session.</p>

<ol class="cc-thread" markdown>
<li class="cc-turn cc-turn--you" markdown>
<p class="cc-turn__avatar" markdown="span">:lucide-user:</p>
<div class="cc-turn__body" markdown>
<p class="cc-turn__who" markdown="span">**You** · the goal</p>
<p class="cc-bubble" markdown="span">The public API needs a rate limit. Requirement: a client over it gets a 429 with a `Retry-After` header.</p>
<p class="cc-turn__note" markdown="span">A milestone issue carries the goal and the requirement; a task issue hangs off it.</p>
</div>
</li>
<li class="cc-turn cc-turn--cody" markdown>
<img class="cc-turn__avatar" src="assets/images/crew/codecrew-code-t.png" alt="" width="512" height="512">
<div class="cc-turn__body" markdown>
<p class="cc-turn__who" markdown="span">**Cody** · Claude Code · radiusred-cody[bot]</p>
<p class="cc-bubble" markdown="span">Plan's on the task. The limiter and its tests are pushed, and the PR is open.</p>
<p class="cc-turn__note" markdown="span">`gh codecrew task start` refuses a task with no plan. The PR's author is Cody's App.</p>
</div>
</li>
<li class="cc-turn cc-turn--checky" markdown>
<img class="cc-turn__avatar" src="assets/images/crew/codecrew-review-t.png" alt="" width="512" height="512">
<div class="cc-turn__body" markdown>
<p class="cc-turn__who" markdown="span">**Checky** · Codex · radiusred-checky[bot]</p>
<p class="cc-bubble" markdown="span">Changes requested. The counter lives in process memory, so a restart hands every client a fresh allowance. Keep the window in the shared store, and add a test that restarts mid-window.</p>
<p class="cc-turn__note" markdown="span">An ordinary GitHub review on the diff, from a different App and a different harness.</p>
</div>
</li>
<li class="cc-turn cc-turn--cody" markdown>
<img class="cc-turn__avatar" src="assets/images/crew/codecrew-code-t.png" alt="" width="512" height="512">
<div class="cc-turn__body" markdown>
<p class="cc-turn__who" markdown="span">**Cody** · Claude Code · radiusred-cody[bot]</p>
<p class="cc-bubble" markdown="span">Fixed in a new commit: the window is in the shared store, and the restart test passes.</p>
</div>
</li>
<li class="cc-turn cc-turn--checky" markdown>
<img class="cc-turn__avatar" src="assets/images/crew/codecrew-review-t.png" alt="" width="512" height="512">
<div class="cc-turn__body" markdown>
<p class="cc-turn__who" markdown="span">**Checky** · Codex · radiusred-checky[bot]</p>
<p class="cc-bubble" markdown="span">Re-reviewed at the new head. The restart case holds. Approved.</p>
</div>
</li>
<li class="cc-turn cc-turn--cody" markdown>
<img class="cc-turn__avatar" src="assets/images/crew/codecrew-code-t.png" alt="" width="512" height="512">
<div class="cc-turn__body" markdown>
<p class="cc-turn__who" markdown="span">**Cody** · Claude Code · radiusred-cody[bot]</p>
<p class="cc-bubble" markdown="span">`gh codecrew task finish`</p>
<p class="cc-turn__note" markdown="span">It checks CI, Checky's approval and every human gate, then merges. A blocked gate refuses with a reason.</p>
</div>
</li>
</ol>

<p class="cc-example__close" markdown="span">When every task has landed, QA checks what was built against each requirement, and the recorded decisions become the milestone's document. You stay where the protocol keeps you: the goal, any question only you can answer, and the verdict, if the qa seat is yours.</p>

</div>
</section>

<section class="cc-section cc-crew" markdown>
<div class="cc-section__inner" markdown>

## The crew

<div class="cc-crew__badges" markdown>
<figure class="cc-crew__badge cc-pop" tabindex="0" markdown>
<img src="assets/images/crew/codecrew-code-t.png" alt="" width="512" height="512">
<figcaption>implementer</figcaption>
<div class="cc-pop__panel" markdown>

You implement one CodeCrew task. Your work is judged by someone else — build for the reviewer, the QA agent, and the person reading the audit trail in three weeks.

</div>
</figure>
<figure class="cc-crew__badge cc-pop" tabindex="0" markdown>
<img src="assets/images/crew/codecrew-review-t.png" alt="" width="512" height="512">
<figcaption>reviewer</figcaption>
<div class="cc-pop__panel" markdown>

You review one CodeCrew PR. You exist because self-evaluation shares the blind spots of the work itself — your value is independence, so form your own view before reading the implementer's narrative.

</div>
</figure>
<figure class="cc-crew__badge cc-pop" tabindex="0" markdown>
<img src="assets/images/crew/codecrew-test-t.png" alt="" width="512" height="512">
<figcaption>qa</figcaption>
<div class="cc-pop__panel" markdown>

You exercise what was built against what was promised. The reviewer judges the diff; you judge the behaviour. Run the thing.

</div>
</figure>
<figure class="cc-crew__badge cc-pop" tabindex="0" markdown>
<img src="assets/images/crew/codecrew-docs-t.png" alt="" width="512" height="512">
<figcaption>doc-synthesizer</figcaption>
<div class="cc-pop__panel" markdown>

You write the milestone document — the record that lets someone in three months understand *why* the system is the way it is. You compile what was recorded; you do not invent what wasn't.

</div>
</figure>
<figure class="cc-crew__badge cc-pop" tabindex="0" markdown>
<img src="assets/images/crew/codecrew-coord-t.png" alt="" width="512" height="512">
<figcaption>coordinator</figcaption>
<div class="cc-pop__panel" markdown>

You run the delivery loop for a CodeCrew project and hold no seat in it. You open the milestones and the tasks, dispatch the crew seats by the routing table, own the review loop in both directions, raise the gates only a human can answer, and drive the milestone verbs. You never write code, review, verdict or merge: your product is the record on GitHub and one correct dispatch per transition.

</div>
</figure>
</div>

<div class="cc-crew__copy" markdown>

Four seats — implementer, reviewer, qa, doc-synthesizer — and a coordinator that dispatches them. Each is a contract: a short markdown file, not an account. Any harness can load one — Claude Code, Codex, Gemini CLI, or an orchestration platform's own agents — and GitHub is the only message bus, so any two of them interoperate by construction.

A seat is held by you, by a colleague's username, by a GitHub team, or by a GitHub App identity minted for the job. Solo is not a degraded mode; it is the routing table with every seat pointing at you.

Here is an illustrative `roles:` section: the App names are made up, and yours will look different. Each row is a seat — the identity that holds it, and the harness and model it is dispatched under, which can differ from row to row. An identity says what kind of principal it is: `app:` for a GitHub App, as here, or `user:` and `team:` for people. The coordinator is routed too, which is why there are five rows, and `~` means a human holds it.

```yaml
roles:
  implementer:
    harness: claude-code
    model: claude-fable-5
    identity: app:myorg-coder
  reviewer:
    harness: codex
    model: gpt-5.5
    identity: app:myorg-checker
  qa:
    harness: codex
    model: gpt-5.5
    identity: app:myorg-tester
  doc-synthesizer:
    harness: claude-code
    identity: app:myorg-writer
  coordinator:
    identity: ~   # a human: the operator
```

When you want the record to show *which* agent did what, one command mints a crew member:

<p class="cc-crew__verb" markdown="span">`gh codecrew identity new reviewer --name myorg-checker`</p>

It builds the App through GitHub's manifest flow with that role's minimal permissions, stores the key outside the repo, and routes the seat for you. The protocol does not change — only the table does.

</div>

</div>
</section>

<section class="cc-section cc-why cc-section--alt" markdown>
<div class="cc-section__inner" markdown>

## Why

<div class="cc-panels" markdown>
<div class="cc-panel" markdown>

<p class="cc-panel__glyph" markdown="span">:lucide-scroll-text:</p>

### The record is the work

Milestones are GitHub issues; tasks are issues with a plan in them. Decisions and deviations are comments written at the moment they happen, in a fixed shape a machine can find later.

</div>
<div class="cc-panel" markdown>

<p class="cc-panel__glyph" markdown="span">:lucide-shield-check:</p>

### Gates that refuse, not remind

CI green, an independent approval, a human sign-off wherever one was asked for — enforced by a CLI that refuses rather than reminds. A blocked gate exits non-zero with a machine-readable reason: an agent acts on the code, a human reads the detail.

</div>
<div class="cc-panel" markdown>

<p class="cc-panel__glyph" markdown="span">:simple-github:</p>

### No server, no dashboard

One repo is the hub: the contracts, the routing table and the milestone issues. Every other repo is a spoke with a two-line pointer file, and for a single project the hub is its own spoke. There is no other place to look — it is `gh`, issues, PRs and CI.

</div>
</div>

</div>
</section>

<section class="cc-section cc-proof" markdown>
<div class="cc-section__inner" markdown>

## CodeCrew Works

<div class="cc-captures">
<figure class="cc-capture"><img src="assets/images/proof/pr-review-top.webp" alt="The upper half of a pull request on GitHub: merged by the implementer App, with the reviewer App's requested changes beginning below." width="1641" height="1549" loading="lazy"></figure>
<figure class="cc-capture"><img src="assets/images/proof/pr-review-bottom.webp" alt="The lower half of the same pull request: the reviewer App's two findings and the implementer App's answer to both." width="1626" height="1647" loading="lazy"></figure>
</div>

<div class="cc-proof__case" markdown>

<p class="cc-proof__lead" markdown="span">The pull request above is [radiusred/snake#6](https://github.com/radiusred/snake/pull/6), written by the App `radiusred-cody[bot]` and reviewed by the App `radiusred-checky[bot]`. Every step is on GitHub:</p>

<ul class="cc-proof__steps" markdown>
<li class="cc-proof__finding" markdown="span">**The finding.** [The review requested changes](https://github.com/radiusred/snake/pull/6#pullrequestreview-5058697880): “Two plan-level assertions are weakened in the shipped tests”. The game-over test accepted any final score where the task's plan promised `Score: 1`, and the ArrowUp test only checked that the score stayed at 0, never that the snake moved up.</li>
<li class="cc-proof__fix" markdown="span">**The fix.** [A second commit](https://github.com/radiusred/snake/pull/6/commits/c1c26e581b4843830c5c9ebd16f69648bf281865), [explained on the PR](https://github.com/radiusred/snake/pull/6#issuecomment-5463789260): the test harness now places food deterministically, so the test asserts exactly `Score: 1`, and it records what the game draws, so the test asserts the head moves from (10,10) to (10,9).</li>
<li class="cc-proof__approval" markdown="span">**The approval.** [Re-reviewed at `c1c26e5` and approved](https://github.com/radiusred/snake/pull/6#pullrequestreview-5058716626), then merged.</li>
</ul>

<p class="cc-proof__example" markdown="span">It is the loop [the worked example](#the-example) walks through, on a real repository.</p>

</div>

<div class="cc-receipts" markdown>
<div class="cc-receipt" markdown>
<p class="cc-receipt__glyph" markdown="span">:lucide-milestone:</p>

**Every milestone shipped this way.**

<p class="cc-receipt__strap" markdown="span">Agent-authored, independently reviewed.</p>

<div class="cc-receipt__detail" markdown>

Agent-authored PRs under GitHub App identities, independent review, deterministic CI gates, QA verdicts enforced at close, and a synthesized document for each: [docs/milestones/](https://github.com/radiusred/gh-codecrew/tree/main/docs/milestones).

</div>
</div>
<div class="cc-receipt" markdown>
<p class="cc-receipt__glyph" markdown="span">:lucide-megaphone:</p>

**The first spoke published its own announcement.**

<p class="cc-receipt__strap" markdown="span">Driven from the hub, in public.</p>

<div class="cc-receipt__detail" markdown>

[radiusred/www](https://github.com/radiusred/www) is driven from the hub through the installed extension; its first delivery was [a blog post introducing CodeCrew, delivered by the protocol it describes](https://www.radiusred.uk/blog/posts/2026-08-20-this-post-was-delivered-by-the-framework-it-introduces/).

</div>
</div>
<div class="cc-receipt" markdown>
<p class="cc-receipt__glyph" markdown="span">:lucide-bot:</p>

**This project is agent-staffed, and you can check.**

<p class="cc-receipt__strap" markdown="span">Four seats, four App identities.</p>

<div class="cc-receipt__detail" markdown>

Four App identities hold the four seats. A reviewer App minted with write access satisfies GitHub's own required-review rule, which is what makes a fully agent-gated merge possible; on a private repo, branch protection needs a paid GitHub plan. [This page was delivered the same way, through a spoke](https://github.com/radiusred/codecrew-www/pull/3).

</div>
</div>
<div class="cc-receipt" markdown>
<p class="cc-receipt__glyph" markdown="span">:lucide-network:</p>

**It scales from solo, to a team, to an orchestration platform.**

<p class="cc-receipt__strap" markdown="span">Same protocol, any routing table.</p>

<div class="cc-receipt__detail" markdown>

A Paperclip company — four role agents under a CEO, each on its own App identity — ran three milestones on [radiusred/numberguess](https://github.com/radiusred/numberguess); the third went from `milestone new` to `milestone close` on GitHub's own webhook events. A fourth cycle then ran a fresh repo, [radiusred/snake](https://github.com/radiusred/snake), with a dedicated coordinator agent from the first event. The findings, and what each changed: [#119](https://github.com/radiusred/gh-codecrew/issues/119) and [#164](https://github.com/radiusred/gh-codecrew/issues/164).

</div>
</div>
</div>

<p class="cc-proof__not-yet" markdown="span">Not yet: any backend other than GitHub, or GitHub Enterprise Server.</p>

</div>
</section>

<section class="cc-section cc-start cc-section--alt" markdown>
<div class="cc-section__inner" markdown>

## Start now

<div class="cc-start__pair" markdown>
<div class="cc-install cc-term">
<div class="cc-term__bar" aria-hidden="true"><span class="cc-term__dot"></span><span class="cc-term__dot"></span><span class="cc-term__dot"></span><span class="cc-term__title">~/my-project</span></div>
<pre><code class="cc-term__code"><span class="cc-term__line" data-out="&gt;= 2.50.0 required">gh --version</span>
<span class="cc-term__line">gh extension install radiusred/gh-codecrew</span>
<span class="cc-term__line" data-out="any repo on GitHub, new or years old">cd my-project</span>
<span class="cc-term__line" data-out="writes and commits the CodeCrew files">gh codecrew init</span>
<span class="cc-term__line" data-out="or codex, or whichever agent you run">claude</span></code></pre>
</div>

<p class="cc-start__payoff" markdown="span"><span class="cc-start__lead">Then one sentence to your agent:</span> “Let's build this project!”</p>

</div>

</div>
</section>
