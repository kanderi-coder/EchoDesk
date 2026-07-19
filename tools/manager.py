import importlib
from typing import Any


class VisionTool:
    """A simple vision tool wrapper for EchoDesk."""

    def __init__(self) -> None:
        self.capture = None
        self.reader = None
        self.analyzer = None

    def read_screen(self) -> dict[str, Any]:
        """Capture and analyze the screen contents."""
        try:
            if self.capture is None:
                vision_capture = importlib.import_module("vision.capture")
                self.capture = vision_capture.ScreenCapture()

            if self.reader is None:
                vision_reader = importlib.import_module("vision.reader")
                self.reader = vision_reader.ScreenReader()

            if self.analyzer is None:
                vision_analyzer = importlib.import_module("vision.analyzer")
                self.analyzer = vision_analyzer.ScreenAnalyzer()

            screenshot_path = self.capture.take_screenshot()
            text = self.reader.read_image(screenshot_path)
            summary = self.analyzer.analyze(text)
            return {
                "success": True,
                "action": "read_screen",
                "message": "Screen read successfully.",
                "result": summary,
            }
        except Exception as exc:
            return {
                "success": False,
                "action": "read_screen",
                "message": "Unable to read the screen.",
                "details": str(exc),
            }


class ToolManager:
    """Dynamic tool registry and executor for EchoDesk."""

    def __init__(self) -> None:
        self._tools: dict[str, Any] = {}

    def register_tool(self, name: str, tool: Any) -> dict[str, Any]:
        """Register a tool by name."""
        if not isinstance(name, str) or not name.strip():
            return self._error("Tool name must be a non-empty string.")

        self._tools[name] = tool
        return self._success("register_tool", f"Tool '{name}' registered.")

    def unregister_tool(self, name: str) -> dict[str, Any]:
        """Remove a tool from the registry."""
        if name in self._tools:
            del self._tools[name]
            return self._success("unregister_tool", f"Tool '{name}' unregistered.")

        return self._error("Tool not found.", details=f"Tool '{name}' does not exist.")

    def get_tool(self, name: str) -> Any | None:
        """Return a registered tool object by name."""
        return self._tools.get(name)

    def list_tools(self) -> list[str]:
        """Return the names of all registered tools."""
        return sorted(self._tools.keys())

    def execute(self, tool_name: str, method_name: str, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Execute a method on a registered tool by reflection."""
        tool = self.get_tool(tool_name)
        if tool is None:
            return self._error("Tool not available.", details=f"Tool '{tool_name}' is not registered.")

        method = getattr(tool, method_name, None)
        if not callable(method):
            return self._error(
                "Tool method not available.",
                details=f"Method '{method_name}' not found on tool '{tool_name}'.",
            )

        try:
            result = method(*args, **kwargs)
            if isinstance(result, dict) and "success" in result:
                return result
            return {
                "success": True,
                "action": f"{tool_name}.{method_name}",
                "result": result,
            }
        except Exception as exc:
            return self._error(
                "Tool execution failed.",
                details=f"{tool_name}.{method_name} raised: {type(exc).__name__}: {exc}",
            )

    def register_default_tools(self) -> dict[str, Any]:
        """Register EchoDesk's initial tool set."""
        try:
            memory_module = importlib.import_module("memory_engine.memory_engine")
            knowledge_module = importlib.import_module("knowledge.knowledge")
            internet_module = importlib.import_module("internet.internet")
            planner_module = importlib.import_module("planner.planner")
            automation_module = importlib.import_module("automation.automation")
            desktop_module = importlib.import_module("desktop.controller")
            context_module = importlib.import_module("context.context")
            agent_module = importlib.import_module("agent.agent")
            workflow_module = importlib.import_module("workflow.workflow")

            self.register_tool("MemoryEngine", memory_module.MemoryEngine())
            self.register_tool("KnowledgeEngine", knowledge_module.KnowledgeEngine())
            self.register_tool("InternetEngine", internet_module.InternetEngine())
            automation_tool = automation_module.AutomationEngine()
            self.register_tool("AutomationEngine", automation_tool)
            self.register_tool("PlannerEngine", planner_module.PlannerEngine(automation_tool))
            self.register_tool("DesktopController", desktop_module.DesktopController())
            self.register_tool("ContextEngine", context_module.get_context_engine())
            self.register_tool("WorkflowEngine", workflow_module.WorkflowEngine(self))
            self.register_tool("AgentEngine", agent_module.AgentEngine(self))
            self.register_tool("Vision", VisionTool())

            return self._success("register_default_tools", "Default tools registered.")
        except Exception as exc:
            return self._error("Failed to register default tools.", details=str(exc))

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
