from mss import mss
from PIL import Image
import os


class ScreenCapture:

    def __init__(self):
        self.sct = mss()


    def take_screenshot(self):

        screenshot_path = os.path.join(
            os.getcwd(),
            "screenshot.png"
        )

        monitor = self.sct.monitors[1]

        screenshot = self.sct.grab(monitor)

        image = Image.frombytes(
            "RGB",
            screenshot.size,
            screenshot.rgb
        )

        image.save(screenshot_path)

        return screenshot_path