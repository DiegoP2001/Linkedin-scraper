from classes.linkedin import LinkedinScrapper, ResponseValue
from classes.logger import Logger
from dotenv import load_dotenv
from typing import List, Optional
from time import sleep
from openai import OpenAI
from models.models import *
from config.config import Config
import json
import psutil
import os

if Config.ENVIRONMENT != "dev":
    load_dotenv('/home//linkedin/.env')

class LinkedinManager:    
    """
        This class is like a menu to handle all posible LinkedinScrapper functionalities.
    """

    def __init__(self, linkedin_config: dict) -> None:
        self.scrapper = LinkedinScrapper(
                            search_params=linkedin_config.get("search_params", [""]),
                            search_filters=linkedin_config.get("search_filters", [{}]),
                            username=linkedin_config.get("username", os.getenv("LINKEDIN_USERNAME")),
                            password=linkedin_config.get("password", os.getenv("LINKEDIN_PASSWORD")),
                            user=linkedin_config.get("user"),
                            _profile_name=linkedin_config.get("profile_name", os.getenv("PROFILE_NAME")),
                            _path_to_profile=linkedin_config.get("path_to_profile", "/tmp/chrome-selenium-profile" if Config.ENVIRONMENT != "dev" else r"C:\Users\USER\AppData\Local\Google\Chrome\User Data\Profile 13")
        )

    def reset_scrapper(self, linkedin_scrapper: LinkedinScrapper):
        if self.check_chrome_is_working(): 
            self.close_chrome()
            self.scrapper = None
            self.scrapper = linkedin_scrapper

    def close_chrome(self):
        try:
            self.scrapper.quit()
        except Exception as e:
            print(f"Something went wrong at {self.close_chrome.__name__}: {e}")
    
    def check_chrome_is_working(self) -> bool:
        for process in psutil.process_iter(['pid', 'name']):
            if process.info['name'] == 'chrome' or process.info['name'] == 'chrome.exe':
                return True
        return False

    def setup_enviroment(self):

        try:
            self.scrapper.navigate_to(self.scrapper._url)
            if self.scrapper.is_login_required():
                self.scrapper.login()
        except Exception as e:
            self.scrapper.logger.log(f"Something went wrong: {e}. \n{self.setup_enviroment.__name__}")
            print(f"Something went wrong: {e}. \n{self.setup_enviroment.__name__}")

    def set_linkedin_cookies(self):
        """
        The user must log in to his Linkedin user account and copy all the cookies
        """
        sleep(2)
        cookies = self.scrapper._user.get("cookies", "No hay cookies")

        for cookie in cookies:            
            if 'name' in cookie and 'value' in cookie:
                cookie.pop('sameSite', None)  # Ignora la clave sameSite si está presente
                self.scrapper.browser.add_cookie(cookie)
            
        self.scrapper.browser.refresh()

    def scrap_general_data(self, filters: List[dict], params: List[dict], filter_group_id: int, pages_to_search: int) -> bool: 
        try: 
            self.scrapper._search_filters = filters
            self.scrapper._search_params = params
            
            self.setup_enviroment()

            scrapped_succesfully = self.scrapper.scrap_search_result_data(pages=pages_to_search, filter_group_id=filter_group_id)
            return scrapped_succesfully
        except Exception as e:
            import traceback
            self.scrapper.logger.log(f"Error: {e}")
            self.scrapper.logger.log(traceback.format_exc())
            self.scrapper.logger.log(f"Something went wrong: {e}. \n{self.scrap_general_data.__name__}")
            print(f"Something went wrong: {e}. \n{self.scrap_general_data.__name__}")
            return False
        finally:
            self.close_chrome()

    def deep_scrapp_members_data(self, members_list: List[dict]) -> ResponseValue:
        """
            This is a deep scrapp of the given members.
        """
        try:
            self.setup_enviroment()
            response: ResponseValue = self.scrapper.profile_deep_scrap(members_list)
            return response
        except Exception as e:
            self.scrapper.logger.log(f"Something went wrong: {e}. \n{self.deep_scrapp_members_data.__name__}, \nBrowser is working: {self.check_chrome_is_working}")
            print(f"Something went wrong: {e}. \n{self.deep_scrapp_members_data.__name__}")
            return ResponseValue(ok=False, data=None)
        finally:
            self.close_chrome()
        
    def connect_with_valuable_members(self, members: List[dict], message: str) -> ResponseValue:
        """
              connection request to valuable members for our organization.

            :param members: List of members [ { 'id': xxxxx, 'message': 'Hola <nombre> es un placer conectar contigo.' } ]
        """
        try:
            self.setup_enviroment()
            response = self.scrapper.connect_with(members, message)
            return response
        except Exception as e:
            self.scrapper.logger.log(f"Something went wrong: {e}. \n{self.connect_with_valuable_members.__name__}, \nBrowser is working: {self.check_chrome_is_working}")
            print(f"Something went wrong: {e}. \n{self.connect_with_valuable_members.__name__}")
            return ResponseValue(ok=False, data=None)
        finally:
            self.close_chrome()

    def send_messages(self, members: List[dict], subject, message) -> ResponseValue:
        """
            Description
        """
        try:
            self.setup_enviroment()
            response = self.scrapper.send_messages(members, subject, message)
            return response
        except Exception as e:
            self.scrapper.logger.log(f"Something went wrong: {e}. \n{self.send_messages.__name__}, \nBrowser is working: {self.check_chrome_is_working}")
            print(f"Something went wrong: {e}. \n{self.send_messages.__name__}")
            return ResponseValue(ok=False, data=None)
        finally:
            self.close_chrome()
    
    def check_unread_messages(self):
        try:
            self.setup_enviroment()
            response = self.scrapper.check_unread_messages()
            return response
        except Exception as e:
            self.scrapper.logger.log(f"Something went wrong: {e}. \n{self.check_unread_messages.__name__}, \nBrowser is working: {self.check_chrome_is_working}")
            print(f"Something went wrong: {e}. \n{self.check_unread_messages.__name__}")
            return ResponseValue(ok=False, data=[])
        finally:
            self.close_chrome()
        
    def check_invitations(self):
        try:
            self.setup_enviroment()
            response = self.scrapper.check_accepted_connection_requests()
            return response
        except Exception as e:
            self.scrapper.logger.log(f"Something went wrong: {e}. \n{self.check_invitations.__name__}, \nBrowser is working: {self.check_chrome_is_working}")
            print(f"Something went wrong: {e}. \n{self.check_invitations.__name__}")
            return ResponseValue(ok=False, data=[])
        finally:
            self.close_chrome()

    def accept_incoming_invitations(self):
        try:
            self.setup_enviroment()
            response = self.scrapper.accept_incoming_connection_requests()
            return response
        except Exception as e:
            self.scrapper.logger.log(f"Something went wrong: {e}. \n{self.accept_incoming_invitations.__name__}, \nBrowser is working: {self.check_chrome_is_working}")
            print(f"Something went wrong: {e}. \n{self.accept_incoming_invitations.__name__}")
            return ResponseValue(ok=False, data=[])
        finally:
            self.close_chrome()

    # Extract this method outside this class, it does not belong here
    def process_data_with_GPT(self, data: list, parameter: str, extra_context: Optional[str] = None):
        
        openai_client = OpenAI(api_key=os.getenv("CHAT_GPT_API_KEY"))
        members_to_return = {
                    "contacts": []
                }
        
        raw_data = data

        ia_role = f"""
                    Eres un profesional de la iluminación y tu función es desarrollar negocio (business development), e
                    sto es realizar ventas para la empresa EKIONA Iluminación solar también conocida como EKIONA Solar Lighting. 
                    En la empresa en la que trabajo diseñamos, fabricamos y comercializamos farolas solares de desarrollo tecnológico propio,
                    de alta calidad y con las que proporcionamos soluciones customizadas y adaptadas a las necesidades específicas de cada 
                    cliente.

                    En este caso, dentro de la búsqueda de "{ parameter }", Quiero identificar personas que tengan:
                    
                    •	Poder de decisión en la compra de farolas solares
                    •	Poder de influencia en la compra de farolas solares
                    •	Poder de decisión en la prescripción de farolas solares
                    •	Poder de influencia en la prescripción de farolas solares

                    Estas personas pueden tener puestos como { extra_context if extra_context is not None else "los que tu piensas que serían posibles compradores o contactos valiosos para el desarrollo comercial de EKIONA" }.
                    Es importante que las personas que elijas tengan estos puestos como actual, si lo tiene en anterior, exclúyelos.
                    Tu labor es excluir los perfiles de la lista que según estas indicaciones claramente no tienen poder ni interés en 
                    farolas solares y devolver todos los perfiles que si pueden tener un potencial según los criterios indicados anteriormente.
                    Si el idioma del rol de la persona está en otro idioma, traduce el 'message' del JSON al idioma correspondiente.
                    Devuelve un JSON con el siguiente formato: {{ 'contacts' : [ {{ id: <id>, 'message': <Hola NOMBRE . Soy Fernando de EKIONA. He visto que eres (puesto (formateado de manera natural)) en (Empresa (Solo el nombre de la empresa)). Me gustaría conectar y compartir nuestros proyectos y conocimiento en iluminación solar. Saludos> }} ] }}.
                    Es muy importante que no me devuelvas ninguna persona repetida en la lista. 
        """

        data_length: int = len(raw_data)
        step: int = 20 if data_length >= 20 else data_length

        for chunk in range(0, data_length, step):
            data_to_proccess = json.dumps(raw_data[chunk: chunk+step], ensure_ascii=False, indent=2).encode("utf8")

            try:
                completion = openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                                        {
                                            "role": "system", 
                                            "content": ia_role
                                        },
                                        {
                                            "role": "user",
                                            "content": f"\n{data_to_proccess}"
                                        }
                    ],
                    response_format={ "type": 'json_object' },
                    temperature=0.3,
                    max_tokens=5000,
                    top_p=1,
                    frequency_penalty=0,
                    presence_penalty=0
                )

                gpt_response = completion.choices[0].message.content

                try:
                    json_response = json.loads(gpt_response)
                except json.JSONDecodeError as e:
                    print(f"JSON mal formado antes de enviarlo a GPT: {e}")
                    print(data_to_proccess.decode("utf-8"))  # Muestra el JSON problemático
                    return ResponseValue(ok=False, data=None)


                valuable_members_ids = [vm["id"] for vm in json_response["contacts"]]
                SearchResult.query.filter(SearchResult.id.in_(valuable_members_ids)).update({"is_valuable": True}, synchronize_session="fetch")
                db.session.commit()

                for valuableMember in json_response['contacts']:
                    member: SearchResult = SearchResult.query.filter_by(id=valuableMember.get("id")).first()
                    if member is not None:
                        valuableMember["fullname"] = member.fullname
                        valuableMember["profile_image_src"] = member.profile_image_src
                        valuableMember["profile_link"] = member.profile_link
                        valuableMember["role"] = member.role
                        members_to_return["contacts"].append(valuableMember)
                        
                sleep(3)

            except Exception as e:
                print(f"Something went wrong processing the data: {e}")
                openai_client.close()
                return ResponseValue(ok=False, data=members_to_return if len(members_to_return) > 0 else None)
                

        openai_client.close()
        return ResponseValue(ok=True, data=members_to_return)
        
    
