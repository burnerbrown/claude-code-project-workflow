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
   - **Hardware** (if the project involves physical hardware / circuit board design):
     - What is the power source? (USB, battery, wall adapter, solar, PoE)
     - What is the target form factor / enclosure? Any size constraints?
     - What environment will it operate in? (indoor, outdoor, temperature range, humidity, vibration)
     - What sensors, actuators, displays, or external devices need to connect?
     - What communication is needed? (WiFi, BLE, LoRa, Ethernet, USB, wired serial)
     - Is this a one-off prototype, small batch, or production volume? (affects component selection and DFM)
     - Will the user design the PCB themselves (in KiCad) or outsource it?
     - Is hand-soldering required, or is reflow assembly available?
     - Any regulatory requirements? (CE, FCC, UL — affects EMC and safety design)
     - Any existing dev kit or prototype to build from?
     - **PCB fabrication preferences** (do NOT finalize the fab house here — final selection happens in Step 4 after component choices are known, since components determine required fab capabilities):
       - Have you used a PCB fab house before? Which one? Were you happy with them? (e.g., JLCPCB, PCBWay, OSH Park, Eurocircuit, local fab)
       - Will you use the fab's assembly service (SMT pick-and-place) or assemble the boards yourself?
       - Is cost a priority, or are advanced capabilities (fine-pitch, HDI, impedance control) more important?
       - Note: We will help you choose the best fab house for this project in Step 4, after the Hardware Engineer selects components. Some components (fine-pitch QFN, BGA, etc.) require fab capabilities that not all houses offer. We'll match the fab to your actual design needs rather than guessing up front.
   - **Prior Art**: Has the user tried other solutions? What worked or didn't?
3. **Challenge assumptions** gently — if something seems under-specified or risky, point it out.
4. **Build a shared mental model** — by the end, both you and the user should have the same picture of what this project involves.
5. **Identify risks and unknowns** that will need to be addressed in later steps.

## What to Avoid
- Don't finalize scope or feature lists yet — that's Step 3
- Don't pick technologies or design architecture — that's Step 4
- Don't dismiss ideas as "too hard" — explore them and note concerns
- Don't rush — this step can take multiple exchanges

## Update Project CLAUDE.md
Before creating the handoff, update the project-local `CLAUDE.md` to reflect the current state:
- **Workflow Step**: 2 (Discovery) — complete
- **Resume**: Say "start step 3 for [project]"

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

## Hardware Requirements (if applicable)
[Power source, form factor, environment, sensors/actuators, communication, volume, assembly method, regulatory needs. Remove this section if the project is software-only.]

### PCB Fabrication Preferences
[User's preferred fab house (if any), prior experience, assembly method (fab service vs self-assembly), cost vs capability priority. Final fab house selection happens in Step 4 after components are chosen.]

## Identified Risks
[Things that could be problems — technical risks, unknowns, dependencies]

## Open Questions
[Anything still unresolved heading into specification]

## Key Decisions Made
[Any decisions agreed upon during discovery]
```
