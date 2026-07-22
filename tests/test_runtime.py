import unittest
from types import SimpleNamespace

from runtime.runtime import RuntimeEngine
from planner.planner import ExecutionPlan, PlanStep


class DummyExecutionEngine:
    def execute_plan(self, plan):
        return SimpleNamespace(success=True, output="executed")


class FailingExecutionEngine:
    def execute_plan(self, plan):
        raise RuntimeError("Failure during execution")


class TestRuntimeEngine(unittest.TestCase):
    def test_execute_route_executes_plan_with_execution_engine(self):
        runtime = RuntimeEngine()
        runtime.tool_manager.register_tool("ExecutionEngine", DummyExecutionEngine())

        plan = ExecutionPlan(
            goal="test",
            steps=[
                PlanStep(
                    id="1",
                    tool="test",
                    action="Action",
                    description="Description",
                    expected_result="Expected",
                )
            ],
        )
        route_payload = {"route": "execute_plan", "plan": plan}
        response = runtime._execute_route("test", route_payload)

        self.assertEqual(response, "executed")

    def test_execute_route_returns_missing_engine_message(self):
        runtime = RuntimeEngine()
        runtime.tool_manager.unregister_tool("ExecutionEngine")
        route_payload = {"route": "execute_plan", "plan": {}}

        self.assertEqual(runtime._execute_route("test", route_payload), "Execution engine is not available.")

    def test_execute_route_returns_no_plan_message(self):
        runtime = RuntimeEngine()
        runtime.tool_manager.register_tool("ExecutionEngine", DummyExecutionEngine())

        response = runtime._execute_route("test", {"route": "execute_plan", "plan": None})
        self.assertEqual(response, "No execution plan was provided.")

    def test_execute_route_handles_execution_exception_gracefully(self):
        runtime = RuntimeEngine()
        runtime.tool_manager.register_tool("ExecutionEngine", FailingExecutionEngine())

        plan = ExecutionPlan(goal="test", steps=[])
        response = runtime._execute_route("test", {"route": "execute_plan", "plan": plan})

        self.assertIn("Execution failed with an exception", response)


if __name__ == "__main__":
    unittest.main()
