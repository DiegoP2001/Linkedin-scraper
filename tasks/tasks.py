from celery import shared_task
from dotenv import load_dotenv
from classes.linkedin import ResponseValue
from manager import LinkedinManager
from config.config import Config
from classes.email.sender import Sender
from models.models import SearchResult
from typing import List
from classes.constants.email_templates import CONNECTIONS_ACCEPTED_BY_FERNANDO
from routes.decorators.api_decorators import register_task

if Config.ENVIRONMENT != "dev":
    load_dotenv('/home/ekiona/linkedin/.env')

def setup_manager(user: dict):
   return LinkedinManager(linkedin_config={
       "user": user
   })

@shared_task(ignore_result=True, queue="linkedin_queue", bind=True)
@register_task
def test(self, user: dict):
    setup_manager({"user": user})


@shared_task(ignore_result=False, queue="linkedin_queue", bind=True)
@register_task
def scrapp_linkedin_data(self, user: dict, filters: List[dict], parameters: List[dict], filter_group_id: int, pages: int = 100) -> bool:
    manager: LinkedinManager = setup_manager(user)
    scrapped_successfully = manager.scrap_general_data(filters, parameters, filter_group_id=filter_group_id, pages_to_search=pages)
    return {
        "ok": scrapped_successfully,
        "data": []
    }


@shared_task(ignore_result=False, queue="linkedin_queue", bind=True)
@register_task
def deep_scrapp(self, user: dict, members_list: List[dict]):
    manager: LinkedinManager = setup_manager(user)
    response: ResponseValue = manager.deep_scrapp_members_data(members_list)
    if response.ok:
        return {
            "ok": response.ok,
            "data": response.data
        }
    return {
        "ok": response.ok,
        "data": []
    }

@shared_task(igore_result=False, queue="linkedin_queue", bind=True)
@register_task
def connect_with_members(self, user: dict, members_list, message):
    manager: LinkedinManager = setup_manager(user)
    total_members = len(members_list)

    self.update_state(state="STARTED", meta={"processed": 0, "total": total_members})
    response: ResponseValue = manager.connect_with_valuable_members(members_list, message)

    self.update_state(state="SUCCESS", meta={"processed": total_members, "total": total_members})

    if response.ok:
        return {
            "ok": response.ok,
            "data": response.data
        }
    return {
        "ok": response.ok,
        "data": []
    }

@shared_task(igore_result=False, queue="linkedin_queue", bind=True)
@register_task
def send_message_to(self, user: dict, members_list, subject, message):
    manager: LinkedinManager = setup_manager(user)
    response: ResponseValue = manager.send_messages(members_list, subject, message)
    if response.ok:
        return {
            "ok": response.ok,
            "data": response.data
        }
    return {
        "ok": response.ok,
        "data": []
    }


@shared_task(ignore_result=False, queue="linkedin_queue", bind=True)
@register_task
def process_data_with_GPT(self, user: dict, members_list, parameter: str, extra_context: str):
    manager: LinkedinManager = setup_manager(user)
    response: ResponseValue = manager.process_data_with_GPT(members_list, parameter, extra_context)
    if response.ok:
        return {
            "ok": response.ok,
            "data": response.data
        }
    return {
        "ok": response.ok,
        "data": []
    }


@shared_task(ignore_result=False, queue="linkedin_queue", bind=True)
@register_task
def check_accepted_invitations(self, user: dict):
    manager: LinkedinManager = setup_manager(user)
    response: ResponseValue = manager.check_invitations()
    notifier = Sender()
    if response.ok:
        if len(response.data) > 0:
            email_header = """
                <div>
                    <h1 style="font-size: 2rem; font-weight: 800; text-align: center;">Solicitudes de contacto aceptadas</h1>
                    <div style="font-size: 1.2rem; display: flex; justify-content: center;">
                        <ul style="display: flex; flex-direction: column; justify-content: center; align-items: flex-start; gap: 10px;">
                    \n
            """

            email_items = "\n".join(
                    f"""
                        <li style="list-style: none;">
                            <div style="display: flex; justify-content: center; align-items: center; gap: 10px;">
                                <a href="{person.get('profile_link', '#')}" target="_blank">
                                <img style="max-width: 80px; max-height: 80px; border-radius: 50%;" 
                                    src="{person.get('profile_image_src', '#')}" 
                                    alt="Foto de {person.get('fullname', 'Usuario')}">
                                </a>
                                <p class="profile-name">
                                    <strong>{person.get('fullname', 'Usuario')}</strong> ha aceptado tu invitación.
                                </p>
                            </div>
                        </li>
                    """
                for person in response.data
            )

            email_footer = """
                \n
                        </ul>
                    </div>
                </div>
            """

            email = "".join([email_header, email_items, email_footer])
        else:
            email = "<h1 style='text-align: center;'>No hay solicitudes aceptadas.</h1>"
            
        notifier.send_email_v2_gmail_api(
                    user_email="info@ekiona.com",
                    recipients_email=[user],
                    subject="Solicitudes de conexión aceptadas",
                    message_body=email
        )
        return {
            "ok": response.ok,
            "data": response.data
        }
    return {
        "ok": response.ok,
        "data": []
    }

