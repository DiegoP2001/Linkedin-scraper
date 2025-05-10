from app import create_app
from tasks.scheduled_tasks import *

flask_app, celery = create_app()
celery_app = flask_app.extensions["celery"]
