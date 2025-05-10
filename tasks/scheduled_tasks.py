from app import celery
from celery import Celery
from celery.schedules import crontab
from models.models import User, db
from typing import List
from models.models import ScheduledTask, CustomMembersList
from datetime import datetime
from sqlalchemy import or_, func


@celery.on_after_configure.connect
def setup_periodic_tasks(sender: Celery, **kwargs):
    sender.add_periodic_task(
        crontab(minute="*"),
        run_scheduled_tasks.s(),
        name="Run dynamic scheduled tasks"
    )

@celery.task(queue="linkedin_queue")
def run_scheduled_tasks():
    now = datetime.now()
    today_weekday = now.weekday()

    # Tareas diarias solamente tienen hora
    # Tareas semanales solamente tienen hora y día de la semana
    # Tareas mensuales solamente tienen fecha y hora

    daily_tasks: List[ScheduledTask] = ScheduledTask.query.filter \
    (
        ScheduledTask.is_repeated == True,
        ScheduledTask.day_of_week == - 1,
        ScheduledTask.hour == now.hour,
        ScheduledTask.minute == now.minute,
    ).all()

    weekly_tasks: List[ScheduledTask] = ScheduledTask.query.filter \
    (
        ScheduledTask.is_repeated==True,
        ScheduledTask.day_of_week==today_weekday,
        ScheduledTask.hour==now.hour,
        ScheduledTask.minute==now.minute
    ).all()

    monthly_tasks: List[ScheduledTask] = ScheduledTask.query.filter \
    (
        ScheduledTask.is_repeated == True,
        ScheduledTask.activation_date == now,
        ScheduledTask.hour == now.hour,
        ScheduledTask.minute == now.minute
    ).all()

    one_time_tasks: List[ScheduledTask] = ScheduledTask.query.filter \
    (
        ScheduledTask.is_repeated == False,
        ScheduledTask.is_executed == False,
        ScheduledTask.hour == now.hour,
        ScheduledTask.minute == now.minute,
        or_(
            ScheduledTask.day_of_week == today_weekday,
            func.date(ScheduledTask.activation_date) == now.date()
        )
    ).all()

    for task in one_time_tasks:
        user: User = User.query.get(task.user_id)
        task_to_execute = celery.tasks.get(task.task_name, None)
        parameters = task.task_params
        parameters["user"] = user.to_dict()
        if parameters.get("members_list") is not None:
            list_of_members_param: CustomMembersList = CustomMembersList.query.filter(CustomMembersList.name==parameters["members_list"]).first()
            parameters["members_list"] = [list_of_members_param.to_dict()["members"]]
        if task_to_execute is not None:
            task_to_execute.apply_async(queue="linkedin_queue", kwargs=parameters)
            print(f"Task: {task.task_name} sended to execute ...")
            task.is_executed = True
    db.session.commit()

    repetitive_tasks = daily_tasks + weekly_tasks + monthly_tasks

    for task in repetitive_tasks:
        user: User = User.query.get(task.user_id)
        task_to_execute = celery.tasks.get(task.task_name, None)
        parameters = task.task_params
        parameters["user"] = user.to_dict()
        if parameters.get("members_list") is not None:
            list_of_members_param: CustomMembersList = CustomMembersList.query.filter(CustomMembersList.name==parameters["members_list"]).first()
            parameters["members_list"] = [list_of_members_param.to_dict()["members"]]
        if task_to_execute is not None:
            task_to_execute.apply_async(queue="linkedin_queue", kwargs=parameters)
            print(f"Task: {task.task_name} sended to execute ...")
