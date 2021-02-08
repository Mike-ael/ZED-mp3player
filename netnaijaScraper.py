from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import InvalidArgumentException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
from queue import Queue
import os
import datetime
from threading import Thread
from typing import List
from voicemessages import fileFoundMessage, searchMessage
videoDownloadCancelledFlag = Queue(maxsize=1)
videoDownloadErrors = Queue(maxsize=2)
videoDownloadNotification = Queue(maxsize=2)


class VideoDownLoad():
    def __init__(self):
        self.chromeOptions = Options()
        self.chromeOptions.add_argument('--disable-notifications')
        self.chromeOptions.add_argument('--headless')
        self.driver = None
        self.driver1 = None
        self.driver2 = None
        self.mp4Link = None
        self.srtLink = None
        self.downloadLinkSearchDone = False
        self.downloadPath = r'C:\Users\HP\Downloads'
        self.fileDownloaded = False #used to notify checkDownloadCancelled function

    def headlessDownloadRequirement(self, driver):
        params = {'behavior': 'allow', 'downloadPath': self.downloadPath}
        driver.execute_cdp_cmd('Page.setDownloadBehavior', params)

    def checkFilePresence(self, numberOfFilesInitially, timeNow, extension):
        found = False
        while not found and videoDownloadErrors.qsize() == 0:
            numberOfFilesNow = len(os.listdir(self.downloadPath))
            if numberOfFilesNow > numberOfFilesInitially:
                for folders, subfolders, files in os.walk(self.downloadPath):
                    for file in files:
                        try:
                            creationTime = datetime.datetime.fromtimestamp(os.path.getctime(os.path.join(folders, file)))
                            if creationTime > timeNow:
                                if file.endswith(extension):
                                    return
                        except FileNotFoundError:
                            videoDownloadErrors.put("FILE NOT FOUND")
                        except BaseException as error:
                            videoDownloadErrors.put(error)



    def quitMp4Download(self):
        try:
            videoDownloadErrors.put('Download cancelled', block=False)
        except WebDriverException:
            pass
        except AttributeError:
            pass

    def checkMp4DownloadCancelled(self):
        while videoDownloadCancelledFlag.qsize() == 0 and self.fileDownloaded == False:
            pass
        if not self.fileDownloaded:
            cancelled = videoDownloadCancelledFlag.get(block=False)
            print(cancelled)
            if cancelled:
                videoDownloadCancelledFlag.put(True, block=False)
                self.quitMp4Download()

    def connectionCheck(self):
        while self.fileDownloaded == False:
            try:
                self.driver1.switch_to.window(self.driver1.window_handles[1])
                self.driver1.get('https://google.com')
                sleep(5)
            except WebDriverException as error:
                videoDownloadErrors.put(error)
                break

    def startSRTDownload(self, link):
        try:
            numberOfFilesInitially = len(os.listdir(self.downloadPath))
            timeNow = datetime.datetime.now()
            fileChecker = Thread(target=self.checkFilePresence, args=[numberOfFilesInitially, timeNow, r'.srt'])
            fileChecker.start()
            self.driver2 = webdriver.Chrome(options=self.chromeOptions)
            self.driver2.get(link)
            self.headlessDownloadRequirement(self.driver2)
            downloadButton = self.driver2.find_element_by_css_selector(
                """div[id = 'app-content'] div[id = 'file-page'] div[id = 'action-buttons'] button""")
            downloadButton.click()
            fileChecker.join()
            if videoDownloadErrors.qsize() == 0:
                videoDownloadNotification.put(True, block = False)
                self.driver2.quit()
            elif videoDownloadCancelledFlag.qsize() == 1:
                raise BaseException
            elif videoDownloadErrors.qsize() > 0:
                raise BaseException
        except NoSuchElementException as error:
            videoDownloadErrors.put(error, block=False)
            self.driver2.quit()
            raise error
        except InvalidArgumentException as error:
            videoDownloadErrors.put(error, block=False)
            self.driver2.quit()
            raise error
        except WebDriverException as error:
            videoDownloadErrors.put(error, block=False)
            self.driver2.quit()
            raise error
        except BaseException as error:
            self.driver2.quit()
            raise error

    def startMP4Download(self, link):
        try:
            downloadCancelCheck = Thread(target=self.checkMp4DownloadCancelled, args=())
            downloadCancelCheck.start()
            numberOfFilesInitially = len(os.listdir(self.downloadPath))
            timeNow = datetime.datetime.now()
            fileChecker = Thread(target=self.checkFilePresence, args=[numberOfFilesInitially, timeNow, r'.mp4'])
            fileChecker.start()
            self.driver1 = webdriver.Chrome(options=self.chromeOptions)
            self.driver1.get(link)
            self.headlessDownloadRequirement(self.driver1)
            downloadButton = self.driver1.find_element_by_css_selector("""div[id = 'app-content'] div[id = 'file-page'] div[id = 'action-buttons'] button""")
            downloadButton.click()
            fileFoundMessage()
            connectionChecker = Thread(target = self.connectionCheck, args = [])
            connectionChecker.start()
            fileChecker.join()
            self.fileDownloaded = True
            if videoDownloadErrors.qsize() == 0:
                videoDownloadNotification.put(True, block = False)
                downloadCancelCheck.join()
                connectionChecker.join()
                self.driver1.quit()
            elif videoDownloadCancelledFlag.qsize() == 1:
                downloadCancelCheck.join()
                connectionChecker.join()
                raise BaseException
            elif videoDownloadCancelledFlag.qsize() == 0 and videoDownloadErrors.qsize() > 0:
                videoDownloadCancelledFlag.put(False, block=False)
                downloadCancelCheck.join()
                connectionChecker.join()
                raise BaseException
        except NoSuchElementException as error:
            videoDownloadErrors.put(error)
            self.driver1.quit()
            raise error
        except InvalidArgumentException as error:
            videoDownloadErrors.put(error, block=False)
            self.driver1.quit()
            raise error
        except WebDriverException as error:
            videoDownloadErrors.put(error, block=False)
            self.driver1.quit()
            raise error
        except BaseException as error:
            self.driver1.quit()
            raise error


    def search(self, string, link):
        return string in link


    def checkSearchCancelled(self):
        while videoDownloadCancelledFlag.qsize() == 0 and self.downloadLinkSearchDone == False:
            pass
        if not self.downloadLinkSearchDone:
            self.quitMainDriverDownload()

    def quitMainDriverDownload(self):
        try:
            videoDownloadErrors.put("Download cancelled", block=False)
            self.driver.quit()
        except WebDriverException:
            pass
        except AttributeError:
            pass

    def findFileLink(self, movie_name, _season=0, _episode=0):
        if movie_name == '':
            videoDownloadErrors.put('ERROR: Movie name field cannot be empty')
            raise
        else:
            downloadCanceledCheck = Thread(target=self.checkSearchCancelled, args=())
            downloadCanceledCheck.start()
            searchMessage()
            movieName = movie_name
            episode = "episode-" + str(_episode)
            season = "season-" + str(_season)
            if season == 'season-0' or episode == 'episode-0':
                season, episode = '', ''
            folder = "Video"
            print(season, episode)
            try:
                self.driver = webdriver.Chrome(options=self.chromeOptions)
                self.driver.get("http://netnaija.com/search")
                self.driver.get_cookies()
                input1 = self.driver.find_element_by_css_selector("div[class = 'row'] div[class='input'] input")
                for elem in movieName:
                    input1.send_keys(elem)
                    sleep(.2)
                input2 = self.driver.find_element_by_css_selector("div[class = 'row'] div[class='input'] select")
                input2.send_keys(folder)
                input2.submit()
                links = WebDriverWait(self.driver, 15).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '''div[id= 'search-page'] \
                                                            div[id = 'search-results'] main[class = 'search-results-list'] article[class = 'result'] \
                                                            div[class = 'result-info'] h3[class = 'result-title'] a''')))
                self.found = False
                while not self.found:
                    for link in links:
                        l = link.get_attribute('href')
                        print(l)
                        if self.search(season, str(l)):
                            print(f'found link -> {l}')
                            self.found = True
                            parts: List = str(l).replace('https://', '').split('/')
                            parts.pop()
                            seasonFolder: str = 'https://' + '/'.join(parts)
                            print(seasonFolder)
                            self.driver.get(seasonFolder)
                            break
                    if not self.found:
                        try:
                            nextPage = WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, '''div[class = 'pages'] div[class = '\
                                                                            page-listing'] span[class = 'a-page'] a[title = 'Next Page']''')))
                            print("Going to the next page")
                            nextPage.click()
                        except NoSuchElementException as error:
                            self.driver.quit()
                            videoDownloadErrors.put(error)
                            raise error
                        links = WebDriverWait(self.driver, 15).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '''div[id= 'search-page'] \
                                                                    div[id = 'search-results'] main[class = 'search-results-list'] article[class = 'result']\
                                                                                    div[class = 'result-info'] h3[class = 'result-title'] a''')))
                seasonLinks = self.driver.find_elements_by_css_selector("""article[class = 'a-file'] div[class = 'info'] h3[class = 'file-name'] a""")
                #repurposing self.found
                self.found = False
                for link in seasonLinks:
                    l = link.get_attribute('href')
                    print(l)
                    if self.search(episode, str(l)) and self.search(season, str(l)):
                        print(f'found link -> {l}')
                        self.found = True
                        self.driver.get(l)
                        break
                if self.found == False:
                    raise FileNotFoundError()
                else:
                    downloadLinks = WebDriverWait(self.driver, 15).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[class = 'video-download'] p a" )))
                    print(len(downloadLinks))
                    self.mp4Link = downloadLinks[3].get_attribute('href')
                    self.srtLink = downloadLinks[4].get_attribute('href')
            except IndexError as error:
                self.driver.quit()
                videoDownloadErrors.put(error, block=False)
                raise error
            except FileNotFoundError as error:
                self.driver.quit()
                videoDownloadErrors.put("ERROR: FILE NOT FOUND", block=False)
                raise error
            except ElementClickInterceptedException as error:
                self.driver.quit()
                videoDownloadErrors.put(error, block=False)
                raise error
            except TimeoutException as error:
                self.driver.quit()
                videoDownloadErrors.put(error, block=False)
                raise error
            except NoSuchElementException as error:
                self.driver.quit()
                videoDownloadErrors.put(error, block=False)
                raise error
            except WebDriverException as error:
                self.driver.quit()
                videoDownloadErrors.put(error, block=False)
                raise error
            else:
                self.downloadLinkSearchDone = True
                self.driver.quit()
                return self.mp4Link, self.srtLink