import datetime
import threading
import traceback
from typing import Any

from brain.router import Router
from context.context import get_context_engine
from memory.memory import Memory
from tools.manager import ToolManager


class RuntimeEngine:
    """Runtime engine for the EchoDesk application.

    RuntimeEngine initializes the tool ecosystem and drives the main command
    loop from stdin. It integrates routing, execution, context, memory, and
    workflow tools while protecting the runtime from crashes.
    """

    SPECIAL_COMMANDS = {
        "exit": "Exit the runtime.",
        "quit": "Exit the runtime.",
        "help": "Show available runtime commands.",
        "tools": "List registered tools.",
        "status": "Show runtime status summary.",
        "history": "Show recent conversation history.",
    }

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._start_time = datetime.datetime.now()
        self.router = Router()
        self.task_executor = self.router.executor
        self.tool_manager = self.task_executor.tool_manager
        self.intent_engine = self.task_executor.intent_engine
        self.context_engine = get_context_engine()
        self.memory_engine = self.tool_manager.get_tool("MemoryEngine")
        self.knowledge_engine = self.tool_manager.get_tool("KnowledgeEngine")
        self.internet_engine = self.tool_manager.get_tool("InternetEngine")
        self.planner_engine = self.tool_manager.get_tool("PlannerEngine")
        self.agent_engine = self.tool_manager.get_tool("AgentEngine")
        self.workflow_engine = self.tool_manager.get_tool("WorkflowEngine")
        self.automation_engine = self.tool_manager.get_tool("AutomationEngine")
        self.desktop_controller = self.tool_manager.get_tool("DesktopController")
        self.vision_tool = self.tool_manager.get_tool("Vision")
        self.memory_history = Memory()
        self._running = False

    def start(self) -> None:
        """Start the EchoDesk runtime loop."""
        self._running = True
        self._start_time = datetime.datetime.now()
        print("EchoDesk Runtime started. Type 'help' for available commands.")

        while self._running:
            try:
                command = input("EchoDesk> ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nExiting EchoDesk Runtime.")
                break

            if not command:
                continue

            try:
                lowered = command.strip().lower()

                if lowered in ("exit", "quit"):
                    print("Exiting EchoDesk Runtime.")
                    break

                if lowered == "help":
                    print(self._help_text())
                    continue

                if lowered == "tools":
                    self._print_tools()
                    continue

                if lowered == "status":
                    self._print_status()
                    continue

                if lowered == "history":
                    self._print_history()
                    continue

                self._process_command(command)
            except Exception as exc:
                print("An unexpected error occurred while processing the command.")
                print(str(exc))
                traceback.print_exc()

        self._running = False

    def _process_command(self, command: str) -> None:
        """Process a user command through the established EchoDesk flow."""
        with self._lock:
            route = self.router.route(command)
            response = self._execute_route(command, route)
            self._update_memory_engine(command, response)
            self._update_context_with_response(response)

            print(response)
            print(f"[route={route}]")

    def _update_memory_engine(self, command: str, response: Any) -> None:
        if self.memory_engine is None:
            return

        try:
            if hasattr(self.memory_engine, "remember_fact"):
                self.memory_engine.remember_fact("last user command", command)
                self.memory_engine.remember_fact("last assistant response", str(response))
        except Exception:
            pass

    def _update_context_with_response(self, response: Any) -> None:
        try:
            if self.context_engine is not None and isinstance(response, str):
                self.context_engine.add_assistant_message(response)
        except Exception:
            pass

    def _execute_route(self, command: str, route: str) -> str:
        try:
            if isinstance(route, dict) and route.get("route") == "execute_plan":
                return self._execute_plan(route.get("plan"))

            if route == "greeting":
                return "Hello! I am EchoDesk. How can I help you?"

            if route == "time":
                now = datetime.datetime.now()
                return f"The current time is {now.strftime('%H:%M:%S')}"

            if route == "history":
                try:
                    conversations = self.memory_history.recall()
                    return f"I remember {len(conversations)} conversations."
                except Exception:
                    return "I could not retrieve conversation history right now."

            if route == "screenshot":
                screenshot_result = self.tool_manager.execute("DesktopController", "take_screenshot")
                if screenshot_result.get("success"):
                    return screenshot_result.get("message", "Screenshot taken.")
                return screenshot_result.get("message", "Unable to take a screenshot.")

            if route == "vision":
                vision_result = self.tool_manager.execute("Vision", "read_screen")
                if vision_result.get("success"):
                    result_value = vision_result.get("result")
                    return result_value if isinstance(result_value, str) else vision_result.get("message", "Vision result available.")
                return vision_result.get("message", "Unable to read the screen.")

            if route == "knowledge":
                knowledge_result = self.knowledge_engine.search(command)
                if knowledge_result is not None:
                   if isinstance(knowledge_result, dict):
                       return knowledge_result.get("message", str(knowledge_result))
                   return str(knowledge_result)

                internet_result = self.internet_engine.search(command)
                return str(internet_result)

            return "I don't understand that request yet."
        except Exception as exc:
            return f"An error occurred while executing the request: {exc}"

    def _execute_plan(self, plan: Any) -> str:
       """Execute an ExecutionPlan using the shared ExecutionEngine."""
       if plan is None:
           return "No execution plan was provided."

       execution_engine = self.tool_manager.get_tool("ExecutionEngine")
       if execution_engine is None:
           return "Execution engine is not available."

       try:
           result = execution_engine.execute_plan(plan)
           if hasattr(result, "success") and result.success:
               if result.output is not None:
                   return str(result.output)
               return "Execution completed successfully."

           error_message = getattr(result, "error", None)
           if error_message:
               return f"Execution failed: {error_message}"
           return "Execution failed due to an unknown error."
       except Exception as exc:
           return f"Execution failed with an exception: {type(exc).__name__}: {exc}"

    def _help_text(self) -> str:
        lines = ["EchoDesk Runtime commands:"]
        for name, desc in self.SPECIAL_COMMANDS.items():
            lines.append(f"  {name}: {desc}")
        lines.append("  Any other text is treated as a user command.")
        return "\n".join(lines)

    def _print_tools(self) -> None:
        tools = self.tool_manager.list_tools() if self.tool_manager else []
        print("Registered tools:")
        for tool in tools:
            print(f"  - {tool}")

    def _print_history(self) -> None:
        if self.context_engine is None:
            print("No context engine available.")
            return

        history_result = self.context_engine.get_recent_history()
        history = history_result.get("result") if isinstance(history_result, dict) else []
        if not history:
            print("No conversation history available.")
            return

        print("Recent history:")
        for entry in history:
            time_text = entry.get("time", "")
            role = entry.get("role", "unknown")
            message = entry.get("message", "")
            print(f"  [{time_text}] {role}: {message}")

    def _print_status(self) -> None:
        status = self.get_status_summary()
        print("EchoDesk Runtime Status:")
        print(f"  Uptime: {status.get('uptime', 'unknown')}")
        print(f"  Loaded engines: {', '.join(status.get('loaded_engines', []))}")
        print(f"  Registered tools: {', '.join(status.get('registered_tools', []))}")
        print(f"  Memory facts: {status.get('memory_facts', 0)}")
        print(f"  Workflow count: {status.get('workflow_count', 0)}")
        print(f"  Current goal: {status.get('current_goal', 'none')}")
        print(f"  Pending tasks: {status.get('pending_tasks', [])}")
        print(f"  Completed tasks: {status.get('completed_tasks', [])}")
        print(f"  Active application: {status.get('active_application', 'none')}")
        print(f"  Active document: {status.get('active_document', 'none')}")

    def get_status_summary(self) -> dict[str, Any]:
        with self._lock:
            uptime = datetime.datetime.now() - self._start_time
            memory_facts = self._count_memory_facts()
            workflow_count = self._count_workflows()
            context_summary = self._context_summary()
            tools = self.tool_manager.list_tools() if self.tool_manager else []
            return {
                "uptime": str(uptime).split(".")[0],
                "loaded_engines": [
                    "Router",
                    "IntentEngine",
                    "ContextEngine",
                    "MemoryEngine",
                    "KnowledgeEngine",
                    "InternetEngine",
                    "PlannerEngine",
                    "ExecutionEngine",
                    "AgentEngine",
                    "WorkflowEngine",
                    "AutomationEngine",
                    "DesktopController",
                    "Vision",
                    "ToolManager",
                ],
                "registered_tools": tools,
                "memory_facts": memory_facts,
                "workflow_count": workflow_count,
                **context_summary,
            }

    def _count_memory_facts(self) -> int:
        if self.memory_engine is None:
            return 0
        try:
            facts = getattr(self.memory_engine, "_payload", {}).get("facts")
            return len(facts) if isinstance(facts, list) else 0
        except Exception:
            return 0

    def _count_workflows(self) -> int:
        if self.workflow_engine is None:
            return 0
        try:
            workflow_result = self.workflow_engine.list_workflows()
            workflows = workflow_result.get("result") if isinstance(workflow_result, dict) else []
            return len(workflows) if isinstance(workflows, list) else 0
        except Exception:
            return 0

    def _context_summary(self) -> dict[str, Any]:
        if self.context_engine is None:
            return {
                "current_goal": "none",
                "pending_tasks": [],
                "completed_tasks": [],
                "active_application": "none",
                "active_document": "none",
            }

        try:
            goal = self.context_engine.get_goal().get("result")
            pending = self.context_engine.get_pending_tasks().get("result")
            completed = self.context_engine.get_completed_tasks().get("result")
            active_app = self.context_engine.get_active_application().get("result")
            active_doc = self.context_engine.get_active_document().get("result")
            return {
                "current_goal": goal or "none",
                "pending_tasks": pending or [],
                "completed_tasks": completed or [],
                "active_application": active_app or "none",
                "active_document": active_doc or "none",
            }
        except Exception:
            return {
                "current_goal": "none",
                "pending_tasks": [],
                "completed_tasks": [],
                "active_application": "none",
                "active_document": "none",
            }


if __name__ == "__main__":
    RuntimeEngine().start()
