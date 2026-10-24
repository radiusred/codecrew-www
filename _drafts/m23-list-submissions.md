# M23-R6: list submissions and roundup notes, drafted

Working notes for [radiusred/gh-codecrew#423](https://github.com/radiusred/gh-codecrew/issues/423), M23-R6, drafted on [radiusred/codecrew-www#79](https://github.com/radiusred/codecrew-www/issues/79). This file is not a blog post. It has no front matter on purpose, so `main.py` never publishes it, and `tests/test_main.py` keeps it that way.

The operator makes every submission and sends both notes (the milestone's Gates). R6 asks for each submission to be linked on #423 with its outcome.

Every claim below can be checked at [codecrew.works](https://codecrew.works/) or in the hub's [README](https://github.com/radiusred/gh-codecrew#readme). Figures were read on 2026-10-24: the hub had 7 stars, was created on 2026-08-20, had its last commit on `main` that day, and is Apache-2.0.

## 1. hesreallyhim/awesome-claude-code

**How to submit.** Use the web form only: [Recommend a Resource](https://github.com/hesreallyhim/awesome-claude-code/issues/new?template=recommend-resource.yml). Its [CONTRIBUTING.md](https://github.com/hesreallyhim/awesome-claude-code/blob/main/CONTRIBUTING.md) says a recommendation must be made by a person through the form, never as a PR and never with the `gh` CLI, and only one resource at a time.

**Eligibility.** The rule is "at least 14 days old (14 days since first commit on default branch) AND show signs of active development", or at least 100 stars. CodeCrew meets the first: its first commit was on 2026-08-20, and it is still committed to.

**The form, field by field.**

- **Display Name:** CodeCrew
- **Category:** Agent Orchestration > SDLC
- **Link:** https://github.com/radiusred/gh-codecrew
- **Author Name:** Radius Red (or the operator's own name, if preferred)
- **Author Link:** https://github.com/radiusred
- **Description** (the form asks for 1 to 3 sentences of 10 to 500 characters, "Descriptive, not promotional. Don't address the reader."; this draft is one line of 384 characters, backticks included):

  > A `gh` extension and protocol under which Claude Code, Codex or other coding agents work a GitHub project in separate roles, each able to act through its own GitHub App. One agent implements a task and a separate session reviews it, and `task finish` refuses to merge until CI is green and the required review is in. Plans, decisions and QA verdicts are kept as issue and PR comments.

**Why SDLC.** The SDLC subsection lists workflows that carry a change from plan to review: Charrette's plans, slices and layered pull request reviews, or OctoShell's reviewer agent. CodeCrew covers the same arc, from a task's plan through review, QA and a milestone write-up. The top level of Agent Orchestration fits less well, because its entries mostly start and manage agent sessions (Claude Squad, Agent 007, OpenRig), and CodeCrew starts no agents: you do, or an orchestrator does.

**The checklist.** The form has five required boxes. The operator ticks each one only when it is true:

1. "I have visited this repo before with my own eyes, and I have confirmed that this resource is sufficiently distinct from any existing resource"
2. "All links are working and publicly accessible"
3. "This resource is specific to Claude Code". **This one needs the operator's judgement.** CodeCrew works with Claude Code but is not specific to it: its role instructions are plain files any harness can load, and the [comparison page](https://codecrew.works/why/compared/) says so. CONTRIBUTING.md calls a Claude Code focus "not a hard requirement but it is a guideline", while the form makes the box required. If the box cannot honestly be ticked, CodeCrew is better left off this list.
4. "I have read the CONTRIBUTING.md"
5. "I promise I actually did these things and not doing so is shameful and lazy"

The sixth box says "Do not check the following box". Leave it unchecked.

## 2. bradagi/awesome-cli-coding-agents

**How to submit.** A pull request to its [README](https://github.com/bradAGI/awesome-cli-coding-agents#contributing) ("PRs welcome!").

**Its rules.** An entry "Must have a **CLI or terminal interface**", "Must be able to **read/write code or run commands** autonomously", and must link "a **valid, active** project". The format is name and link, star count, and a "**1–2 line description** — what it does, who it's for", with the license optional. Entries are "sorted by GitHub stars within each section". CodeCrew is a CLI that agents run, and it runs commands itself: it merges pull requests and posts the record. It does not write code, which is why it belongs with the harnesses rather than the agents.

**Section.** Harnesses & orchestration > **Agent infrastructure** ("Sandboxes, routers, browser/terminal automation, and extension tools"). Its neighbours there are the closest match: Beads (an issue tracker for coding agents), Squelette and SAKO (gates on agents' work), and GitHub Agentic Workflows (another `gh` extension). The Orchestrators & autonomous loops section was considered and passed over, because CodeCrew starts no agents.

**Position.** By stars, as the README read on 2026-10-24 (its "Last updated" line says 2026-10-19): after Terminai (`⭐ 7`) and before SpecWave (`⭐ 6`). Recheck the hub's star count, and the line's position, on the day.

**The entry line:**

```markdown
- **[CodeCrew](https://github.com/radiusred/gh-codecrew)** `⭐ 7` — `gh` extension and protocol for coding agents (Claude Code, Codex or others) working a GitHub project in separate roles, each able to act through its own GitHub App. One agent implements, a separate session reviews, and `task finish` refuses to merge until CI is green and the required review is in; plans, decisions and QA verdicts live as issue and PR comments. Go, Apache-2.0.
```

## 3. Notes to roundup authors

Both notes link the [comparison page](https://codecrew.works/why/compared/). Each channel below is one the author's own page gives. Sign either note as the operator.

### Vishal Mysore: "Spec-Driven Development Is Eating Software Engineering: A Map of 30+ Agentic Coding Frameworks (2026)"

[The article](https://medium.com/@visrow/spec-driven-development-is-eating-software-engineering-a-map-of-30-agentic-coding-frameworks-6ac0b5e2b484) was published on Medium on 2026-03-09. It sorts tools into four layers, and its "Planning & Task Systems" layer (Taskmaster, Agent OS, Beads, Feature-Driven-Flow) is where CodeCrew would sit.

**Channel:** a response on the article, on Medium. The article page also links a Mastodon account, `@visrow@me.dm`.

> Hi Vishal,
>
> Your map of spec-driven development frameworks is a useful way to sort a crowded field. I help run CodeCrew, an open-source `gh` extension for coding agents that work on GitHub in separate roles. It might fit your Planning & Task Systems layer. Each task is a GitHub issue with its plan in the body. One agent builds the change, and a separate session reviews it before the CLI will merge it. The decisions are recorded as comments along the way. It does not write specs, so it sits beside Spec Kit and OpenSpec rather than replacing them. We wrote a plain comparison with Spec Kit, BMAD, OpenSpec and GSD here: https://codecrew.works/why/compared/
>
> Thanks for the map,
> [the operator's name], Radius Red

### Daniel Vaughan: "Spec-Driven Development Frameworks for Codex CLI"

[The article](https://codex.danielvaughan.com/2026/05/22/spec-driven-development-frameworks-codex-cli-spec-kit-kiro-openspec-patterns-best-practices/) was published on 2026-05-22. Its full title is "Spec-Driven Development Frameworks for Codex CLI: Patterns, Best Practices, and the 2026 Landscape". It covers Spec Kit, Kiro, Tessl, OpenSpec, BMAD-METHOD, cc-sdd and Codex-Spec.

**Channel:** LinkedIn, https://www.linkedin.com/in/danielpvaughan. The article page names no channel, but it links his main site, [danielvaughan.com](https://danielvaughan.com/), which says: "The best way to reach me professionally is LinkedIn."

> Hi Daniel,
>
> Thank you for your map of spec-driven development frameworks for Codex CLI. I help run CodeCrew, an open-source `gh` extension for coding agents that work on GitHub in separate roles. It is not a spec framework, but it may fit next to one. One setup it supports has Claude Code build a change and Codex review it in a fresh session, under its own GitHub App identity. The CLI will not merge until CI is green and that review is in. Its role instructions are plain files that Codex loads like any other harness. We wrote a plain comparison with Spec Kit, BMAD, OpenSpec and GSD here: https://codecrew.works/why/compared/
>
> All the best,
> [the operator's name], Radius Red
