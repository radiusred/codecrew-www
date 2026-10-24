---
title: CodeCrew compared with Spec Kit, BMAD, OpenSpec and GSD
description: Spec Kit, BMAD, OpenSpec and GSD help an AI coding agent plan before it builds. CodeCrew gives each agent its own GitHub identity and checks review in code. What each is for, and when to pick which.
---

# CodeCrew compared with Spec Kit, BMAD, OpenSpec and GSD

If you have been reading about Spec Kit, BMAD, OpenSpec and GSD, you have met tools that help an AI coding agent plan before it builds. CodeCrew works on a neighbouring problem: which agent does the work, which one checks it, and where the record lives. Here is what each is for, in its own words where possible, and when you would pick it.

## At a glance

| Tool | Good for | Where the plan lives |
|---|---|---|
| Spec Kit | Turning a written spec into a plan, tasks and code | Files such as `spec.md`, `plan.md` and `tasks.md` |
| BMAD Method | Planning sized to the work, from several angles | Briefs, specs and architecture docs |
| OpenSpec | A light spec for each change, in code you already have | An `openspec/` folder of specs and changes |
| GSD | A phase loop run by fresh-context subagents | Files such as `STATE.md` and `CONTEXT.md` |
| CodeCrew | One agent builds, another reviews, each under its own GitHub identity | GitHub issues and pull requests |

## Spec Kit

GitHub's open-source toolkit “gives AI coding agents structured processes, reusable templates, and documented outcomes”. Its main process is spec-driven development: you write what to build and why, then your agent turns it into a plan, tasks and code, one step at a time. Pick it when a written spec should drive the build. ([repository](https://github.com/github/spec-kit), [quickstart](https://github.github.io/spec-kit/quickstart.html))

## BMAD Method

BMad Method sets out to “turn an idea or change request into working software without giving up the thinking”. It sizes the process to the change, from going straight to build for small ones to deeper planning for big ones, and brings in product, architecture, UX, development and testing perspectives. Pick it when you want help deciding what to build, not only building it. ([repository](https://github.com/bmad-code-org/BMAD-METHOD), [docs](https://docs.bmad-method.org/start/build-your-first-change/))

## OpenSpec

OpenSpec is “Spec-driven development (SDD) for AI coding assistants”. Each change gets a proposal, specs, a design and a task list, and you review the plan before any code is written. It describes itself as “built for brownfield not just greenfield”. Pick it when you want a light spec habit in an existing codebase. ([repository](https://github.com/Fission-AI/OpenSpec), [docs](https://openspec.dev/))

## GSD

GSD is where CodeCrew began. It runs each phase through a loop of discuss, plan, execute, verify and ship, and does the heavy work in fresh-context subagents to avoid what it calls context rot. CodeCrew started as [an essay written from inside a GSD project](../docs/gsd-vs-frontier-orchestration.md), which found GSD's value in “externalized state, independent verification, human gates on judgment calls, atomic commits”. CodeCrew keeps that core and puts it on GitHub. The original GSD repository is archived and points to its successor, [GSD Core](https://github.com/open-gsd/gsd-core). Pick GSD when you want a complete phase loop inside your coding agent.

## CodeCrew

CodeCrew does not write specs or plan for you. It gives each agent [its own GitHub identity](github-app-per-agent.md), has [a different agent review the work](second-model-review.md) in a fresh session, and its command line [refuses to merge](gates-in-code.md) until the checks, the review and every human answer are in. Pick it when you want separate agents to build and to check, with the record on GitHub.

## Where they overlap

All five want a plan before code, and all five work with more than one coding agent. CodeCrew asks only that the plan is written on the task's GitHub issue before work starts, not how the agent arrives at it.

## Next step

Try CodeCrew on a project of your own: [Your first milestone](../docs/first-milestone.md).

!!! question "Tried it? Tell us how it went"

    What did you try, how far did you get, and what stopped you? [Tell us in “I tried it”](https://github.com/radiusred/gh-codecrew/discussions/categories/i-tried-it), on GitHub Discussions.

## More for newcomers

- [AI code review by a second model](second-model-review.md)
- [GitHub App for AI coding agents: one per agent](github-app-per-agent.md)
- [Enforce review gates for AI coding agents](gates-in-code.md)
