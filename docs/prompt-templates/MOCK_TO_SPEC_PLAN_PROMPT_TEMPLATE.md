# Agent Prompt Template - Mock to Spec to Executable Plan

> How to use this file: copy the Prompt section below into agent chat, replace the
> placeholders, and ask the agent to produce the spec and plan artifacts only.
> This template is for features that start from a mock and need a high-fidelity
> handoff before implementation begins.

This is not the default path for every feature.
If you only need an executable plan and do not need a separate spec, use
[MOCK_PLAN_ONLY_PROMPT_TEMPLATE.md](MOCK_PLAN_ONLY_PROMPT_TEMPLATE.md) instead.

Workflow role:
This is the escalation path when plan-only is no longer enough.
Think of the three templates as:

- `PLAN_ONLY` = default workflow
- `MOCK_TO_SPEC_PLAN` = escalation when you need a separate durable contract
- `MOCK_DISCOVERY` = pre-planning reconnaissance only when needed

## Quick Decision Matrix

| Question | If yes | If no |
|---|---|---|
| Do you need a separate durable contract for what the feature is, not just how to implement it? | Use this template | Use the plan-only template |
| Is the feature important, nuanced, or likely to benefit from a review checkpoint before implementation? | Use this template | Plan-only may be enough |
| Is the implementation shape still unclear even before spec writing? | Run discovery first, then use this template | Use this template directly |

Default rule:
Use this template when the feature needs contract-first rigor, not just execution guidance.

Definition:
A `durable contract` or `durable spec document` means a separate written artifact that defines
what the feature is supposed to be, independent of the implementation plan.
It should be good enough to act as a stable reference point for later review, iteration,
or implementation by a different agent or in a later session.

Use this workflow when you want that separate contract to capture things like:

- the intended layout and visual contract
- copy and state behavior
- DOM structure requirements where markup choice matters
- by-design deviations from the mock or design system

If you only need execution guidance and do not need that separate contract, use the
plan-only template instead.

Recommended sequence:

1. If the implementation shape is still unclear, run [MOCK_DISCOVERY_PROMPT_TEMPLATE.md](MOCK_DISCOVERY_PROMPT_TEMPLATE.md) first.
2. Then use this template to produce the durable spec and executable plan.

This template always uses `plan-then-write`.
First use a planning-mode agent to build the spec and plan in memory.
Then, in the same chat, switch to a writing-capable agent and ask it to write the approved artifacts to disk.

Fresh chat is optional here, not mandatory.
If you keep the same chat, explicitly instruct the agent to re-anchor on the mock, the referenced repo files, and any saved discovery artifact before writing.

---

## Inputs To Fill In

Replace the placeholders below before using the prompt.

| Placeholder | Meaning |
|---|---|
| `[FEATURE_NAME]` | Short feature name |
| `[WORK_PACKAGE_NAME]` | Optional work package / slice name |
| `[MOCK_PATH]` | Path to the source mock, prototype, HTML, screenshot set, or design file notes |
| `[SPEC_PATH]` | Where the functional spec should be written |
| `[PLAN_PATH]` | Where the executable implementation plan should be written |
| `[DISCOVERY_PATH]` | Optional path to a prior discovery memo if one exists |
| `[RELEVANT_CODE_PATHS]` | Existing folders/files the agent must inspect before writing the spec/plan |
| `[SUPPORTING_DOC_PATHS]` | Existing requirements, UX notes, ADRs, CSS tokens, component docs |
| `[IMPLEMENTATION_SCOPE]` | What this work package is allowed to deliver |
| `[OUT_OF_SCOPE]` | What must not be built in this package |
| `[STORYBOOK_MODE]` | Optional policy override: `forced-on`, `forced-off`, or `agent-decide`. Default: `agent-decide` |
| `[BROWSER_TOOLING]` | Browser tooling available, for example Chrome DevTools MCP |

---

## General Guard Rail Rules

These are the recurring rules that should apply to any future feature that starts life as a mock.

1. The mock is the primary source of truth for visual intent. The spec is derived from it, not the other way around.
2. Before writing the spec, extract a mock-conformance inventory: layout, copy, states, hierarchy, spacing signals, visual treatments, and any obvious responsive behavior.
3. If browser tooling is available, inspect the mock with computed-style checks before writing the spec. Do not rely on memory or screenshots alone when the mock is inspectable HTML.
4. The spec must capture measured or explicit visual requirements for key elements. Do not leave critical layout or styling implied by screenshots.
5. Every visual requirement in the plan must trace back to either the mock or a documented by-design deviation.
6. Storybook is useful for isolated components, but it is never sufficient to sign off page-level integration or global CSS interactions.
7. If Storybook is used, the plan must still include live preview verification in the real integrated page context.
8. If Storybook is not used, the plan must specify an alternative verification harness, such as a fixture page, preview site, Playwright page, or dedicated local HTML harness.
9. Every visual verification phase must check computed CSS properties, not just element counts, text content, or DOM presence.
10. Any CSS token referenced in component code must already exist in the shared token source or be explicitly added as part of the plan.
11. Before implementation, audit global element selectors in shared CSS (`header`, `section`, `h2`, etc.) for possible collisions with planned markup.
12. The plan must separate two concerns:
    spec fidelity: does the written spec match the mock?
    implementation correctness: does the code match the spec?
