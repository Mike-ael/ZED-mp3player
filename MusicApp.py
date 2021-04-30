'''
Author: Michael Ejiofor Obi
Date Started: 21 june 2020
Date Completed: ...A project is never complete
Name: ZED Music Player
Description:
    this is a music player application, built using Tkinter GUI and pygame library.
    it also use the Mutagen library(an MPEG 3 library, for use to check the length of a song).
:return:
'''
from threading import Thread
from concurrent.futures import ThreadPoolExecutor, as_completed
import tkinter as tk
import tkinter.messagebox
import tkinter.simpledialog
from mutagen.mp3 import MP3, MutagenError, HeaderNotFoundError
import pygame
from tkinter import ttk
from SearchForSongs import searchForSongs, update, musicFilePathList, musicFilenameList
from time import sleep
from random import randrange
import re
import os
from queue import Queue, Empty, Full
from loadMusicProperties import Properties
from mutagen.id3 import ID3
from PIL import Image, UnidentifiedImageError
from io import BytesIO
from voicemessages import downloadMessage
from mp3pawScraper import MusicDownload, musicDownloadErrors, musicDownloadNotification
from mp3pawScraper import musicDownloadCancelledFlag
from netnaijaScraper import VideoDownLoad, videoDownloadCancelledFlag
from netnaijaScraper import ElementClickInterceptedException, TimeoutException
from netnaijaScraper import NoSuchElementException, WebDriverException, InvalidArgumentException
from netnaijaScraper import videoDownloadErrors, videoDownloadNotification
from tfpdlScraper import tfpdl_videoDownloadErrors, tfpdl_videoDownloadCancelledFlag
from tfpdlScraper import tfpdl_videoDownloadNotification, TFPDLVideoDownload

pygame.mixer.pre_init(44100, 16, 2, 1024 * 4)
pygame.init()
currentSongIndex = 0
currentSong = 0
previousSongIndex = 0
nextSongIndex = 0
playNext = False
#variables to represent the various states of the music player
play, pause, stop, prev, next, idle = 0, 1, 2, 3, 4, 5
musicLength = 0
currentEvent = idle
pastEvent = idle
musicTrackerPosition = 0
currentVolumeInPixel = 100
popupON = False
popupCounter = 0
yposition = 0
lengthInPixel = 0
timerStart = True
time = 0
songPlayed = False
tabID = -1
numberOfPlaylists = 0
maxNumberOfPlayList = 2
playListNames = []
playListContent = []  #a potentially multi-dimensional list
playListMusicIndex = []# list to hold the real index of the songs added to both playlists
playlistNamesFile = 'playlistnames.txt'
command1 = None
command2 = None
searchListBoxEmpty = True
songPlayingFromSearchList = False
currentIndexPlayingInSearchList = 0
songPlayingFromPlaylist = []
currentIndexPlayingInPlaylist = []
subwooverImageString1 = 'music logo1.gif'
subwooverImageString2 = 'music_art.gif'
playlistTabCurrentlyOn = -1

window = tk.Tk()
window.resizable(False, False)
window.overrideredirect(True)
window.attributes("-alpha", 0.8)
canvas = tk.Canvas(window, width = 1050, height = 500, bg = "#000000")
canvas.pack()
canvas.create_text(500, 200, text = "ZED MP3 PLAYER", font = "Helvetica 80", fill = "cyan")
image = tk.PhotoImage(file = "Start.gif")
canvas.create_image(500, 350, image = image)

class Repeat:
    def __init__(self):
        self.__number = 0
    def changeState(self):
        self.__number += 1
        self.checkState()
    def checkState(self):
        if self.__number > 2:
            self.__number = 0
    def getValue(self):
        return self.__number
#the Repeat class is used to keep track of how many times the repeat button has been clicked
#if number == 0, the button hasn't been clicked, the song doesnt repeat
#if number == 1, the current song repeats continuously until its is set to another number
#if number == 2, the current song repeats once and moves on to the next song


