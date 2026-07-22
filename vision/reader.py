import os


class ScreenReader:
    def __init__(self):
        try:
            import easyocr
            print("Loading EasyOCR... (first launch may take a minute)")
            self.reader = easyocr.Reader(['en'], gpu=False)
        except ImportError:
            self.reader = None

    def read_image(self, image_path):
        """
        Reads all text from an image and returns it as a single string.
        """

        if self.reader is None:
            return "Screen reading is not available because EasyOCR is not installed."

        if not os.path.exists(image_path):
            return "Image not found."

        results = self.reader.readtext(image_path)

        if not results:
            return "No text detected."

        lines = []

        for result in results:
            text = result[1]
            lines.append(text)

        return "\n".join(lines)