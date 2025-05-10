from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
from typing import List
from time import sleep
from classes.constants.tags import *
from enum import Enum
from classes.utils import normalize_text

import abc
import random

class FilterTypes(Enum):
    Touchable="TouchableFilter"
    Location="LocationFilter"
    Input="InputFilter"

class Filter(metaclass=abc.ABCMeta):
    """
        Abstract class to be inherited by any filter
        
        :param **kwargs: [name='John', value='Doe']
    """
    def __init__(self, wait: WebDriverWait, **kwargs) -> None:
        self._wait = wait
        for key, item in kwargs.items():
            setattr(self, f'_{key}', item)

    @property 
    def name(self):
        return self._name

    @name.setter
    def name(self, new_name) -> None:
        self._name = new_name

    @property
    def value(self) -> str:
        return self._value
    
    @value.setter
    def value(self, new_value) -> None:
        self._value = new_value

    def get_elements(self, by: By, value: str) -> List[WebElement]:
        try:
            elements = self._wait.until(EC.presence_of_all_elements_located((by, value)), message=f"Element {value} not found.")
        except Exception as e:
            print(e)
            return []
        return elements

    @abc.abstractmethod
    def apply_filter(self):
        """
        Abstract method that must be implemented by subclasses.
        """
        pass


class TouchableFilter(Filter):
    """
       Returns an instance of a (Filter by Click on it) 
    """
    def __init__(self, wait: WebDriverWait, **kwargs) -> None:
        super().__init__(wait, **kwargs)
        

    def apply_filter(self):

        wait = self._wait

        filter_applied = False
        filter_container = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, FILTER_CONTAINER)), message="Filter container not found.")
        filters: List[WebElement] = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ALL_FILTERS)), message="Filters are not available.")

        # Here we filter by "Person" review in further meetings
        for filter in filters:
            if filter.text == self._name: 
                wait.until(EC.element_to_be_clickable(filter), message=f"Filter {filter.text} is not clickable.")
                try:
                    sleep(random.uniform(0.5, 2.1))
                    filter.click()
                except StaleElementReferenceException:
                    filter_applied=True
                filter_applied = True
                print(f"Filter {filter.text} is applied")
                break
        
        return filter_applied
                

class LocationFilter(Filter):
    """
        Returns a specific location filter to use only at Linkedin.   
    """

    def __init__(self, location: str, wait: WebDriverWait, **kwargs) -> None:
        super().__init__(wait, **kwargs)
        self._location = location

    def apply_filter(self) -> bool:

        """
            Returns True if the filter was applied succesfully otherwise returns False.
        """
        wait = self._wait
        location = self._location

        filter_applied = False
        filter_container = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, FILTER_CONTAINER)))
        filters = self.get_elements(By.CSS_SELECTOR, ALL_FILTERS)

        if len(filters) > 0:
            for filter in filters:
                if filter.text == "Ubicaciones":
                    sleep(random.uniform(0.7, 1.8))
                    filter.click()
                    location_form = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, FILTER_FORM)))
                    location_input = self.get_elements(By.CSS_SELECTOR, SEARCH_INPUT_FILTER)
                    if len(location_input) > 0:
                        for index, element in enumerate(location_input):
                            if "ubicación" in element.get_attribute("placeholder").lower():
                                for letter in location:
                                    sleep(random.uniform(0.2, 0.9))
                                    element.send_keys(letter) # Galicia / Galiza, España
                                sleep(random.uniform(0.5, 1.3))
                                location_list = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, FILTER_HIDDEN_SELECT_LIST)))
                                span_to_select = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, FILTER_SPAN_SUGGESTED_TEXT)))
                                sleep(random.uniform(0.7, 1.5))
                                span_to_select[0].click()
                                show_results_btn = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, BUTTON_SHOW_FILTER_RESULTS)))
                                for btn in show_results_btn:
                                    if len(btn.text) > 0:
                                        btn_to_press = wait.until(EC.element_to_be_clickable(btn))
                                        sleep(random.uniform(0.3, 0.8))
                                        btn_to_press.click()
                                        filter_applied = True
                                        break
                            if filter_applied:
                                break
                if filter_applied:
                    break

        return filter_applied


