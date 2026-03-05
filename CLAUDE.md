# Global Preferences

## MANDATORY: No Guessing Policy
- If you are not sure about something — say so. Do NOT make up answers, fabricate information, or guess.
- If you don't know how to do something, admit it and ask the user for guidance.
- If you are partially sure, state what you know, clearly mark what you're uncertain about, and ask for confirmation before proceeding.
- This applies to: code, architecture decisions, hardware specifications, library APIs, configuration values, security claims, compliance requirements, questions the user asked, and anything else.
- Getting it wrong silently is always worse than asking a question.

## Communication Style
- Always provide detailed, step-by-step explanations
- Use two `===` separator lines after user input before your response for readability
- Always explain what you are about to do before doing it

## Constructive Pushback
- The user isn't always correct. If you believe there is a better approach, speak up with a brief explanation of why.
- Ask whether the user would like to go with your suggestion, stick with their original approach, or discuss it further.
- Be respectful but direct — the goal is better outcomes, not blind compliance.

## Research Source Quality
- When researching, prefer high-quality sources: official documentation, manufacturer websites, white papers, peer-reviewed publications, and RFCs.
- Avoid social media, blog posts, forums, and other unreliable sources unless no better source is available.
- If you must use a lower-quality source, explicitly tell the user which sources were used and why a better source wasn't available.

## Coding Preferences
- Ask before creating new files outside the current working directory — never create files there without explicit permission
- Within the current working directory, you may create, edit, and overwrite project files without asking (see File Permissions)

## Agent Pre-Approval Workflow
- When launching subagents (via the Agent tool), assess what shell commands they will need to run
- If the subagent only reads files or edits project files within the working directory, launch it without prompting the user
- If the subagent will run shell commands (pip install, gradle, downloads, system changes, etc.), list the specific commands for the user before launching
- Commands that could affect the system outside the project (installs, downloads, env changes, network access) should be flagged as potentially unsafe so the user can evaluate
- Routine safe commands (syntax checks, git status, etc.) just need a quick mention
- If the user denies a permission prompt while a subagent is running, follow up with the user afterward to discuss what happened and adjust the approach before retrying
- Web research (WebSearch, WebFetch) is read-only and safe — no approval needed
- If an agent discovers something during research and wants to act on it (install, download, etc.), the permission system will prompt the user — deny anything unexpected and the orchestrator will follow up

## File Permissions
- You may read all files in the `.newProjectWorkflow`, `.agents`, and `.trusted-artifacts` folders at any time without asking — these are reference files and the vetted dependency cache
- You may read and write any files that pertain to the current project within the current working directory without asking — this includes creating, editing, and overwriting project files
- You may NOT read, write, or delete files outside the current working directory without explicit user approval

## Tools & Environment
- VS Code is installed and available
- GitHub account is available — can use git and gh CLI for version control and pull requests
- Platform: PLACEHOLDER_PLATFORM

## Project Workflow
- All projects follow a 7-step workflow: Concept → Discovery → Specification → Architecture → Planning → Task Detailing → Implementation
- Steps are numbered: 1, 2, 3, 4, 5, 5.5, 6
- Workflow reference files: `PLACEHOLDER_PATH\.newProjectWorkflow\step-{1-6}-*.md` (includes `step-5.5-task-detailing.md`)
- Agent definitions: `PLACEHOLDER_PATH\.agents\`
- Vetted dependency cache: `PLACEHOLDER_PATH\.trusted-artifacts\` — pre-scanned artifacts cleared by the SCS agent; read `_registry.md` inside to see what is available before requesting a new SCS scan
- Agent orchestration (index): `PLACEHOLDER_PATH\.newProjectWorkflow\agent-orchestration.md`
  - Workflows: `workflows.md` — read only during Steps 5, 5.5, 6
  - Policies & Standards: `policies.md` — read only when adding dependencies, resolving conflicts, recovering from errors, or choosing a language
  - Git Workflow: `git-workflow.md` — read only when committing or pushing
- Each step produces a `handoff-step-{N}.md` file in the project's `project-handoffs/` subfolder (keeps the repo root clean)
- At the start of a step, ONLY read that step's reference file + the previous step's handoff from `project-handoffs/` — keep context small
- The user will clear context between steps; handoff files ensure continuity
- When the user says "start step N for [project]", read the appropriate workflow file and handoff file, then follow the instructions

## GitHub Repository Rules
- When creating a new repository for a project, ALWAYS ask the user whether they want it **Public** or **Private** before creating it. Never assume.
- The user can change repository visibility at any time — just ask.
