import unittest
from unittest.mock import MagicMock

from desktop.controller import DesktopController
from desktop.workflow import DesktopWorkflow


class TestDesktopWorkflow(unittest.TestCase):
    def test_available_actions_returns_supported_action_list(self):
        workflow = DesktopWorkflow(controller=MagicMock())

        actions = workflow.available_actions()

        self.assertIn("open_application", actions)
        self.assertIn("wait", actions)
        self.assertIn("copy_clipboard", actions)

    def test_execute_runs_actions_in_order(self):
        mock_controller = MagicMock()
        mock_controller.open_application.return_value = {"success": True, "action": "open_application"}
        mock_controller.type_text.return_value = {"success": True, "action": "type_text"}
        mock_controller.set_clipboard.return_value = {"success": True, "action": "set_clipboard"}

        workflow = DesktopWorkflow(controller=mock_controller)
        actions = [
            {"action": "open_application", "name": "notepad"},
            {"action": "type_text", "text": "Hello"},
            {"action": "set_clipboard", "text": "EchoDesk"},
        ]

        result = workflow.execute(actions)

        self.assertTrue(result["success"])
        self.assertEqual(result["completed"], 3)
        self.assertEqual(len(result["results"]), 3)
        mock_controller.open_application.assert_called_once_with("notepad")
        mock_controller.type_text.assert_called_once_with("Hello")
        mock_controller.set_clipboard.assert_called_once_with("EchoDesk")

    def test_execute_stops_on_action_failure(self):
        mock_controller = MagicMock()
        mock_controller.open_application.return_value = {"success": True, "action": "open_application"}
        mock_controller.type_text.return_value = {"success": False, "action": "type_text", "message": "Failed."}

        workflow = DesktopWorkflow(controller=mock_controller)
        actions = [
            {"action": "open_application", "name": "notepad"},
            {"action": "type_text", "text": "Hello"},
            {"action": "set_clipboard", "text": "EchoDesk"},
        ]

        result = workflow.execute(actions)

        self.assertFalse(result["success"])
        self.assertEqual(result["completed"], 1)
        self.assertEqual(len(result["results"]), 2)
        self.assertIn("Workflow execution stopped", result["message"])

    def test_validate_action_rejects_unknown_action(self):
        workflow = DesktopWorkflow(controller=MagicMock())

        validation = workflow.validate_action({"action": "unknown_action"})

        self.assertFalse(validation["success"])
        self.assertIn("Unsupported workflow action", validation["message"])

    def test_validate_action_requires_parameters(self):
        workflow = DesktopWorkflow(controller=MagicMock())

        validation = workflow.validate_action({"action": "type_text"})

        self.assertFalse(validation["success"])
        self.assertIn("type_text requires a 'text' field", validation["message"])

    def test_wait_action_adds_delay(self):
        mock_controller = MagicMock()
        workflow = DesktopWorkflow(controller=mock_controller)

        result = workflow.execute([{"action": "wait", "seconds": 0.01}])

        self.assertTrue(result["success"])
        self.assertEqual(result["completed"], 1)
        self.assertEqual(result["results"][0]["action"], "wait")


class TestDesktopControllerWorkflowIntegration(unittest.TestCase):
    def test_execute_workflow_delegates_to_desktop_workflow(self):
        mock_workflow = MagicMock()
        mock_workflow.execute.return_value = {"success": True, "completed": 1, "results": []}
        controller = DesktopController(workflow=mock_workflow)

        result = controller.execute_workflow([{"action": "wait", "seconds": 0.0}])

        mock_workflow.execute.assert_called_once()
        self.assertTrue(result["success"])

    def test_available_workflow_actions_delegates_to_desktop_workflow(self):
        mock_workflow = MagicMock()
        mock_workflow.available_actions.return_value = ["wait", "open_application"]
        controller = DesktopController(workflow=mock_workflow)

        result = controller.available_workflow_actions()

        mock_workflow.available_actions.assert_called_once()
        self.assertEqual(result, ["wait", "open_application"])


if __name__ == "__main__":
    unittest.main()