class InputFilter(Filter):
    """
        :param filter_name: The text written on the filter. Example "Ubicaciones", "Empresa actual", "En busca de personal" ...
        :param input_value: The text you want to write over the filter input.
        :param placeholder: The text written on the input placeholder. Example "Añade una ubicación"
    """
    def __init__(self, filter_name: str, input_value: str, placeholder: str, wait: WebDriverWait, **kwargs) -> None:
        super().__init__(wait, **kwargs)
        self._name = filter_name
        self._input_value = input_value
        self._placeholder = placeholder


    def apply_filter(self):
        
        try:
            wait = self._wait
            name = self._name
            input_text = self._input_value
            placeholder = self._placeholder.lower()

            filter_applied = False
            filter_container = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, FILTER_CONTAINER)), message="Filter container not found.")
            filters = self.get_elements(By.CSS_SELECTOR, ALL_FILTERS)

            if len(filters) > 0:
                for filter in filters:
                    if filter.text.lower() == name.lower():
                        filter.click()
                        form = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, FILTER_FORM)), message="Filter form not found.")
                        input = self.get_elements(By.CSS_SELECTOR, SEARCH_INPUT_FILTER)
                        if len(input) > 0:
                            for index, element in enumerate(input):
                                if placeholder in element.get_attribute("placeholder").lower():
                                    for letter in input_text:
                                        sleep(random.uniform(0.2, 0.9))
                                        element.send_keys(letter) # Text to introduce over the input filter ...
                                    sleep(random.uniform(0.3, 1.1))
                                    location_list = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, FILTER_HIDDEN_SELECT_LIST)), message="Filter hidden select list not found.")
                                    span_to_select = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, FILTER_SPAN_SUGGESTED_TEXT)), message="Filter span not found.")
                                    span_to_select[0].click()
                                    sleep(random.uniform(0.5, 1.7))
                                    show_results_btn = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, BUTTON_SHOW_FILTER_RESULTS)), message="Button show filter results not found.")
                                    for btn in show_results_btn:
                                        if len(btn.text) > 0:
                                            btn_to_press = wait.until(EC.element_to_be_clickable(btn))
                                            sleep(random.uniform(0.5, 0.7))
                                            btn_to_press.click()
                                            filter_applied = True
                                            break
                                if filter_applied:
                                    break
                    if filter_applied:
                        break
            return filter_applied
        except Exception as e:
            print(e)
            return False


