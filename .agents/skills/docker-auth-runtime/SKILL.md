---
name: docker-auth-runtime
description: Use when changing Docker/compose setup, authentication directory mounts, and runtime preflight checks for manager and workers.
---

# Docker Auth Runtime

## Use this skill when
- Editing Dockerfile or docker-compose services.
- Changing auth mount behavior for GH/Codex/Copilot.
- Adding runtime startup checks.

## Required mount policy
- Mount host auth directories read-only when feasible.
- Validate presence of required auth paths at startup.
- Fail with actionable error if required auth directories are missing.

## Required runtime checks
- Confirm required CLIs are installed and discoverable in PATH.
- Print versions for manager, codex, and copilot tools.
- Surface mount status without exposing sensitive file contents.
