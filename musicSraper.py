from queue import Queue
from mp3pawScraper import mp3pawscraper
urlList = ['https://mp3paw.com/']
errorString = Queue()
downloaded = Queue()
def setSongDetailsAndDownoad(artistName, songTitle):
    if artistName == '' or songTitle == '':
        errorString.put("ERROR: fields cannot be empty")
    else:
        newArtistName = parse(artistName.lower().strip())
        newSongTitle = parse(songTitle.lower().strip())
        for url in urlList:
            try:
                print(url)
                downloaded.put(mp3pawscraper(newArtistName, newSongTitle))
            except Exception:
                pass

def parse(string):
    tempstr = str()
    for elem in string:
        if elem == ' ':
            tempstr += '-'
        else:
            tempstr += elem
    return tempstr