13. Any divergence discovered later must be classified as one of:
    `fixed`, `by-design`, or `deferred`.
    No divergence may remain unclassified.
14. Visual sign-off requires side-by-side comparison of mock vs integrated output, plus computed-style checks on key elements.
15. The agent must not implement feature code while writing the spec and plan unless the human explicitly asks for implementation in the same request.

---

## Prompt

You are preparing the implementation handoff for `[FEATURE_NAME]`.

This work package is `[WORK_PACKAGE_NAME]`.

Your job in this prompt is to create two artifacts only:

1. A functional / UX handoff spec at `[SPEC_PATH]`
2. An executable implementation plan at `[PLAN_PATH]`

Do not implement product code in this prompt unless I explicitly ask for implementation.

### Scope

- Allowed scope: `[IMPLEMENTATION_SCOPE]`
- Out of scope: `[OUT_OF_SCOPE]`

### Source material

- Mock: `[MOCK_PATH]`
- Discovery memo (optional): `[DISCOVERY_PATH]`
- Relevant code paths to inspect first: `[RELEVANT_CODE_PATHS]`
- Supporting docs to inspect first: `[SUPPORTING_DOC_PATHS]`
- Storybook mode (optional policy override; default `agent-decide`): `[STORYBOOK_MODE]`
- Browser tooling available: `[BROWSER_TOOLING]`

### Operating rules

Follow these rules exactly.

#### 0. Use plan-then-write

This workflow always uses planning-mode first:

- first build the spec and plan in memory only
- do not write files to disk in the first step
- output a compact continuity block that the next same-chat step can use
- wait for the explicit follow-up instruction to write `[SPEC_PATH]` and `[PLAN_PATH]`

Before finalizing either artifact, re-ground on primary sources.

#### 1. Read before writing

Before drafting either artifact, read the mock and the relevant code/docs in full.
You must understand:

- current architecture and page structure
- shared CSS token source
- any global element selectors that could affect planned markup
- current test commands and preview workflow
- existing component or template patterns worth reusing

If the mock is inspectable HTML and browser tooling is available, inspect it in a browser.
Do not write the spec from memory.
If a discovery memo is provided, read it too, but treat it as a secondary input.
It is a decision record and accelerator, not a substitute for re-reading the mock and the key repo files.
Inspect the repo first and use the canonical commands you find in places like `Makefile`,
`package.json`, task configs, and existing docs. Do not ask the human to provide or
override those commands. If Storybook is used, use the repo-defined Storybook command.
Only ask follow-up questions if the repo is genuinely ambiguous.

#### 2. Create a mock-conformance inventory first

Before writing the spec, produce an internal inventory of the mock covering:

- section hierarchy and page placement
- key copy strings and dynamic copy states
- layout model for each major block
- card / panel treatments
- badge, pill, and emphasis treatments
- spacing and density patterns
- visual state variants
- interaction affordances
- responsive clues visible in the mock

For inspectable mocks, use computed-style checks for key elements. Capture at least:

- `display`
- `flex-direction` or `grid-template-columns`
- `background-color`
- `color`
- `border`
- `border-radius`
- `padding`
- `font-size`

Do not skip this step.

#### 3. Decide the verification harness

Handle Storybook this way:

- If `[STORYBOOK_MODE]` is `forced-on`, design the plan to use Storybook where useful.
- If `[STORYBOOK_MODE]` is `forced-off`, do not use Storybook.
- If `[STORYBOOK_MODE]` is `agent-decide` or omitted, decide whether Storybook is useful and document the decision in both the spec and the plan.

Use Storybook when most of the following are true:

- the work introduces reusable UI components
- those components have multiple visual states or prop-driven variants
- isolated rendering would materially speed visual verification
- the repo already has Storybook or the setup cost is justified

Do not default to Storybook when most of the work is:

- server-rendered template integration
- page-level layout and global CSS interaction
- one-off markup with little component reuse
- heavily dependent on full-page context

If Storybook is not used, the plan must specify an alternative verification harness.

