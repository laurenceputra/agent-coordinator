# AGENTS.md

This repository implements a manager/worker orchestration runtime (`codex_manager_yolo`).
Use the workflow and skills below for all changes.

## Workflow (required)
1. **Spec gate first**: define scope, acceptance criteria, and risks before editing.
2. **Choose skills**: load only relevant skills from `.agents/skills/`.
3. **Implement minimal diff**: make focused changes in manager/runtime/policy code.
4. **Validate deterministically**: run tests and policy checks before finalizing.
5. **Persist evidence**: ensure task decisions/reviews remain auditable.

## Skill directory
Use these repo-local skills by default:

- `.agents/skills/execution-runtime`  
  Manager/worker execution lifecycle and worker adapter contracts.
- `.agents/skills/decision-policy`  
  Routing thresholds plus review pass/rework/fail decision policy.
- `.agents/skills/docker-auth-runtime`  
  Docker/auth mount conventions and runtime preflight checks.
- `.agents/skills/verification-gates`  
  Required test/validation gates for local checks and CI.

## Responsibilities
- **Manager** owns routing, assignment policy, and review outcomes.
- **Workers** produce implementation output plus evidence (tests/checks/logs).
- **Reviewer** blocks completion if acceptance criteria or quality gates fail.

## Change policy
- Do not bypass review gates for medium/large/high-risk tasks.
- Keep routing and review behavior config-driven where possible.
- Any policy change requires test updates in `tests/`.
