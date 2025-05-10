import smtplib, ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.message import EmailMessage
from typing import Optional
from config.config import SenderConfig
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
from classes.constants.email_templates import OTP_EMAIL
from email.message import EmailMessage
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from typing import List

import os
import base64
import re

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '..', '..', '.env'))


class Sender:
    SERVICE_ACCOUNT_FILE = os.path.join(basedir, 'credentials.json')
    SCOPES = [
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/gmail.settings.basic",
        ]

    def __init__(self, port: Optional[int] = 465, smtp_server: Optional[str] = "smtp.gmail.com", email: Optional[str] = None, password: Optional[str] = None ) -> None:
        self.port = port
        self.email = email or SenderConfig.EMAIL_SENDER
        self.password = password or SenderConfig.PASSWORD_SENDER
        self.smtp_server = smtp_server
        self.context = ssl.create_default_context()

    def send_email(self, receiver_email: str, subject: str, body: str) -> None:

        message = MIMEMultipart()
        message["From"] = self.email
        message["To"] = receiver_email
        message["Subject"] = subject

        message_body = body
        message.attach(MIMEText(body, "plain", "utf-8"))

        try:
            with smtplib.SMTP_SSL(self.smtp_server, self.port, context=self.context) as server:
                server.login(self.email, self.password)
                server.sendmail(self.email, receiver_email, message.as_string())
            print("Correo enviado correctamente")
        
        except Exception as e:
            print(f"Error al enviar el correo: {e}")
    
    # Deprecated
    def send_formatted_email(self, html: str|None, receiver_email: str, subject: str, email_template: Optional[str] = None):
        """
            :param html: Only include the inner code of the 'body' tag.
        """

        if html is None and email_template is None:
            raise Exception(
                "Param 'html' and 'email_template' can't be None both. You must provide one of them."
            )

        message = EmailMessage()
        message["From"] = self.email
        message["To"] = receiver_email
        message["Subject"] = subject

        if email_template is None:
            html_message = f'''
                <!DOCTYPE html>
                    <html>
                        <head>
                        </head>
                        <body style="font-family: 'Trebuchet MS', 'Lucida Sans Unicode', 'Lucida Grande', 'Lucida Sans', Arial, sans-serif; display: flex; flex-direction: column;">
                            <div>
                                {html}
                            </div>
                        </body>
                    </html>     
            '''
        else: 
            html_message = email_template

        message.set_content(html_message, subtype='html')

        try:
            with smtplib.SMTP_SSL(self.smtp_server, self.port, context=self.context) as server:
                server.login(self.email, self.password)
                server.send_message(message)
            print("Correo enviado correctamente")
        except Exception as e:
            print(f"Error al enviar el correo: {e}")
    
    def get_gmail_service(self, user_email):
        """Crea un cliente autenticado para Gmail en nombre de un usuario específico."""
        credentials = service_account.Credentials.from_service_account_file(
            self.SERVICE_ACCOUNT_FILE,
            scopes=self.SCOPES,
            subject=user_email  
        )

        # Construir el servicio de Gmail con las credenciales del usuario
        service = build("gmail", "v1", credentials=credentials)
        return service
    
    def get_gmail_signature(self, service, user_email="me"):
        try:
            signature_data = service.users().settings().sendAs().get(userId=user_email, sendAsEmail=user_email).execute()
            return signature_data.get("signature", "")
        except Exception as e:
            print(f"No se pudo obtener la firma: {e}")
            return ""

    def send_email_v2_gmail_api(self, user_email, recipients_email: List[dict], subject, message_body: str):
        """
        Envía correos personalizados a una lista de destinatarios.

        :param user_email: Correo del remitente.
        :param recipients: Lista de diccionarios con {'email': str, 'name': str}.
        :param subject: Asunto del correo.
        :param message_body_template: Plantilla de texto con {name}.
        :param html_template: Plantilla HTML opcional con {name}.
        """
        service = self.get_gmail_service(user_email)
        # Obtener la firma del usuario
        signature_html = self.get_gmail_signature(service, user_email)

        for recipient in recipients_email:
            recipient_email = recipient.get("email", None)
            recipient_name = recipient.get("name", None)

            if recipient_email is None:
                continue
            
            if recipient_name is not None:
                message_body = message_body.replace("[Nombre]", recipient_name)

            try:
                message = EmailMessage()
                message.add_alternative(message_body + "<br>" + signature_html, subtype="html")

                message["To"] = recipient_email
                message["From"] = user_email
                message["Subject"] = subject

                # Codificar el mensaje en Base64
                encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
                create_message = {"raw": encoded_message}

                # Enviar el correo
                send_message = (
                    service.users()
                    .messages()
                    .send(userId="me", body=create_message)
                    .execute()
                )
                print(f"Correo enviado a {recipient_email}")

            except HttpError as e:
                print(f"Error al enviar correo a {recipient_email}: {e}")

    def get_latest_linkedin_email(self, user_email): # Hecho pero no implementado en ningún sitio
        """Busca el correo más reciente de LinkedIn y extrae el primer enlace encontrado."""
        service = self.get_gmail_service(user_email)

        try:
            # Buscar los últimos correos de LinkedIn en la bandeja de entrada
            response = service.users().messages().list(userId="me", q="from:linkedin.com", maxResults=5).execute()
            messages = response.get("messages", [])

            if not messages:
                print("No se encontraron correos de LinkedIn.")
                return None

            for msg in messages:
                message = service.users().messages().get(userId="me", id=msg["id"]).execute()
                payload = message["payload"]
                
                # Extraer el cuerpo del correo
                email_data = None
                if "parts" in payload:
                    for part in payload["parts"]:
                        if part["mimeType"] == "text/html":
                            email_data = part["body"]["data"]
                            break
                        elif part["mimeType"] == "text/plain":
                            email_data = part["body"]["data"]
                
                if email_data:
                    decoded_email = base64.urlsafe_b64decode(email_data).decode("utf-8")

                    # Buscar el primer enlace en el contenido del correo
                    links = re.findall(r"https?://[^\s<>\"']+", decoded_email)
                    linkedin_links = [link for link in links if "linkedin.com" in link]

                    if linkedin_links:
                        print(f"Enlace encontrado: {linkedin_links[0]}")
                        return linkedin_links[0]

            print("No se encontraron enlaces en los correos de LinkedIn.")
            return None

        except Exception as e:
            print(f"Error al obtener correos: {e}")
            return None