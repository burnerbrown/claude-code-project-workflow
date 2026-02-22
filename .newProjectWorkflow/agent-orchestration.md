# Agent Orchestration Reference

This is the main entry point for agent orchestration. It contains how to use agents, the available agents table, and references to focused files for specific topics. **Only read the focused files when you need them** — see the guidance below.

Each agent file in `PLACEHOLDER_PATH\.agents\` defines a persona, principles, and output format for a focused subagent.

---

## Focused Reference Files

Read these **only when needed** to keep context small:

| File | Path | Read When |
|------|------|-----------|
| **Policies & Standards** | `policies.md` | A dependency is being added, two agents disagree, an agent fails, or choosing a language |
| **Workflows** | `workflows.md` | Steps 5, 5.5, or 6 — when you need the specific agent sequence for a task |
| **Git Workflow** | `git-workflow.md` | Time to commit (after QG approval) or push to remote (workflow complete) |

**Do NOT read these files preemptively.** Only load them when the current task specifically requires their content. The no-guessing rule and governing standards are already baked into each agent's own definition file — you don't need `policies.md` for normal agent execution.

---

## How to Use Agents

### Loading an Agent
To use a specialized agent, read its definition file and pass the contents as a prompt prefix to the Task tool. The pattern is:

1. Read the agent file from `PLACEHOLDER_PATH\.agents\<agent-name>.md`
2. Combine the agent definition with the specific task instructions
3. Pass the combined prompt to the Task tool with `subagent_type: "general-purpose"`

**Example prompt structure for the Task tool:**
```
<agent-definition>
{contents of PLACEHOLDER_PATH\.agents\senior-programmer.md}
</agent-definition>

<task>
{specific task instructions, context, and any output from previous agents}
</task>
```

### Important: Passing Context to Agents
When launching agents, **pass file paths and instructions — not file contents.** Agents can read files in their own context. This keeps the orchestrator's context small.

- Tell agents which files to read and what to do — they will read the files themselves
- Include the specific instructions and acceptance criteria from the checklist in the agent's prompt
- For handoffs between agents, tell the next agent which files were created/modified by the previous agent
- **Exception:** Small, focused context is OK to include directly (e.g., a short code snippet from a QG verdict, specific review findings). If it's more than ~20 lines, pass the file path instead.
- Supply Chain Security: always check `.trusted-artifacts/_registry.md` before invoking the SCS agent — a cache hit means no new scan is needed

### Important: Quality Gate Routing
**All worker agent output must be routed through the Quality Gate (QG) for evaluation.** The orchestrator's workflow for every agent handoff is:

1. Invoke the worker agent with the task — tell it which files to read and what to do
2. Receive the worker agent's output
3. Run a quick sanity check if applicable (e.g., `bash -n` for scripts)
4. Invoke the **Quality Gate** agent with:
   - The file paths to review (let the QG read the files itself)
   - The agent role being evaluated (so the QG knows which acceptance criteria to use)
   - The acceptance criteria from the checklist
5. Receive the QG's verdict
6. **Orchestrator routes based on the verdict:**
   - If APPROVED: commit the approved work, check the subtask box, proceed to the next agent in the checklist
   - If SENT BACK: **resume** the original worker agent (using its saved agent ID) with the QG's specific feedback — see "Agent Lifecycle: Resume on Rework" below
   - If APPROVED WITH CONDITIONS: commit and proceed; track conditions as follow-ups

**The Project Manager agent is optional.** See `workflows.md` "When to Invoke the Project Manager Agent" for the specific situations that warrant a PM invocation. For most tasks, the orchestrator handles routing directly using the checklist's agent sequence.

**Prompt structure for QG evaluation:**
```
You are the Quality Gate agent. Evaluate the {Agent Role}'s output for Task {N} ({Task Name}).

Files to review: {file paths — let the QG read them}
Acceptance criteria: {from the checklist}
QG criteria to evaluate: {P1-P10, T1-T10, etc. — from quality-gate.md}

