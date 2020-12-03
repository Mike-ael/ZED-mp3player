#program to get all the file names of all mp3 files on my hard disk
import os
import subprocess
musicFilenameList = list()
musicFilePathList = list()

def searchForSongs():
    search = subprocess.Popen([r'C:\Users\HP\PycharmProjects\new music player\mp3search.exe'])
    search.wait()

def update():
    global musicFilenameList, musicFilePathList
    if len(musicFilenameList) > 0:
        musicFilenameList.clear()
        musicFilePathList.clear()
    with open('songfile.txt', 'r') as input:
        for file in input.readlines():
            musicFilenameList.append(file.strip())
    with open('songpath.txt', 'r') as input:
        tempList = input.readlines()
        for i in range(len(tempList)):
            musicFilePathList.append(os.path.join(tempList[i].strip(), musicFilenameList[i].strip()))