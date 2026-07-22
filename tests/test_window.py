import unittest
from unittest.mock import MagicMock

from desktop.controller import DesktopController
from desktop.window import WindowManager


class TestWindowManager(unittest.TestCase):
    def test_active_window_returns_active_title_when_available(self):
        mock_window = MagicMock()
        mock_window.title = "Sample App"
        mock_pygetwindow = MagicMock(getActiveWindow=MagicMock(return_value=mock_window))
        manager = WindowManager(pygetwindow_module=mock_pygetwindow)

        result = manager.active_window()

        self.assertTrue(result["success"])
        self.assertEqual(result["result"]["window"], "Sample App")

    def test_list_windows_returns_window_titles(self):
        mock_pygetwindow = MagicMock(getAllTitles=MagicMock(return_value=["App One", "App Two"]))
        manager = WindowManager(pygetwindow_module=mock_pygetwindow)

        result = manager.list_windows()

        self.assertTrue(result["success"])
        self.assertEqual(result["result"]["windows"], ["App One", "App Two"])

    def test_focus_window_activates_matching_window(self):
        mock_window = MagicMock(title="Browser Window")
        mock_window.activate = MagicMock()
        mock_pygetwindow = MagicMock(getAllWindows=MagicMock(return_value=[mock_window]))
        manager = WindowManager(pygetwindow_module=mock_pygetwindow)

        result = manager.focus_window("browser")

        self.assertTrue(result["success"])
        mock_window.activate.assert_called_once()
        self.assertIn("window", result["result"])

    def test_minimize_window_calls_minimize_method(self):
        mock_window = MagicMock(title="Explorer")
        mock_window.minimize = MagicMock()
        mock_pygetwindow = MagicMock(getAllWindows=MagicMock(return_value=[mock_window]))
        manager = WindowManager(pygetwindow_module=mock_pygetwindow)

        result = manager.minimize_window("Explorer")

        self.assertTrue(result["success"])
        mock_window.minimize.assert_called_once()

    def test_maximize_window_calls_maximize_method(self):
        mock_window = MagicMock(title="Editor")
        mock_window.maximize = MagicMock()
        mock_pygetwindow = MagicMock(getAllWindows=MagicMock(return_value=[mock_window]))
        manager = WindowManager(pygetwindow_module=mock_pygetwindow)

        result = manager.maximize_window("Editor")

        self.assertTrue(result["success"])
        mock_window.maximize.assert_called_once()

    def test_restore_window_calls_restore_method(self):
        mock_window = MagicMock(title="Terminal")
        mock_window.restore = MagicMock()
        mock_pygetwindow = MagicMock(getAllWindows=MagicMock(return_value=[mock_window]))
        manager = WindowManager(pygetwindow_module=mock_pygetwindow)

        result = manager.restore_window("Terminal")

        self.assertTrue(result["success"])
        mock_window.restore.assert_called_once()

    def test_close_window_requires_confirmation(self):
        mock_window = MagicMock(title="Editor")
        mock_window.close = MagicMock()
        mock_pygetwindow = MagicMock(getAllWindows=MagicMock(return_value=[mock_window]))
        manager = WindowManager(pygetwindow_module=mock_pygetwindow)

        result = manager.close_window("Editor")

        self.assertFalse(result["success"])
        self.assertIn("confirmation", result["message"].lower())
        self.assertFalse(mock_window.close.called)

    def test_close_window_closes_on_confirm(self):
        mock_window = MagicMock(title="Editor")
        mock_window.close = MagicMock()
        mock_pygetwindow = MagicMock(getAllWindows=MagicMock(return_value=[mock_window]))
        manager = WindowManager(pygetwindow_module=mock_pygetwindow)

        result = manager.close_window("Editor", confirm=True)

        self.assertTrue(result["success"])
        mock_window.close.assert_called_once()

    def test_unknown_window_returns_error(self):
        mock_pygetwindow = MagicMock(getAllWindows=MagicMock(return_value=[]))
        manager = WindowManager(pygetwindow_module=mock_pygetwindow)

        result = manager.focus_window("Nonexistent")

        self.assertFalse(result["success"])
        self.assertIn("not found", result["message"].lower())


class TestDesktopControllerWindowIntegration(unittest.TestCase):
    def test_active_window_delegates_to_window_manager(self):
        mock_manager = MagicMock()
        mock_manager.active_window.return_value = {
            "success": True,
            "action": "active_window",
            "result": {"window": "Sample App"},
        }
        controller = DesktopController(window_manager=mock_manager)

        result = controller.active_window()

        mock_manager.active_window.assert_called_once()
        self.assertEqual(result["result"], {"window": "Sample App"})

    def test_focus_window_delegates_to_window_manager(self):
        mock_manager = MagicMock()
        mock_manager.focus_window.return_value = {
            "success": True,
            "action": "focus_window",
            "result": {"window": "Browser Window"},
        }
        controller = DesktopController(window_manager=mock_manager)

        result = controller.focus_window("Browser Window")

        mock_manager.focus_window.assert_called_once_with("Browser Window")
        self.assertEqual(result["result"], {"window": "Browser Window"})

    def test_close_window_delegates_to_window_manager(self):
        mock_manager = MagicMock()
        mock_manager.close_window.return_value = {
            "success": True,
            "action": "close_window",
            "result": {"window": "Editor"},
        }
        controller = DesktopController(window_manager=mock_manager)

        result = controller.close_window("Editor", confirm=True)

        mock_manager.close_window.assert_called_once_with("Editor", confirm=True)
        self.assertEqual(result["result"], {"window": "Editor"})


if __name__ == "__main__":
    unittest.main()
