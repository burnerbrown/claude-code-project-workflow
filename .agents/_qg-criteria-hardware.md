# QG Acceptance Criteria - Hardware and Firmware Roles

Companion to `quality-gate.md`. Holds the acceptance-criteria tables for the hardware-and-firmware agent roles listed below. The Quality Gate reads ONLY the one companion file containing the role it is gating (see the role-to-file index in `quality-gate.md`), not all three criteria files. The gate's persona, no-guessing rule, core principles, "What This Agent Does NOT Do" boundary, evaluation rules, output format, report placement, and tool restrictions all stay in `quality-gate.md`.

Roles in this file: Embedded Systems Specialist (ES1-ES12), Hardware Engineer (HE1-HE16), Component Sourcing Agent (CS1-CS8), DFM Reviewer (DFM1-DFM10).

---

### Embedded Systems Specialist

The Embedded Specialist operates in two modes. Apply the criteria that match the mode specified by the orchestrator.

**Mode A — Firmware Implementation (Step 6):** The agent designs or writes embedded code. Evaluate against ES1–ES8.

**Mode B — Hardware Design Review from Firmware Perspective (Step 4):** The agent reviews the Hardware Engineer's Mode 1 architecture for firmware-level feasibility. Evaluate against ES9–ES12.

#### Mode A — Firmware Implementation (ES1–ES8)
The Mode A output is APPROVED when ALL of the following are present and complete:

| # | Criterion | What to Check |
|---|-----------|---------------|
| ES1 | Complete Source | Full Rust files with `#![no_std]`/`#![no_main]` where appropriate |
| ES2 | Hardware Abstraction | Peripheral access patterns documented |
| ES3 | Memory Map | Peripheral addresses, register layouts documented |
| ES4 | Timing Analysis | WCET estimates and scheduling feasibility for real-time tasks |
| ES5 | Peripheral Configuration | Pin assignments, clock speeds, DMA channels documented |
| ES6 | Security Section Present | The output includes a security section addressing: hardcoded-credential policy, debug/JTAG/SWD interface protection, firmware update signing, watchdog configuration, input validation policy, and side-channel considerations for security-critical operations. OWASP Embedded Application Security Top 10 (E1–E10) coverage is documented. Existence and structural completeness only — substance review of whether the security choices are correct is owned by the Security Reviewer, not QG. |
| ES7 | Test Strategy | What can be tested in simulation vs requires hardware |
| ES8 | Power Budget Analysis | Power budget present — active, sleep, and deep-sleep current estimates per subsystem with total system budget. Applies even for wall-powered designs (informs regulator sizing and thermal analysis). |

**Reject if (Mode A):** Missing timing analysis for real-time code, no test strategy, or no power budget analysis.

#### Mode B — Hardware Design Review (ES9–ES12)
The Mode B output is APPROVED when ALL of the following are present and complete:

| # | Criterion | What to Check |
|---|-----------|---------------|
| ES9 | Firmware Feasibility | Assessment of whether firmware requirements can be met with the proposed hardware; hardware choices that simplify or complicate the firmware are identified, with trade-off analysis documented |
| ES10 | Pin Mapping Validation | Conflicts, missing capabilities, or suboptimal assignments flagged |
| ES11 | Resource Conflicts | DMA channel, timer, and interrupt priority conflicts identified |
| ES12 | Errata Awareness | Known MCU errata relevant to the firmware design documented |

**Reject if (Mode B):** Firmware feasibility assessment absent, no pin mapping validation, or resource conflicts not analyzed.

**Note:** Full hardware design criteria (component selection, power architecture, BOM, schematic guidance, PCB layout) are evaluated under the **Hardware Engineer** criteria (HE1–HE16), not here.

---

### Hardware Engineer
The hardware engineer operates in three modes. Apply the criteria that match the mode specified by the orchestrator.

**Mode 1 — High-Level Architecture (Step 4):** Evaluate against HE1-HE6, HE11-HE14. HE5 and HE6 are evaluated as partial (power domain identification and pin reservation, not detailed regulator selection or pin-to-component wiring). HE7-HE10 are deferred to per-subsystem and consolidation tasks.

**Mode 2 — Per-Subsystem Detail (Step 6):** Evaluate against HE5-HE9, HE11, HE12, HE15 scoped to the specific subsystem being designed. The subsystem must include: detailed circuit design, component selections with MPNs, pin mapping updates, power budget contribution, schematic design notes, KiCad reference contributions, and subsystem-specific risks.

