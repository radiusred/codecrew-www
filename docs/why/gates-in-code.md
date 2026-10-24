---
title: Enforce review gates for AI coding agents
description: Enforce review gates for AI coding agents in code, not in the prompt. CodeCrew's command line refuses to merge a task or close a milestone until the checks, the review and every human answer are in place.
---

# Enforce review gates for AI coding agents

You can tell an agent not to merge until the tests pass and someone has reviewed the work, and usually it will listen. To enforce review gates for AI coding agents, CodeCrew moves the rule out of the prompt and into a program: the command that merges checks first, and refuses if anything is missing. An agent cannot talk its way past a check that runs in code.

## What gets checked

`gh codecrew task finish` merges a task's pull request only when:

- its CI checks have run, and every one is green;
- it has the approval your setup requires: the reviewer's, or, if you hold the reviewer's job yourself, an approval from someone other than the author, or your own recorded confirmation;
- every question raised for a human has an answer on record;
- it is run by whoever started the task.

`gh codecrew milestone close` closes a milestone only when every task under it is closed, every requirement's latest QA verdict is `satisfied`, and the milestone's write-up is on the default branch.

Earlier still, `gh codecrew task start` refuses a task with no plan.

## What a refusal looks like

This is real output, from the run that checked whether milestone 15 could close ([quoted in its record](https://github.com/radiusred/gh-codecrew/blob/149bd78a32d7180b9a06705c796bb0772b9ccd74/docs/milestones/15-v2-0-1-what-the-fleet-migration-taught.md#L89-L97)). `--dry-run` shows every check in order and changes nothing, and one task was still open:

```
gate milestone open: ok
gate no gate raised: ok
gate tasks closed: refused[OPEN_TASKS]: tasks not closed: radiusred/gh-codecrew#321 (ready)
gate requirements declared: not reached
gate QA verdicts: not reached
gate milestone document: not reached
dry run: nothing written — the live verb stops at the first refusal above
```

Every refusal has that shape: `refused[CODE]: detail`. The code is a fixed name your agent can act on, and the detail says what is missing in plain words.

## Where it stops

The checks hold for work that goes through CodeCrew's commands. They do not take GitHub's merge button away from anyone with write access; GitHub's own branch rules do that, with [one caveat about plans](github-app-per-agent.md#one-caveat-about-required-reviews).

## Next step

Take a first task through the checks: [Your first milestone](../docs/first-milestone.md). Every refusal, and what it means, is in [the specification's refusal table](../docs/spec.md#10-the-cli).

!!! question "Tried it? Tell us how it went"

    What did you try, how far did you get, and what stopped you? [Tell us in “I tried it”](https://github.com/radiusred/gh-codecrew/discussions/categories/i-tried-it), on GitHub Discussions.

## More for newcomers

- [AI code review by a second model](second-model-review.md)
- [GitHub App for AI coding agents: one per agent](github-app-per-agent.md)
- [CodeCrew compared with Spec Kit, BMAD, OpenSpec and GSD](compared.md)
