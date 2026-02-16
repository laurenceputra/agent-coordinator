from codex_manager_yolo.models import Assignment, TaskSpec, WorkResult
from codex_manager_yolo.review import review_result


def _assignment(tier: str = "medium") -> Assignment:
    task = TaskSpec(task_id="1", summary="task", estimated_hours=2, changed_file_count=3, risk_level=1)
    return Assignment(
        task=task,
        worker_type="copilot-cli",
        worker_model="copilot",
        worker_profile="gpt-5.2-xhigh",
        tier=tier,
        score=5,
    )


def test_review_flags_missing_tests_for_medium() -> None:
    result = WorkResult(assignment=_assignment(), output="done", checks_run=["lint"], exit_code=0)
    review = review_result(result)
    assert review.decision == "rework"
    assert "no-tests-mentioned" in review.findings


def test_review_fails_worker_execution_errors() -> None:
    result = WorkResult(assignment=_assignment(), output="", checks_run=["lint"], exit_code=1, stderr="boom")
    review = review_result(result)
    assert review.decision == "fail"
    assert "worker-execution-failed" in review.findings


def test_review_passes_when_checks_and_criteria_present() -> None:
    task = TaskSpec(
        task_id="2",
        summary="task",
        estimated_hours=2,
        changed_file_count=3,
        risk_level=1,
        acceptance_criteria=["timeout"],
    )
    assignment = Assignment(
        task=task,
        worker_type="copilot-cli",
        worker_model="copilot",
        worker_profile="gpt-5.2-xhigh",
        tier="medium",
        score=5,
    )
    result = WorkResult(
        assignment=assignment,
        output="includes timeout handling",
        checks_run=["lint", "unit-tests"],
        exit_code=0,
    )
    review = review_result(result)
    assert review.passed
