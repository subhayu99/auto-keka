import os
import json
import config
from typing import Literal
from selenium import webdriver
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from src.log_utils import cloud_logger as logger
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC


def encode_password(passw: str):
    import hashlib
    return hashlib.sha256(passw.encode()).hexdigest()


def reverse_geocode(lat, lng):
    from geopy.geocoders import Nominatim
    from geopy.location import Location
    from geopy.exc import GeocoderUnavailable
    try:
        geocoder = Nominatim(user_agent = 'automate-keka')
        location: Location = geocoder.reverse((lat, lng))
    except GeocoderUnavailable:
        return None
    return location


def create_file_if_not_exists(file_path: str):
    os.makedirs("/".join(file_path.split("/")[:-1]), exist_ok=True)
    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            json.dump({}, f) if file_path.endswith(".json") else f.write("")

    return file_path


def read_or_write_json(file_path: str, mode: Literal["w", "r"] = "r", data: dict = {}, indent = 4):
    """
    Reads or creates a json file

    Args:
        file_path: path to the file
        data: data to be written to the file
        mode: `w` for write and `r` for read

    Returns:
        None if mode is `w` and loaded json if mode is `r`
    """
    assert mode in ["w", "r"], "Invalid mode"
    assert file_path.endswith(".json"), "Invalid file type"
    create_file_if_not_exists(file_path)
    if mode == "w":
        json.dump(data, open(file_path, "w"), indent=indent)
    elif mode == "r":
        return json.load(open(file_path, "r"))
    return None


def get_chrome_driver(headless=False, enable_logs=False, proxy=""):
    options = Options()
    options.headless = headless
    options.add_argument("--incognito")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    if enable_logs:
        options.set_capability(
            "goog:loggingPrefs", {"performance": "ALL", "browser": "ALL"}
        )
    if proxy:
        options.add_argument(f"--proxy-server={proxy}")
    browser = webdriver.Chrome(ChromeDriverManager().install(), options=options)
    if not headless:
        browser.maximize_window()
    return browser


def get_extract_return_zip_path(url: str):
    import requests
    import zipfile

    # Download the zip file
    response = requests.get(url)

    # Get the zip file name
    url = url.rstrip("/")
    zip_file_name = url.split("/")[-1]

    # Save the zip file to the current directory
    open(zip_file_name, "wb").write(response.content)

    # Extract the zip file in the current directory
    zip_ref = zipfile.ZipFile(zip_file_name, "r")
    zip_ref.extractall("./")
    zip_ref.close()

    # Get the path of the extracted directory
    extracted_dir = f"./{zip_file_name[:-4]}"
    return extracted_dir


def get_browsermob_proxy(version="2.1.4"):
    from browsermobproxy import Server

    file_name = f"browsermob-proxy-{version}"
    url = f"https://github.com/lightbody/browsermob-proxy/releases/download/{file_name}/{file_name}-bin.zip"
    extracted_path = get_extract_return_zip_path(url)

    server = Server(extracted_path)
    server.start()
    proxy = server.create_proxy()
    return proxy


def wait_element(browser: WebDriver, by: By, element_selector):
    """this funstion will make you wait untill the element is located in the browser and returns the completely loaded browser"""
    i = 0
    delay = 5

    while i <= 8:
        i += 1
        try:
            WebDriverWait(browser, delay).until(
                EC.presence_of_element_located((by, element_selector)))
            print("-------------------------")
            break
        except:
            continue
    return browser


def get_log_entries(driver: WebDriver):
    ##visit your website, login, etc. then:
    log_entries = driver.get_log("performance")

    for entry in log_entries:
        try:
            obj_serialized: str = entry.get("message")
            obj = json.loads(obj_serialized)
            message = obj.get("message")
            method = message.get("method")
            if method in ['Network.requestWillBeSentExtraInfo' or 'Network.requestWillBeSent']:
                try:
                    for c in message['params']['associatedCookies']:
                        if c['cookie']['name'] == 'authToken':
                            bearer_token = c['cookie']['value']
                except:
                    pass
            print(type(message), method)
            print('--------------------------------------')
        except Exception as e:
            raise e from None


def get_time_delta(start_time, end_time):
    start_time = datetime.fromisoformat(start_time) if isinstance(start_time, str) else start_time
    end_time = datetime.fromisoformat(end_time) if isinstance(end_time, str) else end_time
    time_delta = end_time - start_time

    return time_delta


def get_delta_day_hr_min_sec(td: timedelta):
    minutes, seconds = divmod(td.total_seconds(), 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)

    return days, hours, minutes, seconds


def format_time_delta(pre: str, td: timedelta, post: str):
    day, hr, min, sec = get_delta_day_hr_min_sec(td)
    message = pre
    if day:
        message += f"{int(day)} days, "
    if hr:
        message += f"{int(hr)} hours, "
    if min and not day:
        message += f"{int(min)} minutes, "
    if sec and not day and not hr:
        message += f"{int(sec)} seconds, "

    return message[:-2] + post