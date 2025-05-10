from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship
from sqlalchemy import JSON, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from sqlalchemy import func
from cryptography.fernet import Fernet
from dotenv import load_dotenv
from typing import List, Optional

import os

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '..', '.env'))

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
SECRET_KEY = os.getenv("LINKEDIN_CRYPTOGRAPHY_MASTER_KEY")
cipher = Fernet(SECRET_KEY.encode())
registered_models = {}

def auto_register(cls):
    registered_models[cls.__name__.lower()] = cls
    return cls

@auto_register
class CustomListDetails(db.Model):
    __tablename__ = "custom_list_details"

    list_name: Mapped[str] = mapped_column(ForeignKey("custom_members_list.name", ondelete="CASCADE"), primary_key=True, comment="Nombre de la lista personalizada")
    search_result_id: Mapped[int] = mapped_column(ForeignKey("search_result.id", ondelete="CASCADE"), primary_key=True, comment="ID del contacto en SearchResult")
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), comment="ID del usuario dueño de la lista")

@auto_register
class CustomMembersList(db.Model):
    __tablename__ = "custom_members_list"

    name: Mapped[str] = mapped_column(primary_key=True, comment="Nombre de la lista único por usuario")
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), primary_key=True, comment="ID del usuario dueño de la lista")

    # Relación con SearchResult (muchos a muchos)
    search_results: Mapped[List["SearchResult"]] = relationship(
        "SearchResult",
        secondary="custom_list_details",
        back_populates="custom_lists"
    )

    def to_dict(self):
        return {
            "name": self.name,
            "user_id": self.user_id,
            "members": [
                search_result.to_dict()
                for search_result in self.search_results
            ]
        }
    

@auto_register
class User(db.Model):
    # __tablename__ = "users"
    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
    username: Mapped[str] = mapped_column(unique=False, nullable=False)
    password: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(unique=True, nullable=False)
    phone_number: Mapped[str] = mapped_column(nullable=True)
    linkedin_username: Mapped[str] = mapped_column(nullable=True)
    linkedin_password: Mapped[str] = mapped_column(nullable=True)
    linkedin_profile_url: Mapped[str] = mapped_column(nullable=True)
    twitter_profile_url: Mapped[str] = mapped_column(nullable=True)
    wantsPushNotifications: Mapped[bool] = mapped_column(nullable=True, default=True)
    wantsEmailNotifications: Mapped[bool] = mapped_column(nullable=True, default=True)
    wantsSMSNotifications: Mapped[bool] = mapped_column(nullable=True, default=True)
    is_superuser: Mapped[bool] = mapped_column(nullable=False, default=False)
    cookies: Mapped[JSON] = mapped_column(JSON, nullable=True, default="", comment="User LinkedIn cookies.")
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now)

    search_results: Mapped[list['SearchResult']] = relationship("SearchResult", back_populates="user")
    scrapping_histories: Mapped[list['ScrappingHistory']] = relationship("ScrappingHistory", back_populates="user")
    filter_group: Mapped[list['FilterGroup']] = relationship("FilterGroup", back_populates="user")
    message_history: Mapped[list['MessageHistory']] = relationship("MessageHistory", back_populates="user")
    scheduled_tasks: Mapped[list['ScheduledTask']] = relationship("ScheduledTask", back_populates="user")
    tasks: Mapped[list['Task']] = relationship("Task", back_populates="user")
    otp: Mapped[list['OTP']] = relationship("OTP", back_populates="user")
    subscription: Mapped[list['Subscription']] = relationship("Subscription", back_populates="user")
    proxy: Mapped[list['Proxy']] = relationship("Proxy", back_populates="user")

    def to_dict(self, with_cookies: Optional[bool] = True):
        return {
            "id": self.id,
            "username": self.username,
            "linkedin_username": self.linkedin_username,
            "email": self.email,
            "linkedin_url": self.linkedin_profile_url,
            "twitter_url": self.twitter_profile_url,
            "wantsPushNotifications": self.wantsPushNotifications,
            "wantsEmailNotifications": self.wantsEmailNotifications,
            "wantsSMSNotifications": self.wantsSMSNotifications,
            "is_superuser": self.is_superuser,
            "cookies": self.cookies if with_cookies else "",
            "created_at": self.created_at,
        }
    
    def set_linkedin_password(self, password):
        encrypted_password = cipher.encrypt(password.encode())
        self.linkedin_password = encrypted_password.decode()

    def get_linkedin_password(self):
        if self.linkedin_password:
            try:
                decrypted_password = cipher.decrypt(self.linkedin_password.encode()).decode()
                return decrypted_password
            except Exception as e:
                print(e)
                return None
        return None


