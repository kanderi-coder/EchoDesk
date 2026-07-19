from voice import EchoVoice
from brain.brain import EchoBrain


voice = EchoVoice()
brain = EchoBrain()


while True:

    command = voice.listen()

    if command == "":
        continue


    if "exit" in command.lower():
        voice.speak("Goodbye")
        break


    response = brain.process(command)

    voice.speak(response)