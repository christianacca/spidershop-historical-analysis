# Agent Prompt Template - Mock Discovery Phase

> How to use this file: copy the Prompt section below into a planning-mode chat,
> replace the placeholders, and ask the agent to do discovery in memory only.
> Then, in the same chat, switch to a writing-capable agent and ask it to write
> the approved discovery memo to disk. This prompt is for the stage after a mock
> is approved but before a spec and executable plan are written.

This is an escalation path, not the default path.
If you already understand the implementation shape and only need an executable plan,
use [MOCK_PLAN_ONLY_PROMPT_TEMPLATE.md](MOCK_PLAN_ONLY_PROMPT_TEMPLATE.md) instead.

Workflow role:
This is a reconnaissance step you use before planning only when needed.
Think of the three templates as:

- `PLAN_ONLY` = default workflow
- `MOCK_TO_SPEC_PLAN` = escalation when you need a separate durable contract
- `MOCK_DISCOVERY` = pre-planning reconnaissance only when needed

You may use this before either of the other two templates when you are not yet sure
which workflow should follow.

This template uses the same `plan-then-write` pattern as the other workflows:
first do the analysis in planning mode, then optionally write the discovery memo to disk
in the same chat using a writing-capable agent.

---

## When To Use This

Use this prompt when the mock is visually settled but the implementation shape is still unclear.

Typical triggers:

- you do not yet know where the code should live
- the mock may touch multiple layers or systems
- you want the agent to identify reuse opportunities before writing the spec
- you are unsure whether Storybook is worth using
- you are unsure whether the next step should be `PLAN_ONLY` or `MOCK_TO_SPEC_PLAN`
- you want the agent to present viable implementation approaches before you authorize planning
- you want a durable discovery memo that can feed the later spec-and-plan step

If the feature is small and the repo context is already obvious, you can skip this prompt and go straight to:

- [MOCK_PLAN_ONLY_PROMPT_TEMPLATE.md](MOCK_PLAN_ONLY_PROMPT_TEMPLATE.md) if you only need an executable plan
- [MOCK_TO_SPEC_PLAN_PROMPT_TEMPLATE.md](MOCK_TO_SPEC_PLAN_PROMPT_TEMPLATE.md) if you already know you need a durable spec as well as a plan

---

## Inputs To Fill In

Replace the placeholders below before using the prompt.

| Placeholder | Meaning |
|---|---|
| `[FEATURE_NAME]` | Short feature name |
| `[WORK_PACKAGE_NAME]` | Optional work package / slice name |
| `[MOCK_PATH]` | Path to the source mock, prototype, HTML, screenshot set, or design notes |
| `[DISCOVERY_PATH]` | Where the discovery memo should be written |
| `[RELEVANT_CODE_PATHS]` | Existing folders/files the agent must inspect |
| `[SUPPORTING_DOC_PATHS]` | Existing requirements, UX docs, ADRs, CSS token files, architecture docs |
| `[IMPLEMENTATION_SCOPE]` | Intended scope for this work package |
| `[OUT_OF_SCOPE]` | What is explicitly not part of this work package |
| `[STORYBOOK_MODE]` | Optional policy override: `forced-on`, `forced-off`, or `agent-decide`. Default: `agent-decide` |
| `[BROWSER_TOOLING]` | Browser tooling available, for example Chrome DevTools MCP |
| `[KNOWN_CONSTRAINTS]` | Any extra human-provided constraints |

---

## Prompt

You are doing the discovery phase for `[FEATURE_NAME]`.

This work package is `[WORK_PACKAGE_NAME]`.

Your job in this prompt is to create one artifact only:

1. A discovery memo at `[DISCOVERY_PATH]`

Do not write the spec.
Do not write the executable plan.
Do not implement product code.
Do not write files to disk in the first step.

### Scope

- Intended scope: `[IMPLEMENTATION_SCOPE]`
- Out of scope: `[OUT_OF_SCOPE]`
- Known constraints: `[KNOWN_CONSTRAINTS]`

### Source material

- Mock: `[MOCK_PATH]`
- Relevant code paths: `[RELEVANT_CODE_PATHS]`
- Supporting docs: `[SUPPORTING_DOC_PATHS]`
- Storybook mode (optional policy override; default `agent-decide`): `[STORYBOOK_MODE]`
- Browser tooling available: `[BROWSER_TOOLING]`

### Operating rules

#### 0. Use plan-then-write

This workflow always uses planning-mode first:

- first build the discovery memo in memory only
- do not write files to disk in the first step
- output a compact continuity block that the next same-chat step can use
- wait for the explicit follow-up instruction to write `[DISCOVERY_PATH]`

