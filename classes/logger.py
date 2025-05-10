import os
from datetime import datetime

basedir = os.path.abspath(os.path.dirname(__file__))

class SingletonMeta(type):
    """
        Metaclass to implement Singleton design pattern
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]

class Logger(metaclass=SingletonMeta):

    def __init__(self) -> None:
        self.log_name = "log.txt"
        self.content = ""
        self.__path = os.path.join(basedir, "..", "log", "log.txt")

    def log(self, log_text: str):

        actual_datetime = datetime.now().strftime("%d-%m-%Y | %H:%M:%S") 

        with open(self.__path, "a", encoding="utf-8") as log_file:
            self.content = log_file.write(f"[{actual_datetime}] {log_text}\n")

    