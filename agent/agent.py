import os
import threading
import time
from typing import Any


class AgentEngine:
    """A reusable agent engine for coordinating multi-step task execution."""

    def __init__(self, tool_manager: Any, max_retries: int = 1) -> None:
        """Initialize the AgentEngine.

        Args:
            tool_manager: The shared ToolManager instance used for tool execution.
            max_retries: The number of recoverable retries per step.
        """
        self.tool_manager = tool_manager
        self.max_retries = max(0, int(max_retries))
        self._lock = threading.RLock()
        self._status = "idle"
        self._current_step: dict[str, Any] | None = None
        self._progress: dict[str, Any] = {
            "total_steps": 0,
            "completed_steps": 0,
            "failed_steps": 0,
            "skipped_steps": 0,
        }
        self._execution_summary: dict[str, Any] = {
            "goal": None,
            "steps": [],
            "errors": [],
            "status": self._status,
        }
        self._cancelled = False

    def execute_goal(self, goal: str) -> dict[str, Any]:
        """Execute a high-level user goal using the available tools."""
        if not isinstance(goal, str) or not goal.strip():
            return self._error("Goal must be a non-empty string.")

        with self._lock:
            self._reset_state(goal)
            self._status = "running"
            self._cancelled = False

        context = self._context_engine()
        if context:
            context.add_user_message(goal)
            context.set_goal(goal)
 
        workflow_response = self.tool_manager.execute("WorkflowEngine", "get_workflow", goal)
        if workflow_response.get("success") and workflow_response.get("result"):
            workflow_exec = self.tool_manager.execute("WorkflowEngine", "execute_workflow", goal)
            return workflow_exec
 
        plan_response = self.tool_manager.execute("PlannerEngine", "plan", goal)
        if not plan_response.get("success") or not plan_response.get("result"):
            knowledge_response = self.tool_manager.execute("KnowledgeEngine", "search", goal)
            self._finalize_summary("no plan available", knowledge_response)
            return knowledge_response
 
        plan = plan_response["result"]
        return self.execute_plan(plan)

    def execute_plan(self, plan: dict[str, Any]) -> dict[str, Any]:
        """Execute a structured plan step by step."""
        if not isinstance(plan, dict):
            return self._error("Plan must be a structured dictionary.")

        steps = plan.get("steps")
        if not isinstance(steps, list) or not steps:
            return self._error("Plan contains no executable steps.")

        with self._lock:
            self._cancelled = False
            self._status = "running"
            self._progress = {
                "total_steps": len(steps),
                "completed_steps": 0,
                "failed_steps": 0,
                "skipped_steps": 0,
            }
            self._execution_summary = {
                "goal": plan.get("goal"),
                "steps": [],
                "errors": [],
                "status": self._status,
            }

        context = self._context_engine()
        if context:
            context.set_goal(plan.get("goal", ""))

        for index, step in enumerate(steps, start=1):
            with self._lock:
                if self._cancelled:
                    self._status = "cancelled"
                    break
                self._current_step = {"index": index, **step}

            pending_message = step.get("description") or step.get("action")
            if context and pending_message:
                context.add_pending_task(pending_message)

            result = self.execute_step(step)
            if not result.get("success"):
                result = self.retry_step(step)

            if not result.get("success"):
                if self._is_recoverable_failure(result):
                    self._record_step_state(step, result, "skipped")
                    with self._lock:
                        self._progress["skipped_steps"] += 1
                    continue
                self._record_step_state(step, result, "failed")
                self._progress["failed_steps"] += 1
                self._status = "failed"
                self._finalize_summary("critical failure", result)
                return result

            self._record_step_state(step, result, "success")
            with self._lock:
                self._progress["completed_steps"] += 1

            if context and pending_message:
                context.complete_task(pending_message)

            memory = self._memory_engine()
            if memory and hasattr(memory, "remember_fact"):
                try:
                    memory.remember_fact("last executed task", pending_message)
                except Exception:
                    pass

        with self._lock:
            if self._cancelled:
                self._status = "cancelled"
            elif self._status != "failed":
                self._status = "completed"
            self._execution_summary["status"] = self._status

        final_message = self._build_final_message()
        summary = self.get_execution_summary()
        return self._success("execute_plan", final_message, result=summary)

    def execute_step(self, step: dict[str, Any]) -> dict[str, Any]:
        """Execute a single plan step using the appropriate tool."""
        if not isinstance(step, dict):
            return self._error("Step must be a structured dictionary.")

        action = (step.get("action") or "").strip().lower()
        target = step.get("target")
        description = step.get("description") or action

        if action in ("launch application", "open application"):
            return self.tool_manager.execute("AutomationEngine", "open_application", target)

        if action == "open website":
            return self.tool_manager.execute("AutomationEngine", "open_website", target)

        if action == "wait":
            return self.tool_manager.execute("AutomationEngine", "wait", str(target))

        if action in ("type text", "type"):
            return self.tool_manager.execute("AutomationEngine", "type_text", target)

        if action in ("press key", "press"):
            return self.tool_manager.execute("AutomationEngine", "press_key", target)

        if action == "hotkey":
            if isinstance(target, str):
                keys = [key.strip() for key in target.split("+") if key.strip()]
                return self.tool_manager.execute("AutomationEngine", "hotkey", *keys)
            return self._error("Invalid hotkey target.")

        if action == "move mouse":
            if isinstance(target, str) and "," in target:
                x, y = [value.strip() for value in target.split(",", 1)]
                return self.tool_manager.execute("AutomationEngine", "move_mouse", x, y)
            return self._error("Invalid mouse coordinates.")

        if action == "click mouse":
            button = "left"
            x = y = None
            if isinstance(target, str) and "," in target:
                x, y = [value.strip() for value in target.split(",", 1)]
            return self.tool_manager.execute("AutomationEngine", "click_mouse", button, x, y)

        if action == "scroll":
            return self.tool_manager.execute("AutomationEngine", "scroll", str(target))

        if action in ("capture screen", "analyze image", "return summary"):
            return self.tool_manager.execute("Vision", "read_screen")

        if action in ("open folder", "sort files", "move files", "review result", "review"):
            return self._success("execute_step", f"Recorded step: {description}.")

        if action == "create folder":
            return self._create_folder(target)

        return self._success("execute_step", f"No executable tool mapped for step: {description}.")

    def retry_step(self, step: dict[str, Any]) -> dict[str, Any]:
        """Retry a step once when the first attempt fails."""
        if not isinstance(step, dict):
            return self._error("Step must be a structured dictionary.")

        retries = step.get("_retries", 0)
        if retries >= self.max_retries:
            return self._error("Step retry limit reached.")

        step["_retries"] = retries + 1
        return self.execute_step(step)

    def cancel(self) -> dict[str, Any]:
        """Cancel the current execution."""
        with self._lock:
            self._cancelled = True
            self._status = "cancelled"
        return self._success("cancel", "Agent execution cancelled.")

    def get_status(self) -> dict[str, Any]:
        """Return the current execution status."""
        with self._lock:
            return self._success("get_status", "Execution status retrieved.", result=self._status)

    def get_current_step(self) -> dict[str, Any]:
        """Return the currently active step."""
        with self._lock:
            return self._success("get_current_step", "Current step retrieved.", result=self._current_step)

    def get_progress(self) -> dict[str, Any]:
        """Return execution progress statistics."""
        with self._lock:
            return self._success("get_progress", "Execution progress retrieved.", result=dict(self._progress))

    def get_execution_summary(self) -> dict[str, Any]:
        """Return the final execution summary."""
        with self._lock:
            return self._success("get_execution_summary", "Execution summary retrieved.", result=dict(self._execution_summary))

    def _create_folder(self, target: Any) -> dict[str, Any]:
        if not isinstance(target, str) or not target.strip():
            return self._error("Folder name must be a non-empty string.")
        try:
            path = os.path.abspath(target.strip())
            os.makedirs(path, exist_ok=True)
            return self._success("create_folder", f"Created folder: {path}.", result=path)
        except Exception as exc:
            return self._error("Failed to create folder.", details=str(exc))

    def _is_recoverable_failure(self, result: dict[str, Any]) -> bool:
        if result.get("success"):
            return False
        details = (result.get("details") or "").lower()
        if "not available" in details or "not supported" in details:
            return True
        if "failed" in details or "unable" in details:
            return True
        return False

    def _build_final_message(self) -> str:
        if self._status == "completed":
            return "Task execution completed successfully."
        if self._status == "cancelled":
            return "Task execution was cancelled."
        return "Task execution stopped due to a critical failure."

    def _record_step_state(self, step: dict[str, Any], result: dict[str, Any], status: str) -> None:
        with self._lock:
            self._execution_summary["steps"].append(
                {
                    "step": step,
                    "result": result,
                    "status": status,
                }
            )
            if not result.get("success"):
                self._execution_summary["errors"].append(
                    {
                        "step": step,
                        "error": result.get("message"),
                        "details": result.get("details"),
                    }
                )

    def _reset_state(self, goal: str) -> None:
        self._current_step = None
        self._progress = {
            "total_steps": 0,
            "completed_steps": 0,
            "failed_steps": 0,
            "skipped_steps": 0,
        }
        self._execution_summary = {
            "goal": goal,
            "steps": [],
            "errors": [],
            "status": "running",
        }

    def _finalize_summary(self, status: str, info: Any) -> None:
        with self._lock:
            self._execution_summary["status"] = status
            self._execution_summary["result"] = info

    def _context_engine(self) -> Any | None:
        return self.tool_manager.get_tool("ContextEngine")

    def _memory_engine(self) -> Any | None:
        return self.tool_manager.get_tool("MemoryEngine")

    def _success(self, action: str, message: str, result: Any | None = None) -> dict[str, Any]:
        response = {"success": True, "action": action, "message": message}
        if result is not None:
            response["result"] = result
        return response

    def _error(self, message: str, details: str | None = None) -> dict[str, Any]:
        response = {"success": False, "action": "error", "message": message}
        if details is not None:
            response["details"] = details
        return response
