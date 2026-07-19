import speech_recognition as sr
import pyttsx3


class EchoVoice:

    def __init__(self):

        self.recognizer = sr.Recognizer()

        self.engine = pyttsx3.init()

        self.engine.setProperty(
            "rate",
            170
        )


    def listen(self):

        with sr.Microphone() as source:

            print("Listening...")

            audio = self.recognizer.listen(source)


        try:

            text = self.recognizer.recognize_google(
                audio
            )

            print(
                "You:",
                text
            )

            return text


        except:

            return ""



    def speak(self, text):

        print(
            "EchoDesk:",
            text
        )

        self.engine.say(text)

        self.engine.runAndWait()