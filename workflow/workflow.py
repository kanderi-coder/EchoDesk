import json
import os
import threading
from typing import Any, Iterable


class WorkflowEngine:
    """A reusable workflow engine for EchoDesk.

    WorkflowEngine manages user-defined workflows, persists them to JSON,
    and executes workflow steps through AgentEngine.
    """

    def __init__(self, tool_manager: Any, storage_path: str | None = None) -> None:
        """Initialize the workflow engine.

        Args:
            tool_manager: The ToolManager instance used to locate AgentEngine.
            storage_path: Optional path to persist workflows.
        """
        self._lock = threading.RLock()
        self.tool_manager = tool_manager
        self.storage_path = storage_path or os.path.join(os.path.dirname(__file__), "workflows.json")
        self._workflows: dict[str, dict[str, Any]] = {}
        self._load_workflows()

    def create_workflow(self, name: str, description: str, steps: list[str]) -> dict[str, Any]:
        """Create and persist a new workflow."""
        if not self._validate_name(name):
            return self._error("Workflow name must be a non-empty string.")

        if self._workflow_exists(name):
            return self._error("Workflow already exists.", details=f"A workflow named '{name}' already exists.")

        if not self._validate_steps(steps):
            return self._error("Workflow steps must be a non-empty list of strings.")

        workflow = {
            "name": name.strip(),
            "description": description.strip() if isinstance(description, str) else "",
            "steps": [step.strip() for step in steps],
        }

        with self._lock:
            self._workflows[name.strip()] = workflow
            save_result = self._save_workflows()

        if not save_result.get("success"):
            return save_result

        return self._success("create_workflow", f"Workflow '{name}' created.", result=workflow)

    def update_workflow(self, name: str, steps: list[str]) -> dict[str, Any]:
        """Update the steps of a saved workflow."""
        if not self._validate_name(name):
            return self._error("Workflow name must be a non-empty string.")

        if not self._validate_steps(steps):
            return self._error("Workflow steps must be a non-empty list of strings.")

        normalized_name = self._normalize_name(name)
        with self._lock:
            workflow = self._find_workflow(normalized_name)
            if workflow is None:
                return self._error("Workflow not found.", details=f"No workflow named '{name}' exists.")
            workflow["steps"] = [step.strip() for step in steps]
            save_result = self._save_workflows()

        if not save_result.get("success"):
            return save_result

        return self._success("update_workflow", f"Workflow '{workflow['name']}' updated.", result=workflow)

    def delete_workflow(self, name: str) -> dict[str, Any]:
        """Delete a saved workflow."""
        if not self._validate_name(name):
            return self._error("Workflow name must be a non-empty string.")

        normalized_name = self._normalize_name(name)
        with self._lock:
            workflow_key = self._find_workflow_key(normalized_name)
            if workflow_key is None:
                return self._error("Workflow not found.", details=f"No workflow named '{name}' exists.")
            del self._workflows[workflow_key]
            save_result = self._save_workflows()

        if not save_result.get("success"):
            return save_result

        return self._success("delete_workflow", f"Workflow '{name}' deleted.")

    def list_workflows(self) -> dict[str, Any]:
        """List all saved workflows."""
        with self._lock:
            workflows = [
                {
                    "name": workflow["name"],
                    "description": workflow["description"],
                    "steps": list(workflow["steps"]),
                }
                for workflow in self._workflows.values()
            ]
        return self._success("list_workflows", "Workflows retrieved.", result=workflows)

    def get_workflow(self, name: str) -> dict[str, Any]:
        """Return a saved workflow by name."""
        if not self._validate_name(name):
            return self._error("Workflow name must be a non-empty string.")

        workflow = self._find_workflow(self._normalize_name(name))
        if workflow is None:
            return self._error("Workflow not found.", details=f"No workflow named '{name}' exists.")
        return self._success("get_workflow", f"Workflow '{workflow['name']}' retrieved.", result=workflow.copy())

    def execute_workflow(self, name: str) -> dict[str, Any]:
        """Execute a saved workflow through the AgentEngine."""
        if not self._validate_name(name):
            return self._error("Workflow name must be a non-empty string.")

        workflow = self._find_workflow(self._normalize_name(name))
        if workflow is None:
            return self._error("Workflow not found.", details=f"No workflow named '{name}' exists.")

        agent_engine = self.tool_manager.get_tool("AgentEngine")
        if agent_engine is None:
            return self._error("AgentEngine is not available.")

        plan = {
            "goal": workflow["name"],
            "reasoning": workflow["description"],
            "steps": [self._translate_workflow_step(step) for step in workflow["steps"]],
            "estimated_complexity": "medium",
            "required_tools": ["automation"],
            "expected_result": f"Workflow '{workflow['name']}' executed.",
        }

        return agent_engine.execute_plan(plan)

    def export_workflow(self, path: str) -> dict[str, Any]:
        """Export all saved workflows to a JSON file."""
        if not isinstance(path, str) or not path.strip():
            return self._error("Export path must be a non-empty string.")

        try:
            directory = os.path.dirname(os.path.abspath(path))
            if directory and not os.path.isdir(directory):
                os.makedirs(directory, exist_ok=True)
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(list(self._workflows.values()), handle, indent=2)
            return self._success("export_workflow", f"Workflows exported to {path}.")
        except Exception as exc:
            return self._error("Failed to export workflows.", details=str(exc))

    def import_workflow(self, path: str) -> dict[str, Any]:
        """Import workflows from a JSON file."""
        if not isinstance(path, str) or not path.strip():
            return self._error("Import path must be a non-empty string.")

        if not os.path.isfile(path):
            return self._error("Import file not found.", details=f"File '{path}' does not exist.")

        try:
            with open(path, "r", encoding="utf-8") as handle:
                content = json.load(handle)
        except Exception as exc:
            return self._error("Failed to load import file.", details=str(exc))

        imported = []
        if isinstance(content, dict):
            workflows = [content]
        elif isinstance(content, list):
            workflows = content
        else:
            return self._error("Invalid workflow import format.")

        with self._lock:
            for workflow in workflows:
                if not isinstance(workflow, dict):
                    continue
                name = workflow.get("name")
                if not self._validate_name(name):
                    continue
                if self._workflow_exists(name):
                    continue
                steps = workflow.get("steps")
                if not self._validate_steps(steps):
                    continue
                description = workflow.get("description", "")
                self._workflows[name.strip()] = {
                    "name": name.strip(),
                    "description": description.strip() if isinstance(description, str) else "",
                    "steps": [step.strip() for step in steps],
                }
                imported.append(name.strip())
            save_result = self._save_workflows()

        if not save_result.get("success"):
            return save_result

        return self._success(
            "import_workflow",
            f"Imported {len(imported)} workflows.",
            result={"imported": imported},
        )

    def _load_workflows(self) -> dict[str, Any]:
        with self._lock:
            if not os.path.isfile(self.storage_path):
                self._workflows = {}
                return self._success("load_workflows", "No existing workflows found.")

            try:
                with open(self.storage_path, "r", encoding="utf-8") as handle:
                    raw = json.load(handle)
                if isinstance(raw, list):
                    self._workflows = {workflow.get("name", ""): workflow for workflow in raw if isinstance(workflow, dict) and workflow.get("name")}
                elif isinstance(raw, dict):
                    self._workflows = {workflow.get("name", ""): workflow for workflow in raw.values() if isinstance(workflow, dict) and workflow.get("name")}
                else:
                    self._workflows = {}
            except Exception:
                self._workflows = {}
            return self._success("load_workflows", "Workflows loaded.")

    def _save_workflows(self) -> dict[str, Any]:
        try:
            with open(self.storage_path, "w", encoding="utf-8") as handle:
                json.dump(list(self._workflows.values()), handle, indent=2)
            return self._success("save_workflows", "Workflows saved.")
        except Exception as exc:
            return self._error("Failed to save workflows.", details=str(exc))

    def _workflow_exists(self, name: str) -> bool:
        return self._find_workflow(self._normalize_name(name)) is not None

    def _normalize_name(self, name: str) -> str:
        return name.strip().lower() if isinstance(name, str) else ""

    def _find_workflow(self, normalized_name: str) -> dict[str, Any] | None:
        if not normalized_name:
            return None
        for workflow in self._workflows.values():
            if workflow["name"].strip().lower() == normalized_name:
                return workflow
        return None

    def _find_workflow_key(self, normalized_name: str) -> str | None:
        if not normalized_name:
            return None
        for workflow_name in self._workflows.keys():
            if workflow_name.strip().lower() == normalized_name:
                return workflow_name
        return None

    def _validate_name(self, name: Any) -> bool:
        return isinstance(name, str) and bool(name.strip())

    def _validate_steps(self, steps: Any) -> bool:
        if not isinstance(steps, list) or not steps:
            return False
        return all(isinstance(step, str) and step.strip() for step in steps)

    def _translate_workflow_step(self, step: str) -> dict[str, Any]:
        normalized = step.strip()
        action = normalized
        target = None

        if not normalized:
            return {"action": action, "target": target, "description": normalized}

        lower = normalized.lower()
        if lower.startswith("open ") or lower.startswith("launch ") or lower.startswith("start "):
            target = normalized.split(" ", 1)[1].strip()
            if "github" in lower and "open" in lower:
                action = "open website"
                target = "https://github.com"
            elif "outlook" in lower and "open" in lower:
                action = "open website"
                target = "https://outlook.office.com"
            else:
                action = "launch application"
        elif lower.startswith("wait "):
            action = "wait"
            target = normalized.split(" ", 1)[1].strip()
        elif lower.startswith("type ") or lower.startswith("type:"):
            action = "type text"
            target = normalized.split(" ", 1)[1].strip()
        elif lower.startswith("press "):
            action = "press key"
            target = normalized.split(" ", 1)[1].strip()
        else:
            action = normalized

        return {"action": action, "target": target, "description": normalized}

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
