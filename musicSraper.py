from queue import Queue
from mp3pawScraper import mp3pawscraper, WebDriverException, ElementClickInterceptedException
from voicemessages import searchMessage
url = 'https://mp3paw.com/'
errorString = Queue()
downloaded = Queue()
def setSongDetailsAndDownoad(artistName, songTitle):
    if artistName == '' or songTitle == '':
        errorString.put("ERROR: fields cannot be empty")
    else:
        searchMessage()
        newArtistName = artistName.lower().strip()
        newSongTitle = songTitle.lower().strip()
        try:
            downloaded.put(mp3pawscraper(newArtistName, newSongTitle))
        except ElementClickInterceptedException as error:
            errorString.put(error)
        except WebDriverException as error:
            errorString.put(error)
