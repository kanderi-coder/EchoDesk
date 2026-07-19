from vision.capture import ScreenCapture


def main():
    capture = ScreenCapture()

    image = capture.take_screenshot()

    image.save("screenshot.png")

    print("EchoDesk Vision Engine is working!")
    print("Screenshot saved as screenshot.png")


if __name__ == "__main__":
    main()