Before finalizing the discovery memo, re-ground on primary sources.

#### 1. Read before concluding

Before writing the discovery memo, read the mock and the relevant code/docs in full.

You must understand:

- current architecture and feature boundaries
- existing component and template patterns
- shared CSS token source and styling conventions
- global selectors or layout rules that could collide with planned markup
- test and preview workflow
- data dependencies, payload shapes, and server/client boundaries where relevant

If the mock is inspectable HTML and browser tooling is available, inspect it in a browser.
Do not rely on screenshots alone if computed styles can be read directly.
Inspect the repo first and use the canonical commands you find in places like `Makefile`,
`package.json`, task configs, and existing docs. Do not ask the human to provide or
override those commands. If Storybook is used, use the repo-defined Storybook command.
Only ask follow-up questions if the repo is genuinely ambiguous.

#### 2. Inspect the mock as a real artifact

Build an internal inventory of the mock covering:

- major sections or blocks
- visible states and variants
- copy and hierarchy
- layout model per block
- card, panel, badge, pill, and emphasis treatments
- interactions visible in the mock
- responsive clues

For inspectable mocks, capture computed values for the key elements, including:

- `display`
- `flex-direction` or `grid-template-columns`
- `background-color`
- `color`
- `border`
- `border-radius`
- `padding`
- `font-size`

#### 3. Decide whether Storybook is worth using later

Handle Storybook this way:

- If `[STORYBOOK_MODE]` is `forced-on`, recommend a Storybook-based verification approach.
- If `[STORYBOOK_MODE]` is `forced-off`, recommend a non-Storybook verification approach.
- If `[STORYBOOK_MODE]` is `agent-decide` or omitted, decide whether Storybook is worth using later and explain why.

Remember: Storybook is good for isolated component states, but insufficient for page-level CSS and global integration issues.

#### 4. Write the discovery memo as a planning input, not a vague summary

Write `[DISCOVERY_PATH]` with these sections:

1. Purpose and scope summary
2. Existing architecture and feature boundaries
3. Candidate implementation approaches
4. Recommended approach and why
5. Reuse opportunities
6. Likely files / modules / templates / components to touch later
7. CSS token and global selector constraints
8. Data / API / DTO / backend implications if relevant
9. Verification harness recommendation
10. Storybook recommendation with rationale
11. Risks and likely drift points
12. Open questions resolved conservatively, or explicitly listed if truly unresolved
13. Recommended work-package boundaries if the feature should be split
14. Recommended next workflow
15. Handoff inputs for the next stage

For `Candidate implementation approaches`:

- present up to 3 viable approaches, not more
- include the main tradeoff for each
- if there is only one credible approach, state that directly rather than inventing weak alternatives

For `Recommended next workflow`:

- choose one of: `PLAN_ONLY`, `MOCK_TO_SPEC_PLAN`, or `stop for human decision`
- explain why that is the correct next step

The final section, `Handoff inputs for the next stage`, must include:

- which downstream workflow the user should run next
- recommended spec path
- recommended plan path
- the must-capture visual requirements that the later spec must spell out explicitly
- the must-check integration risks that the later plan must include

The discovery memo is an input to the next stage, but not the only input.
The later plan-only or spec+plan prompt must still re-read the mock and the key repo files.
Use the discovery memo as an accelerator and decision record, not as a substitute for primary sources.

#### 5. Required quality bar

The memo must be strong enough that a later spec-and-plan agent can use it as a durable input.

Do not stop at observations like "looks like a card grid".
Tie observations to the existing repo and likely implementation consequences.

#### 6. End state for this chat step

After building the discovery memo in memory:

- summarize the proposed discovery memo structure
- summarize the candidate approaches and the recommended one
- summarize the top implementation risks
- summarize the recommended next workflow and why
- summarize the Storybook recommendation and why
- output a short instruction block for the next same-chat step:
	`Switch to writing-capable agent mode and write the approved discovery memo to [DISCOVERY_PATH]`
- stop

Do not write files to disk until explicitly asked.

#### 7. Default behavior after writing the file

After writing `[DISCOVERY_PATH]`:

- summarize the top implementation risks
- summarize the recommended next workflow and why
- summarize the Storybook recommendation and why
- stop

Do not begin writing the spec or the executable plan unless I explicitly ask you to continue.

### Deliverable

Write:

- `[DISCOVERY_PATH]`

Then report:

1. where the file was written
2. whether Storybook was recommended, rejected, or mandated
3. the top 5 findings that the later spec/plan stage must preserve
