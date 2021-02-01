import mutagen
from threading import Thread
from mutagen.mp3 import MP3, MutagenError

class Properties(object):
    def __init__(self, pathList):
        self.initializeList(pathList)
        self.loadProperties(pathList)
    def initializeList(self, pathList):
        self.size = len(pathList)
        self.genreList = [''] * self.size
        self.artistList = [''] * self.size
        self.albumList = [''] * self.size
        self.songYear = [''] * self.size
        self.songNameList = [''] * self.size
    def clearLists(self):
        self.genreList.clear()
        self.songYear.clear()
        self.albumList.clear()
        self.artistList.clear()
        self.songNameList.clear()
    def mainLoadingFunc(self, begin: int, end: int, pathList):
        for counter in range(begin, end):
            try:
                song = mutagen.File(pathList[counter])
                try:
                    self.genreList[counter] = song['TCON']
                except KeyError:
                    self.genreList[counter] = "unknown genre"
                except MutagenError:
                    self.genreList[counter] = "unknown genre"
                try:
                    self.songNameList[counter] = song['TIT2']
                except KeyError:
                    self.songNameList[counter] = "unknown song name"
                except MutagenError:
                    self.songNameList[counter] = "unknown song name"
                try:
                    self.artistList[counter] = song["TPE1"]
                except KeyError:
                    self.artistList[counter] = "unknown artist"
                except MutagenError:
                    self.artistList[counter] = "unknown artist"
                try:
                    self.albumList[counter] = song['TALB']
                except KeyError:
                    self.albumList[counter] = "unknown album"
                except MutagenError:
                    self.albumList[counter] = "unknown album"
                try:
                    self.songYear[counter] = song['TDRC']
                except KeyError:
                    self.songYear[counter] = "unknown year"
                except MutagenError:
                    self.songYear[counter] = "unknown year"
            except KeyError:
                self.genreList.append("unknown genre")
                self.songNameList.append(pathList[counter])
                self.artistList.append("unknown artist")
                self.albumList.append("unknown album")
                self.songYear.append("unknown year")
            except MutagenError:
                self.genreList.append("unknown genre")
                self.songNameList.append(pathList[counter])
                self.artistList.append("unknown artist")
                self.albumList.append("unknown album")
                self.songYear.append("unknown year")


    def parallelLoadProperties(self, begin: int, end: int, pathList):
        length = end - begin
        blockSize = 150
        if length <= blockSize:
            self.mainLoadingFunc(begin, end, pathList)
        else:
            midPoint: int = begin + length // 2
            Thread(target=self.parallelLoadProperties, args=[begin, midPoint, pathList], daemon=True).start()
            self.parallelLoadProperties(midPoint, end, pathList)


    def loadProperties(self, pathList):
        self.initializeList(pathList)
        self.parallelLoadProperties(0, len(pathList), pathList)