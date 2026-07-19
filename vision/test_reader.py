from capture import ScreenCapture
from reader import ScreenReader
from analyzer import ScreenAnalyzer


def main():

    print("Capturing screen...")

    capture = ScreenCapture()
    image_path = capture.take_screenshot()

    print("Reading screen...")

    reader = ScreenReader()
    text = reader.read_image(image_path)

    analyzer = ScreenAnalyzer()

    summary = analyzer.analyze(text)

    print("\n==============================")
    print("ECHODESK VISION REPORT")
    print("==============================\n")

    print(summary)


if __name__ == "__main__":
    main()