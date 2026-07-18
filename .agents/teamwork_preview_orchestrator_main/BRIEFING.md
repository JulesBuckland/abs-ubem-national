# BRIEFING — 2026-07-16T10:30:00Z

## Mission
Download cited papers via OpenAlex/arXiv APIs and perform adversarial review of manuscript/manuscript.tex.

## 🔒 My Identity
- Archetype: teamwork_preview_orchestrator
- Roles: orchestrator, user_liaison, human_reporter, successor
- Working directory: C:\Users\jules\OneDrive - The University of Manchester\Internships\projects\energy\paper 5\.agents\teamwork_preview_orchestrator_main
- Original parent: top-level
- Original parent conversation ID: e50891bf-90a2-47e7-8ca1-b87dd813a845

## 🔒 My Workflow
- **Pattern**: Project
- **Scope document**: C:\Users\jules\OneDrive - The University of Manchester\Internships\projects\energy\paper 5\PROJECT.md
1. **Decompose**: Decomposed into 4 milestones.
2. **Dispatch & Execute**:
   - **Delegate (sub-orchestrator)**: Spawn a worker/reviewer agent for each milestone.
3. **On failure** (in this order):
   - Retry: nudge stuck agent or re-send task
   - Replace: spawn fresh agent with partial progress
   - Skip: proceed without (only if non-critical)
   - Redistribute: split stuck agent's remaining work
   - Redesign: re-partition decomposition
   - Escalate: report to parent (sub-orchestrators only, last resort)
4. **Succession**: Self-succeed when cumulative sub-agent spawn count >= 16.
- **Work items**:
  1. Initialize Workspace & Metadata [pending]
  2. Download Cited Papers Script & Execution [pending]
  3. Perform Adversarial Manuscript Review [pending]
  4. Perform Verification & 4BV [pending]
- **Current phase**: 1
- **Current focus**: Work item 1: Initialize Workspace & Metadata

## 🔒 Key Constraints
- Never reuse a subagent after it has delivered its handoff — always spawn fresh
- Zero trust policy: verify all subagent claims.

## Current Parent
- Conversation ID: e50891bf-90a2-47e7-8ca1-b87dd813a845
- Updated: not yet

## Key Decisions Made
- Decomposed project into 4 milestones.

## Team Roster
| Agent | Type | Work Item | Status | Conv ID |
|-------|------|-----------|--------|---------|
| 1a6e6f52-990b-4b6e-a200-f84c08d499ac | teamwork_preview_worker | R1: PDF Downloader Script & Execution | completed | 1a6e6f52-990b-4b6e-a200-f84c08d499ac |
| fb6e3b61-74e8-4ddd-8188-266fd5c99dda | teamwork_preview_reviewer | R2: Adversarial Manuscript Review | completed | fb6e3b61-74e8-4ddd-8188-266fd5c99dda |
| bd148c73-1cb3-472f-b75d-079bfacc2d2f | teamwork_preview_auditor | Forensic Integrity Audit | in-progress | bd148c73-1cb3-472f-b75d-079bfacc2d2f |

## Succession Status
- Spawn count: 3 / 16
- Pending subagents: bd148c73-1cb3-472f-b75d-079bfacc2d2f
- Predecessor: none
- Successor: not yet spawned

## Active Timers
- Heartbeat cron: task-31
- Safety timer: none
- On succession: kill all timers before spawning successor
- On context truncation: run `manage_task(Action="list")` — re-create if missing

## Artifact Index
- C:\Users\jules\OneDrive - The University of Manchester\Internships\projects\energy\paper 5\.agents\teamwork_preview_orchestrator_main\plan.md — Orchestrator plan
- C:\Users\jules\OneDrive - The University of Manchester\Internships\projects\energy\paper 5\.agents\teamwork_preview_orchestrator_main\progress.md — Liveness heartbeat and progress
- C:\Users\jules\OneDrive - The University of Manchester\Internships\projects\energy\paper 5\.agents\teamwork_preview_orchestrator_main\context.md — Context metadata
- C:\Users\jules\OneDrive - The University of Manchester\Internships\projects\energy\paper 5\.agents\teamwork_preview_orchestrator_main\ORIGINAL_REQUEST.md — Verbatim user request
- C:\Users\jules\OneDrive - The University of Manchester\Internships\projects\energy\paper 5\PROJECT.md — Global project index and layout
