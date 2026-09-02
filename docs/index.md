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

# Agent-driven software delivery, with the receipts kept in GitHub. { .cc-hero__headline }

<p class="cc-hero__sub" markdown="span">CodeCrew is a third option, and a small one: **the record is the work.** Decisions and deviations are comments written at the moment they happen, in a fixed shape a machine can find later.</p>

<p class="cc-cta" markdown="span">[Start now](#start-now){ .cc-button .cc-button--primary } [Read the docs](https://github.com/radiusred/gh-codecrew#readme){ .cc-button }</p>

</div>
</div>
</section>

<section class="cc-section cc-how" markdown>
<div class="cc-section__inner" markdown>

## How it works

<div class="cc-steps" markdown>
<div class="cc-step" markdown>

### Milestone

A GitHub issue, with its requirements written into it.

</div>
<div class="cc-step" markdown>

### Task

An issue with a plan in it, hung off the milestone.

</div>
<div class="cc-step" markdown>

### PR

Gates on the way in: CI green, an independent approval, a human sign-off where one was asked for. Enforced by a CLI that refuses rather than reminds.

</div>
<div class="cc-step" markdown>

### Record

At milestone close, one role compiles the comments into a document that goes through the same review as code.

</div>
</div>

</div>
</section>

<section class="cc-section cc-why cc-section--alt" markdown>
<div class="cc-section__inner" markdown>

## Why

<div class="cc-panels" markdown>
<div class="cc-panel" markdown>

### The record is the work

Milestones are GitHub issues; tasks are issues with a plan in them. Decisions and deviations are comments written at the moment they happen, in a fixed shape a machine can find later.

</div>
<div class="cc-panel" markdown>

### Gates that refuse, not remind

The gates — CI green, an independent approval, a human sign-off wherever one was asked for — are enforced by a CLI that refuses rather than reminds. A blocked gate exits non-zero with a machine-readable reason: an agent acts on the code, a human reads the detail.

</div>
<div class="cc-panel" markdown>

### No server, no dashboard

There is no server, no dashboard, no new place to look. It is `gh`, issues, PRs, and five short role contracts any agent harness can read.

</div>
</div>

</div>
</section>

<section class="cc-section cc-proof" markdown>
<div class="cc-section__inner" markdown>

## It has shipped

<div class="cc-receipts" markdown>

- **Seven milestones of the framework were delivered with it.** Agent-authored PRs under GitHub App identities, independent review, deterministic CI gates, QA verdicts enforced at close, and a synthesized document for each: [docs/milestones/](https://github.com/radiusred/gh-codecrew/tree/main/docs/milestones).
- **The first spoke published its own announcement.** [radiusred/www](https://github.com/radiusred/www) is driven from the hub through the installed extension; its first delivery was [a blog post introducing CodeCrew, delivered by the protocol it describes](https://www.radiusred.uk/blog/posts/2026-08-20-this-post-was-delivered-by-the-framework-it-introduces/).
- **An orchestration platform drove it with no human but at the gates.** A Paperclip company, four role agents under a CEO on their own App identities, ran three milestones on [radiusred/numberguess](https://github.com/radiusred/numberguess); the third went from `milestone new` to `milestone close` on GitHub's own webhook events.
- **A fresh repo, coordinated from the first event.** A fourth cycle ran [radiusred/snake](https://github.com/radiusred/snake) with a dedicated coordinator agent from the first webhook; the findings are the logs on [#119](https://github.com/radiusred/gh-codecrew/issues/119) and [#164](https://github.com/radiusred/gh-codecrew/issues/164).

</div>

</div>
</section>

<section class="cc-section cc-start cc-section--alt" markdown>
<div class="cc-section__inner" markdown>

## Start now

<div class="cc-install" markdown>

```sh
gh extension install radiusred/gh-codecrew
cd my-project            # any repo on GitHub, brand new or years old
gh codecrew init         # writes and commits .codecrew.yml, roles/, AGENTS.md, CLAUDE.md, ROADMAP.md
claude                   # or codex, or whichever coding agent you run
```

</div>

Then one sentence to your agent: *Let's build this project!*

You do not run the verbs. Your agent does. You are needed at three moments: when a gate asks you a question, when a PR wants your review, and when a milestone wants your verdict.

</div>
</section>