#### 4. Write the spec as the mock-derived truth document

Write `[SPEC_PATH]` so it is strong enough that a later agent can implement from it without guessing.

The spec must include:

1. Purpose and scope
2. Explicit out-of-scope list
3. Section or feature layout description
4. Heading / copy / empty-state / state-specific copy contracts
5. Component or block inventory
6. DOM structure requirements where markup choice matters
7. Visual contract for key elements
8. Interaction and state rules
9. Data contract or payload expectations if relevant
10. Accessibility requirements if relevant
11. Responsive behavior expectations if visible or inferable
12. By-design deviations table
13. Open questions resolved conservatively, or explicitly documented if truly unresolved

For visual contract sections, do not use vague wording like "looks like the mock".
Capture specifics for the key elements that drive the look:

- layout model
- text treatment
- badge / pill treatments
- card wrapper treatments
- border radius tier
- token usage expectations
- any allowed hardcoded exceptions and why

If the mock and the existing design system conflict, state exactly how the implementation
should reconcile them.

#### 5. Write the implementation plan as an executable checklist

Write `[PLAN_PATH]` as a phase-based plan that another agent can execute directly.

The plan must:

- be ordered phase-by-phase
- define exact files to create or modify where that can be predicted
- define exact tests or validation commands per phase
- define exact browser verification checks per phase when visuals matter
- include acceptance criteria that are observable, not vague
- include a feed-forward log section at the end

The plan must include the housekeeping protocol below at the end of every phase:

```
[ ] H1 - Mark every task checkbox in the phase as complete only after it is actually done
[ ] H2 - Reflection scan against the code smell checklist; fix issues before continuing
[ ] H3 - Feed-forward log entry with dated notes, even if there are no new findings
[ ] H4 - Commit with a phase-specific message, then verify with `git log --oneline -1`
[ ] GATE - Output the phase completion block with real test / commit / story status
```

Include this GATE block template in the plan:

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

#### 6. Add the extra guard rails that prevent mock drift

The plan must include explicit tasks for all of the following where relevant:

1. A pre-implementation mock parity audit
   Outcome: a recorded list of expected styles / layout properties for key elements.

2. CSS token existence validation
   Outcome: every `var(--token)` planned for new code is verified against the shared token source.

3. Global CSS collision audit
   Outcome: planned markup avoids or documents risks from shared selectors such as `header`, `section`, `h2`, `button`, etc.

4. Real-page verification
   Outcome: the integrated preview page is checked, not just isolated component renders.

5. Computed-style checks
   Outcome: critical visual assertions use computed values such as `backgroundColor`, `fontSize`, `borderRadius`, `flexDirection`, and `display`.

6. Divergence log
   Outcome: every mismatch found later is recorded as `fixed`, `by-design`, or `deferred`.

7. Spec-vs-mock review gate
   Outcome: before any implementation phase begins, the plan requires a review that the written spec still matches the mock.

8. Final visual acceptance pass
   Outcome: side-by-side comparison of mock vs integrated output, plus computed-style checks on the live page.

#### 7. Use repo-approved commands only

Do not invent ad hoc test or preview commands if the repo already has approved commands.
Prefer the project's task runner. In this repo that is usually `make`.

If the right command is unclear, inspect the repo and write the plan using the canonical commands you find.

#### 8. End state for this chat step

After building the spec and plan in memory:

- summarize the proposed spec structure
- summarize the proposed phase structure
- summarize the Storybook decision and why
- list any by-design deviations already identified
- output a short instruction block for the next same-chat step:
   `Switch to writing-capable agent mode and write the approved artifacts to [SPEC_PATH] and [PLAN_PATH]`
- stop

Do not write files to disk until explicitly asked.

#### 9. Default behavior after writing the files

After writing `[SPEC_PATH]` and `[PLAN_PATH]`:

- summarize the main guard rails you added
- summarize the Storybook decision and why
- list any by-design deviations already identified
- stop

Do not start implementing feature code unless I explicitly ask you to continue.

### Required output quality bar

Your spec and plan must be good enough that a future agent can execute the work with minimal ambiguity.
If you find that the mock is underspecified, resolve it by:

1. inspecting the mock more carefully
2. inspecting the surrounding codebase constraints
3. making the most conservative reasonable decision
4. documenting that decision explicitly in the spec and plan

Do not leave high-impact visual behavior implicit.

### Deliverables

Write the two files:

- `[SPEC_PATH]`
- `[PLAN_PATH]`

Then report:

1. where the files were written
2. whether Storybook was chosen, rejected, or left out by explicit instruction
3. the top 5 guard rails added to prevent mock-to-spec drift
