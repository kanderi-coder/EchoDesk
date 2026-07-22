import unittest
from unittest.mock import MagicMock, patch

from desktop.controller import DesktopController
from desktop.keyboard import KeyboardController


class TestKeyboardController(unittest.TestCase):
    @patch("desktop.keyboard.pyautogui")
    def test_type_text_calls_pyautogui_write(self, mock_pyautogui):
        mock_pyautogui.write = MagicMock()
        controller = KeyboardController(pyautogui_module=mock_pyautogui)

        result = controller.type_text("hello")

        self.assertTrue(result["success"])
        mock_pyautogui.write.assert_called_once_with("hello", interval=0.01)

    @patch("desktop.keyboard.pyautogui")
    def test_press_key_calls_pyautogui_press(self, mock_pyautogui):
        mock_pyautogui.press = MagicMock()
        controller = KeyboardController(pyautogui_module=mock_pyautogui)

        result = controller.press_key("enter")

        self.assertTrue(result["success"])
        mock_pyautogui.press.assert_called_once_with("enter")

    @patch("desktop.keyboard.pyautogui")
    def test_hotkey_calls_pyautogui_hotkey(self, mock_pyautogui):
        mock_pyautogui.hotkey = MagicMock()
        controller = KeyboardController(pyautogui_module=mock_pyautogui)

        result = controller.hotkey("ctrl", "c")

        self.assertTrue(result["success"])
        mock_pyautogui.hotkey.assert_called_once_with("ctrl", "c")

    @patch("desktop.keyboard.pyautogui")
    def test_copy_calls_hotkey(self, mock_pyautogui):
        mock_pyautogui.hotkey = MagicMock()
        controller = KeyboardController(pyautogui_module=mock_pyautogui)

        result = controller.copy()

        self.assertTrue(result["success"])
        self.assertIn("ctrl+c", result["message"])
        mock_pyautogui.hotkey.assert_called_once()

    @patch("desktop.keyboard.pyautogui")
    def test_paste_calls_hotkey(self, mock_pyautogui):
        mock_pyautogui.hotkey = MagicMock()
        controller = KeyboardController(pyautogui_module=mock_pyautogui)

        result = controller.paste()

        self.assertTrue(result["success"])
        self.assertIn("ctrl+v", result["message"])
        mock_pyautogui.hotkey.assert_called_once()

    @patch("desktop.keyboard.pyautogui")
    def test_undo_calls_hotkey(self, mock_pyautogui):
        mock_pyautogui.hotkey = MagicMock()
        controller = KeyboardController(pyautogui_module=mock_pyautogui)

        result = controller.undo()

        self.assertTrue(result["success"])
        self.assertIn("ctrl+z", result["message"])
        mock_pyautogui.hotkey.assert_called_once()

    @patch("desktop.keyboard.pyautogui")
    def test_redo_calls_hotkey(self, mock_pyautogui):
        mock_pyautogui.hotkey = MagicMock()
        controller = KeyboardController(pyautogui_module=mock_pyautogui)

        result = controller.redo()

        self.assertTrue(result["success"])
        self.assertIn("ctrl+y", result["message"])
        mock_pyautogui.hotkey.assert_called_once()

    def test_type_text_invalid_input_returns_error(self):
        controller = KeyboardController(pyautogui_module=None)

        result = controller.type_text("")

        self.assertFalse(result["success"])
        self.assertIn("No text was provided", result["message"])

    @patch("desktop.keyboard.pyautogui")
    def test_press_key_invalid_input_returns_error(self, mock_pyautogui):
        controller = KeyboardController(pyautogui_module=mock_pyautogui)

        result = controller.press_key("")

        self.assertFalse(result["success"])
        self.assertIn("No key was specified", result["message"])

    @patch("desktop.keyboard.pyautogui")
    def test_hotkey_invalid_key_returns_error(self, mock_pyautogui):
        controller = KeyboardController(pyautogui_module=mock_pyautogui)

        result = controller.hotkey("ctrl", "")

        self.assertFalse(result["success"])
        self.assertIn("valid string key names", result["message"])


class TestDesktopControllerKeyboardIntegration(unittest.TestCase):
    def test_type_text_delegates_to_keyboard_controller(self):
        mock_keyboard = MagicMock()
        mock_keyboard.type_text.return_value = {"success": True, "action": "type_text", "message": "ok"}
        controller = DesktopController(keyboard_controller=mock_keyboard)

        result = controller.type_text("hello")

        mock_keyboard.type_text.assert_called_once_with("hello")
        self.assertEqual(result["message"], "ok")

    def test_press_key_delegates_to_keyboard_controller(self):
        mock_keyboard = MagicMock()
        mock_keyboard.press_key.return_value = {"success": True, "action": "press_key", "message": "ok"}
        controller = DesktopController(keyboard_controller=mock_keyboard)

        result = controller.press_key("enter")

        mock_keyboard.press_key.assert_called_once_with("enter")
        self.assertEqual(result["message"], "ok")

    def test_hotkey_delegates_to_keyboard_controller(self):
        mock_keyboard = MagicMock()
        mock_keyboard.hotkey.return_value = {"success": True, "action": "hotkey", "message": "ok"}
        controller = DesktopController(keyboard_controller=mock_keyboard)

        result = controller.hotkey("ctrl", "c")

        mock_keyboard.hotkey.assert_called_once_with("ctrl", "c")
        self.assertEqual(result["message"], "ok")

    def test_copy_text_delegates_to_keyboard_controller(self):
        mock_keyboard = MagicMock()
        mock_keyboard.copy.return_value = {"success": True, "action": "shortcut", "message": "ok"}
        controller = DesktopController(keyboard_controller=mock_keyboard)

        result = controller.copy_text()

        mock_keyboard.copy.assert_called_once()
        self.assertEqual(result["action"], "shortcut")

    def test_paste_text_delegates_to_keyboard_controller(self):
        mock_keyboard = MagicMock()
        mock_keyboard.paste.return_value = {"success": True, "action": "shortcut", "message": "ok"}
        controller = DesktopController(keyboard_controller=mock_keyboard)

        result = controller.paste_text()

        mock_keyboard.paste.assert_called_once()
        self.assertEqual(result["action"], "shortcut")


if __name__ == "__main__":
    unittest.main()
