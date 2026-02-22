# Step 1: Concept

## Purpose
Capture the user's core idea in their own words. The goal is to understand WHAT they want to build at a high level — not to solve it, design it, or scope it yet.

## Inputs
- None (this is the starting point)

## How to Run This Step

1. **Listen first.** Let the user explain their idea without interrupting or jumping ahead.
2. **Ask clarifying questions** to make sure you understand the core concept:
   - What problem does this solve?
   - Who is it for?
   - What does success look like?
   - Are there any existing tools/systems this replaces or integrates with?
3. **Summarize back** what you understood in 3-5 sentences and ask the user to confirm or correct.
4. **Do NOT** discuss implementation details, technology choices, architecture, or scope yet. That comes in later steps.

## What to Avoid
- Don't suggest solutions or technologies yet
- Don't estimate effort or complexity
- Don't start scoping features — just understand the core idea
- Don't assume you know what the user means — ask

## Project-Local `CLAUDE.md`
After the user confirms the concept, create a `CLAUDE.md` file in the project root. This file is loaded automatically at the start of every session and serves as the project's living status board. Keep it short (under 25 lines) — it should tell a fresh session exactly what's happening and what to do next.

```markdown
# [Project Name]

## Project Overview
[1-2 sentence description of what this project is]

## Current State
- **Workflow Step**: 1 (Concept) — just created
- **Resume**: Say "start step 2 for [project]"

## Key References
[Added as handoff files are created in later steps]
```

Update this file at the end of every step and after each task completion during Step 6. During Step 6, also update it after each agent phase within a task so that a session crash can recover immediately. The "Current State" section should always reflect reality — what step/task we're on, what was last completed, and what to say to resume.

## Handoff Output
When the user confirms you've captured the concept correctly, create a handoff file in the `project-handoffs/` subfolder. Create the subfolder if it doesn't exist yet.

### Handoff File: `project-handoffs/handoff-step-1.md`

```markdown
# Step 1 Handoff: Concept

## Project Name
[Name of the project]

## Core Concept
[3-5 sentence summary of what the user wants to build]

## Problem Statement
[What problem does this solve?]

## Target User / Audience
[Who is this for?]

## Success Criteria
[What does success look like from the user's perspective?]

## Key Context
[Any important context — existing systems, constraints mentioned, integrations, etc.]

## Open Questions (if any)
[Anything that came up but wasn't resolved — carry forward to Step 2]
```