@auto_register
class SearchResult(db.Model):
    # __tablename__ = "search_result"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=True)
    fullname: Mapped[str] = mapped_column(nullable=True) 
    description: Mapped[str] = mapped_column(nullable=True, comment="Profile description found at the moment we deep_scrapp profiles.")
    profile_link: Mapped[str] = mapped_column(nullable=True)
    profile_image_src: Mapped[str] = mapped_column(nullable=True)
    role: Mapped[str] = mapped_column(nullable=True)
    location: Mapped[str] = mapped_column(nullable=True)
    job_position: Mapped[str] = mapped_column(nullable=True)
    services: Mapped[str] = mapped_column(nullable=True)
    page: Mapped[str] = mapped_column(nullable=True)
    email: Mapped[str] = mapped_column(nullable=True)
    phone: Mapped[str] = mapped_column(nullable=True)
    website: Mapped[str] = mapped_column(nullable=True)
    is_valuable: Mapped[bool] = mapped_column(nullable=True, default=False, comment="ChatGPT set this acording to the defined parameters.")
    connection_request: Mapped[bool] = mapped_column(nullable=True, default=False, comment="This is set to True if 'Connect' request sended to the member, else can be False.")
    connection_request_accepted: Mapped[bool] = mapped_column(nullable=True, default=None, comment="This is to True if member accepts your Linkedin request, and False if after 20 days de member doesn't reply your request.")
    first_message_sended: Mapped[bool] = mapped_column(nullable=True, default=False, comment="Set to True when first message sended to a contact.")
    second_message_sended: Mapped[bool] = mapped_column(nullable=True, default=False, comment="Set to True when second message sended to a contact.")
    responded_to_message: Mapped[bool] = mapped_column(nullable=True, default=False, comment="Set to True when the bot detects that the contact responded to one of our actions.")
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now)

    history_id: Mapped[int] = mapped_column(ForeignKey('scrapping_history.id'), nullable=True, comment="Foreign key to ScrappingHistory")
    history: Mapped['ScrappingHistory'] = relationship("ScrappingHistory",back_populates="search_results")

    param_id: Mapped[int] = mapped_column(ForeignKey('parameter.id'), nullable=True, comment="Foreign key to Parameter")
    param: Mapped['Parameter'] = relationship("Parameter", back_populates="search_results")

    user_id: Mapped[int] = mapped_column(ForeignKey('user.id', name="fk_user"), nullable=True, comment="Foreign key to user")
    user: Mapped['User'] = relationship("User", back_populates="search_results")

    filter_group_id: Mapped[int] = mapped_column(ForeignKey('filter_group.id', name="fk_fgroup"), nullable=True, comment="Foreign key to filter group")
    filter_group: Mapped['FilterGroup'] = relationship("FilterGroup", back_populates="search_results")
    message_history: Mapped['MessageHistory'] = relationship("MessageHistory", back_populates="search_result")

    # Relación con CustomMembersList (muchos a muchos)
    custom_lists: Mapped[List["CustomMembersList"]] = relationship(
        "CustomMembersList",
        secondary="custom_list_details",
        back_populates="search_results"
    )

    def to_dict(self):
        return {   
                'id': self.id,
                'name': self.name,
                'fullname': self.fullname,
                'profile_link': self.profile_link,
                'profile_image_src': self.profile_image_src,
                'role': self.role,
                'location': self.location,
                'job_position': self.job_position,
                'services': self.services,
                'phone': self.phone,
                'email': self.email,
                'page': self.page,
                'is_valuable': self.is_valuable,
                'connection_request': self.connection_request,
                'connection_request_accepted': self.connection_request_accepted,
                'first_message_sended': self.first_message_sended,
                'second_message_sended': self.second_message_sended,
                'responded_to_message': self.responded_to_message,
                'created_at': self.created_at,
                'filter_group': self.filter_group.to_dict(),    
                'filter_group_location': self.filter_group.get_location()            
        }
    
    def get_messages(self):
        message_history: MessageHistory = MessageHistory.query.filter(MessageHistory.search_result_id == self.id).first()
        if not message_history: 
            return {
                "messages": []
            }
        
        messages: List[Message] = Message.query.filter(Message.message_history_id == message_history.id).all()
        serialized_messages = [message.to_dict() for message in messages]
        return {
            "messages": serialized_messages
        }


