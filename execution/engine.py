from __future__ import annotations
import time
from datetime import datetime
from typing import Any

from planner.planner import ExecutionPlan, PlanStep
from .executor import ExecutionStepExecutor
from .result import ExecutionResult


class ExecutionEngine:
    """Engine responsible for executing structured execution plans."""

    def __init__(self, step_executor: ExecutionStepExecutor | None = None) -> None:
        self.step_executor = step_executor or ExecutionStepExecutor()
        self._cancelled = False
        self._paused = False
        self._current_step_index = 0
        self._current_step: PlanStep | None = None

    def execute_plan(self, plan: ExecutionPlan, max_retries: int = 1) -> ExecutionResult:
        """Execute an ExecutionPlan step by step and return an ExecutionResult."""
        result = ExecutionResult()
        result.started_at = datetime.now()

        if not isinstance(plan, ExecutionPlan):
            result.add_log("Invalid execution plan provided.")
            result.finalize(success=False, error="Invalid execution plan.")
            return result

        result.add_log(f"Starting execution plan: {plan.goal}")

        for index, step in enumerate(plan.steps):
            if self._cancelled:
                result.add_log("Execution cancelled before step execution.")
                break

            while self._paused:
                result.add_log("Execution paused.")
                time.sleep(0.1)

            self._current_step_index = index
            self._current_step = step
            result.add_log(f"Executing step {index + 1}/{len(plan.steps)}: {step.action}")

            step_result = self._execute_step_with_retries(step, max_retries)
            if step_result.get("success"):
                result.completed_steps += 1
                result.add_log(f"Step succeeded: {step.action}")
                continue

            result.failed_step = step
            result.error = step_result.get("message") or "Step failed."
            result.add_log(f"Step failed: {step.action}. Error: {result.error}")

            if step.optional:
                result.add_log(f"Optional step failed; continuing execution: {step.action}")
                continue

            result.finalize(success=False, failed_step=step, error=result.error)
            return result

        if self._cancelled:
            result.finalize(success=False, error="Execution cancelled.")
            return result

        result.finalize(success=True, output="Execution completed successfully.")
        return result

    def _execute_step_with_retries(self, step: PlanStep, max_retries: int) -> dict[str, Any]:
        attempt = 0
        last_result: dict[str, Any] = {"success": False, "message": "No execution attempt made."}

        while attempt <= max_retries:
            attempt += 1
            last_result = self.step_executor.execute_step(step)
            if last_result.get("success"):
                return last_result
            if attempt <= max_retries:
                time.sleep(0.1)
        return last_result

    def retry_step(self, step: PlanStep, max_retries: int = 1) -> dict[str, Any]:
        """Retry a single failed step up to the provided retry limit."""
        return self._execute_step_with_retries(step, max_retries)

    def pause_execution(self) -> None:
        """Pause the currently running execution."""
        self._paused = True

    def resume_execution(self) -> None:
        """Resume a paused execution."""
        self._paused = False

    def cancel_execution(self) -> None:
        """Cancel the current execution flow."""
        self._cancelled = True

    @property
    def is_paused(self) -> bool:
        return self._paused

    @property
    def is_cancelled(self) -> bool:
        return self._cancelled

    @property
    def current_step(self) -> PlanStep | None:
        return self._current_step
