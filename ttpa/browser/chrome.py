"""Chrome Web Browser Implementation"""


from asyncio import timeout
from typing import Any, Callable, Literal, TypeVar

from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.webdriver import WebDriver

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.switch_to import SwitchTo
from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.relative_locator import RelativeBy
from selenium.webdriver.support.ui import WebDriverWait

from .base import DEFAULT_WAIT_TIMEOUT, BrowserBase


D = TypeVar('D', bound=RemoteWebDriver | WebElement)
T = TypeVar('T')


class ChromeBrowser(BrowserBase):

    def __init__(self, headless: bool = False):
        options = Options()

        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-blink-features=AutomationControlled')

        if headless:
            options.add_argument("--headless=new")

        # Get the correct path for Windows
        # user_data_dir = os.path.join(os.environ['LOCALAPPDATA'], 'Google', 'Chrome', 'User Data')
        
        # Add necessary options to prevent crashes and detection
        # chrome_options.add_argument(f'--user-data-dir={user_data_dir}')
        # chrome_options.add_argument('--profile-directory=Default')
        # chrome_options.add_argument('--no-sandbox')
        # chrome_options.add_argument('--disable-dev-shm-usage')
        # chrome_options.add_argument('--remote-debugging-port=9222')
        # chrome_options.add_argument('--disable-gpu')
        # chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        # chrome_options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
        # chrome_options.add_experimental_option('useAutomationExtension', False)

        self.driver = WebDriver(service=Service(), options=options)

        self.wait = WebDriverWait(self.driver, DEFAULT_WAIT_TIMEOUT)


    def close(self) -> None:
        """Closes the current window."""
        self.driver.close()


    @property
    def current_window_handle(self) -> str:
        """Returns the handle of the current window.

        Returns:
            The handle of the current window.

        Example:
            `handle = driver.current_window_handle`
        """
        return self.driver.current_window_handle


    def execute_script(
            self,
            script: str,
            *args: Any
        ) -> Any:
        """Synchronously Executes JavaScript in the current window/frame.

        Args:
            script: The javascript to execute.
            *args: Any applicable arguments for your JavaScript.

        Example:
            ```
            id = "username"
            value = "test_user"
            driver.execute_script("document.getElementById(arguments[0]).value = arguments[1];", id, value)
            ```
        """        
        return self.driver.execute_script(script, *args)


    def find_element(
            self, by: str | RelativeBy = By.ID, value: str | None = None
        ) -> WebElement:
        return self.driver.find_element(by, value)


    def find_elements(
            self,
            by: str = By.ID,
            value: str | None = None
        ) -> list[WebElement]:
        return self.driver.find_elements(by, value)


    def get(self, url: str) -> None:
        self.driver.get(url)


    @property
    def headless(self) -> bool:
        """Returns whether the browser is running in headless mode."""
        return '--headless=new' in self.driver.capabilities.get('goog:chromeOptions', {}).get('args', [])


    @property
    def name(self) -> str:
        """Returns the name of the browser."""
        return "chrome"


    def set_script_timeout(self, time_to_wait: float) -> None:
        self.driver.set_script_timeout(time_to_wait)


    @property
    def switch_to(self) -> SwitchTo:
        """Return an object containing all options to switch focus into.

        Returns:
            An object containing all options to switch focus into.

        Examples:
            `element = driver.switch_to.active_element`
            `alert = driver.switch_to.alert`
            `driver.switch_to.default_content()`
            `driver.switch_to.frame("frame_name")`
            `driver.switch_to.frame(1)`
            `driver.switch_to.frame(driver.find_elements(By.TAG_NAME, "iframe")[0])`
            `driver.switch_to.parent_frame()`
            `driver.switch_to.window("main")`
        """      
        return self.driver.switch_to


    def wait_for(
            self,
            condition: Callable[[D], Literal[False] | T],
            timeout: float = DEFAULT_WAIT_TIMEOUT,
            timeout_message: str = '',
        ) -> T:
        """Wait until condition returns a value that is not False.

        Calls the method provided with the driver as an argument until the
        return value does not evaluate to ``False``.

        Args:
            condition: A callable object that takes a WebDriver instance as an
                argument.
            timeout: The maximum time to wait for the condition to become true.
            timeout_message: Optional message for TimeoutException.

        Returns:
            The result of the last call to `condition`.

        Raises:
            TimeoutException: If `condition` does not return a truthy value within
                the WebDriverWait object's timeout.

        Example:
            >>> from selenium.webdriver.common.by import By
            >>> from selenium.webdriver.support.ui import WebDriverWait
            >>> from selenium.webdriver.support import expected_conditions as EC
            >>>
            >>> browser = create_browser()  # Replace with actual browser creation
            >>>
            >>> # Wait until an element is visible on the page
            >>> element = browser.wait_for(EC.visibility_of_element_located((By.ID, "exampleId")), timeout=10)
            >>> print(element.text)
        """        
        return WebDriverWait(self.driver, timeout).until(condition, timeout_message)


    @property
    def window_handles(self) -> list[str]:
        """Returns a list of handles for all open windows.

        Returns:
            A list of handles for all open windows.

        Example:
            `handles = driver.window_handles`
        """
        return self.driver.window_handles


    def quit(self) -> None:
        self.driver.quit()
