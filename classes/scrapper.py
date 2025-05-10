from typing import List
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent
from time import sleep
from config.config import Config
from config.proxies.chrome_extension import ChromeProxy
from config.proxies.proxy import get_random_proxy_by_city

import undetected_chromedriver as u_chrome
import random
import time

class Scrapper:
    r"""
            Returns class instance of a simple scrapper (only works with Chrome) V.0.1

            :param *options: Chrome options as str
            :param profile_name: Profile name found at: \path_to_profile\Profile #
            :param path_to_profile: C:\Users\USER\AppData\Local\Google\Chrome\User Data\
    """

    def __init__(self, *options: str, profile_name: str, path_to_profile: str, language="es") -> None:
        self._language = language
        self._options = Options()
        self._user_agent = UserAgent()

        # proxy = get_random_proxy_by_city("Madrid").split(":")

        # self._proxy = ChromeProxy(
            # host = proxy[0],
            # port = int(proxy[1]),
            # username = proxy[2],
            # password = proxy[3]
        # )

        for option in options:
            self._options.add_argument(option)
        if profile_name and path_to_profile:
            self._options.add_argument("--disable-webrtc")
            self._options.add_argument("--no-sandbox")
            self._options.add_argument(f"user-agent={self._user_agent.getChrome}")
            #if Config.ENVIRONMENT != "dev":
            #    self._options.add_argument("--headless=new")
            self._options.add_argument("--disable-gpu")
            self._options.add_argument("--disable-dev-shm-usage")
            self._options.add_argument("--window-size=1920x1080")  # Ajustar la resolución
            self._options.add_argument("--start-maximized")
            self._options.add_argument("--display=:1")
            # self._options.add_argument(f"--load-extension={self._proxy.create_extension()}")
        
        self.browser = u_chrome.Chrome(service=Service(ChromeDriverManager().install()), options=self._options)
        self.browser.execute_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            window.navigator.chrome = { runtime: {} };
            Object.defineProperty(navigator, 'languages', { get: () => ['es-ES', 'es'] });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
        """)

    def navigate_to(self, website_url) -> None:
        sleep(2)
        self.browser.get(website_url)

    def quit(self) -> None:
        self.browser.quit()

    def wait(self, timeout: float) -> WebDriverWait:
        """
            Returns a WebDriverWait class instance.

            :param timeout: The value of timeout it has to wait
            :return: Class instance
        """
        return WebDriverWait(self.browser, timeout)

    def isOnWebsite(self, website_title: str) -> bool:
        if (website_title.lower() in self.browser.title.lower()):
            return True
        return False

    def get_elements(self, by: By, value: str) -> List[WebElement]:
        """
            Returns a tuple containing the type of selector and its corresponding value.

            :param by: The type of selector (By.CSS_SELECTOR, By.TAG_NAME, By.ID, etc.)
            :param value: The value of the selector
            :return: A tuple (By.<type>, value)
        """
        ByAllowedValues = [By.CSS_SELECTOR, By.TAG_NAME, By.ID, By.CLASS_NAME, By.NAME, By.LINK_TEXT, By.PARTIAL_LINK_TEXT, By.XPATH]
        if not by in ByAllowedValues: return None

        elements = self.browser.find_elements(by, value)

        return elements

    def is_element_available(element_list: List[WebElement]):
        """
            Returns True if the length of the element_list > 0

            :param element_list: The elements list ( ** List[WebElement] **)
            :return: -> bool
        """
        is_available = False

        if not isinstance(element_list, list):
            raise TypeError("""
                                Parameter type must be List[WebElement]
                            """)
        else:

            for element in element_list:
                if not isinstance(element, WebElement):
                    raise TypeError("""
                                Parameter type must be List[WebElement]
                            """)

            if len(element_list) > 0:
                is_available = True
            else:
                is_available = False

        return is_available


    def execute_sync_script(self, script: str):
        return self.browser.execute_script(script)

    def execute_asynchronous_script(self, script: str):
        return self.browser.execute_async_script(script)

    def await_url(self, url: str) -> bool:
        """
            Method to await the specified url finish loading and let us interact with it.

            :param url: The url to await
        """
        wait = self.wait(timeout=15)
        try:
            is_in_url = wait.until(EC.url_to_be(url))
            return is_in_url
        except:
            return False
        
    # Método no funciona
    def move_cursor_randomly(self, moves=5, delay=0.5):
        """
        Mueve el cursor a posiciones aleatorias en la ventana del navegador.
        
        :param driver: Instancia del WebDriver de Selenium.
        :param moves: Número de movimientos aleatorios.
        :param delay: Tiempo de espera entre movimientos.
        """
        for _ in range(moves):
            x = random.randint(10, 1920)  # Ajusta según la resolución de tu viewport
            y = random.randint(10, 1080)
            
            script = f"document.dispatchEvent(new MouseEvent('mousemove', {{clientX: {x}, clientY: {y}}}))"
            self.browser.execute_script(script)
            
            print(f"Cursor simulado en ({x}, {y})")
            time.sleep(delay)


