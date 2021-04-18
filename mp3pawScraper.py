import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import ElementClickInterceptedException, NoSuchElementException
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from threading import Thread
import os
import datetime
from voicemessages import fileFoundMessage
from queue import Queue
from voicemessages import searchMessage
musicDownloadCancelledFlag = Queue(maxsize=1)
musicDownloadErrors = Queue(maxsize=2)
musicDownloadNotification = Queue(maxsize=1)
#this is a flag for the download checking thread


class MusicDownload():
    def __init__(self):
        self.driver = None
        self.path = r'C:\Users\HP\Downloads'
        self.webUrl = r'https://mp3paw.com/'
        self.chrome_options = Options()
        self.chrome_options.add_argument('--disable-notifications')
        self.chrome_options.add_argument('--headless')
        self.fileDownloaded = False
    def checkFilePresence(self, numberOfFilesInitially, timeNow, extension, artistName, songTitle):
        found = False
        isFile = lambda music_file, name, title: name.lower() in music_file.lower() or \
                                                 title.lower() in music_file.lower()
        while not found and musicDownloadErrors.qsize() == 0:
            numberOfFilesNow = len(os.listdir(self.path))
            if numberOfFilesNow > numberOfFilesInitially:
                for folders, subfolders, files in os.walk(self.path):
                    for file in files:
                        try:
                            if isFile(file, artistName, songTitle):
                                creationTime = datetime.datetime.fromtimestamp(os.path.getctime(
                                    os.path.join(folders, file)))
                                if creationTime > timeNow:
                                    if file.endswith(extension):
                                        found = True
                                        return
                        except FileNotFoundError:
                            musicDownloadErrors.put("FILE NOT FOUND")
                        except BaseException as error:
                            musicDownloadErrors.put(error)
        print('exiting')

    def quitDownload(self):
        try:
            musicDownloadErrors.put("Download cancelled", block=False)
            print('download cancelled')
        except WebDriverException:
            pass
        except AttributeError:
            pass

    def checkCancelled(self):
        while musicDownloadCancelledFlag.qsize() == 0 and self.fileDownloaded == False:
            pass
        if not self.fileDownloaded:
            cancelled = musicDownloadCancelledFlag.get(block=False)
            print(cancelled)
            if cancelled:
                musicDownloadCancelledFlag.put(True, block=False)
                self.quitDownload()


    def findSongInText(self, textElement, artistName: str, songTitle: str):
        artistName = artistName.lower()
        songTitle = songTitle.lower()
        return True if artistName in str(textElement.text).lower() and \
                       songTitle in str(textElement.text).lower() else False

    def connectionCheck(self):
        while self.fileDownloaded == False:
            try:
                self.driver.get('https://google.com')
                time.sleep(5)
            except WebDriverException as error:
                musicDownloadErrors.put(error)
                break

    def checkAndCorrectNewTab(self, numberOfTabs, button):
        """
        function to switch to the correct tab if a new tab was created by the browswer.
        :param numberOfTabs:
        :param button:
        :return:
        """
        if (numberOfTabs < len(self.driver.window_handles)):
            self.driver.switch_to.window(self.driver.window_handles[0])
            button.click()

    def mp3pawscraper(self, artistName, songTitle):
        if artistName == '' or songTitle == '':
            musicDownloadErrors.put("ERROR: fields cannot be empty")
            raise
        else:
            try:
                searchMessage()
                artistName = artistName.lower().strip()
                songTitle = songTitle.lower().strip()
                downloadCanceledCheck = Thread(target=self.checkCancelled, args=[])
                downloadCanceledCheck.start()
                numberOfFilesInitially = len(os.listdir(self.path))
                timeNow = datetime.datetime.now()
                self.driver = webdriver.Chrome(options=self.chrome_options)
                self.driver.get(self.webUrl)
                self.driver.get_cookies()
                searchElem = self.driver.find_element_by_id('search')
                keyword = artistName + " " + songTitle
                for letter in keyword:
                    searchElem.send_keys(letter)
                    time.sleep(.1)
                time.sleep(1)
                searchElem.send_keys(Keys.ENTER)
                elementTextList = self.driver.find_elements_by_css_selector("div[class='mp3-head'] h3")
                index: int = 0
                for text in elementTextList:
                    if self.findSongInText(text, artistName, songTitle):
                        downloadElem = self.driver.find_elements_by_css_selector('li[class="mp3dl"]')[index]
                        numberOfTabs: int = len(self.driver.window_handles)
                        downloadElem.click()
                        self.checkAndCorrectNewTab(numberOfTabs=numberOfTabs, button=downloadElem)
                        self.driver.get_cookies()
                        time.sleep(2)
                        fileChecker = Thread(target=self.checkFilePresence,
                                             args=(numberOfFilesInitially, timeNow, '.mp3', songTitle, artistName))
                        fileChecker.start()
                        self.driver.switch_to.window(self.driver.window_handles[2])
                        time.sleep(3)
                        buttons = self.driver.find_elements_by_css_selector('ul > li')
                        params = {'behavior': 'allow', 'downloadPath': self.path}
                        self.driver.execute_cdp_cmd('Page.setDownloadBehavior', params)
                        for i in range(5):
                            buttons[7].click()
                            time.sleep(i)
                            break
                        time.sleep(1)
                        connectionChecker = Thread(target=self.connectionCheck, args=[])
                        connectionChecker.start()
                        if musicDownloadCancelledFlag.qsize() == 0:
                            fileFoundMessage()
                        fileChecker.join()
                        self.fileDownloaded = True
                        # if download was not cancelled and no filesystem error
                        if musicDownloadErrors.qsize() == 0:
                            musicDownloadNotification.put(True, block=False)
                            downloadCanceledCheck.join()
                            connectionChecker.join()
                            self.driver.quit()
                        elif musicDownloadCancelledFlag.qsize() == 1:
                            downloadCanceledCheck.join()
                            connectionChecker.join()
                            raise BaseException
                        elif musicDownloadCancelledFlag.qsize() == 0 and musicDownloadErrors.qsize() > 0:
                            musicDownloadCancelledFlag.put(False, block=False)
                            downloadCanceledCheck.join()
                            connectionChecker.join()
                            raise BaseException
                        break #break out of for loop
                    index += 1
                    if index == len(elementTextList) - 1:
                        raise FileNotFoundError
                #end for loop

            except ElementClickInterceptedException as error:
                musicDownloadErrors.put(error, block=False)
                self.driver.quit()
                raise error
            except NoSuchElementException as error:
                musicDownloadErrors.put(error, block=False)
                self.driver.quit()
                raise error
            except WebDriverException as error:
                musicDownloadErrors.put(error, block=False)
                self.driver.quit()
                raise error
            except FileNotFoundError as error:
                musicDownloadErrors.put("FILE NOT FOUND", block=False)
                self.driver.quit()
                raise error
            except BaseException as error:
                musicDownloadErrors.put(error, block=False)
                self.driver.quit()
                raise error