class MusicPlayerGUI:
    def __init__(self):
        global numberOfPlaylists
        global playListNames
        global playListContent
        global tabID
        self.currentMusicTimequeue = None
        self.path = r'C:\\'
        self.searchSongsInCDriveThread = Thread(target= self.loadSongs)
        self.searchSongsInCDriveThread.setDaemon(False)
        self.searchSongsInCDriveThread.start()
        self.searchSongsInCDriveThread.join()
        #read in the playlist content and the playlist names

        self.file = open(playlistNamesFile, 'a')
        self.file.close()
        self.file = open(playlistNamesFile, 'r')
        playListNames = [filename for filename in self.file.readlines()]
        self.file.close()
        for counter in range(len(playListNames)):
            numberOfPlaylists += 1
            playListContent.append([])
            playListMusicIndex.append([])
            self.file = open(playListNames[counter].strip() + '.txt', 'r')
            playListContent[counter] = [musicfiles.strip() for musicfiles in self.file.readlines()]
            self.file.close()

            self.file = open(playListNames[counter].strip() + 'MI.txt', 'r')
            playListMusicIndex[counter] = [int(index.strip()) for index in self.file.readlines()]
            self.file.close()


        # A list to store the indexes of the music files as their ID
        self.musicID = []
        for number in range(len(musicFilenameList)):
            self.musicID.append(number)

        window.destroy()

        self.window = tk.Tk()
        self.playing = False
        self.startTime = 0
        self.shuffle = tk.IntVar()
        self.list = []
        self.searchListSongIndex = []
        self.window.title('ZED music player')
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background="#000000")
        style.configure('TCanvas', background="#000000")
        style.configure('TEntry', background="#000000")
        style.configure('TLabel', background="#000000", foreground='#00c8ff')
        style.configure('TCheckbutton', background = "#000000")
        style.configure('TButton', background="#000000", foreground='#00c8ff')
        self.window.resizable(False, False)
        self.tabcontrol = ttk.Notebook(self.window)
        self.tabcontrol.bind('<Button-3>', self.postPlaylistDeletePopup)
        self.tabs = []
        tab1 = ttk.Frame(self.tabcontrol)
        self.tabcontrol.add(tab1, text = '    Home    ')
        self.tabs.append(tab1)
        tab2 = ttk.Frame(self.tabcontrol)
        self.tabcontrol.add(tab2, text = '    Songs    ')
        self.tabs.append(tab2)
        tab3 = ttk.Frame(self.tabcontrol)
        self.tabcontrol.add(tab3, text = '    Search    ')
        self.tabs.append(tab3)
        tab4 = ttk.Frame(self.tabcontrol)
        self.tabcontrol.add(tab4, text = '    Music Download   ')
        self.tabs.append(tab4)
        tab5 = ttk.Frame(self.tabcontrol)
        self.tabcontrol.add(tab5, text= '    Video Download   ')
        self.tabs.append(tab5)
        self.tabcontrol.pack()
        self.beginTime = tk.StringVar()
        self.endTime = tk.StringVar()
        self.beginTime.set('00:00')
        self.endTime.set('00:00')
        self.subWooferCanvas = tk.Canvas(tab1, width = 1050, height = 350, bg = "#000000")
        self.subWooferCanvas.pack()
        self.subwooferImage = tk.PhotoImage(file = subwooverImageString1)
        self.subWooferCanvas.create_image(525, 160, image = self.subwooferImage, \
                                          tags = 'subwooferImage')
        self.musicLineAndTimerFrame = ttk.Frame(tab1)
        self.musicLineAndTimerFrame.pack()
        self.startTimeLabel = ttk.Label(self.musicLineAndTimerFrame, textvariable=self.beginTime)
        self.startTimeLabel.grid(row = 0, column = 0)
        self.musicLineCanvas = tk.Canvas(self.musicLineAndTimerFrame, width = 600, height = 10, bg = "#000000")
        self.musicLineCanvas.grid(row = 0, column = 1)
        self.endTimeLabel = ttk.Label(self.musicLineAndTimerFrame, textvariable = self.endTime)
        self.endTimeLabel.grid(row = 0, column = 2)
        self.musicLineCanvas.bind('<Button-1>', self.moveMusicLine)
        self.hifiButtonCanvas = tk.Canvas(tab1, width = 800, height = 50, bg = "#000000")
        self.hifiButtonCanvas.pack()
        prevImage = tk.PhotoImage(file = 'newprev button.gif')
        stopImage = tk.PhotoImage(file = 'music stop.gif')
        playImage = tk.PhotoImage(file = 'newplay button .gif')
        pauseImage = tk.PhotoImage(file = 'newanother pause.gif')
        nextImage = tk.PhotoImage(file = 'newsimilar next button.gif')
        self.volumeImage = tk.PhotoImage(file = 'volume.gif')
        self.volumeOutImage = tk.PhotoImage(file = 'volume out.gif')
        shuffleImage = tk.PhotoImage(file = 'shuffle.gif')
        self.repeatImage = tk.PhotoImage(file = 'repeat.gif')
        self.repeatOnceImage = tk.PhotoImage(file = 'repeat1.gif')
        searchImage = tk.PhotoImage(file = 'search.gif')
        webImage = tk.PhotoImage(file='_landscape2.gif')
        videoDownloadImage = tk.PhotoImage(file = 'd1.gif')
        downloadCancelImage = tk.PhotoImage(file = 'd2.gif')
        self.repeat = Repeat()
        self.repeatVar = tk.IntVar()
        # playlist menu
        #...................................................
        #...................................................
        #..................................................
        self.playlistMenuBar = tk.Menu(self.window)
        self.window.config(menu=self.playlistMenuBar)
        self.playlistMenu = tk.Menu(self.playlistMenuBar, tearoff=0)
        self.playlistMenuBar.add_cascade(label="playlist", menu=self.playlistMenu)
        self.playlistMenu.add_command(label= 'Add new', command = self.createPlaylist)
        ttk.Checkbutton(self.hifiButtonCanvas, image = shuffleImage, variable = self.shuffle, command = self.processShuffle)\
            .grid(row = 0, column = 0, padx = 10)
        self.repeatButton = ttk.Checkbutton(self.hifiButtonCanvas, image=self.repeatImage, variable=self.repeatVar, command=self.processRepeat)
        self.repeatButton.grid(row=0, column=1, padx=10)
        ttk.Button(self.hifiButtonCanvas, image = prevImage, command = self.previous).grid(row = 0, column = 2)
        ttk.Button(self.hifiButtonCanvas, image = stopImage, command = self.stop).grid(row = 0, column = 3)
        ttk.Button(self.hifiButtonCanvas, image = playImage, command = self.play).grid(row = 0, column = 4)
        ttk.Button(self.hifiButtonCanvas, image = pauseImage, command = self.pause).grid(row = 0, column = 5)
        ttk.Button(self.hifiButtonCanvas, image = nextImage, command = self.next).grid(row = 0, column = 6)
        self.volumeImageLabel = ttk.Label(self.hifiButtonCanvas, image = self.volumeImage)
        self.volumeImageLabel.grid(row = 0, column = 7, padx = 5, pady = 10)
        self.volumeLineCanvas = tk.Canvas(self.hifiButtonCanvas, bg = "#000000", width = 100, height = 10)
        self.volumeLineCanvas.grid(row = 0, column = 8)
        self.volumeLineCanvas.create_rectangle(0, 0, currentVolumeInPixel, 12, tags = 'rect', fill = '#00c8ff')
        self.volumeLineCanvas.bind('<Button-1>', self.changeVolume)
        self.volumeLineCanvas.bind('<Key>', self.changeVolume)
        ttk.Button(self.hifiButtonCanvas, text = "Reload", command = lambda: Thread(target=self.updateSongList, args=[], daemon=True).start()).\
            grid(row= 0, column = 9, ipadx = 0, padx = 5)
        self.songFrame = tk.Frame(tab2, bg = "#000000")
        self.songFrame.pack()
        self.yScroll = ttk.Scrollbar(self.songFrame, orient=tk.VERTICAL)
        self.yScroll.grid(row=0, column=1, sticky=tk.N + tk.S)
        self.listBox = tk.Listbox(self.songFrame, width = 115, height = 21, selectmode = tk.SINGLE, yscrollcommand=self.yScroll.set, \
                                  bg = "#000000", fg = "cyan", activestyle = 'dotbox', font = 'Helvetica 12', selectforeground = '#ffffff')
        self.yScroll['command'] = self.listBox.yview
        self.listBox.tk_focusFollowsMouse()
        self.listBox.bind('<Return>', self.playMusic)
        self.listBox.bind('<Button-1>', self.playMusic)
        self.listBox.bind('<Enter>', self.highlight)
        self.listBox.bind('<Leave>', self.unhighlight)
        self.listBox.bind('<Motion>', self.highlight)
        self.listBox.bind('<Button-3>', self.processPopup)
        self.listBox.grid(row = 0, column = 0)
        self.searchFrame = tk.Frame(tab3)
        self.searchFrame.pack()
        self.searchListBoxFrame = tk.Frame(tab3)
        self.searchListBoxFrame.pack()
        self.searchSong = tk.StringVar()
        ttk.Label(self.searchFrame, text = 'Enter:').grid(row = 0, column = 0, padx = 20, pady = 5)
        ttk.Entry(self.searchFrame, textvariable = self.searchSong, justify = tk.LEFT, width = 50).\
            grid(row = 0, column = 1, pady = 5)
        ttk.Button(self.searchFrame, image = searchImage, command = self.searchForSong).grid(row = 0, column = 2, pady = 5)
        self.yviewScroll = ttk.Scrollbar(self.searchListBoxFrame, orient=tk.VERTICAL)
        self.yviewScroll.grid(row=1, column=1, sticky=tk.N + tk.S)
        self.searchlistBox = tk.Listbox(self.searchListBoxFrame, width=115, height=19, selectmode=tk.SINGLE,\
                                        yscrollcommand=self.yviewScroll.set, bg="#000000", fg="cyan", activestyle='dotbox',\
                                        font='Helvetica 12')
        self.yviewScroll['command'] = self.searchlistBox.yview
        self.searchlistBox.tk_focusFollowsMouse()
        self.searchlistBox.bind('<Return>', self.playSearch)
        self.searchlistBox.bind('<Button-1>', self.playSearch)
        self.searchlistBox.bind('<Button-3>', self.processSearchPopup)
        self.searchlistBox.bind('<Enter>', self.highlightSearchList)
        self.searchlistBox.bind('<Leave>', self.unhighlightSearchList)
        self.searchlistBox.bind('<Motion>', self.highlightSearchList)
        self.searchlistBox.grid(row=1, column=0)

        self.downloadFrame = tk.Frame(tab4)
        self.downloadFrame.pack()
        self.songName = tk.StringVar()
        self.artistName = tk.StringVar()
        ttk.Label(self.downloadFrame, text = 'Artist:').grid(row = 0, column = 0, padx = 20, pady = 5)
        ttk.Entry(self.downloadFrame, textvariable = self.artistName, justify = tk.LEFT, width = 50).\
            grid(row = 0, column = 1, pady = 5)
        ttk.Label(self.downloadFrame, text = 'Song Title:').grid(row = 1, column = 0, padx = 20, pady = 5)
        ttk.Entry(self.downloadFrame, textvariable = self.songName, justify = tk.LEFT, width = 50).\
            grid(row = 1, column = 1, pady = 5)
        ttk.Button(self.downloadFrame, image = searchImage, command = self.searchSongInWeb).grid(row = 1, column = 2, padx = 5, pady = 5)
        ttk.Button(self.downloadFrame, image=downloadCancelImage, command=self.cancelMusicDownload). \
            grid(row=1, column=3, padx=5, pady=5, sticky=tk.S)
        downloadCanvas = tk.Canvas(tab4, width = 1050, height = 330, bg = "#000000")
        downloadCanvas.pack()
        downloadCanvas.create_image(530, 175, image=webImage)

        self.videoFrame = tk.Frame(tab5, bg = '#000000', width = 1050, height = 200)
        self.videoFrame.grid_propagate(0)
        self.videoFrame.pack()
        #downloadVideoCanvas = tk.Canvas(tab5, width=1050, height = 222, bg="#000000")
        #downloadVideoCanvas.pack()
        #downloadVideoCanvas.create_image(530, 100, image=webImage)

        self.movieName = tk.StringVar()
        self.episode = tk.StringVar()
        self.season = tk.StringVar()
        self.website = tk.StringVar()

        ttk.Label(self.videoFrame, text = 'Website:').grid(row=0, column = 0, padx = 5, pady = 5, sticky= tk.W)
        website_choice = ttk.Combobox(self.videoFrame, width = 50, textvariable = self.website, state= 'readonly')
        website_choice['values'] = ("Netnaija", "TFPDL")
        website_choice.grid(row = 0, column = 1)
        website_choice.current(1)

        ttk.Label(self.videoFrame, text='Movie Name:').grid(row=1, column=0, padx=5, pady=5, sticky = tk.W)
        ttk.Entry(self.videoFrame, textvariable=self.movieName, justify=tk.LEFT, width=53). \
            grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(self.videoFrame, text='Season:').grid(row=2, column=0, padx=5, pady=5, sticky = tk.W)
        season = ttk.Combobox(self.videoFrame, width = 50, textvariable = self.season)
        season['values'] = (1,2,3,4,5,6,7,8,9,10)
        season.grid(row = 2, column = 1, padx = 5, pady = 5)
        ttk.Label(self.videoFrame, text='Episode:').grid(row=3, column=0, padx=5, pady=5, sticky = tk.W)
        episode = ttk.Combobox(self.videoFrame, width=50, textvariable=self.episode)
        episode['values'] = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
        episode.grid(row=3, column=1, padx=5, pady=5)
        ttk.Button(self.videoFrame, image=videoDownloadImage, command=self.searchVideoInWeb).\
            grid(row=4, column=0, padx=5, pady=5, sticky = tk.S)
        ttk.Button(self.videoFrame, image=downloadCancelImage, command=self.cancelDownload). \
            grid(row=4, column=1, padx=5, pady=5, sticky = tk.S)

        # display playlists tabs if any
        self.playlistListBox = []
        self.playlistFrame = []
        self.playlistScroll = []
        self.userPlaylistMenu = []
        for counter in range(0, len(playListNames)):
            tab = ttk.Frame(self.tabcontrol)
            self.tabcontrol.add(tab, text="    " + playListNames[counter].strip() + "    ")
            self.tabs.append(tab)
            frame = tk.Frame(tab, bg = 'gray')
            frame.pack()
            self.playlistFrame.append(frame)
            self.playlistScroll.append(ttk.Scrollbar(self.playlistFrame[counter], orient = tk.VERTICAL))
            self.playlistScroll[counter].grid(row=0, column=1, sticky = tk.N + tk.S)
            self.playlistListBox.append(tk.Listbox(self.playlistFrame[counter], width = 115, height = 21, selectmode = tk.SINGLE,\
                                                   yscrollcommand = self.playlistScroll[counter].set, bg = "#000000", fg = "cyan", activestyle = 'dotbox',\
                                                   font = 'Helvetica 12'))
            self.playlistListBox[counter].grid(row = 0, column = 0)
            self.playlistScroll[counter]['command'] = self.playlistListBox[counter].yview
            tabID += 1
            songPlayingFromPlaylist.append(False)
            currentIndexPlayingInPlaylist.append(0)

            def handler(event, self=self, i=counter):
                type = event.type
                if event.num == 1:
                    return self.playPlaylistMusic(event, i)
                elif event.keysym == 'Return':
                    return self.playPlaylistMusic(event, i)
                elif str(type) == 'Enter':
                    return self.highlightPlaylist(event, i)
                elif str(type) == 'Leave':
                    return self.unhighlightPlaylist(event, i)
                elif str(type) == 'Motion':
                    return self.highlightPlaylist(event, i)
                elif event.num == 3:
                    return self.processPlaylistPopup(event, i)

            self.playlistListBox[counter].bind('<Return>', handler)
            self.playlistListBox[counter].bind('<Button-1>', handler)
            self.playlistListBox[counter].bind('<Enter>', handler)
            self.playlistListBox[counter].bind('<Leave>', handler)
            self.playlistListBox[counter].bind('<Motion>', handler)
            self.playlistListBox[counter].bind('<Button-3>', handler)

            self.userPlaylistMenu.append(tk.Menu(self.playlistListBox[counter], tearoff = 0, bg="#000000", fg='cyan', font='Times 8 bold'))
            self.userPlaylistMenu[counter].add_command(label = 'Play', command = self.playSelectionInPlaylist, columnbreak = 1)
            self.userPlaylistMenu[counter].add_command(label='Play Next', command= self.setNextInPlaylist, columnbreak=1)
            self.userPlaylistMenu[counter].add_command(label='Remove', command= self.removeSongFromPlaylist, columnbreak=1)
            self.userPlaylistMenu[counter].add_command(label='Properties', command= self.showPlaylistProperty, columnbreak=1)



        #populate the playlist listbox if any content has been added before
        i = 0
        for row in playListContent:
            for col in row:
                self.playlistListBox[i].insert(tk.END, col)
            i += 1
        # display playlist names under playlist if any
        if len(playListNames) == 1:
            self.playlistMenu.add_command(label=playListNames[0], command=lambda: self.switchToPlaylistTab(0))
        elif len(playListNames) == 2:
            self.playlistMenu.add_command(label=playListNames[0], command=lambda: self.switchToPlaylistTab(0))
            self.playlistMenu.add_command(label=playListNames[1], command=lambda: self.switchToPlaylistTab(1))

        #menu commands for the main listbox
        self.playlistOptionsMenu = tk.Menu(self.listBox, tearoff=0, bg="#000000", fg='cyan', font='Times 8 bold')
        self.menu = tk.Menu(self.listBox, tearoff = 0, bg = "#000000", fg = 'cyan', font = 'Times 8 bold')
        self.menu.add_command(label = 'Play', command = self.playSelection, columnbreak = 1)
        self.menu.add_command(label = 'Play Next', command = self.setNextIndex, columnbreak = 1)
        self.menu.add_command(label = 'Delete', command = self.deleteSong, columnbreak = 1)
        self.menu.add_command(label = 'Properties', command = self.showProperties, columnbreak = 1)
        self.menu.add_cascade(label = "Add to", menu = self.playlistOptionsMenu, columnbreak = 1)

        #menu commands for the search listbox
        self.searchPlaylistOptionsMenu = tk.Menu(self.searchlistBox, tearoff=0, bg="#000000", fg='cyan', font='Times 8 bold')
        self.searchmenu = tk.Menu(self.searchlistBox, tearoff=0, bg="#000000", fg='cyan', font = 'Times 8 bold')
        self.searchmenu.add_command(label='Play', command=self.playSearchSelection, columnbreak = 1)
        self.searchmenu.add_command(label='Play Next', command=self.setNextSearchIndex, columnbreak = 1)
        self.searchmenu.add_command(label='Delete', command=self.deleteSongSearch, columnbreak = 1)
        self.searchmenu.add_command(label='Properties', command=self.showSearchedSongProperties, columnbreak = 1)
        self.searchmenu.add_cascade(label = "Add to", menu = self.searchPlaylistOptionsMenu, columnbreak = 1)

        if len(playListNames) == 1:
            self.playlistOptionsMenu.add_command(label=playListNames[0], command=self.addToPlaylist0FromListbox, columnbreak = 1)
            self.searchPlaylistOptionsMenu.add_command(label = playListNames[0], command = self.addToPlaylist0FromSearchListbox, columnbreak = 1)
        elif len(playListNames) == 2:
            self.playlistOptionsMenu.add_command(label=playListNames[0], command=self.addToPlaylist0FromListbox, columnbreak = 1)
            self.playlistOptionsMenu.add_command(label=playListNames[1], command=self.addToPlaylist1FromListbox, columnbreak = 1)
            self.searchPlaylistOptionsMenu.add_command(label=playListNames[0], command=self.addToPlaylist0FromSearchListbox, columnbreak = 1)
            self.searchPlaylistOptionsMenu.add_command(label=playListNames[1], command=self.addToPlaylist1FromSearchListbox, columnbreak = 1)
        self.window.protocol("WM_DELETE_WINDOW", self.close)

        self.fillListBox()
        self.seasonQueue = Queue(maxsize=2)
        self.episodeQueue = Queue(maxsize=2)
        self.movieNameQueue = Queue(maxsize=2)
        self.artistNameQueue = self.songNameQueue = Queue(maxsize=2)
        self.musicDownloadExecutor = ThreadPoolExecutor(max_workers=1)
        self.musicDownloadList = Queue(maxsize=2)
        self.videoDownloadExecutor = ThreadPoolExecutor(max_workers=1)
        self.videoDownloadList = Queue(maxsize=2)
        self.videoDownloadSite = Queue(maxsize=2)
        self.window.mainloop()

    #function on another thread called to load the songs from the ROM to a list before the Player starts
    def loadSongs(self):
        try:
            searchForSongs()
            update()
            self.properties = Properties(musicFilePathList)
        except tk.TclError:
            pass

    def fillListBox(self):
        for elem in musicFilenameList:
            self.listBox.insert(tk.END, elem)

    def searchSongInWeb(self):
        try:
            self.songNameQueue.put(self.songName.get(), block=False)
            self.artistNameQueue.put(self.artistName.get(), block=False)
            self.musicDownloadList.put(self.musicDownloadExecutor.submit(self.scrapeMp3paw), block=False)
        except Full:
            tkinter.messagebox.showerror('Error Message', 'ERROR: Cant have more than one download(s) queued')

    def scrapeMp3paw(self):
        try:
            self.musicDownload = MusicDownload()
            self.musicDownload.mp3pawscraper(self.artistNameQueue.get(), self.songNameQueue.get())
            if not musicDownloadNotification.empty():
                downloadMessage()
                tkinter.messagebox.showinfo('Download Message', f'Download Complete')
                while not musicDownloadNotification.empty():
                    _ = musicDownloadNotification.get(block=False)
                self.updateSongList()
        except ElementClickInterceptedException:
            tkinter.messagebox.showerror('Error Message', f'{musicDownloadErrors.get()}')
        except WebDriverException:
                tkinter.messagebox.showerror('Error Message', f'{musicDownloadErrors.get()}')
        except FileNotFoundError:
            tkinter.messagebox.showerror('Error Message', f'{musicDownloadErrors.get()}')
        except BaseException:
            tkinter.messagebox.showerror('Error Message', f'{musicDownloadErrors.get()}')
        finally:
            # delete task from queue
            self.musicDownloadList.get(block=False)
            while musicDownloadCancelledFlag.empty() == False:
                _ = musicDownloadCancelledFlag.get(block=False)
            while musicDownloadErrors.empty() == False:
                _ = musicDownloadErrors.get(block=False)

    def cancelMusicDownload(self):
        try:
            if self.musicDownloadList.qsize() != 0:
                musicDownloadCancelledFlag.put(True, block=False)
        except Full:
            tkinter.messagebox.showerror('Error Message:', 'ERROR: No download is ongoing')

    def searchVideoInWeb(self):
        try:
            self.movieNameQueue.put(self.movieName.get(), block=False)
            self.seasonQueue.put(self.season.get(), block=False)
            self.episodeQueue.put(self.episode.get(), block=False)
            if self.website.get() == 'Netnaija':
                self.videoDownloadSite.put('N', block=False)
                self.videoDownloadList.put(self.videoDownloadExecutor.submit(self.scrapeNetnaija), block = False)
            elif self.website.get() == 'TFPDL':
                self.videoDownloadSite.put('T', block=False)
                self.videoDownloadList.put(self.videoDownloadExecutor.submit(self.scrapeTFPDL), block = False)
        except Full:
            tkinter.messagebox.showerror('Error Message', 'ERROR: Cant have more than one download(s) queued')

    def scrapeNetnaija(self):
        try:
            self.videoDownload = VideoDownLoad()
            mp4Link, srtLink = self.videoDownload.findFileLink(self.movieNameQueue.get(), self.seasonQueue.get(), self.episodeQueue.get())
            downloadExecutorList = []
            with ThreadPoolExecutor(max_workers=2) as downloadExecutor:
                downloadExecutorList.append(downloadExecutor.submit(self.videoDownload.startMP4Download, (mp4Link)))
                downloadExecutorList.append(downloadExecutor.submit(self.videoDownload.startSRTDownload, (srtLink)))
            for downloadResults in as_completed(downloadExecutorList):
                downloadResults.result()
            # if both downloads are complete and successful
            if videoDownloadNotification.empty() == False:
                downloadMessage()
                tkinter.messagebox.showinfo('Download Message', f'Download Complete')
                while not videoDownloadNotification.empty():
                    _ = videoDownloadNotification.get(block=False)
                
        except IndexError:
            tkinter.messagebox.showerror('Error Message', f'{videoDownloadErrors.get()}')
        except FileNotFoundError:
            tkinter.messagebox.showerror('Error Message', f'{videoDownloadErrors.get()}')
        except ElementClickInterceptedException:
            tkinter.messagebox.showerror('Error Message', f'{videoDownloadErrors.get()}')
        except InvalidArgumentException:
            tkinter.messagebox.showerror('Error Message', f'{videoDownloadErrors.get()}')
        except TimeoutException:
            tkinter.messagebox.showerror('Error Message', f'{videoDownloadErrors.get()}')
        except NoSuchElementException:
            tkinter.messagebox.showerror('Error Message', f'{videoDownloadErrors.get()}')
        except WebDriverException:
                tkinter.messagebox.showerror('Error Message', f'{videoDownloadErrors.get()}')
        except BaseException:
            tkinter.messagebox.showerror('Error Message', f'{videoDownloadErrors.get()}')
        finally:
            # delete task from queue
            self.videoDownloadList.get(block=False)
            self.videoDownloadSite.get(block=False)
            while videoDownloadCancelledFlag.empty() == False:
                _ = videoDownloadCancelledFlag.get(block=False)
            while videoDownloadErrors.empty() == False:
                _ = videoDownloadErrors.get(block=False)

    def scrapeTFPDL(self):
        try:
            self.tfpdlVideoDownload = TFPDLVideoDownload()
            self.tfpdlVideoDownload.download(self.movieNameQueue.get(), self.seasonQueue.get(), self.episodeQueue.get())
            if tfpdl_videoDownloadNotification.empty() == False:
                downloadMessage()
                tkinter.messagebox.showinfo('Download Message', f'Download Complete')
                while not tfpdl_videoDownloadNotification.empty():
                    _ = tfpdl_videoDownloadNotification.get(block=False)
        except IndexError:
            tkinter.messagebox.showerror('Error Message', f'{tfpdl_videoDownloadErrors.get()}')
        except FileNotFoundError:
            tkinter.messagebox.showerror('Error Message', f'{tfpdl_videoDownloadErrors.get()}')
        except AssertionError:
            tkinter.messagebox.showerror('Error Message', f'{tfpdl_videoDownloadErrors.get()}')
        except ElementClickInterceptedException:
            tkinter.messagebox.showerror('Error Message', f'{tfpdl_videoDownloadErrors.get()}')
        except InvalidArgumentException:
            tkinter.messagebox.showerror('Error Message', f'{tfpdl_videoDownloadErrors.get()}')
        except TimeoutException:
            tkinter.messagebox.showerror('Error Message', f'{tfpdl_videoDownloadErrors.get()}')
        except NoSuchElementException:
            tkinter.messagebox.showerror('Error Message', f'{tfpdl_videoDownloadErrors.get()}')
        except WebDriverException:
                tkinter.messagebox.showerror('Error Message', f'{tfpdl_videoDownloadErrors.get()}')
        except BaseException:
            tkinter.messagebox.showerror('Error Message', f'{tfpdl_videoDownloadErrors.get()}')
        finally:
            # delete task from queue
            self.videoDownloadList.get(block=False)
            self.videoDownloadSite.get(block=False)
            while tfpdl_videoDownloadCancelledFlag.empty() == False:
                _ = tfpdl_videoDownloadCancelledFlag.get(block=False)
            while tfpdl_videoDownloadErrors.empty() == False:
                _ = tfpdl_videoDownloadErrors.get(block=False)


    def cancelDownload(self):
        try:
            if self.videoDownloadList.qsize() != 0:
                letter = self.videoDownloadSite.get(block=False)
                if letter == 'N':
                    videoDownloadCancelledFlag.put(True, block=False)
                elif letter == 'T':
                    tfpdl_videoDownloadCancelledFlag.put(True, block=False)
        except Full:
            tkinter.messagebox.showerror('Error Message:', 'ERROR: No download is ongoing')
        except Empty:
            pass

    def updateSongList(self):
        sleep(12)
        try:
            searchForSongs()
            update()
        except tk.TclError:
            pass
        self.listBox.delete(0, len(musicFilenameList)-1)
        self.fillListBox()
        self.properties.clearLists()
        self.properties.loadProperties(musicFilePathList)

    def highlight(self, event):
        global popupON
        global popupCounter
        if popupON is not True:
            self.listBox.selection_clear(0, tk.END)
            self.listBox.selection_set(self.listBox.nearest(event.y))
        elif popupON is True:
            popupCounter += 1
            if popupCounter == 2:
                popupCounter = 0
                popupON = False

    def unhighlight(self, event):
        self.listBox.selection_clear(0, tk.END)

    def highlightSearchList(self, event):
        global popupON
        global popupCounter
        global yposition
        yposition = event.y
        if popupON is not True:
            self.searchlistBox.selection_clear(0, tk.END)
            self.searchlistBox.selection_set(self.searchlistBox.nearest(event.y))
        elif popupON is True:
            popupCounter += 1
            if popupCounter == 2:
                popupCounter = 0
                popupON = False

    def unhighlightSearchList(self, event):
        self.searchlistBox.selection_clear(0, tk.END)

    def highlightPlaylist(self, event, tabid=0):
        if len(self.tabs) == 5:
            tabid = 0
        global popupON
        global popupCounter
        global yposition
        yposition = event.y
        if popupON is not True:
            self.playlistListBox[tabid].selection_clear(0, tk.END)
            self.playlistListBox[tabid].selection_set(self.playlistListBox[tabid].nearest(event.y))
        elif popupON is True:
            popupCounter += 1
            if popupCounter == 2:
                popupCounter = 0
                popupON = False

    def unhighlightPlaylist(self, event, tabid=0):
        if len(self.tabs) == 5:
            tabid = 0
        self.playlistListBox[tabid].selection_clear(0, tk.END)

    def playSelection(self):
        global currentSong, previousSongIndex
        global musicTrackerPosition
        global popupON
        global currentEvent
        global songPlayingFromSearchList
        global currentIndexPlayingInSearchList
        global songPlayingFromPlaylist, currentIndexPlayingInPlaylist
        currentIndexPlayingInSearchList = 0
        songPlayingFromSearchList = False
        for _ in range(len(playListNames)):
            currentIndexPlayingInPlaylist[_] = 0
            songPlayingFromPlaylist[_] = False
        popupON = False
        musicTrackerPosition = 0
        self.subWooferCanvas.delete('text')
        self.subWooferCanvas.update()
        if currentEvent == play or currentEvent == pause:
            global timerStart
            timerStart = False
            self.timerThread.join()
        self.musicLineCanvas.delete('line')
        self.musicLineCanvas.update()
        self.listBox.selection_clear(0, tk.END)
        self.listBox.selection_set(self.listBox.nearest(yposition))
        previousSongIndex = currentSong
        currentSong = self.listBox.curselection()[0]
        currentEvent = play
        self.Play(self.listBox.curselection()[0])

    def playSearchSelection(self):
        global currentSong, previousSongIndex
        global musicTrackerPosition
        global popupON
        global songPlayingFromSearchList
        global currentEvent
        global currentIndexPlayingInSearchList
        global songPlayingFromPlaylist, currentIndexPlayingInPlaylist
        for _ in range(len(playListNames)):
            currentIndexPlayingInPlaylist[_] = 0
            songPlayingFromPlaylist[_] = False
        songPlayingFromSearchList = True
        currentIndexPlayingInSearchList = 0
        popupON = False
        musicTrackerPosition = 0
        self.subWooferCanvas.delete('text')
        self.subWooferCanvas.update()
        self.musicLineCanvas.delete('line')
        self.musicLineCanvas.update()
        if currentEvent == play or currentEvent == pause:
            global timerStart
            timerStart = False
            self.timerThread.join()
        self.searchlistBox.selection_clear(0, tk.END)
        self.searchlistBox.selection_set(self.searchlistBox.nearest(yposition))
        index = self.searchListSongIndex[self.searchlistBox.curselection()[0]]
        currentIndexPlayingInSearchList = index
        previousSongIndex = currentSong
        currentSong = musicFilenameList.index(musicFilenameList[index])
        currentEvent = play
        self.Play(musicFilenameList.index(musicFilenameList[index]))

    def playSelectionInPlaylist(self):
        global currentSong, previousSongIndex
        global musicTrackerPosition
        global popupON
        global songPlayingFromSearchList
        global currentIndexPlayingInSearchList
        global currentEvent
        global songPlayingFromPlaylist, currentIndexPlayingInPlaylist
        tabid = playlistTabCurrentlyOn
        if len(playListContent) == 1:
            currentIndexPlayingInPlaylist[tabid] = 0
            songPlayingFromPlaylist[tabid] = True
        elif len(playListContent) == 2:
            if tabid == 0:
                currentIndexPlayingInPlaylist[tabid] = 0
                songPlayingFromPlaylist[tabid] = True
                currentIndexPlayingInPlaylist[1], songPlayingFromPlaylist[1] = 0, False
            else:
                currentIndexPlayingInPlaylist[tabid] = 0
                songPlayingFromPlaylist[tabid] = True
                currentIndexPlayingInPlaylist[0], songPlayingFromPlaylist[0] = 0, False
        songPlayingFromSearchList = False
        currentIndexPlayingInSearchList = 0
        popupON = False
        musicTrackerPosition = 0
        self.subWooferCanvas.delete('text')
        self.subWooferCanvas.update()
        self.musicLineCanvas.delete('line')
        self.musicLineCanvas.update()
        if currentEvent == play or currentEvent == pause:
            global timerStart
            timerStart = False
            self.timerThread.join()
        self.playlistListBox[tabid].selection_clear(0, tk.END)
        self.playlistListBox[tabid].selection_set(self.playlistListBox[tabid].nearest(yposition))
        index = playListMusicIndex[tabid][self.playlistListBox[tabid].curselection()[0]]
        currentIndexPlayingInPlaylist[tabid] = index
        previousSongIndex = currentSong
        currentSong = musicFilenameList.index(musicFilenameList[index])
        currentEvent = play
        self.Play(currentSong)

    def setNextIndex(self):
        global nextSongIndex
        global playNext
        global popupON
        popupON = False
        self.listBox.selection_clear(0, tk.END)
        self.listBox.selection_set(self.listBox.nearest(yposition))
        nextSongIndex = self.listBox.curselection()[0]
        playNext = True

    def setNextSearchIndex(self):
        global nextSongIndex
        global playNext
        global popupON
        popupON = False
        self.searchlistBox.selection_clear(0, tk.END)
        self.searchlistBox.selection_set(self.searchlistBox.nearest(yposition))
        nextSongIndex = self.searchListSongIndex[self.searchlistBox.curselection()[0]]
        playNext = True

    def setNextInPlaylist(self):
        global nextSongIndex
        global playNext
        global popupON
        popupON = False
        tabid = playlistTabCurrentlyOn
        self.playlistListBox[tabid].selection_clear(0, tk.END)
        self.playlistListBox[tabid].selection_set(self.playlistListBox[tabid].nearest(yposition))
        nextSongIndex = playListMusicIndex[tabid][self.playlistListBox[tabid].curselection()[0]]
        playNext = True

    def deleteSong(self):
        global popupON
        popupON = False
        self.listBox.selection_clear(0, tk.END)
        self.listBox.selection_set(self.listBox.nearest(yposition))
        indexToDelete = self.listBox.curselection()[0]
        answer = tkinter.messagebox.askokcancel('<Delete file>', f'''Are you sure you want to delete this?
        {musicFilenameList[indexToDelete]} wont be on this device anymore''')
        if answer:
            try:
                os.unlink(musicFilePathList[indexToDelete])
                musicFilenameList.remove(musicFilenameList[indexToDelete])
                musicFilePathList.remove(musicFilePathList[indexToDelete])
                self.listBox.delete(0, len(musicFilenameList))
                for elem in musicFilenameList:
                    self.listBox.insert(tk.END, elem)
                self.checkAndUpdatePlaylists(indexToDelete)
                self.properties.loadProperties(musicFilePathList)
            except PermissionError as error:
                tkinter.messagebox.showerror('<Delete Error>', error)
        else:
            pass

    def deleteSongSearch(self):
        global popupON
        popupON = False
        self.searchlistBox.selection_clear(0, tk.END)
        self.searchlistBox.selection_set(self.searchlistBox.nearest(yposition))
        indexToDelete = self.searchlistBox.curselection()[0]
        fileToDelete = self.list[indexToDelete]
        indexToDelete = musicFilenameList.index(fileToDelete)
        answer = tkinter.messagebox.askokcancel('<Delete file>', f'''Are you sure you want to delete this?
        {fileToDelete} wont be on this device anymore''')
        if answer:
            try:
                os.unlink(musicFilePathList[indexToDelete])
                self.list.remove(fileToDelete)
                self.searchListSongIndex.remove(musicFilenameList.index(fileToDelete))
                musicFilenameList.remove(musicFilenameList[indexToDelete])
                musicFilePathList.remove(musicFilePathList[indexToDelete])
                self.listBox.delete(0, len(musicFilenameList))
                self.searchlistBox.delete(0, len(self.searchListSongIndex))
                for elem in self.list:
                    self.searchlistBox.insert(tk.END, elem)
                for elem in musicFilenameList:
                    self.listBox.insert(tk.END, elem)
                self.checkAndUpdatePlaylists(indexToDelete)
                self.properties.loadProperties(musicFilePathList)
            except PermissionError as error:
                tkinter.messagebox.showerror('<Delete Error>', error)
        else:
            pass

    def checkAndUpdatePlaylists(self, indexToDelete):
        i = 0
        for playlist in playListNames:
            if indexToDelete in playListMusicIndex[i]:
                index = playListMusicIndex[i].index(indexToDelete)
                del playListMusicIndex[i][index]
                del playListContent[i][index]
            else:
                for counter in range(len(playListContent[i])):
                    playListMusicIndex[i][counter] = musicFilenameList.index(playListContent[i][counter])
            file = open(playlist.strip() + 'MI.txt', 'w')
            file2 = open(playlist.strip() + '.txt', 'w')
            for counter in range(len(playListMusicIndex[i])):
                file.write(str(playListMusicIndex[i][counter]) + '\n')
                file2.write(playListContent[i][counter] + '\n')
            file.close()
            file2.close()
            self.playlistListBox[i].delete(0, len(playListMusicIndex[i]))
            for music in playListContent[i]:
                self.playlistListBox[i].insert(tk.END, music)
            i += 1

    def removeSongFromPlaylist(self):
        global popupON
        global playListContent
        global playListMusicIndex
        popupON = False
        tabid = playlistTabCurrentlyOn
        self.playlistListBox[tabid].selection_clear(0, tk.END)
        self.playlistListBox[tabid].selection_set(self.playlistListBox[tabid].nearest(yposition))
        indexToRemove = self.playlistListBox[tabid].curselection()[0]
        self.playlistListBox[tabid].delete(0, len(playListContent[tabid]))
        del playListContent[tabid][indexToRemove]
        del playListMusicIndex[tabid][indexToRemove]
        file = open(playListNames[tabid].strip() + '.txt', 'w')
        for _ in playListContent[tabid]:
            file.write(_ + '\n')
            self.playlistListBox[tabid].insert(tk.END, _)
        file.close()
        file = open(playListNames[tabid].strip() + 'MI.txt', 'w')
        for _ in playListMusicIndex[tabid]:
            file.write(str(_) + '\n')
        file.close()

    def showProperties(self):
        try:
            global popupON
            popupON = False
            self.listBox.selection_clear(0, tk.END)
            self.listBox.selection_set(self.listBox.nearest(yposition))
            indexToShowProperties = self.listBox.curselection()[0]
            length = MP3(musicFilePathList[indexToShowProperties]).info.length
            length = round(length)
            minutes = length // 60
            seconds = length % 60
            minutesInString = str(minutes)
            secondsInString = str(seconds)
            if minutes < 10:
                minutesInString = '0' + str(minutes)
            if seconds < 10:
                secondsInString = '0' + str(seconds)
            time = minutesInString + ':' + secondsInString
            tkinter.messagebox.showinfo('<File Properties>', f'''
Song title: {self.properties.songNameList[indexToShowProperties]}
Artist: {self.properties.artistList[indexToShowProperties]}
Genre:  {self.properties.genreList[indexToShowProperties]}
Album: {self.properties.albumList[indexToShowProperties]}
Length: {time}
Year: {self.properties.songYear[indexToShowProperties]}
file Location: {musicFilePathList[indexToShowProperties]}
''')
        except HeaderNotFoundError as error:
            tkinter.messagebox.showerror('Error Message', f"Error encountered trying to read mp3 file\n{error}")
        except MutagenError as error:
            tkinter.messagebox.showerror('Error Message', f"Error encountered trying to read mp3 file\n{error}")

    def showSearchedSongProperties(self):
        try:
            global popupON
            popupON = False
            self.searchlistBox.selection_clear(0, tk.END)
            self.searchlistBox.selection_set(self.searchlistBox.nearest(yposition))
            indexToShowProperties = self.searchlistBox.curselection()[0]
            fileToShowProperties = self.list[indexToShowProperties]
            indexToShowProperties = musicFilenameList.index(fileToShowProperties)
            length = MP3(musicFilePathList[indexToShowProperties]).info.length
            length = round(length)
            minutes = length // 60
            seconds = length % 60
            minutesInString = str(minutes)
            secondsInString = str(seconds)
            if minutes < 10:
                minutesInString = '0' + str(minutes)
            if seconds < 10:
                secondsInString = '0' + str(seconds)
            time = minutesInString + ':' + secondsInString
            tkinter.messagebox.showinfo('<File Properties>',f'''
title: {self.properties.songNameList[indexToShowProperties]}
Artist: {self.properties.artistList[indexToShowProperties]}
Genre: {self.properties.genreList[indexToShowProperties]}
Album: {self.properties.albumList[indexToShowProperties]}
Length: {time}
Year: {self.properties.songYear[indexToShowProperties]}
file Location: {musicFilePathList[indexToShowProperties]}
''')
        except HeaderNotFoundError as error:
            tkinter.messagebox.showerror('Error Message', f"Error encountered trying to read mp3 file\n{error}")
        except MutagenError as error:
            tkinter.messagebox.showerror('Error Message', f"Error encountered trying to read mp3 file\n{error}")

    def showPlaylistProperty(self):
        global popupON
        popupON = False
        tabid = playlistTabCurrentlyOn
        try:
            self.playlistListBox[tabid].selection_clear(0, tk.END)
            self.playlistListBox[tabid].selection_set(self.playlistListBox[tabid].nearest(yposition))
            index = self.playlistListBox[tabid].curselection()
            indexToShowProperties = playListMusicIndex[tabid][index[0]]
            length = MP3(musicFilePathList[indexToShowProperties]).info.length
            length = round(length)
            minutes = length // 60
            seconds = length % 60
            minutesInString = str(minutes)
            secondsInString = str(seconds)
            if minutes < 10:
                minutesInString = '0' + str(minutes)
            if seconds < 10:
                secondsInString = '0' + str(seconds)
            time = minutesInString + ':' + secondsInString
            tkinter.messagebox.showinfo('<File Properties>', f'''
            title: {self.properties.songNameList[indexToShowProperties]}
            Artist: {self.properties.artistList[indexToShowProperties]}
            Genre: {self.properties.genreList[indexToShowProperties]}
            Album: {self.properties.albumList[indexToShowProperties]}
            Length: {time}
            Year: {self.properties.songYear[indexToShowProperties]}
            file Location: {musicFilePathList[indexToShowProperties]}
            ''')
        except IndexError:
            pass


    def processShuffle(self):
        pass

    def processRepeat(self):
        global currentSong
        global nextSongIndex, playNext
        self.repeat.changeState()
        if self.repeat.getValue() == 2:
            self.repeatVar.set(1)
            self.repeatButton["image"] = self.repeatOnceImage
            playNext = True
            nextSongIndex = currentSong
        elif self.repeat.getValue() == 1:
            self.repeatButton["image"] = self.repeatImage
            playNext = True
            nextSongIndex = currentSong
        else:
            self.repeatButton["image"] = self.repeatImage

    def changeVolume(self, event):
        global currentVolumeInPixel
        if event.num == 1:
            x = event.x
            if 100 >= x and x >= 90:
                currentVolumeInPixel = 100
            elif 90 >= x and x >= 80:
                currentVolumeInPixel = 90
            elif 80 >= x and x >= 70:
                currentVolumeInPixel = 80
            elif 70 >= x and x >= 60:
                currentVolumeInPixel = 70
            elif 60 >= x and x >= 50:
                currentVolumeInPixel = 60
            elif 50 >= x and x >= 40:
                currentVolumeInPixel = 50
            elif 40 >= x and x >= 30:
                currentVolumeInPixel = 40
            elif 30 >= x and x >= 20:
                currentVolumeInPixel = 30
            elif 20 >= x and x >= 10:
                currentVolumeInPixel = 20
            elif 10 >= x and x >= 5:
                currentVolumeInPixel = 10
            elif 5 >= x and x >= 0:
                currentVolumeInPixel = 0
            self.setVolume(x)
        elif event.keycode == 38:
            if currentVolumeInPixel < 100:
                currentVolumeInPixel += 10
                self.setVolume(currentVolumeInPixel)
        elif event.keycode == 40:
            if currentVolumeInPixel > 0:
                currentVolumeInPixel -= 10
                self.setVolume(currentVolumeInPixel)

    def setVolume(self, value):
        if value > 0:
            self.volumeImageLabel = ttk.Label(self.hifiButtonCanvas, image=self.volumeImage)
            self.volumeImageLabel.grid(row=0, column=7, padx=5, pady=10)
        if value == 0:
            self.volumeImageLabel = ttk.Label(self.hifiButtonCanvas, image=self.volumeOutImage)
            self.volumeImageLabel.grid(row=0, column=7, padx = 5, pady = 10)
        pygame.mixer.music.set_volume(value / 100)
        self.volumeLineCanvas.delete('rect')
        self.volumeLineCanvas.create_rectangle(0, 0, currentVolumeInPixel, 12, tags='rect', fill='#00c8ff')
        self.volumeLineCanvas.update()

    def doRegexSearch(self, songStr, song):
        songRegex = re.compile(songStr)
        return songRegex.search(song)

        # called when the user searches for particular items
    def searchForSong(self):
        global searchListBoxEmpty
        if self.searchSong.get().isspace():
            pass
        else:
            searchListBoxEmpty = False
            if len(self.list) > 0:
                self.searchlistBox.delete(0, len(self.list))
                self.list.clear()
                self.searchListSongIndex.clear()
            searchString = str(self.searchSong.get())
            counter = 0 #counter is used to track the index of the songs being added to the search list box
                        #with respect to the main music list.
            #you can also search for songs from multiple artists by separating their names by space
            #separate the names and load them in a list
            artistNames = [names.strip() for names in searchString.split()]
            for name in artistNames:
                nameCapitalized = name.title()
                nameInUppercase = name.upper()
                nameInLowercase = name.lower()
                for song in musicFilenameList:
                    if self.doRegexSearch(name, song) is not None or self.doRegexSearch(nameCapitalized, song) \
                            or self.doRegexSearch(nameInUppercase, song) or self.doRegexSearch(nameInLowercase, song):
                        if song not in self.list:
                            self.list.append(song)
                            self.searchListSongIndex.append(counter)
                    counter += 1
                counter = 0
            for elem in self.list:
                self.searchlistBox.insert(tk.END, elem)

    def processPopup(self, event):
        global popupON
        global yposition
        popupON = True
        yposition = event.y
        self.listBox.selection_clear(0, tk.END)
        xpos = event.x_root - event.x + 200
        self.menu.post(xpos, event.y_root - 9)

    def processSearchPopup(self, event):
        if searchListBoxEmpty == False:
            global popupON
            global yposition
            popupON = True
            yposition = event.y
            xpos = event.x_root - event.x + 200
            self.searchmenu.post(xpos, event.y_root - 9)

    def processPlaylistPopup(self, event, tabid = 0):
        global popupON
        global yposition
        global playlistTabCurrentlyOn
        if tabid == 1:
            tabid = 0 if len(playListContent) == 1 else 1
        playlistTabCurrentlyOn = tabid
        popupON = True
        yposition = event.y
        xpos = event.x_root - event.x + 200
        self.userPlaylistMenu[tabid].post(xpos, event.y_root - 9)


    def createPlaylist(self):
        global tabID
        global playListNames
        global numberOfPlaylists
        global playListMusicIndex
        global currentIndexPlayingInPlaylist, songPlayingFromPlaylist
        self.playlistName = tk.StringVar()
        if numberOfPlaylists == maxNumberOfPlayList:
            tkinter.messagebox.showerror("Playlist Creation Error", "Maximum number of playlist reached")
        else:
            while True:
                try:
                    self.playlistName = tkinter.simpledialog.askstring("<Create playlist>", "Name")
                    if self.playlistName == None:
                        pass
                    elif self.playlistName == "":
                        raise NameError
                    elif len(self.playlistName) > 20:
                        raise BaseException
                    else:
                        global command1
                        global command2
                        tabID += 1
                        tabid = tabID
                        tab = ttk.Frame(self.tabcontrol)
                        self.tabcontrol.add(tab, text="  " + self.playlistName + "  ")
                        self.tabs.append(tab)
                        frame = tk.Frame(tab, bg = 'gray')
                        frame.pack()
                        scroll = ttk.Scrollbar(frame, orient = tk.VERTICAL)
                        scroll.grid(row = 0, column = 1, sticky = tk.N + tk.S)
                        playListMusicIndex.append([])
                        self.playlistListBox.append(tk.Listbox(frame, width = 115, height = 21, selectmode = tk.SINGLE, yscrollcommand = scroll.set,\
                                    bg = "#000000", fg = "cyan", activestyle = 'dotbox', font = 'Helvetica 12'))
                        self.playlistListBox[tabid].grid(row = 0, column = 0)
                        scroll['command'] = self.playlistListBox[tabid].yview
                        def handler(event, self=self, i=tabid):
                            type = event.type
                            if event.num == 1:
                                return self.playPlaylistMusic(event, i)
                            elif event.keysym == 'Return':
                                return self.playPlaylistMusic(event, i)
                            elif str(type) == 'Enter':
                                return self.highlightPlaylist(event, i)
                            elif str(type) == 'Leave':
                                return self.unhighlightPlaylist(event, i)
                            elif str(type) == 'Motion':
                                return self.highlightPlaylist(event, i)
                            elif event.num == 3:
                                return self.processPlaylistPopup(event, i)

                        self.playlistListBox[tabid].bind('<Return>', handler)
                        self.playlistListBox[tabid].bind('<Button-1>', handler)
                        self.playlistListBox[tabid].bind('<Enter>', handler)
                        self.playlistListBox[tabid].bind('<Leave>', handler)
                        self.playlistListBox[tabid].bind('<Motion>', handler)
                        self.playlistListBox[tabid].bind('<Button-3>', handler)

                        self.userPlaylistMenu.append(tk.Menu(self.playlistListBox[tabid], tearoff=0, bg="#000000", fg='cyan',font='Times 8 bold'))
                        self.userPlaylistMenu[tabid].add_command(label='Play',command=lambda: self.playSelectionInPlaylist(), columnbreak=1)
                        self.userPlaylistMenu[tabid].add_command(label='Play Next',command=lambda: self.setNextInPlaylist(), columnbreak=1)
                        self.userPlaylistMenu[tabid].add_command(label='Remove',command=lambda: self.removeSongFromPlaylist(),columnbreak=1)
                        self.userPlaylistMenu[tabid].add_command(label='Properties',command=lambda: self.showPlaylistProperty(),columnbreak=1)

                        self.playlistMenu.add_command(label=self.playlistName, command=lambda: self.switchToPlaylistTab(tabid))

                        if tabid == 0:
                            command1 = self.addToPlaylist0FromListbox
                            command2 = self.addToPlaylist0FromSearchListbox
                        elif tabid == 1:
                            command1 = self.addToPlaylist1FromListbox
                            command2 = self.addToPlaylist1FromSearchListbox
                        self.playlistOptionsMenu.add_command(label=self.playlistName, command=command1, columnbreak=1)
                        self.searchPlaylistOptionsMenu.add_command(label=self.playlistName, command=command2,\
                                                                   columnbreak=1)
                        playListNames.append(self.playlistName)
                        file = open(playlistNamesFile, 'a')
                        file.write(self.playlistName + '\n')
                        file.close()
                        file = open(self.playlistName + '.txt', 'w')
                        file.close()
                        file = open(self.playlistName + 'MI.txt', 'w')
                        file.close()
                        playListContent.append([])
                        currentIndexPlayingInPlaylist.append(0)
                        songPlayingFromPlaylist.append(False)
                        numberOfPlaylists += 1
                    break
                except NameError:
                    tkinter.messagebox.showerror("Name Error", "Name cannot be empty")
                except BaseException:
                    tkinter.messagebox.showerror("Name Error", "Playlist name should not have more than 20 characters")

    def switchToPlaylistTab(self, tabNum):
        while True:
            try:
                self.tabcontrol.select([tabNum + 4])
                break
            except tk.TclError:
                tabNum -= 1

    def addToPlaylist0FromListbox(self):
        global playListContent
        global playListMusicIndex
        self.listBox.selection_clear(0, tk.END)
        self.listBox.selection_set(self.listBox.nearest(yposition))
        index = self.listBox.curselection()[0]
        playListContent[0].append(musicFilenameList[index])
        playListMusicIndex[0].append(index)
        self.playlistListBox[0].delete(0, len(playListContent[0]))
        for elem in playListContent[0]:
            self.playlistListBox[0].insert(tk.END, elem)
        file = open(playListNames[0].strip() + '.txt', 'a')
        file.write(playListContent[0][len(playListContent[0]) - 1] + '\n')
        file.close()
        file = open(playListNames[0].strip() + 'MI.txt', 'a')
        file.write(str(playListMusicIndex[0][len(playListMusicIndex[0]) - 1]) + '\n')
        file.close()

    def addToPlaylist1FromListbox(self):
        global playListContent
        global playListMusicIndex
        i = 0 if len(playListContent) == 1 else 1
        self.listBox.selection_clear(0, tk.END)
        self.listBox.selection_set(self.listBox.nearest(yposition))
        index = self.listBox.curselection()[0]
        playListContent[i].append(musicFilenameList[index])
        playListMusicIndex[i].append(index)
        self.playlistListBox[i].delete(0, len(playListContent[i]))
        for elem in playListContent[i]:
            self.playlistListBox[i].insert(tk.END, elem)
        file = open(playListNames[i].strip() + '.txt', 'a')
        file.write(playListContent[i][len(playListContent[i]) - 1] + '\n')
        file.close()
        file = open(playListNames[i].strip() + 'MI.txt', 'a')
        file.write(str(playListMusicIndex[i][len(playListMusicIndex[i]) - 1]) + '\n')
        file.close()

    def addToPlaylist0FromSearchListbox(self):
        global playListContent
        global playListMusicIndex
        self.searchlistBox.selection_clear(0, tk.END)
        self.searchlistBox.selection_set(self.searchlistBox.nearest(yposition))
        index = self.searchListSongIndex[self.searchlistBox.curselection()[0]]
        playListContent[0].append(musicFilenameList[index])
        playListMusicIndex[0].append(index)
        self.playlistListBox[0].delete(0, len(playListContent[0]))
        for elem in playListContent[0]:
            self.playlistListBox[0].insert(tk.END, elem)
        file = open(playListNames[0].strip() + '.txt', 'a')
        file.write(playListContent[0][len(playListContent[0]) - 1] + '\n')
        file.close()
        file = open(playListNames[0].strip() + 'MI.txt', 'a')
        file.write(str(playListMusicIndex[0][len(playListMusicIndex[0]) - 1]) + '\n')
        file.close()

    def addToPlaylist1FromSearchListbox(self):
        global playListContent
        global playListMusicIndex
        i = 0 if len(playListContent) == 1 else 1
        self.searchlistBox.selection_clear(0, tk.END)
        self.searchlistBox.selection_set(self.searchlistBox.nearest(yposition))
        index = self.searchListSongIndex[self.searchlistBox.curselection()[0]]
        playListContent[i].append(musicFilenameList[index])
        playListMusicIndex[i].append(index)
        self.playlistListBox[i].delete(0, len(playListContent[1]))
        for elem in playListContent[i]:
            self.playlistListBox[i].insert(tk.END, elem)
        file = open(playListNames[i].strip() + '.txt', 'a')
        file.write(playListContent[i][len(playListContent[i]) - 1] + '\n')
        file.close()
        file = open(playListNames[i].strip() + 'MI.txt', 'a')
        file.write(str(playListMusicIndex[i][len(playListMusicIndex[i]) - 1]) + '\n')
        file.close()

    def postPlaylistDeletePopup(self, event, called = 0):
        '''
        this function uses indirect recursion to construct a popup menu and then post it at the position
        indicated by event
        :param event:
        :param called:
        :return:no return value
        '''
        if called == 0:
            self.showPopup(event, called + 1)
        elif called == 1 and self.rightClickedTab > 4:
            self.deleteMenu.post(event.x_root, event.y_root)

    def showPopup(self, event, called):
        #retrieve the index of the tab right-clicked on....it starts from zero
        self.rightClickedTab = self.tabcontrol.tk.call(self.tabcontrol._w, "identify", "tab", event.x, event.y)
        if self.rightClickedTab <= 3:
            pass
        else:
            self.deleteMenu = tk.Menu(self.tabs[0], tearoff = 0, bg = "#000000", fg = 'cyan', font = 'Times 8 bold')
            self.deleteMenu.add_command(label = 'Delete', command = lambda: self.deletePlaylist(self.rightClickedTab))
            self.postPlaylistDeletePopup(event, called)

    def deletePlaylist(self, tabid):
        '''
        function that deletes a play list. It deletes the file containing the playlist content,
        it deletes the list that temporary stores the playlist content while the program is running
        and finally it forgets the tab used to disolay the playlist
        :param tabid:
        :return: nothing:
        '''
        tabIndex = 0 if tabid == 4 else 1
        #tabIndex = len(self.tabs) - tabid - 1
        global playListContent
        global playListNames
        global numberOfPlaylists
        global tabID
        answer = tkinter.messagebox.askokcancel('<Delete Playlist>', 'Are you sure you want to delete this playlist')
        if answer:
            file = open(playlistNamesFile, 'r')
            list = [filename.strip() for filename in file.readlines()]
            playlistTodelete = list[tabIndex] + '.txt'
            playListIndexFileToDelete = list[tabIndex] + 'MI.txt'
            file.close()
            path = os.getcwd()
            try:
                os.unlink(path + '\\' + playlistNamesFile)
                os.unlink(path + '\\' + playlistTodelete)
                os.unlink(path + '\\' + playListIndexFileToDelete)
            except PermissionError as e:
                tkinter.messagebox.showerror("<Permission Error>", e)
                return
            del list[tabIndex]
            if len(list) > 0:
                file = open(playlistNamesFile, 'w')
                file.write(list[0] + '\n')
                file.close()
            self.playlistListBox[tabIndex].delete(0, len(playListContent[tabIndex]))
            del playListContent[tabIndex]
            del self.playlistListBox[tabIndex]
            del playListNames[tabIndex]
            self.tabcontrol.forget(tabid)
            numberOfPlaylists -= 1
            tabID -= 1
            self.playlistOptionsMenu.delete(tabIndex)
            self.searchPlaylistOptionsMenu.delete(tabIndex)
            self.playlistMenu.delete(tabIndex + 1) #since "add new" has already taken 0 position
            del self.tabs[tabIndex]
        else:
            pass

    def playMusic(self, event):
        """called when a particular index has been clicked in the main playlist listbox
        :param event:
        :param tabid:
        :return: void
        """
        global previousSongIndex
        global currentSongIndex
        global musicTrackerPosition
        global currentSong
        global currentEvent
        global songPlayingFromSearchList
        global currentIndexPlayingInSearchList
        global currentIndexPlayingInPlaylist, songPlayingFromPlaylist
        for _ in range(len(playListNames)):
            currentIndexPlayingInPlaylist[_] = 0
            songPlayingFromPlaylist[_] = False
        songPlayingFromSearchList = False
        currentIndexPlayingInSearchList = 0

        if currentEvent != idle:
            global timerStart
            timerStart = False
            self.timerThread.join()
            self.musicLineCanvas.delete('line')
            self.musicLineCanvas.update()
        musicTrackerPosition = 0
        try:
            currentSongIndex = self.listBox.curselection()
            previousSongIndex = currentSong
            currentSong = currentSongIndex[0]
            currentEvent = play
            self.Play(currentSongIndex[0])
        except IndexError:
            pass

    def playSearch(self, event):
        """called when a particular index has been clicked in the search playlist listbox
        :param event:
        :param tabid:
        :return: void
        """
        global previousSongIndex
        global currentSongIndex
        global musicTrackerPosition
        global currentSong
        global currentEvent
        global songPlayingFromSearchList
        global currentIndexPlayingInSearchList
        global currentIndexPlayingInPlaylist, songPlayingFromPlaylist
        for _ in range(len(playListNames)):
            currentIndexPlayingInPlaylist[_] = 0
            songPlayingFromPlaylist[_] = False

        if currentEvent != idle:
            global timerStart
            timerStart = False
            self.timerThread.join()
            self.musicLineCanvas.delete('line')
            self.musicLineCanvas.update()
        musicTrackerPosition = 0
        try:
            previousSongIndex = currentSong
            currentSongIndex = self.searchlistBox.curselection()#returns  a tuple
            currentSong = self.searchListSongIndex[currentSongIndex[0]]
            currentIndexPlayingInSearchList = currentSong
            currentEvent = play
            songPlayingFromSearchList = True
            self.Play(currentSong)
        except IndexError:
            pass

    def playPlaylistMusic(self, event, tabid):
        """called when a particular index has been clicked in the user created playlist listbox
        :param event:
        :param tabid:
        :return: void
        """
        global previousSongIndex, currentSongIndex
        global musicTrackerPosition
        global currentEvent, currentSong
        global songPlayingFfromSearchList, currentIndexPlayingInSearchList
        global currentIndexPlayingInPlaylist, songPlayingFromPlaylist
        #potential bug in the logic.....too burnt up to fix(probably in a later version)
        #now that i have regained interest...i have forgotten what the bug is about,,,prolly gonna wait for user feedbacks.
        if tabid == 1:
            tabid = 0 if len(playListContent) == 1 else 1
        if len(playListContent) == 1:
            currentIndexPlayingInPlaylist[tabid] = 0
            songPlayingFromPlaylist[tabid] = True
        elif len(playListContent) == 2:
            if tabid == 0:
                currentIndexPlayingInPlaylist[tabid] = 0
                songPlayingFromPlaylist[tabid] = True
                currentIndexPlayingInPlaylist[1], songPlayingFromPlaylist[1] = 0, False
            else:
                currentIndexPlayingInPlaylist[tabid] = 0
                songPlayingFromPlaylist[tabid] = True
                currentIndexPlayingInPlaylist[0], songPlayingFromPlaylist[0] = 0, False

        songPlayingFromSearchList = False
        currentIndexPlayingInSearchList = 0
        musicTrackerPosition = 0

        if currentEvent != idle:
            global timerStart
            timerStart = False
            self.timerThread.join()
            self.musicLineCanvas.delete('line')
            self.musicLineCanvas.update()
        musicTrackerPosition = 0
        try:
            currentSongIndex = self.playlistListBox[tabid].curselection()
            previousSongIndex = currentSong
            currentSong = playListMusicIndex[tabid][currentSongIndex[0]]
            currentIndexPlayingInPlaylist[tabid] = currentSong
            currentEvent = play
            self.Play(currentSong)
        except IndexError:
            pass


    def play(self):
        '''
        called when the play button is presed.
        it checks if the current state is not on play the proceeds o perform its function
        :return:
        '''
        if len(musicFilenameList) > 0:
            global currentEvent
            if currentEvent != play:
                try:
                    self.Play(currentSong)
                except TypeError:
                    self.Play(0)
        else:
            pass

    def moveMusicLine(self, event):
        global time
        global lengthInPixel
        global musicTrackerPosition
        x, y = event.x, event.y
        if currentEvent == play:
            self.Play(currentSong, x)
        elif currentEvent == pause:
            try:
                musicObject = MP3(musicFilePathList[currentSong])
                musicLength = musicObject.info.length
                pygame.mixer.music.rewind()
                pos = round((musicLength * x) // 600)
                pygame.mixer.music.set_pos(pos)
                musicTrackerPosition = lengthInPixel = x
                global timerStart
                timerStart = False
                self.timerThread.join()
                time = pos
                timeInString = self.convertTimeToString(time)
                self.beginTime.set(timeInString)
                self.currentMusicTimequeue.put(timeInString)
                self.musicLineCanvas.delete('line')
                self.musicLineCanvas.update()
                self.musicLineCanvas.create_rectangle(0, 0, lengthInPixel, 11, fill='#00c8ff', tags='line')
                self.musicLineCanvas.update()
            except IndexError:
                pass
            except MutagenError:
                pass

    def createText(self):
        self.subWooferCanvas.delete('text')
        self.subWooferCanvas.update()
        text = musicFilenameList[currentSong]
        self.subWooferCanvas.create_text(500, 330, text=text, font='Times 11 bold italic', tags= 'text', justify = tk.CENTER,\
                                         state = tk.DISABLED, fill = '#00c8ff')
        self.subWooferCanvas.update()

    def showTimer(self, musicLength):
        length = round(musicLength)
        minutes = length // 60
        seconds = length % 60
        minutesInString = str(minutes)
        secondsInString = str(seconds)
        if minutes < 10:
            minutesInString = '0' + str(minutes)
        if seconds < 10:
            secondsInString = '0' + str(seconds)
        time = minutesInString + ':' + secondsInString
        self.endTime.set(time)


    def musicTimer(self, musicLengthInSeconds, pixelPerSecond, pos):
        global lengthInPixel
        global timerStart
        global pastEvent
        global time
        counter = 0
        if pastEvent == pause:
            counter = time
            if pos != 0:
                counter = round(pos / pixelPerSecond)
            pastEvent = idle
        while counter <= musicLengthInSeconds and timerStart:
            sleep(1)
            time = counter
            self.time2 = self.convertTimeToString(time)
            self.currentMusicTimequeue.put(self.time2)
            lengthInPixel += pixelPerSecond
            counter += 1

    def musicLengthTracker(self, position = 0, index = 0):
        global musicLength
        global musicTrackerPosition
        global currentEvent
        global lengthInPixel
        global timerStart
        timerStart = True
        self.createText()
        self.currentMusicTimequeue = Queue()
        try:
            tags = ID3(musicFilePathList[index])
            picture = tags.get("APIC:").data
            im = Image.open(BytesIO(picture))
            im = im.resize((350, 300))
            im.save("music_art.gif")
            self.subwooferImage = tk.PhotoImage(file=subwooverImageString2)
        except UnidentifiedImageError:
            self.subwooferImage = tk.PhotoImage(file=subwooverImageString1)
            pass
        except AttributeError:
            self.subwooferImage = tk.PhotoImage(file=subwooverImageString1)
        except IndexError:
            self.subwooferImage = tk.PhotoImage(file=subwooverImageString1)
            pass
        except MutagenError:
            self.subwooferImage = tk.PhotoImage(file=subwooverImageString1)
            pass
        if currentEvent == play:
            try:
                # line to make obvious which line in the listbox is active. i.e which music is playing
                self.listBox.itemconfig(index= previousSongIndex, foreground= "cyan")
                self.listBox.itemconfig(index= index, foreground= "#ffA500")
                if songPlayingFromSearchList:
                    #this if statement is to check for the times when a song is searched initially, as a previous index is
                    #not yet present.
                    if previousSongIndex in self.searchListSongIndex:
                        self.searchlistBox.itemconfig(index=self.searchListSongIndex.index(previousSongIndex), foreground="cyan")
                    self.searchlistBox.itemconfig(index = self.searchListSongIndex.index(index), foreground = "#ffA500")
                elif (songPlayingFromSearchList == False and self.searchlistBox.size() > 0):
                    for line in range(0, self.searchlistBox.size()):
                        self.searchlistBox.itemconfig(index= line, \
                                                      foreground="cyan")
                musicLength = round(musicLength)
                self.showTimer(musicLength)
                minLength = musicLength // 60
                secLength = musicLength % 60
                musicLengthInSeconds = minLength * 60 + secLength
                pixelPerSecond = round(600 / musicLength, 2)
                self.timerThread = Thread(target=self.musicTimer, args=[musicLengthInSeconds, pixelPerSecond, position])
                if position != 0:
                    lengthInPixel = position
                else:
                    lengthInPixel = musicTrackerPosition
                self.timerThread.start()
                while (currentEvent == play or lengthInPixel <= 600 or self.beginTime.get() < self.endTime.get()) and \
                        (currentEvent != pause and currentEvent != stop):
                    self.musicLineCanvas.create_rectangle(0, 0, lengthInPixel, 11, fill='#00c8ff', tags='line')
                    self.subWooferCanvas.create_image(525, 160, image=self.subwooferImage, tags='subwooferImage')
                    self.musicLineCanvas.update()
                    self.subWooferCanvas.update()
                    try:
                        self.beginTime.set(self.currentMusicTimequeue.get(block = True, timeout= 0.05))
                    except Empty:
                        pass
                    musicTrackerPosition = lengthInPixel
                    if (lengthInPixel > 590 or lengthInPixel >= 600.0) and self.beginTime.get() >= self.endTime.get():
                        lengthInPixel = 0
                        self.beginTime.set('00:00')
                        self.endTime.set('00:00')
                        currentEvent = idle
                        musicTrackerPosition = 0
                        self.musicLineCanvas.delete('line')
                        self.musicLineCanvas.update()
                        self.subWooferCanvas.delete('subwooferImage')
                        self.subWooferCanvas.update()
                        self.next()
            except ZeroDivisionError:
                pass
            except BaseException:
                pass

    def convertTimeToString(self, time2):
        if time2 < 10:
            time2 = '00:0' + str(time)
        elif time2 >= 10 and time < 60:
            time2 = '00:' + str(time2)
        elif time2 >= 60 and time2 < 600:
            min = '0' + str(time2 // 60)
            sec = time2 % 60
            if sec < 10:
                sec = '0' + str(sec)
            else:
                sec = str(sec)
            time2 = min + ':' + sec
        else:
            min = str(time2 // 60)
            sec = time2 % 60
            if sec < 10:
                sec = '0' + str(sec)
            else:
                sec = str(sec)
            time2 = min + ':' + sec
        return time2

    def Play(self, index, position = 0):
        '''
        main play function that must be called before any song starts...
        :param index: index of music to be played, position of music length tracker
        :param position: _1, _2
        :return: void
        '''
        global songPlayed
        global musicLength
        global currentEvent
        global pastEvent
        songPlayed = True
        file = open('music volume file.txt', 'a')
        file.write(str(index) + '\n')
        file.close()
        try:
            musicObject = MP3(musicFilePathList[index])
            musicLength = musicObject.info.length
        except IndexError:
            pass
        except MutagenError:
            pass
        if currentEvent == pause:
            pygame.mixer.music.unpause()
            pastEvent = pause
            currentEvent = play
            self.musicLengthTracker(position, index)
        else:
            pygame.mixer.music.load(musicFilePathList[index])
            pygame.mixer.music.play()
            if position != 0:
                if currentEvent == play or currentEvent == pause:
                    global timerStart
                    timerStart = False
                    self.timerThread.join()
                    pastEvent = pause
                pygame.mixer.music.rewind()
                pos = (musicLength * position) // 600
                pygame.mixer.music.set_pos(pos)
                self.musicLineCanvas.delete('line')
                self.musicLineCanvas.update()
            currentEvent = play
            self.musicLengthTracker(position, index)

    def pause(self):
        '''
        This function temporarily stops the music playback
        :return:
        '''
        if len(musicFilenameList) > 0:
            global currentEvent
            if currentEvent != stop:
                try:
                    global musicTrackerPosition
                    global timerStart
                    timerStart = False
                    pygame.mixer.music.pause()
                    currentEvent = pause
                    self.timerThread.join()
                except tk.TclError:
                    pass
        else:
            pass

    def stop(self):
        '''
        This function stops the music playback
        :return:
        '''
        if len(musicFilenameList) > 0:
            try:
                global musicTrackerPosition
                global currentEvent
                global lengthInPixel
                global timerStart
                timerStart = False
                lengthInPixel = 0
                pygame.mixer.music.stop()
                currentEvent = stop
                musicTrackerPosition = 0
                self.musicLineCanvas.delete('line')
                self.timerThread.join()
            except tk.TclError:
                pass
        else:
            pass


    def previous(self):
        '''
        This function plays the previous song in the list
        :return:
        '''
        if len(musicFilenameList) > 0:
            try:
                global currentEvent
                global musicTrackerPosition
                global currentSongIndex
                global currentSong, previousSongIndex
                global lengthInPixel
                global currentIndexPlayingInSearchList
                lengthInPixel = 0
                musicTrackerPosition = 0
                if currentEvent == play or currentEvent == pause:
                    global timerStart
                    timerStart = False
                    self.timerThread.join()
                currentEvent = prev
                self.musicLineCanvas.delete('line')
                self.musicLineCanvas.update()
                self.subWooferCanvas.delete('text')
                self.subWooferCanvas.update()
                if songPlayingFromSearchList:
                    previousSongIndex = currentSong
                    currentIndexPlayingInSearchList = self.searchListSongIndex[self.searchListSongIndex.index(currentIndexPlayingInSearchList) - 1]
                    currentSong = currentIndexPlayingInSearchList
                    self.Play(currentSong)

                elif len(playListNames) == 1 and songPlayingFromPlaylist[0]:
                    previousSongIndex = currentSong
                    currentIndexPlayingInPlaylist[0] = playListMusicIndex[0][playListMusicIndex[0].index(currentIndexPlayingInPlaylist[0]) - 1]
                    currentSong = currentIndexPlayingInPlaylist[0]
                    self.Play(currentSong)

                elif len(playListNames) == 2 and songPlayingFromPlaylist[0] or len(playListNames) == 2 and songPlayingFromPlaylist[1]:
                    previousSongIndex = currentSong
                    if songPlayingFromPlaylist[0]:
                        currentIndexPlayingInPlaylist[0] = playListMusicIndex[0][playListMusicIndex[0].index(currentIndexPlayingInPlaylist[0]) - 1]
                        currentSong = currentIndexPlayingInPlaylist[0]
                        self.Play(currentSong)
                    elif songPlayingFromPlaylist[1]:
                        currentIndexPlayingInPlaylist[1] = playListMusicIndex[1][playListMusicIndex[1].index(currentIndexPlayingInPlaylist[1]) - 1]
                        currentSong = currentIndexPlayingInPlaylist[1]
                        self.Play(currentSong)

                else:
                    previousSongIndex = currentSong
                    if currentSong == 0:
                        currentSong = len(musicFilenameList) - 1
                        self.Play(currentSong)
                    else:
                        currentSong -= 1
                        self.Play(currentSong)
            except tk.TclError:
                pass
        else:
            pass


    def next(self):
        '''
        This function plays the next song in the list
        :return:
        '''
        if len(musicFilenameList) > 0:
            try:
                global currentEvent
                global musicTrackerPosition
                global currentSongIndex
                global currentSong, previousSongIndex
                global playNext
                global lengthInPixel
                global currentIndexPlayingInSearchList
                global currentIndexPlayingInPlaylist
                global playListNames
                lengthInPixel = 0
                musicTrackerPosition = 0
                if currentEvent == play or currentEvent == pause:
                    global timerStart
                    timerStart = False
                    self.timerThread.join()
                    while self.timerThread.is_alive():
                        sleep(0.5)
                currentEvent = next
                self.musicLineCanvas.delete('line')
                self.musicLineCanvas.update()
                self.subWooferCanvas.delete('text')
                self.subWooferCanvas.update()
                if songPlayingFromSearchList:
                    if playNext is False:
                        previousSongIndex = currentSong
                        if self.shuffle.get() == 0:
                            if currentIndexPlayingInSearchList == self.searchListSongIndex[len(self.searchListSongIndex) - 1]:
                                currentIndexPlayingInSearchList = self.searchListSongIndex[0]
                            else:
                                currentIndexPlayingInSearchList = self.searchListSongIndex[self.searchListSongIndex.index(currentIndexPlayingInSearchList) + 1]
                        elif self.shuffle.get() == 1:
                            if (len(self.searchListSongIndex) == 1):
                                currentIndexPlayingInSearchList = self.searchListSongIndex[0]
                            elif (len(self.searchListSongIndex) > 1):
                                index = randrange(0, len(self.searchListSongIndex) - 1)
                                currentIndexPlayingInSearchList = self.searchListSongIndex[index]
                        currentSong = currentIndexPlayingInSearchList
                        self.Play(currentSong)
                    else:
                        playNext = False
                        currentSong = nextSongIndex
                        self.Play(nextSongIndex)
                elif len(playListNames) == 1 and songPlayingFromPlaylist[0]:
                    previousSongIndex = currentSong
                    if playNext is False:
                        if self.shuffle.get() == 0:
                            if currentIndexPlayingInPlaylist[0] == playListMusicIndex[0][len(playListMusicIndex[0]) - 1]:
                                currentIndexPlayingInPlaylist[0] = playListMusicIndex[0][0]
                            else:
                                currentIndexPlayingInPlaylist[0] = playListMusicIndex[0][playListMusicIndex[0].index(currentIndexPlayingInPlaylist[0]) + 1]
                        elif self.shuffle.get() == 1:
                            index = randrange(0, len(playListContent[0]) - 1)
                            currentIndexPlayingInPlaylist[0] = playListMusicIndex[0][index]
                        currentSong = currentIndexPlayingInPlaylist[0]
                        self.Play(currentSong)
                    else:
                        playNext = False
                        currentSong = nextSongIndex
                        self.Play(nextSongIndex)
                elif len(playListNames) == 2 and songPlayingFromPlaylist[0] or len(playListNames) == 2 and songPlayingFromPlaylist[1]:
                    previousSongIndex = currentSong
                    if songPlayingFromPlaylist[0]:
                        if playNext is False:
                            if self.shuffle.get() == 0:
                                if currentIndexPlayingInPlaylist[0] == playListMusicIndex[0][len(playListMusicIndex[0]) - 1]:
                                    currentIndexPlayingInPlaylist[0] = playListMusicIndex[0][0]
                                else:
                                    currentIndexPlayingInPlaylist[0] = playListMusicIndex[0][playListMusicIndex[0].index(currentIndexPlayingInPlaylist[0]) + 1]
                            elif self.shuffle.get() == 1:
                                index = randrange(0, len(playListContent[0]) - 1)
                                currentIndexPlayingInPlaylist[0] = playListMusicIndex[0][index]
                            currentSong = currentIndexPlayingInPlaylist[0]
                            self.Play(currentSong)
                        else:
                            playNext = False
                            currentSong = nextSongIndex
                            self.Play(nextSongIndex)
                    elif songPlayingFromPlaylist[1]:
                        if playNext is False:
                            if self.shuffle.get() == 0:
                                if currentIndexPlayingInPlaylist[1] == playListMusicIndex[1][len(playListMusicIndex[1]) - 1]:
                                    currentIndexPlayingInPlaylist[1] = playListMusicIndex[1][0]
                                else:
                                    currentIndexPlayingInPlaylist[1] = playListMusicIndex[1][playListMusicIndex[1].index(currentIndexPlayingInPlaylist[1]) + 1]
                            elif self.shuffle.get() == 1:
                                index = randrange(0, len(playListContent[1]) - 1)
                                currentIndexPlayingInPlaylist[1] = playListMusicIndex[1][index]
                            currentSong = currentIndexPlayingInPlaylist[1]
                            self.Play(currentSong)
                        else:
                            playNext = False
                            currentSong = nextSongIndex
                            self.Play(nextSongIndex)

                else:
                    previousSongIndex = currentSong
                    if playNext is False:
                        if self.shuffle.get() == 0:
                            if currentSong == len(musicFilenameList) - 1:
                                currentSong = 0
                            else:
                                currentSong += 1
                            self.Play(currentSong)
                        elif self.shuffle.get() == 1:
                            currentSong = randrange(0, len(musicFilenameList) - 1)
                            self.Play(currentSong)
                    elif playNext is True:
                        if self.repeat.getValue() == 1:
                            currentSong = nextSongIndex
                            self.Play(nextSongIndex)
                        else:
                            playNext = False
                            currentSong = nextSongIndex
                        self.Play(nextSongIndex)
            except tk.TclError:
                pass
        else:
            pass

    def close(self):
        '''
        this function is called when the user explicity closed the applicaton
        by pressing the X icon on windows or its equivalent on other platforms.
        it waits for the current running thread(if any) to join the main thread
        before closing the application
        :return:
        '''
        global timerStart
        if songPlayed:
            try:
                timerStart = False
                self.timerThread.join()
            except AttributeError:
                pass
        sleep(0.2)
        self.window.destroy()

window.after(1000, MusicPlayerGUI)

window.mainloop()