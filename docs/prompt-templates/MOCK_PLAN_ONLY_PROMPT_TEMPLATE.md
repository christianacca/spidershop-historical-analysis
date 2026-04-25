# Agent Prompt Template - Mock Plan Only

> How to use this file: copy the Prompt section below into a planning-mode chat,
> replace the placeholders, and ask the agent to build the executable plan in memory
> only. Then, in the same chat, switch to a writing-capable agent and ask it to write
> the approved plan to disk.

This is the default, lightweight workflow.
Use this when you do not need a separate discovery phase or a separate spec document.

Workflow role:
This is the normal starting point.
Think of the three templates as:

- `PLAN_ONLY` = default workflow
- `MOCK_TO_SPEC_PLAN` = escalation when you need a separate durable contract
- `MOCK_DISCOVERY` = pre-planning reconnaissance only when needed

## Quick Decision Matrix

| Question | If yes | If no |
|---|---|---|
| Do you need only execution guidance, not a separate durable contract? | Use this template | Consider the spec+plan template |
| Is the mock clear enough that the plan can be built directly from the mock and repo context? | Use this template | Run discovery first |
| Are you optimizing for the shortest same-chat workflow? | Use this template | Consider spec+plan if the feature needs stronger control points |

Default rule:
If you can safely answer "I only need a plan" then start here.

Definition:
A `durable spec document` means a separate written artifact that defines what the feature
is supposed to be, independent of the implementation plan.
It is meant to survive beyond the current chat and act as a future reference point for
review, iteration, or later implementation work.

Use a separate spec when you need a stable contract for things like:

- the intended layout and visual contract
- copy and state behavior
- DOM structure requirements where markup choice matters
- by-design deviations from the mock or design system

If you do not need that separate contract, and the plan itself can safely carry the work,
use this template.

---

## When To Use This

Use this template by default when:

- the feature is local or moderately sized
- you already understand the broad architecture
- you do not need a separate durable spec document that will act as an independent contract
- the mock is clear enough that a plan can be written directly from it
- you want to keep the workflow in one chat until the plan is written to disk

Escalate to the other templates only when needed:

- use [MOCK_DISCOVERY_PROMPT_TEMPLATE.md](MOCK_DISCOVERY_PROMPT_TEMPLATE.md)
  when the implementation shape is still unclear
- use [MOCK_TO_SPEC_PLAN_PROMPT_TEMPLATE.md](MOCK_TO_SPEC_PLAN_PROMPT_TEMPLATE.md)
  when the feature needs a durable spec as well as an executable plan;
  that workflow always uses planning-mode first, then same-chat write-to-disk

---

## Inputs To Fill In

Replace the placeholders below before using the prompt.

| Placeholder | Meaning |
|---|---|
| `[FEATURE_NAME]` | Short feature name |
| `[MOCK_PATH]` | Path to the mock, prototype, HTML, screenshot set, or design notes |
| `[PLAN_PATH]` | Where the executable plan should eventually be written |
| `[DISCOVERY_PATH]` | Optional path to a prior discovery memo if one exists |
| `[RELEVANT_CODE_PATHS]` | Existing folders/files the agent must inspect |
| `[SUPPORTING_DOC_PATHS]` | Existing requirements, UX docs, ADRs, CSS token files, architecture docs |
| `[IMPLEMENTATION_SCOPE]` | What this work package is allowed to deliver |
| `[OUT_OF_SCOPE]` | What must not be built in this package |
| `[STORYBOOK_MODE]` | Optional policy override: `forced-on`, `forced-off`, or `agent-decide`. Default: `agent-decide` |
| `[BROWSER_TOOLING]` | Browser tooling available, for example Chrome DevTools MCP |

---

## Prompt

You are preparing the executable implementation plan for `[FEATURE_NAME]`.

Your job in this prompt is to build the plan in memory only.

Do not write files to disk yet.
Do not implement product code.
Do not create a separate spec unless I explicitly ask for one.

### Scope

