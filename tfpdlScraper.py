from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.common.exceptions import ElementClickInterceptedException, ElementNotInteractableException
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from time import sleep
from typing import List
from queue import Queue
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import datetime
import pyautogui
from contextlib import suppress
tfpdl_videoDownloadCancelledFlag = Queue(maxsize=1)
tfpdl_videoDownloadErrors = Queue(maxsize=2)
tfpdl_videoDownloadNotification = Queue(maxsize=2)
from voicemessages import fileFoundMessage, searchMessage

class TFPDLVideoDownload():
    def __init__(self):
        self.chromeOptions = self.chromeOptions1 = Options()
        self.chromeOptions.add_argument('--disable-notifications')
        self.chromeOptions1.add_argument('--disable-notifications')
        #self.chromeOptions.add_argument('--headless')
        self.driver = None
        self.downloadPath = r'C:\Users\HP\Downloads'
        self.fileDownloaded = False #used to notify checkDownloadCancelled function
        self.selector = """div[class = 'wrapper full-site'] div[class = 'container'] div[id = 'main-content'] 
        div[class = 'content-wrap'] div[class = 'content'] """
        self.resolution = "480p"
        self.fileDownloaded = False

    def parse(self, num: int):
        if (num < 10):
            return '0' + str(num)
        return str(num)

    def findMovieLink(self, driver, string, checkStr):
        self.foundLink: bool = False
        while True:
            try:
                linksOnCurrentPage = WebDriverWait(driver, 15).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, f'''{self.selector} div[class = 'post-listing '] article h2 a''')))
                print(f'length = {len(linksOnCurrentPage)}')
                for link in linksOnCurrentPage:
                    strLink = str(link.get_attribute('href'))
                    print(strLink)
                    if string in strLink and self.resolution in strLink and 'complete' not in strLink:
                        print(f'found link -> {strLink}')
                        self.foundLink = True
                        return strLink
                if not driver.title.startswith(checkStr):
                    driver.switch_to.window(driver.window_handles[0])
                nextPage = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, f'''{self.selector} div[class = 'pagination'] span[id = 'tie-next-page'] a''')))
                sleep(2)
                driver.get(nextPage.get_attribute('href'))
            except IndexError as error:
                raise error
            except ElementClickInterceptedException as error:
                raise error
            except NoSuchElementException as error:
                raise error
            except TimeoutException:
                raise TimeoutException("ERROR: scraper timeout because file link not found.")
            except WebDriverException as error:
                raise error



    def getFileLink(self, driver):
        try:
            for tab in driver.window_handles:
                driver.switch_to.window(tab)
                if 'xproxxx' in driver.title:
                    break
            assert 'xproxxx' in driver.title, "ERROR: can't find correct tab"
            #proceed for links
            print(driver.title)
            action1 = ActionChains(driver)
            link1 = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, '''form[id = 'landing'] div[id = 'landing'] div[class = 'wait'] center img''')))
            action1.move_to_element(link1).click().perform()
            sleep(5)
            print(driver.title)
            action2 = ActionChains(driver)
            link2 = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[id = 'landing'] div[class = 'to'] a")))
            action2.move_to_element(link2).click().perform()
            sleep(5)
            print(driver.title)
            action3 = ActionChains(driver)
            link3 = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".spoint")))
            action3.move_to_element(link3).click().perform()
            sleep(5)
            if 'safe.txt' not in driver.title:
                self.moveToCorrectTab(driver, 'safe.txt')
            #send keys and submit form
            form: List = WebDriverWait(driver, 15).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "form[method = 'post'] p input")))
            innerParagraphs = driver.find_elements_by_css_selector("form[method = 'post'] p")
            if len(innerParagraphs) == 3:
                raise Exception("ERROR: A captcha challenge is blocking the progress of the crawler")
            elif len(innerParagraphs) == 2:
                password = 'tfpdl'
                for char in password:
                    form[0].send_keys(char)
                sleep(1)
                form[1].click()
            fileLink = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[href ^= 'https://firefiles']")))
            return fileLink
        except AssertionError as error:
            raise error
        except ElementClickInterceptedException as error:
            raise error
        except NoSuchElementException as error:
            raise error
        except TimeoutException as error:
            raise error
        except WebDriverException as error:
            raise error
        except BaseException as error:
            raise error

    def moveToCorrectTab(self, driver, expectedTitle):
        for index in range(len(driver.window_handles)):
            driver.switch_to.window(driver.window_handles[index])
            if expectedTitle in driver.title:
                break

    def clickFirstDownloadButton(self,xPosition=0, yPosition=0):
        tabsNum = len(self.driver.window_handles)
        pyautogui.scroll(-100)
        sleep(2)
        pyautogui.moveTo(xPosition, yPosition)
        sleep(2)
        pyautogui.doubleClick()
        if len(self.driver.window_handles) > tabsNum:
            print('got here')
            sleep(2)
            self.driver.switch_to.window(self.driver.window_handles[0])
            print('switched back to first window')
            sleep(2)
            pyautogui.scroll(-100)
            sleep(2)
            pyautogui.moveTo(xPosition, yPosition)
            sleep(2)
            pyautogui.doubleClick()
        sleep(5)

    def clickSecondDownloadButton(self):
        lenOfTabs = len(self.driver.window_handles)
        pyautogui.scroll(-200)
        sleep(2)
        self.clickButtonPosition()
        if (len(self.driver.window_handles) > lenOfTabs):
            self.driver.switch_to.window(self.driver.window_handles[0])
            self.clickButtonPosition()
        sleep(3)

    def clickButtonPosition(self):
        x: int = 799
        for y in range(300, 700, 15):
            pyautogui.moveTo(x, y)
            if pyautogui.pixelMatchesColor(x, y, (100, 177, 38), tolerance= 5):
                break
        pyautogui.doubleClick()

    def clickThirdDownloadButton(self):
        lenOfTabs = len(self.driver.window_handles)
        pyautogui.scroll(-200)
        sleep(2)
        self.clickButtonPosition()
        if (len(self.driver.window_handles) > lenOfTabs):
            self.driver.switch_to.window(self.driver.window_handles[0])
            self.clickButtonPosition()

    def checkDownloadCancelled(self):
        while tfpdl_videoDownloadCancelledFlag.qsize() == 0 and tfpdl_videoDownloadErrors.qsize() == 0 \
                and not self.fileDownloaded:
            pass
        if tfpdl_videoDownloadCancelledFlag.qsize() == 1:
            tfpdl_videoDownloadErrors.put("Download cancelled", block=False)
            raise BaseException

    def checkFilePresence(self, numberOfFilesInitially, timeNow, extension):
        found = False
        with suppress(FileNotFoundError, BaseException):
            while not found and tfpdl_videoDownloadErrors.qsize() == 0:
                numberOfFilesNow = len(os.listdir(self.downloadPath))
                if numberOfFilesNow > numberOfFilesInitially:
                    for folders, subfolders, files in os.walk(self.downloadPath):
                        for file in files:
                            creationTime = datetime.datetime.fromtimestamp(
                                os.path.getctime(os.path.join(folders, file)))
                            if creationTime > timeNow:
                                if file.endswith(extension):
                                    self.fileDownloaded = True
                                    return

    def connectionCheck(self):
        self.driver.switch_to.window(self.driver.window_handles[1])
        self.driver.get('https://google.com')
        self.driver.minimize_window()
        while self.fileDownloaded == False and tfpdl_videoDownloadErrors.qsize() == 0:
            try:
                self.driver.refresh()
                #self.driver.switch_to.window(self.driver.window_handles[1])
                #self.driver.get('https://google.com')
                sleep(10)
            except WebDriverException as error:
                tfpdl_videoDownloadErrors.put(error, block = False)
                raise error

    def download(self, movieName: str, season: str = '', episode: str = ''):
        if movieName == '':
            tfpdl_videoDownloadErrors.put('ERROR: Movie name field cannot be empty')
            raise BaseException
        else:
            try:
                searchMessage()
                executor = ThreadPoolExecutor(max_workers=3)
                downloadCancelCheck = executor.submit(self.checkDownloadCancelled)
                movieName = '+'.join(movieName.split())
                season, episode = self.parse(int(season)), self.parse(int(episode))
                string = 's' + season + 'e' + episode
                print(string)
                self.driver = webdriver.Chrome(options=self.chromeOptions)
                url = r'https://tfp.is/?s=' + movieName
                self.driver.get(url)
                self.driver.get_cookies()
                movieLink = self.findMovieLink(self.driver, string, "tfp.is")
                sleep(1)
                self.driver.get(movieLink)
                downloadButton = WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, f'''{self.selector} article \
                                        div[class = 'post-inner'] div[class = 'entry'] a[href ^= 'https://www.tfp.is']''')))
                print(downloadButton.get_attribute("href"))
                self.driver.get(downloadButton.get_attribute("href"))
                downloadFileLink = self.getFileLink(self.driver).get_attribute('href')
                print(downloadFileLink)
                sleep(2)
                self.driver.quit()
                numberOfFilesInitially = len(os.listdir(self.downloadPath))
                timeNow = datetime.datetime.now()
                fileChecker = executor.submit(self.checkFilePresence, numberOfFilesInitially, timeNow, '.mkv')
                self.driver = webdriver.Chrome(options=self.chromeOptions1)
                self.driver.get(downloadFileLink)
                self.driver.maximize_window()
                self.clickFirstDownloadButton(667, 539)
                self.clickSecondDownloadButton()
                self.clickThirdDownloadButton()
                fileFoundMessage()
                connectionChecker = executor.submit(self.connectionCheck)
                for downloadResult in as_completed([downloadCancelCheck, fileChecker, connectionChecker]):
                    downloadResult.result()
                #if no errors were thrown in all three functions running in the ThreadPoolExecutor
                tfpdl_videoDownloadNotification.put(True, block=False)
            except IndexError as error:
                print(-1)
                self.driver.quit()
                tfpdl_videoDownloadErrors.put(error, block=False)
                raise error
            except AssertionError as error:
                self.driver.quit()
                tfpdl_videoDownloadErrors.put(error, block=False)
                raise error
            except ElementClickInterceptedException as error:
                self.driver.quit()
                tfpdl_videoDownloadErrors.put(error, block=False)
                raise error
            except NoSuchElementException as error:
                self.driver.quit()
                tfpdl_videoDownloadErrors.put(error, block=False)
                raise error
            except TimeoutException as error:
                self.driver.quit()
                tfpdl_videoDownloadErrors.put(error, block=False)
                raise error
            except ElementNotInteractableException as error:
                self.driver.quit()
                tfpdl_videoDownloadErrors.put(error, block=False)
                raise error
            except WebDriverException as error:
                self.driver.quit()
                tfpdl_videoDownloadErrors.put(error, block=False)
                raise error
            except BaseException as error:
                self.driver.quit()
                tfpdl_videoDownloadErrors.put(error, block=False)
                raise error
            else:
                self.driver.quit()