@auto_register
class MessageHistory(db.Model):

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
    message: Mapped['Message'] = relationship("Message", back_populates="message_history")
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id', name="fk_user"), nullable=True, comment="Foreign key to user")
    created_at: Mapped[datetime] = mapped_column(nullable=True, default=datetime.now)
    user: Mapped['User'] = relationship("User", back_populates="message_history")
    search_result_id: Mapped[int] = mapped_column(ForeignKey('search_result.id', name="fk_search_result"), nullable=True, comment="Foreign key to search result (contact)")
    search_result: Mapped['SearchResult'] = relationship("SearchResult", back_populates="message_history")


@auto_register
class Message(db.Model): 
    # En principio esto solo se utilizará para guardar los mensajes que se reciben.
    # Se plantea a futuro que se guarden también los mensajes enviados por el usuario.
    # Tener en cuenta que esto es más complicado debido a que el usuario lo puede hacer manualmente desde LinkedIn. 

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
    message: Mapped[str] = mapped_column(nullable=True, default="", comment="Message received from the user.")
    from_search_result: Mapped[bool] = mapped_column(nullable=True, default=False, comment="Mark as True if message comes from the search_resul person. False if the user is who sended the message.")
    user_notified: Mapped[bool] = mapped_column(nullable=False, default=False, comment="If the account owner (User) have been notified about this message")
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now)
    message_history_id: Mapped[int] = mapped_column(ForeignKey('message_history.id', name="fk_message_history"), nullable=True, comment="Foreign key to message history.")
    message_history: Mapped['MessageHistory'] = relationship("MessageHistory", back_populates="message")

    def to_dict(self):
        return {
            "message": self.message,
            "user_notified": self.user_notified,
            "created_at": self.created_at,
            "user": {
                "id": self.message_history.search_result.id,
                "fullname": self.message_history.search_result.fullname,
                "email": self.message_history.search_result.email,
                "created_at": self.message_history.search_result.created_at
            }
        }

    def save(self, message: str, user: dict, search_result_id: int, from_search_result: Optional[bool] = False):
        try:
            user_id = user.get("id")
            if not user_id:
                raise ValueError("The user has no valid ID.")

            message_history = MessageHistory.query.filter_by(user_id=user_id).first()

            if not message_history:
                message_history = MessageHistory(
                    user_id=user_id,
                    search_result_id=search_result_id
                )
                db.session.add(message_history)
                db.session.commit()  # Commit inmediato para evitar problemas de concurrencia

            message_in_db = Message.query.join(MessageHistory).filter(
                Message.message == message,
                MessageHistory.user_id == user_id
            ).first()

            if message_in_db is None:
                new_message = Message(
                    user_notified=True,
                    message_history_id=message_history.id,
                    message=message,
                    from_search_result=from_search_result
                )
                db.session.add(new_message)
                db.session.commit()
            else:
                print("Message not saved because it was in db.")
        except IntegrityError as e:
            db.session.rollback()
            print(f"Something went wrong saving the message: {e}")
        except Exception as e:
            db.session.rollback()
            print(f"Unexpected error: {e}")