@shared_task(ignore_result=False, queue="linkedin_queue", bind=True)
@register_task
def massive_mailing(self, user: dict, members_list: List[dict], subject: str, message: str):
    sender = Sender()

    
    try:
        sender.send_email_v2_gmail_api(
            user_email=user.get("email"),
            recipients_email=members_list,
            subject=subject,
            message_body=message,
        )
    except Exception as e:
        return{
            "ok": False,
            "message": f"An error occurred while trying to send massive emails. {e}",
            "data": []
        }
    return {
        "ok": True,
        "message": "Massive mailing successfully executed.",
        "data": []
    }

@shared_task(ignore_result=False, queue="linkedin_queue", bind=True)
@register_task
def check_unread_linkedin_messages(self, user: dict):

    notifier: Sender = Sender()
    manager: LinkedinManager = setup_manager(user)
    response: ResponseValue = manager.check_unread_messages()

    if response.ok:
        if len(response.data) > 0:
            email_text = "\n".join(
                        f"""
                            <div style="margin-bottom: 5px">
                                <h2 style="margin: 0; margin-bottom: 5px;">
                                    <span style="color: rgb(85, 82, 82);">
                                        Tienes { message.get("notifications", 0) } { "notificaciones" if message.get("notifications", 0) > 1 else "notificación" } de
                                    </span>
                                    <span style="font-weight: 800; font-size: 1.7rem;">
                                        <strong>{ message.get("fullname", 0) }</strong>
                                    </span>
                                </h2>
                                <p style="margin: 0; margin-bottom: 5px;">Última notificación:</p>
                                <p style="margin: 0; text-align: center; align-self: center; border-radius: 5px; padding: 10px; width: 50%; background-color: lightcyan;">
                                    { message.get("last_message", 0) }
                                </p>
                            </div>
                        """
                    for message in response.data
            )

            notifier.send_email_v2_gmail_api(
                user_email="info@ekiona.com",
                recipients_email=[user],
                subject="Notificaciones de LinkedIn",
                message_body=email_text            
            )
            return {
                    'ok': response.ok,
                    'message': 'You have unread messages.',
                    'data': response.data
            }
        return {
                'ok': response.ok,
                'message': 'You have no unread messages.',
                'data': response.data
        }
    return {
            'ok': response.ok,
            'message': "An error occurred while trying to check if you have unread messages",
            'data': response.data
    }


@shared_task(ignore_result=False, queue="linkedin_queue", bind=True)
@register_task
def accept_incoming_invitations(self, user: dict):

    notifier: Sender = Sender()    
    manager: LinkedinManager = setup_manager(user)    
    response: ResponseValue = manager.accept_incoming_invitations()

    if response.ok:
        if len(response.data) > 0:
            people_accepted: List[SearchResult] = SearchResult.query.filter(SearchResult.id.in_(response.data), SearchResult.user_id==user.get("id")).all()
            contacts = f"\n\n".join(
                    f"""
                        <tr>
                            <td style="padding: 10px 0; border-bottom: 1px solid #eee;">
                                <table cellpadding="0" cellspacing="0" border="0" style="width: 100%;">
                                    <tr>
                                        <td style="width: 80px; vertical-align: top;">
                                            <a href="{person.profile_link}">
                                                <img src="{person.profile_image_src}" alt="{person.fullname}'s profile picture">
                                            </a>
                                        </td>
                                        <td style="vertical-align: top; padding-left: 15px;">
                                            <a href="{person.profile_link}" class="contact-name">{person.fullname}</a>
                                            <p>{person.role}</p>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                    """
                    for person in people_accepted
            )
            template = CONNECTIONS_ACCEPTED_BY_FERNANDO.replace("[Contacts]", contacts)
            notifier.send_email_v2_gmail_api(
                user_email="info@ekiona.com", 
                recipients_email=[user], 
                subject=f"{user.get('username')} tienes nuevos contactos",
                message_body=template)
    else:
        # notifier.send_email(os.getenv("EMAIL"), f"Ha ocurrido un error en {accept_incoming_invitations.__name__}.", "Aviso")
        pass