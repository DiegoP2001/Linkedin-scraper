from celery import Celery, Task
from flask import Flask
from config.config import Config

def celery_init_app(app: Flask) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask, backend=Config.CELERY["result_backend"])
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    
    celery_app.conf.update({
        'include': [
            "tasks.tasks",
            "tasks.scheduled_tasks"
        ],
        'default_queue': "linkedin_queue"
    })
    
    return celery_app