**Mode 3 — Consolidation (Step 6):** Evaluate against the full criteria HE1-HE16. The consolidated output must include the complete BOM, complete pin mapping, full power budget, PCB layout guidance, all KiCad reference files, and inter-subsystem conflict verification.

| # | Criterion | What to Check | Mode |
|---|-----------|---------------|------|
| HE1 | Design Overview | 2-3 paragraph summary of hardware architecture and key decisions | 1, 3 |
| HE2 | Block Diagram | Mermaid diagram showing subsystems, power domains, and communication links | 1, 3 |
| HE3 | MCU Selection | Comparison table exists with 2–3 MCU candidates. A recommendation is stated. Justification text accompanies the recommendation. Existence/structure check only — substance review of whether the choice and justification are technically sound is owned by Component Sourcing's pass. | 1 |
| HE4 | Communication Protocols | Table of all inter-component links with protocol, speed, voltage, and connector | 1, 3 |
| HE5 | Power Architecture | Mode 1: power domain identification. Mode 2: per-subsystem regulator sizing and budget. Mode 3: complete power tree with full budget table. | 1, 2, 3 |
| HE6 | Pin Mapping | Mode 1: pin reservation per subsystem. Mode 2: detailed pin-to-component wiring for this subsystem. Mode 3: complete MCU pin assignment table. | 1, 2, 3 |
| HE7 | Interface Specifications | For each inter-component link and external connector: protocol choice, speed/frequency, voltage levels, termination requirements, maximum cable length, and connector type | 2, 3 |
| HE8 | Circuit Design & Schematic Notes | Circuit Design section exists with topology described, component values listed, justification statements present, and reference-design citations. Implementation guidance for schematic entry is included. Existence/structure check only — substance review of whether the topology and component values are technically correct is owned by DFM Reviewer / Component Sourcing. | 2, 3 |
| HE9 | Component Selection / BOM | Mode 2: subsystem component list with MPNs. Mode 3: complete BOM. | 2, 3 |
| HE10 | PCB Layout Guidance | Component placement, routing, and stackup recommendations | 3 |
| HE11 | Risk Register | Hardware Risk Register section exists. Each risk has a mitigation statement (thermal, EMC, single-source, tolerances categories addressed where applicable). Existence-only — substance review of whether mitigations are adequate is owned by DFM Reviewer / Component Sourcing. | 1, 2, 3 |
| HE12 | Datasheet Evidence | Component selection rationale references datasheet parameters explicitly (each component's selection cites at least one datasheet parameter). Existence/citation check only — substance review of whether the cited parameters are correctly interpreted is the Hardware Engineer's own work. | 1, 2, 3 |
| HE13 | Subsystem Inventory | Numbered list of all subsystems with name, one-line description, power domain, reserved MCU pins, and key constraints; cross-referenced against block diagram | 1 |
| HE14 | Fab House Compatibility | Comparison section exists listing each design requirement (finest pitch, smallest passive, via type, layer count, impedance control, surface finish) against the preferred fab's documented capabilities. For any flagged mismatch, an alternative-path section is present. Existence/structure check only — substance review of whether comparisons are accurate or alternatives are technically viable is owned by DFM Reviewer. | 1 |
| HE15 | KiCad Reference Files | Mode 2: `hardware/kicad-contributions.md` contains a section for this subsystem with entries for all five file types (BOM rows, net connections, wiring checklist entries, net class assignments, component placement notes). Mode 3: all five files present (bom-kicad-reference.csv, netlist-connection-reference.md, schematic-wiring-checklist.md, layout-net-classes.csv, layout-component-guide.md), structurally complete, and consistent with BOM and pin mapping. | 2, 3 |
| HE16 | Inter-Subsystem Conflict Check | Explicit verification of no shared-pin conflicts, address collisions, power budget overruns, or protocol conflicts between subsystems; resolutions documented for any found | 3 |

**Reject if (Mode 1):** No MCU comparison table, missing block diagram, no subsystem inventory, or pin reservations missing.
**Reject if (Mode 2):** Missing component MPNs, no circuit design detail, no power budget contribution, no pin mapping update for this subsystem, or missing KiCad reference contributions.
**Reject if (Mode 3):** Incomplete BOM, pin mapping gaps, power budget overrun unaddressed, missing KiCad reference files, or inter-subsystem conflicts not verified.

---

### Component Sourcing Agent
The component sourcing agent's output is APPROVED when ALL of the following are present and complete:

| # | Criterion | What to Check |
|---|-----------|---------------|
| CS1 | BOM Validation Summary | Overall health assessment (GREEN/YELLOW/RED) with key findings |
| CS2 | Component Review Table | Every BOM component reviewed for lifecycle, availability, lead time, risk, and fab-assembly-library compatibility (whether the component is in the selected fab's standard parts library; flagged if it requires customer-supplied parts) |
| CS3 | Lifecycle Flags | All NRND/EOL/Obsolete components explicitly flagged |
| CS4 | Second Source | Second-source availability documented for all components |
| CS5 | Alternatives | For each flagged component, 1–2 alternatives are listed with a trade-off statement and a notes-on-required-design-changes section. Existence/structure check only — substance review of whether alternatives are technically viable is owned by Hardware Engineer. |
| CS6 | Cost Summary | Estimated costs at multiple quantities (1, 10, 100, 1000) |
| CS7 | Supply Chain Risk | Supply Chain Risk section exists listing single-source, long-lead, and high-risk components. Counterfeit-risk components are listed in their own subsection (commonly-counterfeited part categories per SAE AS6171: popular MCUs, power MOSFETs, linear regulators) with a sourcing recommendation statement. Existence/structure check only — substance review of whether the risk identifications are complete is owned by Hardware Engineer / Component Sourcing's own producer review. |
| CS8 | Data Freshness | Clear statement about data currency limitations and recommendation to verify |

**Reject if:** Missing lifecycle check on any component, no alternatives for flagged parts, or cost estimates presented as definitive without freshness caveat.

---

### DFM Reviewer
The DFM reviewer's output is APPROVED when ALL of the following are present and complete:

| # | Criterion | What to Check |
|---|-----------|---------------|
| DFM1 | DFM Summary | Overall assessment (PASS/PASS WITH NOTES/NEEDS REVISION) with selected fab house identified and its specific capabilities referenced; or if no fab house was selected, target manufacturing tier (budget/standard/advanced) clearly stated as the basis for review |
| DFM2 | Fabrication Review | Fabrication Review section is present and addresses each PCB parameter (trace width, spacing, via size, layers) against target fab capabilities. Section-existence check only — substance review of whether the parameter checks are correct is the DFM Reviewer's own work. |
| DFM3 | Assembly Review | Assembly Review section is present and addresses component placement, soldering feasibility, fine-pitch handling, hand-solderability, and thermal relief. Section-existence check only — substance review is the DFM Reviewer's own work. |
| DFM4 | Thermal Review | Thermal Review section is present, listing identified hot spots and thermal management recommendations. Section-existence check only — substance review of thermal analysis is the DFM Reviewer's own work. |
| DFM5 | Testability Review | Testability Review section is present and addresses test points, programming header, and debug access. Section-existence check only — substance review is the DFM Reviewer's own work. |
| DFM6 | Mechanical Review | Mechanical Review section is present and addresses board outline, mounting holes, connector placement, and enclosure compatibility. Section-existence check only — substance review is the DFM Reviewer's own work. |
| DFM7 | Findings Table | All findings in structured table with severity (MUST-FIX/SHOULD-FIX/ADVISORY), category, and recommendation |
| DFM8 | Tier Fallback Documentation | If no fab house was selected, the review explicitly states which generic tier (budget/standard/advanced) was used as a fallback and that recommendations are based on assumed capabilities. If a fab house was selected, this criterion is N/A (DFM1 already verifies the fab house and its capabilities are referenced; DFM2 verifies parameters were checked against those capabilities). |
| DFM9 | Recommended Design Rules | Design Rules summary section exists for the target fab tier listing each rule (trace width, spacing, via drill/pad, annular ring, layer count, board thickness, surface finish, impedance control). Each rule states a value or "at fab minimum" with optional justification text. Existence/structure check only — substance review of whether the rule values are at appropriate margins is the DFM Reviewer's own work. |
| DFM10 | Assembly Process Notes | Recommended assembly sequence documented (e.g., paste → place → reflow → inspect → through-hole → test). For mixed-technology boards (SMD + through-hole), the two-process sequence is called out. For hand-assembly prototypes, hand-solderability concerns are noted. |

**Reject if:** No findings table, missing severity classification, fabrication review omitted, or recommended design rules absent.