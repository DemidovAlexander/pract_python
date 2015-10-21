# -*- coding: UTF-8 -*-
from pymongo import MongoClient
from pymongo import ASCENDING
from time import sleep
from datetime import datetime
from json import dumps

from django.conf import settings


def setting(name, default=None):
    return getattr(settings, name, default)

CONNECTION_HOST = setting('MONGO_CONNECTION_HOST')
CONNECTION_PORT = setting('MONGO_CONNECTION_PORT')
WORKER_WATCH_PERIOD = setting('WORKER_WATCH_PERIOD')

def create_mongo_client():
    """
    Подключение к MongoDB-серверу. Используются глобальные константы
    \t``connection_host`` хост подключения\n
    \t``connection_port`` порт подключения
    """

    return MongoClient(CONNECTION_HOST, CONNECTION_PORT)


class OpenMongoConnection(object):
    """Класс для получения объекта соединения с mongo, 
       которое гарантированно будет закрыто по окончании работы
    """

    def __enter__(self):
        self.connection = create_mongo_client()

        return self.connection

    def __exit__(self, exception_type, exception_val, exception_traceback):
        self.connection.close()


class OpenMongoDatabase(object):
    """Класс для получения объекта коллекции, 
       для которой гарантированно будет закрыто соединение по окончании работы
    """

    def __enter__(self):
        self.connection = create_mongo_client()
        self.database = self.connection.tasks_queue.task

        return self.database

    def __exit__(self, exception_type, exception_val, exception_traceback):
        self.connection.close()


# requests
def insert_formatted_task(database, first_path, second_path, task_type):
    """
    Добавляет в коллекцию новое задание. Параметры:\n
    \t``database``: MongoDB коллекция\n
    \t``first_path``: путь к первому файлу\n
    \t``second_path``: путь ко второму файлу\n
    \t``task_type``: тип задания\n
    Возвращает ``id`` добавленного задания или ``None``.
    """

    sources = dumps([first_path, second_path])

    inserted_task = database.insert_one(
        {'status': 'open', 'utc_create': datetime.utcnow(), 'task_type': task_type,
         'sources': sources})

    if inserted_task is not None:
        return inserted_task.inserted_id


def request_completed_task(database, task_id):
    """
    Запрашивает результат выполнения задания. Параметры:\n
    \t``database``: MongoDB коллекция\n
    \t``task_id``: ``id`` ожидаемого задания\n
    Возвращает ``result`` выполненного задания или ``None``.
    """

    task = database.find_one_and_delete({'_id': task_id, 'status': 'complete'})

    if task is not None:
        return task['result']


def request_top_priority_task(database):
    """
    Запрашивает наиболее приоритетное для выполнения задание из коллекции и помечает его как выполняемое. Параметры:\n
    \t``database``: MongoDB коллекция\n
    Возвращает ``id``, ``sources``, ``task_type``  или ``None``, ``None``, ``None``.
    """

    task = database.find_one_and_update({'status': 'open'},
                                        {'$set': {'status': 'in_progress',
                                                  'utc_handle': datetime.utcnow()}},
                                        sort=[('utc_create', ASCENDING)])
    if task is not None:
        return task['_id'], task['sources'], task['task_type']

    else:
        return None, None, None


def update_resolved_task(database, task_id, result):
    """
    Обновляет результат выполнения задания, помечает его как выполненное. Параметры:\n
    \t``database``: MongoDB коллекция\n
    \t``task_id``: идентификатор задания в коллекции\n
    \t``result``: результат выполнения задания\n
    """

    database.update_one({'_id': task_id},
                        {'$set': {'status': 'complete', 'utc_complete': datetime.utcnow(),
                         'result': result}})


# Public API server functions
def redirect_task(first_path, second_path, task_type):
    """
    Функция по работе с очередью заданий для Public API сервера.
    Добавляет задание на выполнение. Параметры:\n
    \t``first_path``: путь к первому файлу\n
    \t``second_path``: путь ко второму файлу\n
    \t``task_type``: тип задания\n
    Возвращает ``id`` добавленного задания или ``None``.
    """

    with OpenMongoDatabase() as database:
        return insert_formatted_task(database, first_path, second_path, task_type)


def get_task_result(task_id):
    """
    Функция по работе с очередью заданий для Public API сервера.
    Запрашивает результат выполнения задания. Параметры:\n
    \t``task_id``: ``id`` запрашиваемого задания\n
    Возвращает ``result`` выполненного задания или ``None``.
    """

    with OpenMongoDatabase() as database:
        return request_completed_task(database, task_id)


# Worker function
def worker_routine(process_task):
    """
    Основная функция Worker по работе с очередью заданий.
    Анализирует очередь на появление новых заданий, выполняет их и обновляет результат выполнения. Параметры:\n
    \t``process``: функция-обработчик задания, принимающая ``task_type``, ``sources``\n
    """

    with OpenMongoDatabase() as database:
        working = True

        while working:
            task_id, sources, task_type = request_top_priority_task(database)

            while task_id is None:
                sleep(WORKER_WATCH_PERIOD)

                task_id, sources, task_type = request_top_priority_task(database)

            result = process_task(task_type, sources)

            update_resolved_task(database, task_id, result)


# Development
def drop_tasks():
    """
    Функция для тестирования. Очищает коллекцию от всех хранимых в ней заданий.\n
    """

    with OpenMongoConnection() as connection:
        connection.tasks_queue.drop_collection('tasks')