- Allowed scope: `[IMPLEMENTATION_SCOPE]`
- Out of scope: `[OUT_OF_SCOPE]`

### Source material

- Mock: `[MOCK_PATH]`
- Discovery memo (optional): `[DISCOVERY_PATH]`
- Relevant code paths: `[RELEVANT_CODE_PATHS]`
- Supporting docs: `[SUPPORTING_DOC_PATHS]`
- Storybook mode (optional policy override; default `agent-decide`): `[STORYBOOK_MODE]`
- Browser tooling available: `[BROWSER_TOOLING]`

### Operating rules

#### 1. Read before planning

Before drafting the plan, read the mock and the relevant code/docs in full.

You must understand:

- current architecture and likely file boundaries
- shared CSS token source and styling conventions
- any global selectors or layout rules that could collide with planned markup
- current test and preview workflow
- existing component or template patterns worth reusing

If the mock is inspectable HTML and browser tooling is available, inspect it in a browser.

Inspect the repo first and use the canonical commands you find in places like `Makefile`,
`package.json`, task configs, and existing docs. Do not ask the human to provide or
override those commands. If Storybook is used, use the repo-defined Storybook command.
Only ask follow-up questions if the repo is genuinely ambiguous.

#### 2. Build the plan directly from primary sources

The plan must be based on:

- the mock
- the discovery memo, if provided
- the repo files you inspected
- supporting docs

Do not rely on memory or generic patterns if the repo provides stronger guidance.
If a discovery memo is provided, use it as a secondary input and decision record.
It must accelerate planning, not replace re-reading the mock and the key repo files.

#### 3. Decide whether Storybook is useful

Handle Storybook this way:

- If `[STORYBOOK_MODE]` is `forced-on`, use it in the plan where useful.
- If `[STORYBOOK_MODE]` is `forced-off`, do not use it.
- If `[STORYBOOK_MODE]` is `agent-decide` or omitted, decide whether it is actually useful and explain why.

Storybook is optional, not mandatory.
If it is not used, the plan must include an alternative visual verification harness.

#### 4. Produce an executable plan, not a loose outline

Build a phase-based plan in memory that another agent can execute directly.

The plan must include:

- ordered phases
- exact files to create or modify where that can be predicted
- exact tests and validation commands per phase
- browser verification steps when visuals matter
- acceptance criteria that are observable, not vague
- a housekeeping protocol at the end of every phase

Use this housekeeping protocol:

```
[ ] H1 - Mark every task checkbox in the phase as complete only after it is actually done
[ ] H2 - Reflection scan against the code smell checklist; fix issues before continuing
[ ] H3 - Feed-forward log entry with dated notes, even if there are no new findings
[ ] H4 - Commit with a phase-specific message, then verify with `git log --oneline -1`
[ ] GATE - Output the phase completion block with real test / commit / story status
```

Include this GATE block in the plan:

```
╔══════════════════════════════════════════════════════════════╗
║  PHASE N COMPLETE                                            ║
╠══════════════════════════════════════════════════════════════╣
║  Tests:    [paste final line of required test command]
║  Commit:   [paste output of: git log --oneline -1]
║  Stories:  [StoryName -> evaluate_script passed] or [N/A]
║  Blockers: none / [deferred item]
╚══════════════════════════════════════════════════════════════╝
```

#### 5. Include the minimum anti-drift guard rails

Even without a separate spec document, the plan must still include:

1. a mock parity check before implementation begins
2. CSS token existence validation for any planned new tokens
3. global CSS collision audit for planned markup
4. real-page verification, not just isolated renders
5. computed-style checks for key visual elements
6. divergence logging as `fixed`, `by-design`, or `deferred`

#### 6. End state for this chat step

When the in-memory plan is complete, output:

1. the proposed phases
2. the Storybook decision and why
3. the top drift risks to watch
4. a short instruction block for the next same-chat step:
   "Switch to writing-capable agent mode and write this plan to `[PLAN_PATH]`"

Stop there.

Do not write the plan file to disk until I explicitly ask for the next step.
