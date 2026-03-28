# Step 3: Specification & Scope

## Purpose
Turn the discovery results into a concrete, documented specification. Define what IS in scope and what is NOT. This becomes the contract for what we're building.

## Inputs
- Read `project-handoffs/handoff-step-2.md` from the project folder

## How to Run This Step

1. **Review the Step 2 handoff** to understand everything discovered.
2. **Define features and requirements** — organize them into:
   - **Must Have (MVP)**: Core features without which the project has no value
   - **Should Have**: Important features that can follow shortly after MVP
   - **Nice to Have**: Features that add value but aren't essential
   - **Out of Scope**: Explicitly list what we are NOT building (this prevents scope creep)
3. **Write functional requirements** for each Must Have feature:
   - What does it do?
   - What are the inputs and outputs?
   - What are the acceptance criteria? (How do we know it's done?)
4. **Write non-functional requirements**:
   - Performance targets (if any)
   - Security requirements
   - Reliability / availability needs
   - Platform / compatibility requirements
5. **Review with the user** — go through each requirement and confirm agreement.
6. **Resolve any remaining open questions** from Step 2.

## What to Avoid
- Don't design the solution — describe WHAT, not HOW
- Don't let scope grow unbounded — push back on "while we're at it" additions
- Don't leave requirements vague — "it should be fast" is not a requirement; "API response under 200ms for 95th percentile" is
- Don't skip the Out of Scope section — it's just as important as what's in scope

## Update Project CLAUDE.md
Before creating the handoff, update the project-local `CLAUDE.md` to reflect the current state:
- **Workflow Step**: 3 (Specification) — complete
- **Resume**: Say "start step 4 for [project]"

## GitHub Repository
After the user approves the specification, this is where we create the project's GitHub repository:
1. **Ask the user** whether the repo should be **Public** or **Private**
2. Initialize the repo with a `project-handoffs/` folder and create an initial commit containing `project-handoffs/handoff-step-1.md`, `project-handoffs/handoff-step-2.md`, and `project-handoffs/handoff-step-3.md`
3. Push to GitHub

**Note:** The full project folder structure (src/, lib/, .gitignore, etc.) is NOT created here — that happens in Step 4 after architecture decisions are made and the language/framework are chosen.

## Handoff Output
When the user approves the specification, create a handoff file in the `project-handoffs/` subfolder.

### Handoff File: `project-handoffs/handoff-step-3.md`

```markdown
# Step 3 Handoff: Specification & Scope

## Project Name
[Name]

## Scope Summary
[One paragraph summarizing what we're building]

## Must Have (MVP)
[Numbered list of MVP features with acceptance criteria]

## Should Have (Post-MVP)
[Numbered list]

## Nice to Have (Future)
[Numbered list]

## Out of Scope
[Explicit list of what we are NOT building]

## Non-Functional Requirements
- Performance: [targets]
- Security: [requirements]
- Platform: [requirements]
- Other: [as applicable]

## Resolved Questions
[Questions from Step 2 that are now answered]

## Assumptions
[Anything we're assuming to be true — if an assumption is wrong, it may change the spec]

## GitHub Repository
- URL: [GitHub repo URL]
- Visibility: [Public / Private]
```
