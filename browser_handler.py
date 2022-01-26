from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from webdriver_manager.chrome import ChromeDriverManager

import os
import time

class BrowserHandler:
    def __init__(self, headless):
        self.driver = None
        self.ec = ec
        self.headless = headless
        self.path_to_driver = self._get_web_driver()

    def _get_web_driver(self):
        print("START: Installing chrome web driver")
        path_to_driver = ChromeDriverManager().install()
        print("DONE: Installing chrome web driver")
        return path_to_driver

    def set_driver(self):
        proxy = os.getenv('http_proxy', '')

        chrome_options = Options()
        chrome_options.add_argument('--proxy-server=%s' % proxy)
        chrome_options.add_argument('--dns-prefetch-disable')
        chrome_options.add_argument('--start-maximized')
        chrome_options.add_argument('--incognito')
        if self.headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')

        self.driver = webdriver.Chrome(executable_path=self.path_to_driver, chrome_options=chrome_options)
        # Delete cookies on startup
        self.driver.delete_all_cookies()

    @property
    def get_driver(self):
        return self.driver

    def get_url(self, url):
        try:
            self.driver.get(url)
            time.sleep(0.1)
        except WebDriverException as e:
            print(e)

    def quit_driver(self):
        self.driver.close()

