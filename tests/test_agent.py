import unittest

from agent.agent import Agent
from agent.context import AgentContext
from planner.planner import ExecutionPlan, PlanStep


class TestAgent(unittest.TestCase):
    def test_selects_knowledge_for_question_when_internet_unavailable(self):
        agent = Agent()
        context = AgentContext(
            user_command="Who invented Python?",
            intent="question",
            screen_available=False,
            internet_available=False,
            memory_available=False,
            knowledge_available=True,
            vision_available=False,
            automation_available=False,
        )

        decision = agent.decide(context)
        self.assertEqual(decision.selected_tool, "KnowledgeEngine")
        self.assertTrue(decision.priority > 0)
        self.assertFalse(decision.requires_confirmation)

    def test_selects_internet_for_search_intent(self):
        agent = Agent()
        context = AgentContext(
            user_command="Search for Python tutorials",
            intent="internet",
            screen_available=False,
            internet_available=True,
            memory_available=False,
            knowledge_available=False,
            vision_available=False,
            automation_available=False,
        )

        decision = agent.decide(context)
        self.assertEqual(decision.selected_tool, "InternetEngine")
        self.assertTrue(decision.requires_internet)

    def test_selects_memory_for_remember_command(self):
        agent = Agent()
        context = AgentContext(
            user_command="Remember this for later",
            intent="memory",
            screen_available=False,
            internet_available=False,
            memory_available=True,
            knowledge_available=True,
            vision_available=False,
            automation_available=False,
        )

        decision = agent.decide(context)
        self.assertEqual(decision.selected_tool, "MemoryEngine")
        self.assertTrue(decision.requires_memory)

    def test_uses_planner_for_multi_step_plan(self):
        agent = Agent()
        plan = ExecutionPlan(
            goal="open chrome and search python",
            steps=[
                PlanStep(id="1", tool="Chrome", action="Launch application", description="Launch Chrome.", expected_result="Chrome opens."),
                PlanStep(id="2", tool="search field", action="Type text", description="Type python.", expected_result="Typed python."),
            ],
        )
        context = AgentContext(
            user_command="Open Chrome and search Python",
            intent="unknown",
            screen_available=False,
            internet_available=True,
            memory_available=False,
            knowledge_available=True,
            vision_available=False,
            automation_available=True,
        )

        decision = agent.decide(context, plan=plan)
        self.assertEqual(decision.selected_tool, "PlannerEngine")
        self.assertFalse(decision.requires_confirmation)

    def test_resolves_single_step_plan_tool(self):
        agent = Agent()
        plan = ExecutionPlan(
            goal="open website example.com",
            steps=[
                PlanStep(id="1", tool="https://www.example.com", action="Open website", description="Open example.com.", expected_result="Website opens."),
            ],
        )
        context = AgentContext(
            user_command="Open website example.com",
            intent="unknown",
            screen_available=False,
            internet_available=True,
            memory_available=False,
            knowledge_available=False,
            vision_available=False,
            automation_available=True,
        )

        decision = agent.decide(context, plan=plan)
        self.assertEqual(decision.selected_tool, "DesktopController")


if __name__ == "__main__":
    unittest.main()
