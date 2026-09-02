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

The reference material lives with the code on GitHub:

- [Overview](https://github.com/radiusred/gh-codecrew#readme) — why you would want a crew, and how it works in four beats
- [Introduction](https://github.com/radiusred/gh-codecrew/blob/main/docs/introduction.md) — the protocol, the contracts, the CLI and its refusal codes
- [Your first milestone](https://github.com/radiusred/gh-codecrew/blob/main/docs/first-milestone.md) — the quickstart, one milestone end to end
- [Identities](https://github.com/radiusred/gh-codecrew/blob/main/docs/identities.md) — running solo, minting App identities, dispatching a role session
- [Specification](https://github.com/radiusred/gh-codecrew/blob/main/SPEC.md) — the protocol itself

## Follow along

The [blog](blog/) carries release notes, design decisions and field reports from building and running CodeCrew. Subscribe via the [Atom feed](blog/atom.xml), or watch the [repository](https://github.com/radiusred/gh-codecrew).

CodeCrew is built by [Radius Red](https://www.radiusred.uk/) and licensed under [Apache 2.0](https://github.com/radiusred/gh-codecrew/blob/main/LICENSE).
