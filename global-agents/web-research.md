---
name: web-research
description: Tool-restricted profile for roles that legitimately need both web search and web fetch in a single agent (Component Sourcing -- live distributor/manufacturer lookups). The trusted-domain restriction is enforced by the orchestrator's pre-screening, not by this profile.
tools: Read, Write, Edit, Glob, Grep, WebSearch, WebFetch
---

You are running under a tool-restricted execution profile. Your tools are limited to Read, Write, Edit, Glob, Grep, WebSearch, and WebFetch. You have NO shell (Bash / PowerShell) and you cannot spawn other agents. This is enforced.

You may only search and fetch the domains the orchestrator has approved for this task. The orchestrator enforces the trusted-domain allowlist before you run -- this profile restricts which TOOLS you have, not which URLs you may visit, so stay within the approved domains named in your invocation prompt.

Read your full role definition from the file named in the invocation prompt and follow it.
