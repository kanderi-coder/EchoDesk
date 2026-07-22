import unittest
from unittest.mock import MagicMock, patch

from desktop.controller import DesktopController
from desktop.mouse import MouseController


class TestMouseController(unittest.TestCase):
    @patch("desktop.mouse.pyautogui")
    def test_move_calls_pyautogui_moveTo(self, mock_pyautogui):
        mock_pyautogui.moveTo = MagicMock()
        controller = MouseController(pyautogui_module=mock_pyautogui)

        result = controller.move(100, 200)

        self.assertTrue(result["success"])
        mock_pyautogui.moveTo.assert_called_once_with(100, 200)
        self.assertEqual(result["message"], "Mouse moved to 100,200.")

    @patch("desktop.mouse.pyautogui")
    def test_click_button_calls_pyautogui_click(self, mock_pyautogui):
        mock_pyautogui.click = MagicMock()
        controller = MouseController(pyautogui_module=mock_pyautogui)

        result = controller.click("right")

        self.assertTrue(result["success"])
        mock_pyautogui.click.assert_called_once_with(button="right")

    @patch("desktop.mouse.pyautogui")
    def test_double_click_calls_pyautogui_doubleClick(self, mock_pyautogui):
        mock_pyautogui.doubleClick = MagicMock()
        controller = MouseController(pyautogui_module=mock_pyautogui)

        result = controller.double_click("left")

        self.assertTrue(result["success"])
        mock_pyautogui.doubleClick.assert_called_once_with(button="left")

    @patch("desktop.mouse.pyautogui")
    def test_drag_calls_pyautogui_dragTo(self, mock_pyautogui):
        mock_pyautogui.moveTo = MagicMock()
        mock_pyautogui.dragTo = MagicMock()
        controller = MouseController(pyautogui_module=mock_pyautogui)

        result = controller.drag(10, 10, 20, 20, duration=0.5)

        self.assertTrue(result["success"])
        mock_pyautogui.moveTo.assert_called_once_with(10, 10)
        mock_pyautogui.dragTo.assert_called_once_with(20, 20, duration=0.5)

    @patch("desktop.mouse.pyautogui")
    def test_position_returns_coordinates(self, mock_pyautogui):
        mock_pyautogui.position = MagicMock(return_value=(5, 7))
        controller = MouseController(pyautogui_module=mock_pyautogui)

        result = controller.position()

        self.assertTrue(result["success"])
        self.assertEqual(result["result"], {"x": 5, "y": 7})

    def test_move_invalid_coordinates_returns_error(self):
        controller = MouseController(pyautogui_module=None)

        result = controller.move("a", "b")

        self.assertFalse(result["success"])
        self.assertIn("Invalid mouse coordinates", result["message"])

    @patch("desktop.mouse.pyautogui")
    def test_click_unknown_button_returns_error(self, mock_pyautogui):
        controller = MouseController(pyautogui_module=mock_pyautogui)

        result = controller.click("unknown")

        self.assertFalse(result["success"])
        self.assertIn("Unsupported mouse button", result["message"])


class TestDesktopControllerMouseIntegration(unittest.TestCase):
    def test_move_mouse_delegates_to_mouse_controller(self):
        mock_mouse = MagicMock()
        mock_mouse.move.return_value = {"success": True, "action": "move", "message": "ok"}
        controller = DesktopController(mouse_controller=mock_mouse)

        result = controller.move_mouse(10, 20)

        mock_mouse.move.assert_called_once_with(10, 20)
        self.assertEqual(result["message"], "ok")

    def test_click_mouse_delegates_to_mouse_controller(self):
        mock_mouse = MagicMock()
        mock_mouse.click.return_value = {"success": True, "action": "click", "message": "ok"}
        controller = DesktopController(mouse_controller=mock_mouse)

        result = controller.click_mouse("left")

        mock_mouse.click.assert_called_once_with("left")
        self.assertEqual(result["message"], "ok")

    def test_scroll_mouse_delegates_to_mouse_controller(self):
        mock_mouse = MagicMock()
        mock_mouse.scroll.return_value = {"success": True, "action": "scroll", "message": "ok"}
        controller = DesktopController(mouse_controller=mock_mouse)

        result = controller.scroll_mouse(5)

        mock_mouse.scroll.assert_called_once_with(5)
        self.assertEqual(result["action"], "scroll")


if __name__ == "__main__":
    unittest.main()
