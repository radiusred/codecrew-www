---
layout: default
title: CodeCrew
description: Agent-driven software delivery, with the receipts kept in GitHub. A protocol, five role contracts, and a gh extension CLI.
---

![CodeCrew](assets/images/codecrew-logo.webp){: class="cc-logo" }

# Agent-driven software delivery,<br>with the receipts kept in GitHub { .hero }

CodeCrew is a small framework for running coding agents on real codebases without losing the *why*. Milestones are GitHub issues. Tasks are issues with a plan in them. Decisions and deviations are comments written at the moment they happen. The gates are enforced by a `gh` extension that refuses rather than reminds.

There is no server, no dashboard, no new place to look. It is `gh`, issues, PRs, and five short role contracts any agent harness can read.

## Start now

```sh
gh extension install radiusred/gh-codecrew
cd my-project            # any repo on GitHub, brand new or years old
gh codecrew init         # writes and commits .codecrew.yml, roles/, AGENTS.md, CLAUDE.md, ROADMAP.md
claude                   # or codex, or whichever coding agent you run
```

Then one sentence to your agent: *Let's build this project!*

You do not run the verbs. Your agent does. You are needed at three moments: when a gate asks you a question, when a PR wants your review, and when a milestone wants your verdict.

## Read next

While we're building out the site, find all the information you need at our [GitHub repo](https://github.com/radiusred/gh-codecrew).
