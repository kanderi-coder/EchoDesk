class ScreenAnalyzer:
    """
    Converts OCR text into a human-friendly summary.
    """

    def analyze(self, text):

        if not text or text == "No text detected.":
            return "I couldn't detect any readable text on the screen."

        summary = []

        lower = text.lower()

        if "visual studio code" in lower or "vscode" in lower:
            summary.append("Visual Studio Code is open.")

        if "powershell" in lower:
            summary.append("A PowerShell terminal is open.")

        if ".py" in lower:
            summary.append("You appear to be working with Python files.")

        if "github" in lower:
            summary.append("GitHub is visible.")

        if "chatgpt" in lower:
            summary.append("ChatGPT is open.")

        if "traceback" in lower:
            summary.append("A Python error traceback is visible.")

        if "echodesk" in lower:
            summary.append("You are working on the EchoDesk project.")

        if not summary:
            summary.append("I can read text on the screen, but I cannot yet identify the application.")

        summary.append("\n----- OCR Preview -----\n")
        summary.append(text[:600])

        return "\n".join(summary)