# Step 2: Discovery

## Purpose
Refine the concept through back-and-forth discussion. Explore the idea from multiple angles, identify unknowns, and surface requirements that the user may not have initially considered.

## Inputs
- Read `project-handoffs/handoff-step-1.md` from the project folder

## How to Run This Step

1. **Review the Step 1 handoff** to understand the core concept.
2. **Explore the idea deeply** by asking targeted questions across these areas:
   - **Users & Use Cases**: Who interacts with this? What are the main workflows?
   - **Data**: What data does this system handle? Where does it come from? Where does it go?
   - **Integrations**: Does this connect to external systems, APIs, hardware, or services?
   - **Constraints**: Are there performance requirements, platform limitations, regulatory needs, or budget constraints?
   - **Edge Cases**: What happens when things go wrong? What are the boundary conditions?
   - **Prior Art**: Has the user tried other solutions? What worked or didn't?
3. **Challenge assumptions** gently — if something seems under-specified or risky, point it out.
4. **Build a shared mental model** — by the end, both you and the user should have the same picture of what this project involves.
5. **Identify risks and unknowns** that will need to be addressed in later steps.

## What to Avoid
- Don't finalize scope or feature lists yet — that's Step 3
- Don't pick technologies or design architecture — that's Step 4
- Don't dismiss ideas as "too hard" — explore them and note concerns
- Don't rush — this step can take multiple exchanges

## Handoff Output
When you and the user agree the discovery is complete, create a handoff file in the `project-handoffs/` subfolder.

### Handoff File: `project-handoffs/handoff-step-2.md`

```markdown
# Step 2 Handoff: Discovery

## Project Name
[Name]

## Refined Concept
[Updated summary incorporating everything learned in discovery]

## Users & Use Cases
[Who uses this and how — list the main use cases]

## Data & Integrations
[What data is involved, where it flows, external systems]

## Constraints & Requirements
[Performance, platform, regulatory, budget, timeline constraints]

## Identified Risks
[Things that could be problems — technical risks, unknowns, dependencies]

## Open Questions
[Anything still unresolved heading into specification]

## Key Decisions Made
[Any decisions agreed upon during discovery]
```
