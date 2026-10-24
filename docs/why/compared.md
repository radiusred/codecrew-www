---
title: CodeCrew compared with Spec Kit, BMAD, OpenSpec and GSD
description: Spec Kit, BMAD, OpenSpec and GSD help you plan and build with an AI coding agent. CodeCrew gives each agent its own GitHub identity and checks review in code. What each is for, and when to pick which.
---

# CodeCrew compared with Spec Kit, BMAD, OpenSpec and GSD

If you have been reading about Spec Kit, BMAD, OpenSpec and GSD, you have met tools for planning and building with an AI coding agent. CodeCrew works on a neighbouring problem: which agent does the work, which one checks it, and where the record lives. Here is what each is for, and when to pick it.

## At a glance

| Tool | Good for | Where it writes things down |
|---|---|---|
| Spec Kit | Turning a written spec into a plan, tasks and code | Files such as `spec.md`, `plan.md` and `tasks.md` |
| BMAD Method | Planning sized to the work, from several angles | Briefs, specs and architecture docs |
| OpenSpec | A proposal, specs and tasks for each change | An `openspec/` folder of specs and changes |
| GSD | A phase loop run by fresh-context subagents | Files such as `STATE.md` and `CONTEXT.md` |
| CodeCrew | One agent builds, a separate one reviews | GitHub issues and pull requests |

## Spec Kit

GitHub's open-source toolkit “gives AI coding agents structured processes, reusable templates, and documented outcomes”. Its core process is spec-driven development: you write what to build and why, and your agent turns it into a plan, tasks and code, one reviewed step at a time. Pick it when a written spec should drive the build. ([repository](https://github.com/github/spec-kit), [quickstart](https://github.github.io/spec-kit/quickstart.html))

## BMAD Method

BMad Method sets out to “turn an idea or change request into working software without giving up the thinking”. It sizes the process to the change and brings in product, architecture, UX, development and testing perspectives when they help. Pick it when you want help deciding what to build, not only building it. ([repository](https://github.com/bmad-code-org/BMAD-METHOD), [docs](https://docs.bmad-method.org/start/build-your-first-change/))

## OpenSpec

OpenSpec is “Spec-driven development (SDD) for AI coding assistants”. Each change gets a proposal, specs, a design and a task list. It describes itself as “built for brownfield not just greenfield”. Pick it when you want a spec for each change, in new or existing code. ([repository](https://github.com/Fission-AI/OpenSpec), [docs](https://openspec.dev/))

## GSD

GSD is where CodeCrew began. It runs each phase through a loop of discuss, plan, execute, verify and ship, with the heavy work in fresh-context subagents to avoid what it calls context rot. CodeCrew started as [an essay written from inside a GSD project](../docs/gsd-vs-frontier-orchestration.md), which found GSD's value in “externalized state, independent verification, human gates on judgment calls, atomic commits”, and puts that core on GitHub. [The original GSD repository](https://github.com/gsd-build/get-shit-done) is archived, and says the project now continues as [GSD Core](https://github.com/open-gsd/gsd-core). Pick GSD when you want a complete phase loop inside your coding agent.

## CodeCrew

CodeCrew does not write specs for you. It gives each agent [its own GitHub identity](github-app-per-agent.md), lets [a different agent review the work](second-model-review.md), and [refuses to merge](gates-in-code.md) until the checks and the review are in. Pick it when you want separate agents to build and to check, on GitHub.

## Where they overlap

**Planning first, mostly.** [Spec Kit](https://github.com/github/spec-kit#spec-driven-development), [OpenSpec](https://github.com/Fission-AI/OpenSpec#see-it-in-action) and [GSD](https://github.com/open-gsd/gsd-core#how-it-works) plan before code. [BMAD](https://github.com/bmad-code-org/BMAD-METHOD#why-bmad) sizes it: clear changes can go straight to build. CodeCrew's `task start` refuses a task with no plan, however the agent arrived at it.

**More than one coding tool.** Each works with several coding tools: Spec Kit ([integrations](https://github.github.io/spec-kit/integrations/index.html)), BMAD ([install](https://github.com/bmad-code-org/BMAD-METHOD#start-building)), OpenSpec ([supported tools](https://openspec.dev/docs/supported-tools)), GSD Core ([installer](https://github.com/open-gsd/gsd-core#quickstart)), and CodeCrew, whose role instructions are plain files any harness can load. Supporting several tools is not the same as having a second agent check the first: in CodeCrew the review comes from a separate session, which can hold a GitHub identity of its own.

## Next step

Try CodeCrew on a project of your own: [Your first milestone](../docs/first-milestone.md).

!!! question "Tried it? Tell us how it went"

    What did you try, how far did you get, and what stopped you? [Tell us in “I tried it”](https://github.com/radiusred/gh-codecrew/discussions/categories/i-tried-it), on GitHub Discussions.

## More for newcomers

- [AI code review by a second model](second-model-review.md)
- [GitHub App for AI coding agents: one per agent](github-app-per-agent.md)
- [Enforce review gates for AI coding agents](gates-in-code.md)
