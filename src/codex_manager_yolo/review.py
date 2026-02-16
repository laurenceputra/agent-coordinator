from __future__ import annotations

from codex_manager_yolo.models import ReviewResult, WorkResult


BLINDSPOT_HINTS = (
    "no-tests-mentioned",
    "no-acceptance-criteria-reference",
    "worker-execution-failed",
)


def review_result(result: WorkResult) -> ReviewResult:
    findings: list[str] = []
    required_followups: list[str] = []

    if result.exit_code != 0:
        findings.append(BLINDSPOT_HINTS[2])
        required_followups.append("rerun-worker-after-fixing-execution-error")

    if "unit-tests" not in result.checks_run and result.assignment.tier in {"medium", "large"}:
        findings.append(BLINDSPOT_HINTS[0])
        required_followups.append("include-unit-tests")

    criteria = result.assignment.task.acceptance_criteria
    if criteria and not any(item.lower() in result.output.lower() for item in criteria):
        findings.append(BLINDSPOT_HINTS[1])
        required_followups.append("reference-acceptance-criteria")

    if not findings:
        return ReviewResult(task_id=result.assignment.task.task_id, decision="pass", findings=[])

    decision = "fail" if BLINDSPOT_HINTS[2] in findings else "rework"
    return ReviewResult(
        task_id=result.assignment.task.task_id,
        decision=decision,
        findings=findings,
        required_followups=required_followups,
    )
