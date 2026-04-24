"""Firefox Web Browser Implementation"""


import os

from glob import glob
from typing import Any, Callable, Literal, TypeVar

from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.switch_to import SwitchTo
from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.relative_locator import RelativeBy
from selenium.webdriver.support.ui import WebDriverWait

from ttpa.constants import WINDOW_SIZE

from .base import DEFAULT_WAIT_TIMEOUT, BrowserBase


D = TypeVar('D', bound=RemoteWebDriver | WebElement)
T = TypeVar('T')


class FirefoxBrowser(BrowserBase):

    def __init__(self, headless: bool = False):
        options = Options()

        # Keep images, CSS, JS enabled (default). Avoid prefs that disable features.

        # Example realistic UA (match your Firefox version/platform)
        options.set_preference("general.useragent.override",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:119.0) Gecko/20100101 Firefox/119.0"
        )

        # attempt to disable webdriver flag
        options.set_preference("dom.webdriver.enabled", False)

        # no-op for FF but kept for parity
        options.set_preference("useAutomationExtension", False)

        if headless:
            options.add_argument("-headless")

        # Use a real profile so cookies, localStorage, and extensions look normal

        # Get the correct path for Windows
        user_profiles_dir = os.path.join(os.environ['LOCALAPPDATA'], 'Mozilla', 'Firefox', 'Profiles')

        candidates = glob('*.default', root_dir=user_profiles_dir)

        if len(candidates) > 0:
            
            user_profile_dir = os.path.join(user_profiles_dir, candidates[0])

            print(f"Using Firefox profile: {user_profile_dir}\n")

            profile = FirefoxProfile(user_profile_dir)

            # Keep images, CSS, JS enabled (default). Avoid prefs that disable features.

            # attempt to disable webdriver flag
            profile.set_preference("dom.webdriver.enabled", False)
            
            # no-op for FF but kept for parity
            profile.set_preference("useAutomationExtension", False)

            profile.update_preferences()

            options.profile = profile

        self.driver = WebDriver(service=Service(), options=options)

        self.wait = WebDriverWait(self.driver, DEFAULT_WAIT_TIMEOUT)

        # Execute a script early to override navigator.webdriver
        self.driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
        )

        # Set a realistic window size and timezone/locale if needed
        self.driver.set_window_size(WINDOW_SIZE[0], WINDOW_SIZE[1])


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
        return self.driver.capabilities.get('moz:headless', False)


    @property
    def name(self) -> str:
        """Returns the name of the browser."""
        return "firefox"


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
        return WebDriverWait(self.driver, timeout).until(condition)


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
