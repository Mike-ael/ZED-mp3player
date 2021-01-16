import pyttsx3

def downloadMessage():
    try:
        voice = pyttsx3.init()
        voice.setProperty('volume', 1.0)
        voice.say('Your download is complete')
        voice.runAndWait()
        return
    except RuntimeError:
        pass

def searchMessage():
    try:
        voice = pyttsx3.init()
        voice.setProperty('volume', 1.0)
        voice.say('Searching for file')
        voice.runAndWait()
        return
    except RuntimeError:
        pass


def fileFoundMessage():
    try:
        voice = pyttsx3.init()
        voice.setProperty('volume', 1.0)
        voice.say('file found!! Download started.')
        voice.runAndWait()
        return
    except RuntimeError:
        pass



