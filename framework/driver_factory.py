import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService


def build_driver(browser="chrome", headless=False, remote_url=None):
    if browser == "chrome":
        options   = webdriver.ChromeOptions()
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        chrome_binary = os.environ.get("CHROME_BINARY")
        if chrome_binary:
            options.binary_location = chrome_binary
    elif browser == "firefox":
        options = webdriver.FirefoxOptions()
        if headless:
            options.add_argument("-headless")
    elif browser == "edge":
        options = webdriver.EdgeOptions()
        if headless:
            options.add_argument("--headless=new")
    else:
        raise ValueError(f"Unsupported browser: {browser}")

    if remote_url:
        driver = webdriver.Remote(command_executor=remote_url, options=options)
    elif browser == "chrome":
        driver_path = os.environ.get("CHROMEDRIVER_PATH")
        service = ChromeService(executable_path=driver_path) if driver_path else ChromeService()
        driver = webdriver.Chrome(options=options, service=service)
    elif browser == "firefox":
        driver = webdriver.Firefox(options=options)
    else:
        driver = webdriver.Edge(options=options)
    driver.set_window_size(1366, 900)
    return driver
