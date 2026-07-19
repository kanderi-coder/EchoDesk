# ===========================
# EchoDesk Project Setup
# ===========================

$folders = @(
    "ui",
    "vision",
    "brain",
    "voice",
    "memory",
    "automation",
    "plugins",
    "assets",
    "tests"
)

foreach($folder in $folders){
    if(!(Test-Path $folder)){
        New-Item -ItemType Directory -Path $folder | Out-Null
    }
}

$files = @(
    "ui/__init__.py",
    "ui/main_window.py",
    "vision/__init__.py",
    "vision/capture.py",
    "brain/__init__.py",
    "brain/brain.py",
    "voice/__init__.py",
    "voice/voice.py",
    "memory/__init__.py",
    "memory/memory.py",
    "automation/__init__.py",
    "automation/automation.py",
    "plugins/__init__.py",
    "tests/test_capture.py",
    "README.md",
    "requirements.txt"
)

foreach($file in $files){
    if(!(Test-Path $file)){
        New-Item -ItemType File -Path $file | Out-Null
    }
}

@"
from mss import mss
from PIL import Image

class ScreenCapture:

    def capture(self):
        with mss() as sct:
            monitor = sct.monitors[1]

            screenshot = sct.grab(monitor)

            image = Image.frombytes(
                "RGB",
                screenshot.size,
                screenshot.rgb
            )

            return image
"@ | Set-Content vision/capture.py

@"
from vision.capture import ScreenCapture

capture = ScreenCapture()

image = capture.capture()

image.save("screenshot.png")

print("EchoDesk Vision Engine is working!")
"@ | Set-Content tests/test_capture.py

Write-Host ""
Write-Host "======================================="
Write-Host " EchoDesk project initialized!"
Write-Host "======================================="