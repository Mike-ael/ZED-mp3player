#program to get all the file names of all mp3 files on my hard disk
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
musicFilenameList = list()
musicFilePathList = list()
executor = ThreadPoolExecutor(max_workers=1)

def searchForSongs():
    search = subprocess.Popen([r'C:\Users\HP\PycharmProjects\new music player\mp3search.exe'])
    search.wait()

def readFilename():
    global musicFilenameList
    with open('songfile.txt', 'r') as input:
        for file in input.readlines():
            musicFilenameList.append(file.strip())

def update():
    global musicFilePathList
    if len(musicFilenameList) > 0:
        musicFilenameList.clear()
        musicFilePathList.clear()
    task = executor.submit(readFilename)
    with open('songpath.txt', 'r') as input:
        for file in input.readlines():
            musicFilePathList.append(file.strip())
    for _ in as_completed([task]):
        i = 0
        for file in range(len(musicFilenameList)):
            musicFilePathList[i] = (os.path.join(musicFilePathList[i], musicFilenameList[i]))
            i += 1