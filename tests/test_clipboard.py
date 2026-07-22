import unittest
from unittest.mock import MagicMock, patch

from desktop.controller import DesktopController
from desktop.clipboard import ClipboardManager


class TestClipboardManager(unittest.TestCase):
    def test_available_returns_success_when_pyperclip_present(self):
        mock_pyperclip = MagicMock(paste=MagicMock(return_value="hello"), copy=MagicMock())
        manager = ClipboardManager(pyperclip_module=mock_pyperclip)

        result = manager.available()

        self.assertTrue(result["success"])
        self.assertEqual(result["action"], "available")

    def test_get_text_reads_from_pyperclip(self):
        mock_pyperclip = MagicMock(paste=MagicMock(return_value="clipboard text"))
        manager = ClipboardManager(pyperclip_module=mock_pyperclip)

        result = manager.get_text()

        self.assertTrue(result["success"])
        self.assertEqual(result["result"]["text"], "clipboard text")

    def test_set_text_writes_to_pyperclip(self):
        mock_pyperclip = MagicMock(copy=MagicMock())
        manager = ClipboardManager(pyperclip_module=mock_pyperclip)

        result = manager.set_text("new text")

        self.assertTrue(result["success"])
        mock_pyperclip.copy.assert_called_once_with("new text")

    def test_copy_returns_clipboard_text(self):
        mock_pyperclip = MagicMock(paste=MagicMock(return_value="copied"))
        manager = ClipboardManager(pyperclip_module=mock_pyperclip)

        result = manager.copy()

        self.assertTrue(result["success"])
        self.assertEqual(result["result"]["text"], "copied")

    def test_paste_returns_clipboard_text(self):
        mock_pyperclip = MagicMock(paste=MagicMock(return_value="pasted"))
        manager = ClipboardManager(pyperclip_module=mock_pyperclip)

        result = manager.paste()

        self.assertTrue(result["success"])
        self.assertEqual(result["result"]["text"], "pasted")

    def test_clear_writes_empty_text(self):
        mock_pyperclip = MagicMock(copy=MagicMock())
        manager = ClipboardManager(pyperclip_module=mock_pyperclip)

        result = manager.clear()

        self.assertTrue(result["success"])
        mock_pyperclip.copy.assert_called_once_with("")

    def test_set_text_invalid_input_returns_error(self):
        manager = ClipboardManager(pyperclip_module=None)

        result = manager.set_text(None)

        self.assertFalse(result["success"])
        self.assertIn("must be a string", result["message"])

    def test_get_text_unavailable_backend_returns_error(self):
        with patch.multiple(
            "desktop.clipboard",
            pyperclip=None,
            tkinter=None,
            win32clipboard=None,
            win32con=None,
        ):
            manager = ClipboardManager(pyperclip_module=None, tkinter_module=None, win32clipboard_module=None, win32con_module=None)

            result = manager.get_text()

            self.assertFalse(result["success"])
            self.assertIn("Clipboard is unavailable", result["message"])


class TestDesktopControllerClipboardIntegration(unittest.TestCase):
    def test_get_clipboard_delegates_to_clipboard_manager(self):
        mock_manager = MagicMock()
        mock_manager.get_text.return_value = {"success": True, "action": "get_text", "result": {"text": "hello"}}
        controller = DesktopController(clipboard_manager=mock_manager)

        result = controller.get_clipboard()

        mock_manager.get_text.assert_called_once()
        self.assertEqual(result["result"]["text"], "hello")

    def test_set_clipboard_delegates_to_clipboard_manager(self):
        mock_manager = MagicMock()
        mock_manager.set_text.return_value = {"success": True, "action": "set_text"}
        controller = DesktopController(clipboard_manager=mock_manager)

        result = controller.set_clipboard("text")

        mock_manager.set_text.assert_called_once_with("text")
        self.assertTrue(result["success"])

    def test_clear_clipboard_delegates_to_clipboard_manager(self):
        mock_manager = MagicMock()
        mock_manager.clear.return_value = {"success": True, "action": "clear"}
        controller = DesktopController(clipboard_manager=mock_manager)

        result = controller.clear_clipboard()

        mock_manager.clear.assert_called_once()
        self.assertTrue(result["success"])

    def test_clipboard_available_delegates_to_clipboard_manager(self):
        mock_manager = MagicMock()
        mock_manager.available.return_value = {"success": True, "action": "available"}
        controller = DesktopController(clipboard_manager=mock_manager)

        result = controller.clipboard_available()

        mock_manager.available.assert_called_once()
        self.assertTrue(result["success"])


if __name__ == "__main__":
    unittest.main()
