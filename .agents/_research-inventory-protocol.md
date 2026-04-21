# Research Inventory Protocol (Shared)

This file defines the Research Inventory Manifest format and rules that worker agents follow when invoked in **research-only mode** by the orchestrator. The orchestrator tells an agent to read this file as part of any research-mode invocation.

**Agents that use this protocol:** Senior Programmer, Test Engineer, Database Specialist, DevOps Engineer, API Designer, Embedded Systems Specialist, Performance Optimizer.

**Not used by:** Component Sourcing — it has a domain-specific variant in its own definition file, because web research is part of its implementation role (not a separate research phase).

## Purpose

When the orchestrator invokes you with a **research-only** prompt (asking you to identify external resources before implementation), you MUST produce a Research Inventory Manifest instead of implementing. Do NOT download, install, fetch, or access any external resources during the research phase — only identify what you will need.

## Manifest Format

For each external resource you anticipate needing, provide:

| Item | Category | Why Needed | Source/URL |
|------|----------|------------|------------|
| [Name/description] | [download / web search / web fetch / tool install / other] | [Brief justification tied to the task] | [URL, package name, or search terms] |

## Categories

- **download**: Package, library, or file to download (triggers SCS workflow if new dependency)
- **web search**: Search engine query for documentation or examples (include search terms)
- **web fetch**: Specific URL to load and read (include full URL — will be assessed for trustworthiness)
- **tool install**: CLI tool, build tool, or utility to install on the system
- **other**: Any other external access (describe specifically)

## Rules

- If you need NO external resources, state "No external resources needed" and the orchestrator will auto-continue to implementation
- Do NOT attempt to download, fetch, or install anything during the research phase
- During implementation, only use resources that the user has approved from your manifest
- If you discover an unexpected need during implementation that was NOT in your manifest, stop and document it — do NOT access the resource without approval
- Write your manifest to the file path the orchestrator specifies (in the `research-inventories/` folder)