class AllFilters(Filter):

    def __init__(self, wait, **kwargs):
        super().__init__(wait, **kwargs)
        self.activator = TouchableFilter(wait=wait, name="Todos los filtros")

    def open(self):
        return self.activator.apply_filter()
    
    def add_filter_option(self, li: WebElement, filter_value: str):
        
        add_option_btn = li.find_elements(By.TAG_NAME, "button")
        
        if len(add_option_btn) > 0:
            placeholder = add_option_btn[0].find_element(By.TAG_NAME, 'span').text
            sleep(random.uniform(0.3, 1))
            add_option_btn[0].click()
            sleep(random.uniform(2, 2.5)) # No puedo hacer wait porque obtendría respuesta instantánea por input con ese placeholder en la barra superior
            add_option_input = li.find_elements(By.CSS_SELECTOR, f"input[placeholder='{placeholder}']")
            if len(add_option_input) > 0:
                for letter in filter_value:
                    sleep(random.uniform(0.2, 0.9))
                    add_option_input[0].send_keys(letter)
                return True
            else:
                print("No se ha encontrado el input para agregar opción")
                return False
        return False

    def apply_filter(self, **kwargs):
        """

            :param **kwargs: [ filter_name = filter_value_to_apply ]

        """
        wait = self._wait
        is_open = self.open()

        try:
            if is_open:
                for filter_name, filter_value in kwargs.items():
                    matched_filter = False
                    all_filters: List[WebElement] = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ALL_FILTERS_LIST)), message="All filters are not available.")
                    for filter in all_filters:
                        filter_name_formatted = filter_name.replace("_", " ")
                        if normalize_text(filter.find_element(By.TAG_NAME, "h3").text) == normalize_text(filter_name_formatted):
                            value_list: List[WebElement] = filter.find_elements(By.CSS_SELECTOR, ALL_FILTERS_LIST_VALUE_ITEMS) # (input, label)
                            if len(value_list) > 0:
                                for li in value_list:
                                    label = li.find_elements(By.CSS_SELECTOR, "p > span")
                                    input = li.find_elements(By.TAG_NAME, "input")
                                    if len(label) > 0 and len(input) > 0:
                                        if normalize_text(filter_value) in normalize_text(label[0].text):
                                            label[0].click()
                                            matched_filter = True
                                            break
                                    else:
                                        matched_filter = self.add_filter_option(li, filter_value)
                                        if matched_filter:
                                            sleep(1)
                                            suggestion_list = li.find_elements(By.CSS_SELECTOR, "div[role='listbox']")
                                            if len(suggestion_list) > 0:
                                                options = suggestion_list[0].find_elements(By.CSS_SELECTOR, ALL_FILTERS_DROPDOWN_SUGGESTION_ELEMENTS)
                                                if len(options) > 0:
                                                    options[0].click()
                                                else:
                                                    print("No se ha encontrado ninguna opción en la lista de valores")
                                            else:
                                                print("No se ha encontrado una lista de opciones")
                                            break
                            else:
                                print("No se ha encontrado la lista de valores del filtro")
                        if matched_filter: 
                            break
                        else:
                            print("No existe el filtro")
                
                apply_filter_btn = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ALL_FILTERS_APPLY_BUTTON)), message="Apply filters button is not available.")
                if len(apply_filter_btn) > 0:
                    apply_filter_btn[0].click()
                return True
            else:
                print("No se ha podido abrir el panel de filtros")
                return False
        except Exception as e:
            print(f"Something went wrong at {self.apply_filter.__name__}: {e}")
            return False
        
    def apply_keywords(self, **kwargs):

        """

            :param **kwargs: [ filter_name = filter_value_to_apply ]

        """
        wait = self._wait
        is_open = self.open()

        try:
            if is_open:
                for filter_name, filter_value in kwargs.items():
                    filter_name_formatted = filter_name.replace("_", " ")
                    matched_filter = False
                    all_filters: List[WebElement] = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ALL_FILTERS_LIST)), message="All filters are not available.")
                    for filter in all_filters:
                        if normalize_text(filter.find_element(By.TAG_NAME, "h3").text) == normalize_text("Palabras clave"):
                            value_list: List[WebElement] = filter.find_elements(By.CSS_SELECTOR, ALL_FILTERS_LIST_VALUE_ITEMS) # (input, label)
                            if len(value_list) > 0:
                                for li in value_list:
                                    label = li.find_elements(By.TAG_NAME, "label")
                                    if len(label) > 0:
                                        if normalize_text(label[0].text) == normalize_text(filter_name_formatted):
                                            input = label[0].find_elements(By.TAG_NAME, "input")
                                            if len(input) > 0:
                                                for letter in filter_value:
                                                    sleep(random.uniform(0.2, 0.9))
                                                    input[0].send_keys(letter)
                                                matched_filter = True
                                                break
                apply_filter_btn = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ALL_FILTERS_APPLY_BUTTON)), message="Apply filters button is not available.")
                if len(apply_filter_btn) > 0:
                    apply_filter_btn[0].click()
                return True
            else:
                print("No se ha podido abrir el panel de filtros")
                return False
        except Exception as e:
            print(f"Something went wrong at {self.apply_keywords.__name__}: {e}")
            return False