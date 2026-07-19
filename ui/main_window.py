from PySide6.QtWidgets import (
    QMainWindow,
    QPushButton,
    QLabel,
    QLineEdit,
    QTextEdit,
    QVBoxLayout,
    QWidget
)

from vision.capture import ScreenCapture
from brain.brain import EchoBrain


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("EchoDesk")
        self.setGeometry(200, 200, 900, 600)

        self.brain = EchoBrain()
        self.capture = ScreenCapture()


        self.chat = QTextEdit()
        self.chat.setReadOnly(True)


        self.input = QLineEdit()
        self.input.setPlaceholderText(
            "Ask EchoDesk something..."
        )


        self.send_button = QPushButton("Send")

        self.capture_button = QPushButton(
            "Capture Screen"
        )


        self.send_button.clicked.connect(
            self.process_command
        )

        self.capture_button.clicked.connect(
            self.capture_screen
        )


        layout = QVBoxLayout()

        layout.addWidget(self.chat)
        layout.addWidget(self.input)
        layout.addWidget(self.send_button)
        layout.addWidget(self.capture_button)


        container = QWidget()
        container.setLayout(layout)

        self.setCentralWidget(container)



    def process_command(self):

        command = self.input.text()

        if command:

            response = self.brain.process(command)

            self.chat.append(
                "You: " + command
            )

            self.chat.append(
                "EchoDesk: " + response
            )

            self.input.clear()



    def capture_screen(self):

        path = self.capture.take_screenshot()

        self.chat.append(
            "EchoDesk: Screenshot saved."
        )

        print(path)