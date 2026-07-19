from capture import ScreenCapture
from reader import ScreenReader


def main():
    print("Capturing screen...")

    capture = ScreenCapture()
    image_path = capture.take_screenshot()

    print("Reading screen...")

    reader = ScreenReader()
    text = reader.read_image(image_path)

    print("\n========================")
    print("SCREEN CONTENT")
    print("========================\n")

    print(text)


if __name__ == "__main__":
    main()