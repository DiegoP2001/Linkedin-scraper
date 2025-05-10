from functools import wraps
from flask import g, jsonify
from http import HTTPStatus
from pywebpush import webpush, WebPushException
from typing import List
from urllib.parse import urlparse

from classes.logger import Logger
from classes.email.sender import Sender
from manager import LinkedinManager
from models.models import Subscription, Task, db
from config.config import Config
from classes.constants.others import TASK_NAMES

import json
import signal
import psutil

def kill_chrome_processes():
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            name = proc.info['name']
            cmdline = proc.info['cmdline']
            if name and 'chrome' in name.lower():
                proc.send_signal(signal.SIGKILL)
            elif cmdline and any('chromedriver' in c for c in cmdline):
                proc.send_signal(signal.SIGKILL)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

def setup_logger_and_manager(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        g.logger = Logger()
        return f(*args, **kwargs)
    return decorated_function

def setup_notifier(f):
    @wraps(f)
    def fn(*args, **kwargs):
        if not hasattr(g, 'notifier'):
            g.notifier = Sender()
        return f(*args, **kwargs)
    return fn

def error_handler(f):
    @wraps(f)
    def fn(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except KeyError as e:
            return jsonify({
                'message': f"Key error: {str(e)}"
            }), HTTPStatus.BAD_REQUEST
        except ValueError as e:
            return jsonify({
                'message': f"Value error: {str(e)}"
            }), HTTPStatus.BAD_REQUEST
        except Exception as e:
            return jsonify({
                'message': f"An unexpected error occurred: {str(e)}"
            }), HTTPStatus.INTERNAL_SERVER_ERROR
    return fn

def register_task(f):
    @wraps(f)
    def fn(self, *args, **kwargs):
        try:
            user = kwargs.get("user")
            if user is None and args:
                user = args[0] if isinstance(args[0], dict) and "id" in args[0] else None

            task_id = getattr(self.request, 'id', None)
            
            if user is None:
                raise ValueError("No se pudo obtener el usuario")

            task = Task(
                id = task_id,
                user_id = user.get("id"),
                name = fn.__name__,
                state = "ACTIVE"
            )
            
            db.session.add(task)
            db.session.commit()
            result = f(self, *args, **kwargs)
            
            task.state="DONE"
            db.session.commit()
            
            if result.get("ok") == False:
                send_task_notification(
                    title=f"Tarea  '{TASK_NAMES.get(fn.__name__, fn.__name__)}' ha finalizado.",
                    description="Ha ocurrido algún error durante el scrapping.",
                    user_id=user.get("id")
                ) 
            else:
                send_task_notification(
                    title=f"Tarea  '{TASK_NAMES.get(fn.__name__, fn.__name__)}' ha finalizado.",
                    description="El scrapping ha sido exitoso.",
                    user_id=user.get("id")
                )
            
            return result
        except Exception as e:
            print(f"❌ Error en la tarea: {e}")
            if task:
                task.state = "FAIL"
                db.session.commit()
            send_task_notification(
                title=f"Tarea  '{TASK_NAMES.get(fn.__name__, fn.__name__)}' ha finalizado.",
                description="Ha ocurrido algún error durante el scrapping.",
                user_id=user.get("id")
            )
            raise  # Relanzamos el error para que Celery lo pueda ver
        finally:
            print("🧹 Cerrando procesos de Chrome...")
            kill_chrome_processes()
            print("✅ Procesos de Chrome cerrados.")
    return fn


def send_task_notification(title: str, description: str, user_id: int) -> bool:
        
        suscriptors: List[Subscription] = Subscription.query.filter(Subscription.user_id == user_id).all()
        if len(suscriptors) == 0:
            return False
        for suscriptor in suscriptors:
            try:
                origin = "{uri.scheme}://{uri.netloc}".format(uri=urlparse(suscriptor.endpoint))
                claims = Config.VAPID_CLAIMS
                claims["aud"] = origin

                webpush(
                    subscription_info={
                        "endpoint": suscriptor.endpoint,
                        "keys": {"p256dh": suscriptor.p256dh, "auth": suscriptor.auth}
                    },
                    data=json.dumps({
                        "title": title,
                        "body": description
                    }),
                    vapid_private_key=Config.VAPID_PRIVATE_KEY,
                    vapid_claims=claims
                )
            except WebPushException as e:
                print(f"Error enviando notificación: {str(e)}")