Produce your evaluation with PASS/FAIL/PARTIAL for each criterion and your overall verdict.
```

**When all workflow steps are complete** (all subtask boxes checked, final QG approval received), the orchestrator commits all work and asks the user for push approval.

### Agent Lifecycle: Resume on Rework

When a worker agent is first launched for a task, the Task tool returns an **agent ID**. The orchestrator should track these IDs for the duration of the current task session. If the Quality Gate sends work back to a previously-invoked agent, **resume that agent** using the `resume` parameter instead of launching a fresh one.

**Why resume instead of launching fresh:**
- The resumed agent retains full context: what files it read, what code it wrote, what decisions it made
- Rework is faster and more accurate because the agent doesn't need to rebuild context from scratch
- The agent can see the QG feedback alongside its own prior work, making targeted fixes easier

**Which agents to resume:**
- **Senior Programmer**: Resume when QG sends code back for fixes, or when reviewers flag issues requiring code changes
- **Test Engineer**: Resume when QG sends tests back, or when code fixes require test updates
- **Security Reviewer**: Resume when re-verifying that flagged issues have been fixed — it remembers its original findings
- **Code Reviewer**: Resume when re-reviewing after significant code changes — it remembers its original review context
- **DevOps Engineer**: Resume when QG sends CI/CD configs or Dockerfiles back — it retains knowledge of pipeline structure, environment variables, and deployment constraints
- **Embedded Systems Specialist**: Resume when QG sends firmware code back — it retains knowledge of hardware constraints, pin mappings, timing requirements, and register configurations
- **Database Specialist**: Resume when QG sends schema/migration work back — it retains context of the full data model, indexing strategy, and design trade-offs
- **API Designer**: Resume when QG sends API spec back — it retains context of resource models, endpoint relationships, error catalogs, and versioning decisions
- **Performance Optimizer**: Resume for the verification phase — it retains context of its original analysis findings for before/after comparison. Also resume if QG sends recommendations back for revision
- **Project Manager**: Resume within a task session when the PM is active (multi-module projects) — it retains cross-module dependency and status context. For single-module projects where the PM is not invoked, this is N/A

**Which agents to invoke fresh each time:**
- **Quality Gate**: Each QG invocation evaluates a different agent's output with different criteria — fresh invocations are appropriate
- **Compliance Reviewer**: One-shot final-gate evaluation — fresh each time
- **Documentation Writer**: One-shot deliverable — fresh each time
- **Supply Chain Security**: Invoke fresh — the Phase 0 cache check automatically skips previously completed work, making scans idempotent
- **Software Architect**: Invoke fresh — only used in Step 6 for Documentation Sprint workflows, providing context summaries that don't benefit from prior session state

**Agent ID tracking rules:**
- Note each worker agent's ID when it's first launched during a task
- Use the `resume` parameter on the Task tool to continue a previously-launched agent
- Agent IDs are held in the orchestrator's working memory and naturally expire when the user does `/clear` between tasks — this is the correct lifecycle since each task gets fresh agents
- No explicit cleanup is needed — the `/clear` between tasks handles it

**Resume prompt structure (rework scenario):**
```
The Quality Gate has sent your work back. Here is the QG's feedback:

{QG verdict with specific findings}

Please address these issues and produce updated output.
```

The resumed agent already has full context of its prior work, so there is no need to re-specify file paths, instructions, or acceptance criteria — just provide the QG feedback.

---

## Available Agents

| Agent | File | Use When |
|-------|------|----------|
| Software Architect | `software-architect.md` | **Step 4**: Designing a new system or component, making technology choices, defining interfaces. Not used in Step 6 — architecture is finalized in Step 4. |
| Senior Programmer | `senior-programmer.md` | Writing implementation code from a design or specification |
| Test Engineer | `test-engineer.md` | Writing unit tests, integration tests, or benchmarks for existing code |
| Security Reviewer | `security-reviewer.md` | Reviewing code for vulnerabilities and security issues |
| Code Reviewer | `code-reviewer.md` | Reviewing code for quality, readability, and maintainability |
| Documentation Writer | `documentation-writer.md` | Writing README files, API docs, ADRs, or setup guides |
| DevOps Engineer | `devops-engineer.md` | Creating Dockerfiles, CI/CD pipelines, build scripts, deployment configs |
| Performance Optimizer | `performance-optimizer.md` | Profiling, benchmarking, and optimizing code performance |
| Database Specialist | `database-specialist.md` | Designing schemas, writing migrations, optimizing queries |
| Embedded Systems Specialist | `embedded-systems-specialist.md` | RTOS firmware, peripheral drivers, bare-metal programming, hardware/circuit design assistance for KiCad |
| API Designer | `api-designer.md` | Designing REST or gRPC APIs, writing OpenAPI specs, protobuf definitions |
| Supply Chain Security | `supply-chain-security.md` | **Step 4**: Full 5-phase scan of all external dependencies. In Step 6, only used if a new dependency is discovered mid-implementation (emergency workflow). **Always check `.trusted-artifacts/_registry.md` before invoking — if the dependency is cached and hash-verified, skip the scan entirely.** Must run synchronously — do NOT use `run_in_background: true`. |
| Compliance Reviewer | `compliance-reviewer.md` | Final-gate NIST/CISA/OWASP compliance assessment |
| Quality Gate | `quality-gate.md` | **Evaluates every agent's output against acceptance criteria** — produces APPROVED/SENT BACK/APPROVED WITH CONDITIONS verdicts with specific feedback and code snippets. |
| Project Manager | `project-manager.md` | **Project coordinator** — receives Quality Gate verdicts, makes routing decisions (proceed/send back), tracks cross-module dependencies, blockers, deferred items, and cross-session continuity via `PROJECT_STATUS.md`. |

All agent files are located in: `PLACEHOLDER_PATH\.agents\`
