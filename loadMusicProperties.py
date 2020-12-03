from SearchForSongs import musicFilePathList
import mutagen
from mutagen.mp3 import MP3, MutagenError
genreList = []
artistList = []
albumList = []
songYear = []
songNameList = []
def loadProperties():
    for counter in range(len(musicFilePathList)):
        try:
            song = mutagen.File(musicFilePathList[counter])
            try:
                genreList.append(song['TCON'])
            except KeyError:
                genreList.append("unknown genre")
            except MutagenError:
                genreList.append("unknown genre")
            try:
                songNameList.append(song['TIT2'])
            except KeyError:
                songNameList.append("unknown song name")
            except MutagenError:
                songNameList.append("unknown song name")
            try:
                artistList.append(song["TPE1"])
            except KeyError:
                artistList.append("unknown artist")
            except MutagenError:
                artistList.append("unknown artist")
            try:
                albumList.append(song['TALB'])
            except KeyError:
                albumList.append("unknown album")
            except MutagenError:
                albumList.append("unknown album")
            try:
                songYear.append(song['TDRC'])
            except KeyError:
                songYear.append("unknown year")
            except MutagenError:
                songYear.append("unknown year")
        except KeyError:
            genreList.append("unknown genre")
            songNameList.append("unknown song name")
            artistList.append("unknown artist")
            albumList.append("unknown album")
            songYear.append("unknown year")
        except MutagenError:
            genreList.append("unknown genre")
            songNameList.append("unknown song name")
            artistList.append("unknown artist")
            albumList.append("unknown album")
            songYear.append("unknown year")