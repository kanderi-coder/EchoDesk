import os
import shutil
import subprocess
from typing import Any, Dict, List, Optional


class ApplicationLauncher:
    """Launch desktop applications using common platform heuristics."""

    SUPPORTED_APPS: Dict[str, List[str]] = {
        "Google Chrome": ["chrome.exe", "chrome"],
        "Microsoft Edge": ["msedge.exe", "msedge", "microsoftedge.exe"],
        "Mozilla Firefox": ["firefox.exe", "firefox"],
        "Visual Studio Code": ["code.exe", "code"],
        "Notepad": ["notepad.exe", "notepad"],
        "Calculator": ["calc.exe", "calculator"],
        "File Explorer": ["explorer.exe", "explorer"],
        "Command Prompt": ["cmd.exe", "cmd"],
        "PowerShell": ["powershell.exe", "pwsh.exe", "powershell"],
    }

    def launch(self, application_name: str) -> dict[str, Any]:
        """Launch the requested application if it can be located."""
        if not isinstance(application_name, str) or not application_name.strip():
            return self._error("No application name was provided.")

        normalized = application_name.strip()
        target = self._find_executable(normalized)
        if target is None:
            supported = ", ".join(self.list_supported())
            return self._error(
                f"Could not find a supported application for '{normalized}'.",
                details=f"Supported applications: {supported}.",
            )

        try:
            if os.name == "nt":
                if target.lower().endswith(".exe") or os.path.basename(target).lower() in ("explorer", "cmd", "pwsh", "powershell"):
                    subprocess.Popen([target], shell=False)
                else:
                    subprocess.Popen(target, shell=True)
            else:
                subprocess.Popen([target])
        except Exception as exc:
            return self._error("Failed to launch the application.", details=str(exc))

        return self._success("launch", f"Launched application: {normalized}.", result=target)

    def is_installed(self, application_name: str) -> bool:
        """Detect whether the requested application is installed."""
        if not isinstance(application_name, str) or not application_name.strip():
            return False

        return self._find_executable(application_name.strip()) is not None

    def list_supported(self) -> List[str]:
        """Return the supported application names."""
        return sorted(self.SUPPORTED_APPS.keys())

    def _find_executable(self, application_name: str) -> Optional[str]:
        if os.path.isabs(application_name) and os.path.exists(application_name):
            return application_name

        normalized = application_name.strip().lower()
        for supported_name, candidates in self.SUPPORTED_APPS.items():
            if normalized == supported_name.lower() or normalized.replace(" ", "") == supported_name.lower().replace(" ", ""):
                path = self._locate_executable(candidates)
                if path:
                    return path

        # Fallback: try to locate by raw name.
        return self._locate_executable([normalized])

    def _locate_executable(self, candidates: List[str]) -> Optional[str]:
        for candidate in candidates:
            launcher_path = shutil.which(candidate)
            if launcher_path:
                return launcher_path

            if os.name == "nt":
                path = self._check_windows_paths(candidate)
                if path:
                    return path

        return None

    def _check_windows_paths(self, candidate: str) -> Optional[str]:
        program_files = os.environ.get("ProgramFiles", "C:\\Program Files")
        program_files_x86 = os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")
        local_app_data = os.environ.get("LOCALAPPDATA", os.path.join(os.path.expanduser("~"), "AppData", "Local"))
        possible_paths = [
            os.path.join(program_files, "Google", "Chrome", "Application", candidate),
            os.path.join(program_files_x86, "Google", "Chrome", "Application", candidate),
            os.path.join(local_app_data, "Programs", "Microsoft VS Code", candidate),
            os.path.join(program_files, "Microsoft VS Code", candidate),
            os.path.join(program_files_x86, "Microsoft VS Code", candidate),
            os.path.join(program_files, "Mozilla Firefox", candidate),
            os.path.join(program_files_x86, "Mozilla Firefox", candidate),
            os.path.join(program_files, "Internet Explorer", candidate),
            os.path.join(program_files_x86, "Internet Explorer", candidate),
            os.path.join(program_files, "WindowsApps", candidate),
            os.path.join(local_app_data, "Microsoft", "WindowsApps", candidate),
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        return None

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
