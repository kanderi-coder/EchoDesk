import unittest
from unittest.mock import MagicMock, patch

from desktop.controller import DesktopController
from desktop.launcher import ApplicationLauncher


class TestApplicationLauncher(unittest.TestCase):
    def test_list_supported_returns_expected_applications(self):
        launcher = ApplicationLauncher()
        supported = launcher.list_supported()

        self.assertIn("Google Chrome", supported)
        self.assertIn("Microsoft Edge", supported)
        self.assertIn("Visual Studio Code", supported)
        self.assertIn("PowerShell", supported)

    @patch("desktop.launcher.shutil.which")
    @patch("desktop.launcher.os.name", "nt")
    def test_is_installed_returns_true_when_executable_exists(self, mock_which):
        mock_which.return_value = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        launcher = ApplicationLauncher()

        self.assertTrue(launcher.is_installed("Google Chrome"))
        mock_which.assert_called()

    @patch("desktop.launcher.shutil.which")
    @patch("desktop.launcher.subprocess.Popen")
    @patch("desktop.launcher.os.name", "nt")
    def test_launch_known_application_uses_subprocess(self, mock_popen, mock_which):
        mock_which.return_value = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        launcher = ApplicationLauncher()

        result = launcher.launch("Google Chrome")

        self.assertTrue(result["success"])
        self.assertEqual(result["action"], "launch")
        mock_popen.assert_called_once_with([mock_which.return_value], shell=False)

    @patch("desktop.launcher.shutil.which")
    def test_launch_unknown_application_returns_error(self, mock_which):
        mock_which.return_value = None
        launcher = ApplicationLauncher()

        result = launcher.launch("UnknownApp")

        self.assertFalse(result["success"])
        self.assertIn("Could not find a supported application", result["message"])


class TestDesktopControllerLauncherIntegration(unittest.TestCase):
    def test_open_application_delegates_to_launcher(self):
        mock_launcher = MagicMock()
        mock_launcher.launch.return_value = {"success": True, "action": "launch", "message": "Opened Chrome."}

        controller = DesktopController(launcher=mock_launcher)
        result = controller.open_application("Google Chrome")

        mock_launcher.launch.assert_called_once_with("Google Chrome")
        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "Opened Chrome.")

    def test_supported_applications_returns_success_response(self):
        expected = ["Google Chrome", "Microsoft Edge"]
        mock_launcher = MagicMock()
        mock_launcher.list_supported.return_value = expected

        controller = DesktopController(launcher=mock_launcher)
        response = controller.supported_applications()

        self.assertTrue(response["success"])
        self.assertEqual(response["result"], expected)

    def test_is_application_installed_returns_success_response(self):
        mock_launcher = MagicMock()
        mock_launcher.is_installed.return_value = True

        controller = DesktopController(launcher=mock_launcher)
        response = controller.is_application_installed("Visual Studio Code")

        self.assertTrue(response["success"])
        self.assertTrue(response["result"])


if __name__ == "__main__":
    unittest.main()
