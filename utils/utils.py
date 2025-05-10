from typing import List
from selenium.webdriver.remote.webelement import WebElement
from datetime import datetime, timedelta
from classes.constants.others import DAY_MAPPING

def is_login_required(browser):
    try:
        from selenium.webdriver.common.by import By

        element = browser.find_element(By.CSS_SELECTOR, ".nav__button-secondary")
        if len(element) > 0:
            login_required = True
    except Exception as e:
        login_required = False
        
    return login_required


def is_element_available(element_list: List[WebElement]):

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


def calculate_next_day_date(day: str):
    day_index = DAY_MAPPING.get(day)
    today_index = datetime.now().weekday() + 1    
    next_time_in_days = (day_index - today_index) % 7
    next_date = datetime.now() + timedelta(days=next_time_in_days)
    return next_date