@auto_register
class ScrappingHistory(db.Model):

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
    url: Mapped[str] = mapped_column(nullable=False, comment="URL scraped", default="www.linkedin.com")
    status_code: Mapped[int] = mapped_column(nullable=False, comment="HTTP status code of the scraping")
    timestamp: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now, comment="Timestamp of the scraping event")
    execution_time: Mapped[float] = mapped_column(nullable=True, comment="Execution time in seconds")
    user_agent: Mapped[str] = mapped_column(nullable=True, comment="User agent used for scraping")
    success: Mapped[bool] = mapped_column(nullable=False, comment="Indicates if the scraping was successful")
    error_message: Mapped[str] = mapped_column(nullable=True, comment="Error message if the scraping failed")

    # Foreign keys
    filter_group_id: Mapped[int] = mapped_column(ForeignKey('filter_group.id'), nullable=True, comment="Foreign key to FilterGroup")
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id', name="fk_user"), nullable=True, comment="Foreign key to user")
    
    # Relationships
    filter_group: Mapped['FilterGroup'] = relationship("FilterGroup", back_populates="scrapping_histories")
    search_results: Mapped[list['SearchResult']] = relationship("SearchResult", back_populates="history")
    user: Mapped['User'] = relationship("User", back_populates="scrapping_histories")


    def to_dict(self):
        return {
            'id': self.id,
            'url': self.url,
            'status_code': self.status_code,
            'timestamp': self.timestamp,
            'execution_time': self.execution_time,
            'user_agent': self.user_agent,
            'success': self.success,
            'error_message': self.error_message,
            'filter': self.filter_group_id,
        }

@auto_register
class FilterGroup(db.Model):

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False, unique=True, comment="The filters group name must be unique")
    filters: Mapped[List[dict]] = mapped_column(JSON, nullable=False, comment="Filters in JSON format")
    created_at: Mapped[datetime] = mapped_column(nullable=True, default=datetime.now)

    # Reverse relationships
    scrapping_histories: Mapped[list['ScrappingHistory']] = relationship("ScrappingHistory", back_populates="filter_group")
    search_results: Mapped[list['SearchResult']] = relationship("SearchResult", back_populates="filter_group")
    campaign: Mapped['Campaign'] = relationship("Campaign", back_populates="filter_group")
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id', name="fk_user"), nullable=True, comment="Foreign key to user")
    user: Mapped['User'] = relationship("User", back_populates="filter_group")

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'filters': self.filters
        }

    def get_location(self):
        location = "Otros"
        for filter in self.filters:
            if filter.get("type", ) == "LocationFilter":
                location = filter.get("value", "Otros")
                break
        return location


@auto_register
class Parameter(db.Model):

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False, comment="Parameter key")
    value: Mapped[str] = mapped_column(nullable=False, comment="Parameter value")
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now)

    search_results: Mapped[list['SearchResult']] = relationship("SearchResult", back_populates="param")


@auto_register
class ScheduledTask(db.Model):
    
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), comment="ID del usuario que programó la tarea", primary_key=True)
    label_name: Mapped[str] = mapped_column(nullable=False, comment="Nombre de la tarea dado por el usuario", primary_key=True)
    
    task_name: Mapped[str] = mapped_column(nullable=False, comment="Nombre de la tarea en celery")
    day_of_week: Mapped[str] = mapped_column(nullable=True, comment="Día de la semana en formato Celery (0-6)")
    hour: Mapped[int] = mapped_column(nullable=False, comment="Hora de ejecución (0-23)")
    minute: Mapped[int] = mapped_column(nullable=False, comment="Minuto de ejecución (0-59)")
    is_repeated: Mapped[bool] = mapped_column(default=True, comment="Indica si la tarea es repetitiva")
    is_executed: Mapped[bool] = mapped_column(default=False, comment="Indica si la tarea es 'is_repeated=False' ya se ha ejecutado")
    task_params: Mapped[List[dict]] = mapped_column(JSON, default=[], nullable=True, comment="A list of the task params")
    activation_date: Mapped[datetime] = mapped_column(nullable=True, comment="Fecha de activación de tareas no repetitivas")
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now, comment="Fecha de creación")

    user: Mapped['User'] = relationship("User", back_populates="scheduled_tasks")

    def to_dict(self):
        return {
            "task_name": self.task_name,
            "label_name": self.label_name,
            "user": self.user.to_dict(), 
            "day_of_week": self.day_of_week,
            "hour": self.hour,
            "minute": self.minute,
            "is_active": True if (self.is_repeated == False and self.is_executed == False) or (self.is_repeated == True) else False, 
            "is_repeated": self.is_repeated,
            "task_params": self.task_params,
            "created_at": self.created_at,
            "activation_date": self.activation_date
        }

