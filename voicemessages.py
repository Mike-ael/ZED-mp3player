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

def musicSearchMessage():
    try:
        voice = pyttsx3.init()
        voice.setProperty('volume', 1.0)
        voice.say('Searching for music file')
        voice.runAndWait()
        return
    except RuntimeError:
        pass


def musicFoundMessage():
    try:
        voice = pyttsx3.init()
        voice.setProperty('volume', 1.0)
        voice.say('Music file found!! Download started.')
        voice.runAndWait()
        return
    except RuntimeError:
        pass

