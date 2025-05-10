from classes.scrapper import Scrapper 
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import *
from typing import List, Optional
from time import sleep
from datetime import datetime
from functools import wraps
from sqlalchemy.exc import IntegrityError
from sqlalchemy import desc

from utils.utils import is_element_available
from classes.utils import get_coordinates_from_location
from classes.constants.tags import * 
from classes.constants.others import CONCTACTS_PER_PAGE, MAX_SEARCHES 
from classes.filters import LocationFilter, TouchableFilter, InputFilter, FilterTypes 
from models.models import * 
from classes.logger import Logger
from classes.utils import is_numeric, get_linkedin_members
from config.config import Config
from classes.filters import AllFilters
from classes.email.sender import Sender
from pywebpush import webpush, WebPushException

import json
import math
import time
import warnings
import requests
import random


basedir = os.path.abspath(os.path.dirname(__file__))


def deprecated(reason="Este método está obsoleto y puede ser eliminado en futuras versiones."):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            warnings.warn(f"{func.__name__} está obsoleto. {reason}",
                            category=DeprecationWarning,
                            stacklevel=2
            )
            return func(*args, **kwargs)
        return wrapper
    return decorator


EMPTY = "[empty]"

class ResponseValue:

    def __init__(self, ok: bool, data: List[dict] | None) -> None:
        self.ok = ok
        self.data = data
        


