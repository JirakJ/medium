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
        self.resource_data = ()
        self.headless = headless
        self.path_to_driver = self._get_web_driver()

    def _get_web_driver(self):
        print("START: Installing chrome web driver")
        path_to_driver = ChromeDriverManager().install()
        print("DONE: Installing chrome web driver")
        return path_to_driver

    def set_resource_data(self, resource_data):
        self.resource_data = resource_data

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

    def get_current_url(self):
        return self.driver.current_url

    def select_item(self, selector, item):
        select = Select(self.driver.find_element(*(By.CSS_SELECTOR, selector)))
        select.select_by_value(item)

    def click_element(self, button):
        self.driver.find_element(*(By.CSS_SELECTOR, button)).click()

    def js_click_element(self, element):
        element = self.driver.find_element(*element)
        self.driver.execute_script("arguments[0].click();", element)

    def js_click_on_element(self, element):
        self.driver.execute_script("arguments[0].click();", element)

    def quit_driver(self):
        self.driver.close()

    def wait_until_element_visible(self, *element, delay=15):
        try:
            WebDriverWait(self.driver, delay).until(lambda driver: self.ec.visibility_of_element_located(element))
            return True
        except TimeoutException:
            return False

    def get_element(self, element, log_error=True) -> WebElement:
        try:
            self.wait_until_element_visible(element)
            r_element = self.driver.find_element(*element)
        except NoSuchElementException:
            raise NoSuchElementException('Element not found.')
        except TimeoutException:
            raise TimeoutException('Takes too long (>5s) to locate element.')
        return r_element

    def get_element_text(self, element):
        return self.get_element(element).text

    def get_element_click(self, element):
        time.sleep(0.1)
        self.get_element(element).click()

    def clear_cookies(self):
        self.driver.delete_all_cookies()
        return self

    def find_element(self, selector):
        return self.driver.find_element(*selector)

    def find_elements(self, selector):
        return self.driver.find_elements(*selector)

    def scroll_view_to_bottom(self):
        self.driver.execute_script("window.scrollTo(0,document.body.scrollHeight);")

    def scroll_element_into_view(self, selector) -> None:
        """
        Method which helps scroll to bottom of current page
        :param selector: tuple(Selector like By.CSS_SELECTOR, By.XPATH etc., string used for identification of element)
        """
        element = self.find_element(selector=selector)
        self.driver.execute_script("arguments[0].scrollIntoView(true);", element)

    def scroll_to_given_element(self, element) -> None:
        """
        Method which helps scroll to bottom of current page
        :param element: WebElement
        """
        self.driver.execute_script("arguments[0].scrollIntoView(true);", element)

    def paste(self, element, data):
        self.driver.execute_script("document.getElementById('{}').value = `{}`".format(element, str(data)))

    def select(self, drop_down, value):
        select = Select(drop_down)
        select.select_by_value(value)

    def solve_lazy_loading(self):
        # scrolling
        lastHeight = self.driver.execute_script("return document.body.scrollHeight")
        # print(lastHeight)

        pause = 0.5
        while True:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(pause)
            newHeight = self.driver.execute_script("return document.body.scrollHeight")
            if newHeight == lastHeight:
                break
            lastHeight = newHeight
            # print(lastHeight)

    def is_displayed(self, selector) -> bool:
        """
        Method which check if element is displayed
        :param selector: tuple(Selector like By.CSS_SELECTOR, By.XPATH etc., string used for identification of element)
        """
        if len(self.driver.find_elements(*selector)) > 0:
            return True
        return False

    def is_clickable(self, element) -> bool:
        """
        Method which check if element is clickable
        :param selector: tuple(Selector like By.CSS_SELECTOR, By.XPATH etc., string used for identification of element)
        """
        if element.is_enabled() and element.is_displayed():
            return True
        return False