@auto_register
class Task(db.Model):

    id: Mapped[str] = mapped_column(primary_key=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), comment="ID del usuario que creó la tarea", primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False, comment="Nombre de la tarea")
    state: Mapped[str] = mapped_column(nullable=False, comment="Task state")
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now)

    user: Mapped['User'] = relationship("User", back_populates="tasks")


    def to_dict(self): 
        return {
            "id": self.id,
            "user": self.user.to_dict(with_cookies=False),
            "name": self.name,
            "state": self.state,
            "created_at": self.created_at,
        }

class OTP(db.Model):

    id: Mapped[int] = mapped_column(primary_key=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), comment="ID del usuario que programó la tarea", primary_key=True)
    code: Mapped[str] = mapped_column(nullable=False, comment="OTP recibido por el usuario en su email.")
    inactive: Mapped[bool] = mapped_column(default=False, comment="Una vez el usuario utiliza el código se coloca como inactivo.")
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now)

    user: Mapped['User'] = relationship("User", back_populates="otp")

@auto_register
class Subscription(db.Model):

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
    endpoint: Mapped[str] = mapped_column(unique=True, nullable=False)
    p256dh: Mapped[str] = mapped_column(nullable=False)
    auth: Mapped[str] = mapped_column(nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id', name="fk_user", ondelete="CASCADE"), nullable=False, comment="Foreign key to user")
    user: Mapped['User'] = relationship("User", back_populates="subscription")


    def to_dict(self):
        return {
            "id": self.id,
            "endpoint": self.endpoint,
            "p256dh": self.p256dh,
            "auth": self.auth,
            "user_id": {
                "username": self.user.username,
                "email": self.user.email
            },
        }


class Proxy(db.Model):

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
    ip_addr: Mapped[str] = mapped_column(nullable=False, comment="Proxy IP")
    port: Mapped[str] = mapped_column(nullable=False, default="8080", comment="Puerto del proxy")
    inactive: Mapped[bool] = mapped_column(nullable=False, default=False, comment="¿Está activo el proxy?")
    spended_mb: Mapped[float] = mapped_column(nullable=False, comment="Cantidad de MB gastados en el ancho de banda")
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id', name="fk_user", ondelete="CASCADE"), nullable=False, comment="Clave foránea")
    user: Mapped['User'] = relationship("User", back_populates="proxy")


@auto_register
class Campaign(db.Model):

    id: Mapped[int] = mapped_column(primary_key=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), comment="ID del usuario que programó la tarea", primary_key=True)

    name: Mapped[str] = mapped_column(nullable=False, comment="Nombre de identificación de la campaña")
    latitude: Mapped[float] = mapped_column(nullable=False, comment="Latitud de la localización de la campaña.")
    longitude: Mapped[float] = mapped_column(nullable=False, comment="Longitud de la localización de la campaña.")
    status: Mapped[str] = mapped_column(nullable=False, default="Pausada", comment="Estado de la campaña")
    last_run: Mapped[datetime] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now)
    
    # Filter group
    filter_group_id: Mapped[int] = mapped_column(ForeignKey('filter_group.id', name="fk_fgroup"), nullable=True, comment="Clave foránea a filter group")
    filter_group: Mapped['FilterGroup'] = relationship("FilterGroup", back_populates="campaign")
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "search_param": self.filter_group.search_results[0].param.value if len(self.filter_group.search_results) > 0 else "",
            "status": self.status,
            "last_run": self.last_run,
            "results": len(self.filter_group.search_results),
            "location": {
                "name": self.filter_group.get_location(),
                "coordinates":{
                    "lat": self.latitude,
                    "lng": self.longitude
                }
            },
            "filter_group": self.filter_group.to_dict(),
            "user_id": self.user_id
        }