import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '..', '.env'))

class Config:
    OPEN_CAGE_BASE_URL = "https://api.opencagedata.com/geocode/v1/json"
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, '..', 'data', 'linkedin.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    JWT_TOKEN_LOCATION = ['headers', 'cookies']
    ENVIRONMENT=os.getenv("ENVIRONMENT")
    CELERY={
        'broker_url': "pyamqp://guest@localhost//",
        'result_backend': "redis://localhost:6379/0",
        'task_ignore_result': False,
        'beat_scheduler': 'celery.beat:PersistentScheduler',  # Asegura que se usa el scheduler
        'beat_schedule_filename': 'celerybeat-schedule',  # Archivo de programación persistente
        'timezone': 'UTC',  # Configura la zona horaria correcta
        # 'beat_schedule': {
        #     'check-unread-messages': {
        #         'task': 'tasks.scheduled_tasks.check_unread_linkedin_messages',  
        #         'schedule': crontab(minute=0, hour='9,16', day_of_week='1-5'),  # A las 9:00 y 16:00
        #     },
    }
    VAPID_PRIVATE_KEY="<< PUT YOUR KEY HERE >>"
    VAPID_PUBLIC_KEY = "<< PUT YOUR KEY HERE >>"
    VAPID_CLAIMS = {"sub": "mailto:youremail@domain.com"}
    


class SenderConfig:
    EMAIL_SENDER = os.getenv("EMAIL")
    PASSWORD_SENDER = os.getenv("PASSWORD")