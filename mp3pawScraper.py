import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from threading import Thread
from concurrent.futures import ThreadPoolExecutor, as_completed
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
        #self.chrome_options.add_argument('--headless')
        self.fileDownloaded = False
    def checkFilePresence(self, downloadPath, numberOfFilesInitially, timeNow):
        found = False
        while not found:
            numberOfFilesNow = len(os.listdir(downloadPath))
            if numberOfFilesNow > numberOfFilesInitially:
                for folders, subfolders, files in os.walk(downloadPath):
                    for file in files:
                        try:
                            creationTime = datetime.datetime.fromtimestamp(os.path.getctime(os.path.join(folders, file)))
                            if creationTime > timeNow:
                                if file.endswith('.mp3'):
                                    return
                        except FileNotFoundError as error:
                            raise error
                        except BaseException as error:
                            raise error

    def quitDownload(self):
        try:
            self.driver.quit()
        except WebDriverException:
            pass
        except AttributeError:
            pass
        finally:
            musicDownloadErrors.put("Download cancelled")

    def checkCancelled(self):
        while not musicDownloadCancelledFlag.qsize() == 1 and not self.fileDownloaded:
            pass
        if not self.fileDownloaded:
            _tempVar = musicDownloadCancelledFlag.get(block=False)
            self.quitDownload()

    def mp3pawscraper(self, artistName, songTitle):
        if artistName == '' or songTitle == '':
            musicDownloadErrors.put("ERROR: fields cannot be empty")
            raise
        else:
            try:
                fileCheckerExecutor = ThreadPoolExecutor(max_workers=1)
                downloadCanceledCheck = Thread(target=self.checkCancelled, args=[], daemon=True)
                downloadCanceledCheck.start()
                searchMessage()
                artistName = artistName.lower().strip()
                songTitle = songTitle.lower().strip()
                numberOfFilesInitially = len(os.listdir(self.path))
                timeNow = datetime.datetime.now()
                self.driver = webdriver.Chrome(options=self.chrome_options)
                self.driver.get(self.webUrl)
                self.driver.get_cookies()
                searchElem = self.driver.find_element_by_id('search')
                keyword = artistName + " " + songTitle
                for letter in keyword:
                    searchElem.send_keys(letter)
                    time.sleep(.3)
                time.sleep(1)
                searchElem.send_keys(Keys.ENTER)
                downloadButton = self.driver.find_elements_by_tag_name('li')
                downloadElem = None
                for tag in downloadButton:
                    if tag.text == "Download MP3":
                        downloadElem = tag
                        break
                time.sleep(2)
                downloadElem.click()
                time.sleep(3)
                windows = self.driver.window_handles
                self.driver.switch_to.window(windows[1])
                self.driver.get_cookies()
                buttons = self.driver.find_elements_by_css_selector('ul > li')
                params = {'behavior': 'allow', 'downloadPath': self.path}
                self.driver.execute_cdp_cmd('Page.setDownloadBehavior', params)
                for i in range(5):
                    buttons[7].click()
                    time.sleep(1)
                    break
                fileFoundMessage()
                future = fileCheckerExecutor.submit(self.checkFilePresence, (self.path, numberOfFilesInitially, timeNow))
                for result in as_completed([future]):
                    result.result()
                musicDownloadNotification.put(True)
                self.fileDownloaded = True
                self.driver.quit()
            except ElementClickInterceptedException as error:
                self.driver.quit()
                musicDownloadErrors.put(error)
                raise error
            except WebDriverException as error:
                self.driver.quit()
                musicDownloadErrors.put(error)
                raise error