---
title: AI code review by a second model
description: AI code review by a second model, with CodeCrew. One coding agent builds the change, and a different model or harness reviews it in a fresh session, under its own GitHub identity.
---

# AI code review by a second model

AI code review by a second model works like this. One coding agent writes the change and opens a pull request. A different agent, ideally running on another model or in another harness, reviews it before it merges. CodeCrew, an extension for GitHub's `gh` command line, sets that up and keeps the whole exchange on GitHub.

## Why a second model helps

A model checking its own work tends to miss what it missed the first time. CodeCrew's reviewer instructions put it plainly: “self-evaluation shares the blind spots of the work itself”. A different model has blind spots too, but they are different ones. So you might have Claude Code build and Codex review, or the other way round.

No review catches every bug. A second opinion from somewhere else is still a better bet than marking your own homework.

## What it looks like

Who does what is a few lines in your project's settings file. The App names here are made up:

```yaml
roles:
  implementer:
    harness: claude-code
    identity: app:myorg-coder
  reviewer:
    harness: codex
    identity: app:myorg-checker
```

## Three things worth knowing

- **The reviewer starts fresh.** It runs in a new session, with none of the builder's conversation. An approval means little if the reviewer watched the code being written.
- **It reviews under its own name.** Each agent can have [a GitHub App of its own](github-app-per-agent.md), so the pull request shows one App as the author and another as the reviewer.
- **You pick the models.** CodeCrew does not start agents or choose models: you do, or an orchestrator does. The settings file records what you intend to run, and a different bot name proves a different App, not a different model.

## Next step

Set up a project and take a first task through: [Your first milestone](../docs/first-milestone.md). When you want an agent reviewer, the identities guide shows [how a review session is started](../docs/identities.md#dispatching-a-role-session).

!!! question "Tried it? Tell us how it went"

    What did you try, how far did you get, and what stopped you? [Tell us in “I tried it”](https://github.com/radiusred/gh-codecrew/discussions/categories/i-tried-it), on GitHub Discussions.

## More for newcomers

- [GitHub App for AI coding agents: one per agent](github-app-per-agent.md)
- [Enforce review gates for AI coding agents](gates-in-code.md)
- [CodeCrew compared with Spec Kit, BMAD, OpenSpec and GSD](compared.md)
