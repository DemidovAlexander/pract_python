# -*- coding: UTF-8 -*-
import swiftclient

from io import BytesIO
from os.path import basename
from mimetypes import guess_type

from django.core.files import File
from django.conf import settings


def setting(name, default=None):
    return getattr(settings, name, default)

PRE_AUTH_URL = setting('PRE_AUTH_URL')
PRE_AUTH_TOKEN = setting('PRE_AUTH_TOKEN')
CONTAINER_NAME = setting('CONTAINER_NAME')


def connect_swift():
    http_conn = swiftclient.http_connection(PRE_AUTH_URL)

    try:
        swiftclient.head_container(PRE_AUTH_URL, PRE_AUTH_TOKEN,
                                   CONTAINER_NAME,
                                   http_conn=http_conn)
    except swiftclient.ClientException:
        swiftclient.put_container(PRE_AUTH_URL, PRE_AUTH_TOKEN,
                                  CONTAINER_NAME,
                                  http_conn=http_conn)
    return http_conn


def open_on_swift(name, mode='rb'):
    headers, content = swiftclient.get_object(PRE_AUTH_URL, PRE_AUTH_TOKEN,
                                              CONTAINER_NAME, name,
                                              http_conn=connect_swift())
    buf = BytesIO(content)
    buf.name = basename(name)
    buf.mode = mode

    return File(buf)


def save_into_swift(name, content):
    content_type = guess_type(name)[0]
    swiftclient.put_object(PRE_AUTH_URL,
                           PRE_AUTH_TOKEN,
                           CONTAINER_NAME,
                           name, content,
                           http_conn=connect_swift(),
                           content_type=content_type)
    return name


def delete_from_swift(name):
    try:
        swiftclient.delete_object(PRE_AUTH_URL, PRE_AUTH_TOKEN,
                                  CONTAINER_NAME, name,
                                  http_conn=connect_swift())
    except swiftclient.ClientException:
        pass