class LinkedinScrapper(Scrapper):
    # _instance = None

    # def __new__(cls, *args, **kwargs):
    #     if cls._instance is None:
    #         cls._instance = super(LinkedinScrapper, cls).__new__(cls)
    #     return cls._instance

    def __init__(   self, *options, search_params, search_filters: List[dict], username: str, password:
                    str, url="https://www.linkedin.com", _profile_name:str , _path_to_profile:str, user: dict
                ) -> None:
        # if not hasattr(self, '_initialized'):
            super().__init__(*options, profile_name=_profile_name, path_to_profile=_path_to_profile)
            self._url = url
            self._search_params = search_params
            self._search_filters = search_filters
            self._username = username
            self._password = password
            self._max_searches = self.set_search_amount_by_param()
            self._user = user
            self.logger = Logger()
            self.notfifier = Sender()
            # self._initialized = True
            # print("INITIALIZED")

    @property
    def username(self):
        return self._username

    @username.setter
    def username(self, new_username):
        self._username = new_username

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, new_password):
        self._password = new_password

    def scroll_to_bottom(self):
        self.browser.find_element(By.TAG_NAME, "body").send_keys(Keys.END)

    def scroll_to_top(self):
        self.browser.find_element(By.TAG_NAME, "body").send_keys(Keys.HOME)

    def validate_cookies(self):
        user_agent = self.execute_sync_script("navigator.userAgent;")
        headers = {
            "User-Agent": user_agent
        }

        try:
            cookies: List[dict] = self._user.get("cookies").get("cookies", [])
            if len(cookies) == 0:
                return None
            cookies_dict = {cookie["name"]: cookie["value"] for cookie in cookies}
            response = requests.get("https://www.linkedin.com/feed/", cookies=cookies_dict, headers=headers)
        except Exception as e:
            print(f"❌ Invalid cookies at: {self.validate_cookies.__name__} -> {e}")
            self.logger.log(f"❌ Invalid cookies at: {self.validate_cookies.__name__} -> {e}")
            return None

        if "Something went wrong" in response.text or response.status_code == 401:
            print("❌ Cookies inválidas o sesión expirada.")
            return None
        else:
            print("✅ Cookies válidas, sesión activa.")
            return cookies
        
    def notify_user_of_linkedin_otp_validation(self) -> bool:
        
        suscriptors: List[Subscription] = Subscription.query.filter(Subscription.user_id == self._user.get("id")).all()
        if len(suscriptor) == 0:
            return False

        success = False
        for suscriptor in suscriptors:
            try:
                webpush(
                    subscription_info={
                        "endpoint": suscriptor.endpoint,
                        "keys": {"p256dh": suscriptor.p256dh, "auth": suscriptor.auth}
                    },
                    data=json.dumps({
                        "title": "LinkedIn requiere verificación",
                        "body": "Haz click aquí para enviar el código"
                    }),
                    vapid_private_key=Config.VAPID_PRIVATE_KEY,
                    vapid_claims=Config.VAPID_CLAIMS
                )
                success = True
            except WebPushException as e:
                print(f"Error enviando notificación a {suscriptor.endpoint}: {str(e)}")

        return success

    def login(self):
        wait = self.wait(timeout=10)
        try:
            
            password_inp = []
            username_inp = []

            try:
                username_inp = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, USERNAME_SELECTOR)), message="Username input not found.")
            except TimeoutException as e:
                self.logger.log(e)
                print(e)
            try:
                password_inp = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, PASSWORD_SELECTOR)), message="Password input not found.")
            except TimeoutException as e:
                self.logger.log(e)
                print(e)

            user: User = User.query.get(self._user.get("id"))
            if len(username_inp) > 0:
                username_inp[0].send_keys(user.linkedin_username)
            if len(password_inp) > 0:
                print(user.linkedin_password)
                print(user.get_linkedin_password())
                password_inp[0].send_keys(user.get_linkedin_password(), Keys.ENTER)

            try:
                time.sleep(random.uniform(3,7))
                # Verificar que no necesita OTP
                try:    
                    code_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='Enter code']")), message="Código de verificación innecesario.")
                    self.notify_user_of_linkedin_otp_validation()
                    verification_code = None
                    wait_time = 0
                    while verification_code is None and wait_time < 300:
                        db.session.expire_all()
                        verification_code: OTP | None = OTP.query.filter(OTP.user_id == self._user.get("id"), OTP.inactive == False).first()
                        wait_time += 1
                        sleep(1)
                    
                    if verification_code is None:
                        raise Exception("El código de verificación no ha sido introducido.")
                    
                    for letter in verification_code.code:
                        sleep(random.uniform(0.1, 0.45))
                        code_input.send_keys(letter)
                    code_input.send_keys(Keys.ENTER)
                    verification_code.inactive = True
                    db.session.commit()
                except Exception as e:
                    print(e)
                    self.logger.log(f"Something went wrong at: {self.login.__name__} -> {e}")

                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, SEARCH_INPUT)), message="Search input not found.")
                user.cookies = self.browser.execute_cdp_cmd("Network.getCookies", {})
                db.session.commit()
            except Exception as e:
                body = self.browser.find_element(By.TAG_NAME, "body").screenshot("./body.png")
                self.logger.log(f"Something went wrong at: {self.login.__name__} -> {e}")
                print("Cookies were not saved.")

        except (Exception) as e:
            self.logger.log(f"Login error {e}")
            print(f"Login error: {e}")

    def is_login_required(self):
        login_required = False
        try:
            wait = self.wait(timeout=10)
            element = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, INITIAL_LOGIN_BUTTON_SELECTOR)), message="Login button not found")
        except Exception as e:
            self.logger.log(f"Something went wrong at: {self.is_login_required.__name__} -> {e}")
            login_required = True
        
        cookies = self.validate_cookies()
        try:
            if cookies is not None:
                for cookie in cookies:            
                    if 'name' in cookie and 'value' in cookie and "linkedin" in cookie.get("domain"):
                        cookie.pop('sameSite', None)  # Ignora la clave sameSite si está presente
                        self.browser.add_cookie(cookie)
                self.browser.refresh()
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, SEARCH_INPUT)), message="")
                return False 
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.logger.log(e)
            
        if len(element) > 0:
            login_required = True
            element[0].click()  
        return login_required


    def apply_filter(self, name: str, wait: WebDriverWait) -> bool:
        filter_name = name
        try: 
            filter = TouchableFilter(wait, name=filter_name)
            filter_applied = filter.apply_filter()
        except StaleElementReferenceException as e:
            print(f"Error aplicando el filtro de '{filter_name}': {e.msg}")
            self.logger.log(f"Error aplicando el filtro de '{filter_name}': {e.msg}")
            filter_applied = True

        return filter_applied
    
    def apply_input_filter(self, name: str, value: str, placeholder: str, wait: WebDriverWait) -> bool:

        try:
            input_filter = InputFilter(name, value, placeholder, wait)
            filter_applied = input_filter.apply_filter()
        except Exception as e:
            self.logger.log(f"Error aplicando el filtro {name}. \n{e}")
            filter_applied = False
        
        return filter_applied

    def apply_location_filter(self, value: str, wait: WebDriverWait) -> bool:

        try:
            location_filter = LocationFilter(value, wait)
            filter_applied = location_filter.apply_filter()
        except (NoSuchElementException, TimeoutException, StaleElementReferenceException) as e:
            filter_applied = False
            self.logger.log(f"Error aplicando el filtro de Ubicación: {e.msg}")
            print(f"Error aplicando el filtro de Ubicación: {e.msg}")

        return filter_applied
    
    def apply_side_filters(self, wait: WebDriverWait, use_keywords: bool, **kwargs):
        try:
            all_filters = AllFilters(wait)
            filter_applied = all_filters.apply_filter(**kwargs)
            if use_keywords:
                filter_applied = all_filters.apply_keywords(**kwargs)
        except (NoSuchElementException, TimeoutException, StaleElementReferenceException) as e:
            filter_applied = False
            self.logger.log(f"Error aplicando el filtro del panel lateral: {e.msg}")
            print(f"Error aplicando el filtro del panel lateral: {e.msg}")

        return filter_applied

    def apply_all_filters(self, waitDriver: WebDriverWait) -> list:

        filter_handler = {
                        FilterTypes.Touchable.value: self.apply_filter,
                        FilterTypes.Location.value: self.apply_location_filter,
                        FilterTypes.Input.value: self.apply_input_filter,
        } 

        filters_applied = []
        for filter in self._search_filters:
            filter_attributes = {}
            type = filter.get("type", None)
            name = filter.get("name", None)
            value = filter.get("value", None)
            placeholder = filter.get("placeholder", None)

            # print("========== FILTERS ===========")
            # print(name)
            # print("========== FILTERS ===========")

            if type is not None:
                filter_attributes['name'] = name
                filter_attributes['wait'] = waitDriver
                if value not in EMPTY:
                    filter_attributes['value'] = value
                if placeholder not in EMPTY:
                    filter_attributes['placeholder'] = placeholder

                match type:
                    case FilterTypes.Touchable.value:
                        filters_applied.append(
                            filter_handler[type](
                                                    name=filter_attributes["name"], 
                                                    wait=filter_attributes["wait"]
                            )
                        )
                    case FilterTypes.Location.value:
                        filters_applied.append(
                            filter_handler[type](
                                                    value=filter_attributes["value"], 
                                                    wait=filter_attributes["wait"]
                            )
                        )
                    case FilterTypes.Input.value:
                        filters_applied.append(
                            filter_handler[type](
                                                    name=filter_attributes["name"], 
                                                    value=filter_attributes["value"], 
                                                    placeholder=filter_attributes["placeholder"], 
                                                    wait=filter_attributes["wait"])
                            )
                    case _:
                        print("NO HAGO MATCH")
                        print(type)
                        pass

            else:
                self.logger.log("Filter 'type' attribute not found in request.")
                filters_applied.append(False)
        return filters_applied    

    # Unused for now
    def clean_all_filters(self, waitDriver: WebDriverWait) -> bool:

        wait = waitDriver
        try:
            all_filters = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ALL_FILTERS)), message="Filters are not available")
            if not all_filters:
                message = f"No filters to clean at: {self.clean_all_filters.__name__}"
                self.logger.log(message) 
                return False
            
            for index, filter in enumerate(all_filters):
                filter.click()
                sleep(2)
                restablish_buttons = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//button[contains(@aria-label, 'Restablecer')]")), message="No restablish button found.")
                show_result_buttons = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, BUTTON_SHOW_FILTER_RESULTS)), message="No show result button found.")
                sleep(2)
                if not restablish_buttons and not show_result_buttons:
                    message = f"No buttons founded at: {self.clean_all_filters.__name__}"
                    self.logger.log(message) 
                    return False

                if restablish_buttons and show_result_buttons:
                    # print(restablish_buttons[index].text.lower(), " -> Restablish button text")
                    if restablish_buttons[index].text.lower() == "restablecer":
                        restablish_buttons[index].click()
                        sleep(1)
                        show_result_buttons[index].click()
                        

            return True

        except Exception as e:
            message = f"Something went wrong: {e} -> {self.clean_all_filters.__name__}"
            self.logger.log(message)
            return False
            

    def scrap_search_result_data(self, pages: int, filter_group_id: int):

        time_start = time.time()
        err = ""
        scrapped_succesfully = False
        wait = self.wait(20)
        data = []
        todays_date = datetime.now().strftime("%d_%m_%Y")

        if Config.ENVIRONMENT != "dev":
            potentials_path = "/home/ekiona/linkedin/data/potentials/"
        else:
            potentials_path = r"C:\Users\Borja\Desktop\Scrapper API\data\potentials" + "\\"

        print(basedir)

        with open(f"{potentials_path}{todays_date}.json", mode="w", encoding="utf-8") as client_file:

            last_param_id: int = Parameter.query.order_by(Parameter.id.desc()).first().id if Parameter.query.count() > 0 else 1
            last_history_id: int = ScrappingHistory.query.order_by(ScrappingHistory.id.desc()).first().id if ScrappingHistory.query.count() > 0 else 1

            for index, param  in enumerate(self._search_params):
                
                parameter_to_add = Parameter(
                    name=param.get("name", "N/A"),
                    value=param.get("value", "N/A")
                )

                db.session.add(parameter_to_add)
                db.session.commit()

                try:
                    search_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, SEARCH_INPUT)), message="Search input not found")
                    search_input.clear()
                    for letter in param.get("value"):
                        sleep(random.uniform(0.2, 0.9))
                        search_input.send_keys(letter)
                    search_input.send_keys(Keys.ENTER)

                    if index == 0:
                        filters_applied = []
                        filters_applied = self.apply_all_filters(wait)
                    else:
                        filters_applied = [True * len(self._search_filters)]
                    sleep(random.uniform(2.2, 5.1))
                    # In case of using advanced filters
                    # self.apply_side_filters(wait, use_keywords=True, sector="Industria manufacturera", titulo="ingeniero, director, arquitecto")
                    
                    if all(filters_applied):

                        for index in range(pages): # Max pages is 20
                            
                            try:
                                search_results = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, SEARCH_RESULTS)), message="No results found for these parameters.")

                                data.append(self.save_lead_data(search_results, last_param_id, last_history_id, filter_group_id))

                                self.scroll_to_bottom()
                                try:
                                    next_page_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, NEXT_PAGE_BTN)), message="Next page button not found.")
                                except Exception as e:
                                    # If user account is not Premium
                                    # Here must be used self.too_many_request_handler()
                                    self.logger.log("El button de página siguiente está desactivado")
                                    next_page_btn = None
                                    
                                sleep(random.uniform(4, 10))

                                if next_page_btn is not None:
                                    next_page_btn.click()
                                    scrapped_succesfully = True
                                else: 
                                    self.logger.log(f"La última página visible es la {index}")
                                    scrapped_succesfully = True
                                    break
                                
                                sleep(random.uniform(4, 10))

                            except (TimeoutException, NoSuchElementException, StaleElementReferenceException, ElementClickInterceptedException) as e:
                                print(f"Error en la página: {index} \n Error: {e}")
                                self.logger.log(f"Error en la página: {index} \n Error: {e}")
                                scrapped_succesfully = True if index > 1 else False 
                                err = str(e)
                                break
                    else:
                        err = f"""Todos los filtros no pudieron ser aplicados para el parámetro: {param.get('value')}"""
                        self.logger.log(err)
                        continue
                except Exception as e:
                    print(f"Error con el parámetro {param.get('value')}: {e}")
                    self.logger.log(f"Error con el parámetro {param.get('value')}: {e}")
                    err = str(f"Error con el parámetro {param.get('value')}: {e}")
                    continue  
            try:
                client_file.write(json.dumps(data, ensure_ascii=False, indent=4))
            except Exception as e:
                self.logger.log(f"Something went wrong at writing data file: {e}")

        end_time = time.time()

        exec_time = round((end_time - time_start), 2)
        status_code = 200 if scrapped_succesfully else 500
        user_agent = self.execute_sync_script("return navigator.userAgent;")
        success = scrapped_succesfully
        error_message = err

        history: ScrappingHistory = ScrappingHistory(
            status_code=status_code,
            execution_time=exec_time,
            user_agent=user_agent,
            success=success,
            error_message=error_message,
            filter_group_id=filter_group_id,
            user_id=self._user.get("id")
        )

        # Crear nueva campaña si no existe
        campaign: Campaign = Campaign.query.filter(Campaign.filter_group_id == filter_group_id).first()
        
        if campaign is None:

            last_campaign: Campaign = Campaign.query.order_by(desc(Campaign.id)).first()

            location_filter = next(
                (f for f in self._search_filters if f["type"] == FilterTypes.Location.value),
                None
            )

            if location_filter:
                location = get_coordinates_from_location(location_filter["value"])
                new_campaign = Campaign(
                    id = last_campaign.id + 1 if last_campaign else 1,
                    user_id = self._user.get("id"),
                    name = f"{self._search_params[0]}_{location_filter['value']}" ,
                    latitude = location["coordinates"]["lat"],
                    longitude = location["coordinates"]["lng"],
                    filter_group_id = filter_group_id
                )

                db.session.add(new_campaign)
        db.session.add(history)
        db.session.commit()

        return scrapped_succesfully


    def save_lead_data(self, search_results_container: WebElement, param_id: int, history_id: int, filter_group_id: int) -> List[object]:

        data = []

        try:                
            persons_in_page = search_results_container.find_elements(By.CSS_SELECTOR, f"[data-view-name='{PROFILE_DIV}']")

            for person in persons_in_page:
                            
                # ID PERFIL
                id = person.get_attribute("data-chameleon-result-urn")
                if id is not None:
                    id_obtained = id.split(":")[3]
                                    
                    id_in_database = SearchResult.query.filter(SearchResult.id==id_obtained).first()

                    if id_in_database is not None:
                        continue
                    if not is_numeric(id_obtained):
                        continue
                    id = id_obtained
                else:
                    self.logger.log(f"Error: no ID found in this profile")
                    continue

                # LINK PERFIL
                link = person.find_elements(By.CSS_SELECTOR, PROFILE_LINK)
                if is_element_available(link):
                    link = link[0].get_attribute("href")
                else:
                    link = "N/A"

                # FOTO DE PERFIL
                avatar = person.find_elements(By.CSS_SELECTOR, PROFILE_IMAGE)
                if is_element_available(avatar):
                    avatar = avatar[0].get_attribute("src")
                else:
                    avatar = "N/A"

                # NOMBRE DE USUARIO
                username = person.find_elements(By.CSS_SELECTOR, PROFILE_NAME)
                if is_element_available(username):
                    username = username[0].get_attribute("alt")
                    if username is None or username == "":
                        #username = result.find_element(By.CSS_SELECTOR, ".entity-result__universal-image > div > .app-aware-link").text
                        username = "Miembro de Linkedin"
                else:
                    username = "Miembro de Linkedin"

                if username.lower() == "miembro de linkedin":
                    continue
                            
                # ROL DEL PERFIL
                role = person.find_elements(By.CSS_SELECTOR, PROFILE_ROLE)
                if is_element_available(role):
                    role = role[0].text
                else:
                    role = "N/A"

                # LOCALIDAD
                location = person.find_elements(By.CSS_SELECTOR, LOCATION) #text
                if is_element_available(location):
                    location = location[0].text
                else:
                    location = "N/A"

                # CARGO QUE OCUPA
                job_position = person.find_elements(By.CSS_SELECTOR, JOB_POSITION) #text
                if is_element_available(job_position):
                    job_position = job_position[0].text
                else:
                    job_position = "N/A"

                # SERVICIOS | CONTACTOS
                services = person.find_elements(By.CSS_SELECTOR, SERVICES_CONTACTS)
                if is_element_available(services):
                    services = services[0].text
                else:
                    services = "N/A"

                # PAGINA DE SERVICIOS
                page = person.find_elements(By.CSS_SELECTOR, SERVICES_PAGE)
                if is_element_available(page):
                    page = page[0].get_attribute("href")
                else:
                    page = "N/A"



                data.append(
                    {
                        username: {
                            "ID": id,
                            "Profile link": link,
                            "Profile image": avatar,
                            "Role": role,
                            "Location": location,
                            "Job position": job_position,
                            "Services": services,
                            "Page": page,
                        },
                    },
                )

                search_results = SearchResult(
                                id=id,
                                name=username.split(" ")[0],
                                fullname=username,
                                profile_link=link,
                                profile_image_src=avatar,
                                role=role,
                                location=location,
                                job_position=job_position,
                                services=services,
                                page=page,
                                history_id=history_id,
                                param_id=param_id,
                                filter_group_id=filter_group_id,
                                user_id=self._user.get("id")
                )

                db.session.add(search_results)
                db.session.commit()
        
        except Exception as e:
            print(f"Something went wrong at {self.save_lead_data.__name__}: {e}")
            self.logger.log(f"Something went wrong at {self.save_lead_data.__name__}: {e}")
            return data

        return data

    def profile_deep_scrap(self, members_list: List[dict], already_in_profile: bool = False) -> ResponseValue: 
        """
            Used to get specifically information about the leads provided (Email, Phone, About Me)
        """
        data = []
        wait = self.wait(timeout=10)
        linkedin_members = get_linkedin_members([member.get("id") for member in members_list])
        if linkedin_members is None:
            return ResponseValue(ok=False, data=None) # ERROR
        
        for member in linkedin_members:
            member_phone = ""
            member_email = ""
            description = ""
            try:
                # Navegamos al perfil del miembro de linkedin
                if not already_in_profile:
                    self.navigate_to(member.profile_link)
                # Intentamos obtener su información de 'About Me'
                try:
                    description = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, DESCRIPTION)))[0].text
                except Exception as e:
                    self.logger.log(e)

                # Intentamos clickar en su Información de contacto
                contact_info_link = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, CONTACT_INFO_HREF)))
                if len(contact_info_link) <= 0:
                    return ResponseValue(ok=False, data=None) # ERROR
                contact_info_link[0].click()

                # Esperamos a que se muestre la ventana de información
                contact_info_window = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, INFO_CONTAINER_GENERAL)))
                if len(contact_info_window) <= 0:
                    return ResponseValue(ok=False, data=None) # ERROR
                
                # Obtenemos la lista de información
                try:
                    contact_info_list = self.get_elements(By.CSS_SELECTOR, INFO_CONTAINER)
                except Exception as e:
                    print(e)
                    self.logger.log(f"Something went wrong at: {self.profile_deep_scrap.__name__} -> {e}")
                # Recorremos la lista de información
                for info_container in contact_info_list:
                    container_description = info_container.find_element(By.CSS_SELECTOR, INFO_DESCRIPTION)
                    if "teléfono".lower() in container_description.text.lower(): 
                        phone_list = info_container.find_elements(By.CSS_SELECTOR, PHONE_CONTAINER) # li
                        for phone_span in phone_list:
                            member_phone = phone_span.find_element(By.CSS_SELECTOR, PHONE).text
                    if "email".lower() in container_description.text.lower():
                        member_email = info_container.find_element(By.CSS_SELECTOR, EMAIL).text                        
                if len(member_phone) > 0:
                    member.phone = member_phone
                if len(member_email) > 0:
                    member.email = member_email
                if description:
                    member.description = description

                data.append(
                    {
                        "id": member.id,
                        "fullname": member.fullname,
                        "img_src": member.profile_image_src,
                        "phone": member_phone if member_phone else "N/A" ,
                        "email": member_email if member_email else "N/A"
                    }
                )

                db.session.add(member)
                db.session.commit()
            
            except Exception as e:
                self.logger.log(f"Something went wrong with {member.fullname}: \n{e}")
            
            sleep(random.uniform(3, 5.3))
                
        if len(data) > 0:
            return ResponseValue(ok=True, data=data)
        return ResponseValue(ok=False, data=None)

    def connect_with(self, lead_objects: List[dict], message: str) -> ResponseValue:
        wait = self.wait(timeout=15)
        leads_status = []
        try: 
            for index, lead in enumerate(lead_objects):

                lead_status = {}
                valuable_lead: SearchResult = SearchResult.query.filter_by(id=lead.get('id')).first()                    
                if valuable_lead:
                    lead_status.update(
                        { 
                            'id': valuable_lead.id,
                            'fullname': valuable_lead.fullname if valuable_lead.fullname else valuable_lead.name 
                        }
                    ) 

                    if (valuable_lead.connection_request==False or valuable_lead.connection_request is None):
                        self.navigate_to(valuable_lead.profile_link)
                        clean_url = valuable_lead.profile_link[:valuable_lead.profile_link.index("?")] + "/"
                        is_in_url = wait.until(EC.url_to_be(clean_url), message="URL not found")
                        try: 
                            try:
                                profile_container: List[WebElement] = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, f"section[data-member-id='{valuable_lead.id}']")), message="El contenedor del perfil no se ha encontrado puesto que el ID de la base de datos no coincide con el del contenedor del perfil actual.")
                            except Exception as e:
                                print(e)
                                self.logger.log(e)
                                continue

                            
                            more_actions_buttons: List[WebElement] = profile_container[0].find_elements(By.XPATH, ".//button[contains(@aria-label, 'Más acciones')]")
                            if len(more_actions_buttons) == 0:
                                print("Más acciones no encontrado.")
                                self.logger.log("No se ha encontrado el botón 'Más acciones'.")
                                continue
                            for more_action in more_actions_buttons:
                                if more_action.is_displayed():
                                    more_action.click()
                                    connect_btns = profile_container[0].find_elements(By.XPATH, ".//div[contains(@aria-label, 'Invita')]")
                                    if len(connect_btns) == 0:
                                        connect_btns = profile_container[0].find_elements(By.XPATH, ".//button[contains(@aria-label, 'Invita')]")
                                        if len(connect_btns) == 0:
                                            self.logger.log(f"No se ha encontrado el botón de 'Conectar' dentro del perfil de {valuable_lead.fullname}")
                                            continue
                                
                            if connect_btns[0].is_displayed():
                                connect_btns[0].click()
                                if index < 12 and message != "":
                                    send_with_message_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, CONNECT_WITH_MESSAGE)), message="Connect with message button not found.")
                                    send_with_message_btn.click()

                                    textarea = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, CONNECT_MESSAGE_AREA_TEXT)), message="Textarea not found.")
                                    for letter in message:
                                        sleep(random.uniform(0.2, 0.9))
                                        textarea.send_keys(letter)
                                    send_invtitation_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, CONNECT_MESSAGE_AREA_SEND_BTN)), message="Send invitation button not found.")
                                    send_invtitation_btn.click()
                                    valuable_lead.connection_request = True
                                    db.session.commit()
                                    # Save message in history
                                    try:
                                        message_to_save: Message = Message()
                                        message_to_save.save(
                                            message=message,
                                            user=self._user,
                                            search_result_id=valuable_lead.id
                                        )
                                    except Exception as e:
                                        self.logger.log(f"Something went wrong at: {self.connect_with.__name__} saving the message in message history.")
                                else:
                                    send_without_message_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, CONNECT_WITHOUT_MESSAGE)), message="Connect without message button not found.")
                                    sleep(random.uniform(2, 3.5))
                                    send_without_message_btn.click()
                                    try:
                                        limit_reached = wait.until(
                                            EC.presence_of_element_located((By.ID, "ip-fuse-limit-alert__header")),
                                            message="Limit not reached yet."
                                        )
                                        if "has alcanzado el límite semanal de invitaciones" in limit_reached.text.lower():
                                            self.logger.log("Limit reached")
                                            return ResponseValue(ok=True, data=leads_status)
                                        else:
                                            print("Limit not reached")
                                            lead_status['status'] = "✔"
                                            lead_status['message'] = "[empty]"
                                            valuable_lead.connection_request = True
                                            db.session.commit()
                                    except TimeoutException:
                                        # No apareció el mensaje, así que no hay límite (o es otro tipo de fallo silencioso)
                                        print("Limit not reached (element not found)")
                                        lead_status['status'] = "✔"
                                        lead_status['message'] = "[empty]"
                                        valuable_lead.connection_request = True
                                        db.session.commit()
                                    except Exception as e:
                                        print("Unexpected error:", str(e))
                                        self.logger.log(f"Something went wrong at: {self.connect_with.__name__}: {e}")
                        except:
                            lead_status.update({ 'status': '✖' })
                            continue
                        leads_status.append(lead_status)
                    else:
                        lead_id = lead.get("id", None)
                        self.logger.log(f"Valuable lead not found ID: {lead_id}")
                
                # Tiempo de espera random para confundir al detector de bots
                sleep(random.uniform(2, 4.6))

            return ResponseValue(ok=True, data=leads_status)
        except Exception as e:
            self.logger.log(f"Something went wrong at {self.connect_with.__name__}: {e}")
            return ResponseValue(ok=False, data=None)

    def make_post(self, img_path: str, text: str):
        # (OPCIONAL NO NECESARIO URGENTEMENTE) OJO se puede hacer con la API de LinkedIn no es necesario automatización con Selnium
        pass

    def open_aside(self) -> WebElement | None:
        """
            This opens the aside message panel and returns it.
        """
        wait = self.wait(timeout=15)

        try:
            aside = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ASIDE)), message="Aside not found.")
            aside_first_div = aside.find_element(By.TAG_NAME, "div")
            aside_first_div_cls = aside_first_div.get_attribute("class")
            if ASIDE_MINIMIZED in aside_first_div_cls:
                aside_btns_container = aside.find_element(By.CSS_SELECTOR, ASIDE_USE_BTNS_CONTAINER)
                aside_btns = aside_btns_container.find_elements(By.TAG_NAME, "button")
                aside_btns[-1].click()
                sleep(2)
            return aside

        except Exception as e:
            self.logger.log(f"Something went wrong: {e}")
            return None

    def send_messages(self, leads: List[dict], subject_text: str, message: str) -> ResponseValue:
        wait = self.wait(timeout=15)
        wait_modal = self.wait(timeout=2)
        messages_status = []

        for lead in leads:

            try:
                message_containers = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, MESSAGE_CONTAINER)), message="No hay mensajes abiertos.")
                print("Hay contenedores de mensajes abiertos, es necesario cerrarlos.")
                for container in reversed(message_containers):
                    close_button = container.find_elements(By.CSS_SELECTOR, MESSAGE_HEADER_BUTTONS)
                    self.browser.execute_script("arguments[0].click();", close_button[len(close_button) - 1])
            except Exception as e:
                self.logger.log(e)
                print("No hay contenedores de mensajes abiertos, justo como debería ser.<")
                pass

            try:
                id = lead.get("id", None)
                name: str = lead.get("name", None)

                if (
                        id is None 
                        or message is None 
                        or name is None
                   ): 
                    continue
                
                message_directed = message.replace("{name}", name.capitalize())
                
                # Obtener profile_link
                member: SearchResult = SearchResult.query.filter_by(id=id).first()
                if member is None:
                    continue

                # En algún momento esto se tendrá que manejar de otra manera para que el usuario pueda enviar mas de un mensaje por LinkedIn
                if member.first_message_sended and member.second_message_sended:
                    continue
                
                # Por ahora solamente se pueden enviar mensajes a miembros valiosos
                if not member.is_valuable:
                    print(member.fullname)
                    continue
                
                self.navigate_to(member.profile_link)

                try:
                    send_message_button = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, SEND_MESSAGE_PROFILE)), message="Send message button is not available.")
                    if send_message_button[1].is_enabled():
                        send_message_button[1].click()
                        
                        # Manejar los que son InMail
                        try:
                            in_mail = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, INMAIL_BANNER)), message="Is not an InMail")
                            self.logger.log("This is an InMail.")
                            continue
                            # No estoy seguro de que hacer todavía con los InMails
                        except Exception as e:
                            self.logger.log(e)
                        
                        header = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, HEADER)), message="Header is not available.")
                        
                        if header:
                            subject = self.browser.find_elements(By.CSS_SELECTOR, SUBJECT)
                            if len(subject) > 0:
                                for letter in subject_text:
                                    sleep(random.uniform(0.1, 0.35))
                                    subject[0].send_keys(letter) 
                            
                            editable_divs = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, MESSAGE)), message="CONTENT EDITABLE NOT FOUND")
                            for content_editable_div_msg in editable_divs:
                                if content_editable_div_msg.is_displayed() and content_editable_div_msg.is_enabled():
                                    i = 0
                                    while i < len(message_directed):
                                        letter = message_directed[i]
                                        try:
                                            content_editable_div_msg.send_keys(letter)
                                            sleep(random.uniform(0.1, 0.35))
                                            i += 1  # solo avanzamos si se envió correctamente
                                        except StaleElementReferenceException:
                                            print("Elemento se volvió stale, reintentando búsqueda...")
                                            editable_divs = wait.until(
                                                EC.presence_of_all_elements_located((By.CSS_SELECTOR, MESSAGE)),
                                                message="CONTENT EDITABLE NOT FOUND"
                                            )
                                            for div in editable_divs:
                                                if div.is_displayed() and div.is_enabled():
                                                    content_editable_div_msg = div
                                                    break
                                    send_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, SEND_MESSAGE_BTN)), message="Send message button not found.")
                                    sleep(random.uniform(3, 5))
                                    send_btn.click()
                                    sleep(random.uniform(2, 3.5))

                                    # Close conversation
                                    # header_controls = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ALL_HEADER_BUTTON_CONTAINER)), message="Header controls not found")
                                    close_button = self.browser.find_elements(By.CSS_SELECTOR, MESSAGE_HEADER_BUTTONS)

                                    sleep(random.uniform(1, 2.5))
                                    self.browser.execute_script("arguments[0].click();", close_button[len(close_button) - 1])
                                    
                                    if not member.first_message_sended:
                                        member.first_message_sended = True
                                    else:
                                        member.second_message_sended = True

                                    db.session.commit()

                                    # Necesitamos guardar el mensaje en el histórico
                                    # Save message in history
                                    message_to_save: Message = Message()
                                    message_to_save.save(
                                        message=message_directed,
                                        user=self._user,
                                        search_result_id=id
                                    )

                                    messages_status.append(
                                        {
                                            'name': name,
                                            'status': '✔',
                                            'message': message_directed,
                                            'description': "SUCCESS"
                                        }
                                    )
                                    
                                else:
                                    print("content_editable_div_msg not interactable")
                                    self.logger.log("content_editable_div_msg not interactable")

                except Exception as e:
                    self.logger.log(f"Something went wrong at: { self.send_messages.__name__} -> {e}")
                    messages_status.append(
                        {
                            'name': name,
                            'status': '✖',
                            'mesage': message_directed,
                            'description': f"{e}"
                        }
                    )
                    continue
            except Exception as e:
                self.logger.log(f"Something went wrong at: { self.send_messages.__name__} -> {e}")
                messages_status.append(
                        {
                            'name': name,
                            'status': '✖',
                            'mesage': message_directed,
                            'description': f"{e}"
                        }
                )
                continue
            finally:
                
                # En caso de que salga el diálogo de confirmación debo cerrarlo
                try:
                    modal_btn = wait_modal.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ASIDE_MODAL_EXIT_WITHOUT_SAVE_BTN)))[-1]
                    modal_btn.click()
                except:
                    pass 
                continue
                
        return ResponseValue(ok=True, data=messages_status)
    

    def set_search_amount_by_param(self) -> int: # this assuming we have 10 possible contacts per search page:
        """
            Acording to the given amount of params this method returns the max search amount by param number.

            :return: math.floor(MAX_SEARCHES / (params_number * CONTACTS_PER_PAGE))
        """
        params_number = len(self._search_params)
        amount_by_param = MAX_SEARCHES / (params_number * CONCTACTS_PER_PAGE)
        return math.floor(amount_by_param)
    
    def check_accepted_connection_requests(self) -> ResponseValue: 
        
        wait = self.wait(timeout=15)
        persons = []

        # Navegamos al aparatado "Mi Red"
        try:
            network_btn: WebElement = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, MY_NETWORK)), message="Network button not founded.")
            sleep(random.uniform(0.5, 1.2))
            network_btn.click()
        except Exception as e:
            self.logger.log("Error on clicking network button.")
            self.logger.log(f"Something went wrong at {self.check_accepted_connection_requests.__name__}: {e}")
            return ResponseValue(ok=False, data=None)
        
        # Ir a All contacts
        try:
            all_contacts: List[WebElement] = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ALL_CONTACTS)), message="All contacts button not founded.")
            my_connections = all_contacts[0].get_attribute("href")
            if my_connections is None:
                self.logger.log("HREF no encontrado.")
                return ResponseValue(ok=False, data=None)  
            sleep(random.uniform(0.5, 1.2))
            self.navigate_to(my_connections)
        except Exception as e:
            self.logger.log("Error on clicking all_contacts button.")
            self.logger.log(f"Something went wrong at {self.check_accepted_connection_requests.__name__}: {e}")
            return ResponseValue(ok=False, data=None)

        # Bajamos lo máximo posible
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")), message="Body not available yet.")
        is_show_more_btn = True
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, SHOW_MORE_BUTTON)), message="Show more button not found.")
        except Exception as e:
            is_show_more_btn = False
        
        if is_show_more_btn:
            while len(self.browser.find_elements(By.CSS_SELECTOR, SHOW_MORE_BUTTON)) > 0:
                self.scroll_to_bottom()
                sleep(random.uniform(2, 3.5))
                self.scroll_to_top()


        # En caso de que cambien a fechas
        # input("Press ENTER ...")
        # profile_containers = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[data-view-name='connections-list']")), message="Profile containers are not available")
        # input("Press ENTER ...")
        # profile_info_containers = [
        #     profile_container.find_element(By.CSS_SELECTOR, "div:first-child") 
        #     for profile_container in profile_containers
        # ]

        # info_dict_list: List[dict] = [
        #     {
        #         "profile_link": profile_info_container.find_elements(By.TAG_NAME, "a")[0],
        #         "fullname": profile_info_container.find_elements(By.TAG_NAME, "p")[0],
        #         "role": profile_info_container.find_elements(By.TAG_NAME, "p")[1],
        #         "contact_date_str": profile_info_container.find_elements(By.TAG_NAME, "p")[2],
        #     }
        #     for profile_info_container in profile_info_containers
        # ]

        # print(json.dumps(info_dict_list, ensure_ascii=False, indent=3))
        # input("Press ENTER ....")

        # Obtenemos listado de nombres
        names_list_elements = self.browser.find_elements(By.CSS_SELECTOR, CONTACT_NAME)
        names_list = [name_element.text for name_element in names_list_elements]

        # Obtenemos los links a los perfiles
        try:
            profile_links_a_el: List[WebElement] = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, CONTACT_PROFILE_LINK)), message="Profile links are not available.")
            connection_time_elements: List[WebElement] = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "time")), message="Time tags not found.")
            
            connection_times = [element.text for element in connection_time_elements]
            connection_time_index = 0
            time_keywords = ["días", "día", "hora", "horas", "semana"]

            profile_links = [element.get_attribute("href") for element in profile_links_a_el]
            
            # Vamos de 2 en 2 porque hay 2 elementos de la misma clase de cada uno en el array
            for index in range(0,len(profile_links), 2):
                if any(keyword == connection_times[connection_time_index].lower()[connection_times[connection_time_index].rfind(" ") + 1:] for keyword in time_keywords) :
                    self.deep_scrapp_people(profile_links[index])
                    connection_time_index += 1
                else:
                    connection_time_index += 1
                    continue
        except Exception as e:
            print(e)
            self.logger.log(f"Something went wrong at: {self.check_accepted_connection_requests.__name__} -> {e}")

        for name in names_list:
            person: SearchResult = SearchResult.query.filter_by(fullname=name).first()

            if person is None:
                continue
            if person.connection_request_accepted:
                continue

            person.connection_request_accepted = True

            persons.append(
                        {
                            "fullname": person.fullname,
                            "profile_image_src": person.profile_image_src,
                            "profile_link": person.profile_link,
                        }
            )
            db.session.commit()
        
        return ResponseValue(ok=True, data=persons)

    def accept_incoming_connection_requests(self) -> ResponseValue:
        """
            Method to accept incoming connection requests from users
        """
        wait = self.wait(timeout=15)
        accepted_contacts = []
        profile_links: List[str] = []
        # Navegamos al aparatado "Mi Red"
        try:
            network_btn: WebElement = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, MY_NETWORK)), message="Network button not founded.")
            network_btn.click()
        except Exception as e:
            self.logger.log("Error on clicking network button.")
            self.logger.log(f"Something went wrong at {self.check_accepted_connection_requests.__name__}: {e}")
            return ResponseValue(ok=False, data=[])
        
        try:
            invitations_list: List[WebElement] = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, INVITATIONS_TO_ACCEPT_LIST)), message="You have no invitations pending to accept.")
            if invitations_list:
                for invitation in invitations_list:
                    a = invitation.find_elements(By.TAG_NAME, "a")
                    if not len(a) > 0:
                        continue
                    profile_links.append(a[0].get_attribute("href"))
                    accept_btn = invitation.find_elements(By.CSS_SELECTOR, ACCEPT_INVITATION_RECEIVED_BTN)
                    if len(accept_btn) > 0:
                        accept_btn[0].click()
                for link in profile_links:
                    id = self.deep_scrapp_people(link)
                    if id:
                        accepted_contacts.append(id)
            return ResponseValue(ok=True, data=accepted_contacts)
        except Exception as e:
            self.logger.log(f"Something went wrong at: {self.accept_incoming_connection_requests.__name__}: {e}")
            return ResponseValue(ok=False, data=[])

    def check_unread_messages(self) -> ResponseValue:
        # Pendiente
        # Paso 1 -> Ir a Mensajes
        notification_data = []
        wait = self.wait(timeout=15)
        self.go_to_mymessages()
        try:
            unread_messages_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, UNREAD_BUTTON)), message="Botón de mensajes 'No leídos' no encontrado.")
            unread_messages_button.click()
            sleep(random.uniform(2,3.5))
        except Exception as e:
            self.logger.log(f"Something went wrong at {self.check_unread_messages.__name__}: {e}")
            return ResponseValue(ok=False, data=[])
        
        try: 
            conversations_list = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, CONVERSATIONS_UL)), message="Lista de conversaciones no encontrada")
        except Exception as e:
            self.logger.log(f"Something went wrong at {self.check_unread_messages.__name__}: {e}")
            return ResponseValue(ok=True, data=[])

        try:
            data = []
            try:
                conversation_items = wait.until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR, CONVERSATIONS_LI)), message="No hay conversaciones pendientes.")
            except Exception as e:
                self.logger.log(f"No hay mensajes sin leer (1). {e}")
                return ResponseValue(ok=True, data=[])
            for item in conversation_items:
                item.click()
                person_name = wait.until(EC.presence_of_all_elements_located((By.ID, PERSON_NAME)), message="Person name not found")[0].text
                messages_li = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, MESSAGES)), message="No se han encontrado los elementos 'li' del apartado de mensajes")
                link: str = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, LINK_TO_PROFILE)), message="Link a perfil no encontrado").get_attribute("href")
                structure = {}
                structure["fullname"] = person_name
                structure["link"] = link
                structure["messages"] = []
                for li in messages_li:
                    message_text = li.find_elements(By.CSS_SELECTOR, MESSAGES_P)
                    if len(message_text) == 0:
                        self.logger.log("No hay mensajes sin leer (2).")
                        return ResponseValue(ok=True, data=[])
                    message: str = message_text[0].text.strip()
                    structure["messages"].append(message) 
                data.append(structure)
        except Exception as e:
            self.logger.log(f"Something went wrong at {self.check_unread_messages.__name__}: {e}")
            return ResponseValue(ok=False, data=[])

        if len(data) == 0:
            self.logger.log(f"Por alguna razón la longitud de data es 0: {self.check_unread_messages.__name__}")
            return ResponseValue(ok=True, data=[])
        
        for value in data:
            id = self.deep_scrapp_people(value["link"])
            if id is not None:
                search_result: SearchResult = SearchResult.query.get(id)
                if search_result:
                    search_result.responded_to_message = True
                    db.session.commit()
                for message_text_value in value["messages"]:
                    if message_text_value:
                        Message().save(
                            message=message_text_value,
                            user=self._user,
                            search_result_id=id,
                            from_search_result=True
                        )

            notification_data.append(
                    {
                        "fullname": value["fullname"] if value["fullname"] else "Desconocido",
                        "notifications": 1, # Falta lógica para obtener solamente la cantidad de nuevos mensajes
                        "last_message": value["messages"][-1] if len(value["messages"]) > 0 else "-notificación-",
                    }
            )
        
        if len(notification_data) == 0:
            return ResponseValue(ok=False, data=[])
        return ResponseValue(ok=True, data=notification_data)

        # Paso 2 -> Marcar "No leídos"
        # Paso 3 -> Recorrer los mensajes no leídos y hacer click sobre cada uno
        # Paso 4 -> Extraer mensaje intercambiado e ID del contacto con link a su perfil
        # Paso 5 -> Guardar mensaje en base de datos
        
        # aside = self.open_aside()
        
        # try:
        #     unread_messages = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ASIDE_UNREAD_MESSAGES_CONTAINER)), message="You have not unread messages.")
        # except Exception as e:  
        #     self.logger.log(e)             
        #     return ResponseValue(ok=True, data=[])
        
        # for message in unread_messages:
        #     try:
        #         message_sender = message.find_element(By.CSS_SELECTOR, ASIDE_UNREAD_MESSAGE_SENDER) # text
        #         notification_container = message.find_element(By.CSS_SELECTOR, ASIDE_NOTIFICATION_CONTAINER)
        #         notification_count = notification_container.find_element(By.CSS_SELECTOR, ASIDE_NOTIFICATION_COUNT) # text
        #         last_received_message = message.find_element(By.CSS_SELECTOR, ASIDE_LAST_SENDER_MESSAGE) # text
                
        #         # if last_received_message:
        #         #     new_message_received = Message(
        #         #         message="",
        #         #         user="",
        #         #         search_result_id=""
        #         #     )

        #         notification_data.append(
        #             {
        #                 "fullname": message_sender.text if message_sender else "Desconocido",
        #                 "notifications": int(notification_count.text) if notification_count else 0,
        #                 "last_message": last_received_message.text if last_received_message else "-notificación-",
        #             }
        #         )
        #     except Exception as e:
        #         self.logger.log(f"Something went wrong getting unread messages: {e}")
        #         continue

        # if len(notification_data) == 0:
        #     return ResponseValue(ok=False, data=[])
        # return ResponseValue(ok=True, data=notification_data)

    def too_many_requests_handler(self) -> WebElement | None:
        """
            :return: Returns 'next_page_btn' if available after waiting 60 seconds and refreshing the page
        """
        sleep(60)
        wait = self.wait(timeout=10)
        self.browser.refresh()
        try:
            next_page_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, NEXT_PAGE_BTN)), message="Next page button not found after refreshing page.")
        except Exception as e:
            self.logger.log(e)
            return None
        return next_page_btn


    def deep_scrapp_people(self, profile_link: str) -> int|None:
        wait = self.wait(timeout=20)
        fullname = "N/A"
        name="N/A"
        job_position = "N/A"
        role="N/A"
        location="N/A"
        try:
            sleep(random.uniform(0.5, 1.2))
            self.navigate_to(profile_link)
            id_element: WebElement = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, INVITATION_ID)), message="ID is not available")
            image_element: WebElement = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, INVITATION_PROFILE_IMAGE)), message="Image is not available")
            experience_is_showing = self.browser.find_elements(By.XPATH, "//span[text()='Experiencia']")
            if len(experience_is_showing) > 0:
                experience_container = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "section:has(> div#experience:first-child)")), message="Experience section is not available.")
                experience = experience_container.find_element(By.CSS_SELECTOR, INVITATION_JOB_POSITION)
                if experience:
                    spans = experience.find_elements(By.CSS_SELECTOR, ".visually-hidden")
                    if len(spans) >= 2:
                        job_position = spans[0].text + " " + spans[1].text
                    if len(spans) == 1:
                        job_position = spans[0].text
            role_and_desc_elements: List[WebElement] = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, INVITATION_ROLE_AND_DESCRIPTION)), message="Role is not available")
            if image_element:
                fullname: str = image_element.get_attribute("title") 
                name = fullname.split(" ")[0]
            
            location_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, INVITATION_LOCATION)), message="Location is not available")
            if location_element:
                location = location_element.text

            if not id_element:
                sleep(random.uniform(0.8, 1.5))
                self.go_to_mynetwork() 
                return None

            id = int(id_element.get_attribute("data-member-id"))
            image = image_element.get_attribute("src")
            if len(role_and_desc_elements) >= 1:
                role = role_and_desc_elements[0].text

            contact_in_db: SearchResult|None = SearchResult.query.filter_by(id=id).first()
            user_fgroup: FilterGroup = FilterGroup.query.filter_by(name=f"Personas-Filtro_no_utilizable_{self._user.get('id')}").first()
            
            sleep(random.uniform(1.5, 3.2))
            if not contact_in_db:
                new_contact = SearchResult(
                    id = id,
                    name = name,
                    fullname = fullname,
                    profile_link = profile_link,
                    profile_image_src = image,
                    role = role,
                    location = location,
                    job_position = job_position,
                    connection_request_accepted = True,
                    user_id = self._user.get("id"),
                    filter_group_id = user_fgroup.id
                )

                db.session.add(new_contact)
                db.session.commit()
                self.profile_deep_scrap([{ "id": id }], already_in_profile=True)
                return id
            else:
                contact_in_db.name = name
                contact_in_db.fullname = fullname
                contact_in_db.profile_link = profile_link
                contact_in_db.profile_image_src = image
                contact_in_db.role = role
                contact_in_db.location = location
                contact_in_db.job_position = job_position
                contact_in_db.connection_request_accepted = True
                db.session.commit()
                self.profile_deep_scrap([{ "id": id }], already_in_profile=True)
                return id
            
        except Exception as e:
            self.logger.log(f"Something went wrong at: {self.deep_scrapp_people.__name__}: {e}")
            return None

    def go_to_mynetwork(self):
        wait = self.wait(timeout=15)
        # Navegamos al aparatado "Mi Red"
        try:
            network_btn: WebElement = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, MY_NETWORK)), message="Network button not founded.")
            network_btn.click()
        except Exception as e:
            self.logger.log("Error on clicking network button.")
            self.logger.log(f"Something went wrong at {self.check_accepted_connection_requests.__name__}: {e}")

    def go_to_mymessages(self):
        wait = self.wait(timeout=15)
        # Navegamos al aparatado "Mensajes"
        try:
            network_btn: WebElement = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, MY_MESSAGES)), message="Network button not founded.")
            network_btn.click()
        except Exception as e:
            self.logger.log("Error on clicking network button.")
            self.logger.log(f"Something went wrong at {self.check_accepted_connection_requests.__name__}: {e}")
            