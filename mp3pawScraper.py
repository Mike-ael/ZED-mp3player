import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.webdriver.chrome.options import Options
from threading import Thread
import os
import datetime
from voicemessages import musicFoundMessage
def checkFilePresence(downloadPath, numberOfFilesInitially, timeNow, artistName, songTitle):
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
                    except FileNotFoundError:
                        pass
                    except BaseException:
                        pass

def mp3pawscraper(artistName, songTitle):
    path = r'C:\Users\HP\Downloads'
    webUrl = r'https://mp3paw.com/'
    numberOfFilesInitially = len(os.listdir(path))
    timeNow = datetime.datetime.now()
    chrome_options = Options()
    chrome_options.add_argument('--disable-notifications')
    chrome_options.add_argument('--headless')
    driver = webdriver.Chrome(options=chrome_options)
    try:
        driver.get(webUrl)
    except:
        driver.quit()
        raise
    driver.get_cookies()
    searchElem = driver.find_element_by_id('search')
    keyword = artistName + " " + songTitle
    for letter in keyword:
        searchElem.send_keys(letter)
        time.sleep(.3)
    time.sleep(1)
    searchElem.send_keys(Keys.ENTER)
    downloadButton = driver.find_elements_by_tag_name('li')
    downloadElem = None
    for tag in downloadButton:
        if tag.text == "Download MP3":
            downloadElem = tag
            break
    time.sleep(2)
    downloadElem.click()
    time.sleep(3)
    windows = driver.window_handles
    driver.switch_to.window(windows[1])
    driver.get_cookies()
    buttons = driver.find_elements_by_css_selector('ul > li')
    params = {'behavior': 'allow', 'downloadPath': path}
    driver.execute_cdp_cmd('Page.setDownloadBehavior', params)
    for i in range(5):
        try:
            buttons[7].click()
            time.sleep(1)
            break
        except ElementClickInterceptedException:
            driver.quit()
            raise
        except BaseException:
            driver.quit()
            raise
    musicFoundMessage()
    fileChecker = Thread(target=checkFilePresence, args=[path, numberOfFilesInitially, timeNow, artistName, songTitle])
    fileChecker.start()
    fileChecker.join()
    driver.quit()
    return True