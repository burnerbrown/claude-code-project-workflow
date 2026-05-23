# Band-Aid Marker Protocol (Shared)

This file defines how a worker agent marks and clears a **band-aid** (a knowingly temporary or improper fix) in code/config it writes. It is the producer-side half of the band-aid rule; the full lifecycle (definition, the two kinds, triage dispositions, opportunistic cleanup, and the canonical-source rule) lives in `step-6-implementation.md` "Band-Aids (Temporary Fixes)".

**Agents that follow this protocol:** Senior Programmer, Test Engineer, Database Specialist, DevOps Engineer, Embedded Systems Specialist, Performance Optimizer — i.e. every producer that writes committed, comment-markable code/config (source, tests, scripts, SQL, Dockerfiles/CI/compose, firmware, benchmarks/sandbox setup).

**Not used by:** agents whose deliverables are specs, docs, or design artifacts rather than executable code/config (API Designer, Documentation Writer, UX/UI Designer, Hardware Engineer) — there is nothing to mark with an inline code comment.

## What a band-aid is

A band-aid is a fix you KNOW is temporary or improper: it works (unblocks progress, passes a test) but is not the proper fix — the real fix is larger or elsewhere, and it leaves technical debt. A change that IS the proper fix (root cause addressed, robust, matches the design) is NOT a band-aid and gets NO marker — it is just done.

## Apply: mark it in the same edit (MANDATORY)

When you apply a band-aid to a file, you MUST, in the SAME edit, add a one-line marker at the spot, using the language's comment syntax (`#`, `//`, `/* */`, `--`, etc.):

```
# FIXME(band-aid): <one line: what's wrong / what the real fix is> — see PASSDOWN
```

The marker is a pointer ONLY, not the full fix. Then surface the band-aid in your advisory notes (what / where / why) so the orchestrator can route it at task-end triage.

Examples by producer: a hardcoded value or stubbed branch (Senior Programmer); a skipped/`xfail` test, a hardcoded expected value, or a commented-out assertion (Test Engineer); a migration shortcut or a relaxed constraint (Database Specialist); a pinned-but-wrong base image or a skipped CI step (DevOps Engineer); a fixed delay instead of a proper interrupt, or a disabled feature (Embedded Systems Specialist).

## Clear: when assigned an opportunistic cleanup

If the orchestrator's prompt asks you to clear an existing `# FIXME(band-aid)` (an opportunistic cleanup — see `step-6-implementation.md` "Band-Aids (Temporary Fixes)" → opportunistic cleanup), apply the real fix AND remove that marker as part of the same work. Leaving the marker after fixing the underlying issue is a defect the Quality Gate catches via its cross-cutting FIXME band-aid clearance check (see `quality-gate.md` "Evaluation Rules").

## Not your call

Whether a band-aid becomes a PASSDOWN note, a new task, or must be surfaced to the user (guardrail-weakening) is decided by the orchestrator at task-end triage, not by you. Your job is to mark it and surface it.
