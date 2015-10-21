# -*- coding: UTF-8 -*-
from io import BytesIO
from re import sub
from mimetypes import guess_type
from os.path import basename
from urllib import parse as urlparse
from datetime import datetime

from django.core.files import File
from django.core.files.storage import Storage
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings

def setting(name, default=None):
    return getattr(settings, name, default)


class SwiftStorage(Storage):
    storage_url = setting('SWIFT_PRE_AUTH_URL')
    token = setting('SWIFT_PRE_AUTH_TOKEN')
    container_name = setting('SWIFT_CONTAINER_NAME')
    auto_overwrite = setting('SWIFT_AUTO_OVERWRITE', False)

    def __init__(self):
        self.last_headers_name = None
        self.last_headers_value = None

        self.http_conn = swiftclient.http_connection(self.storage_url)

        try:
            swiftclient.head_container(self.storage_url, self.token,
                                       self.container_name,
                                       http_conn=self.http_conn)
        except swiftclient.ClientException:
            swiftclient.put_container(self.storage_url, self.token,
                                      self.container_name,
                                      http_conn=self.http_conn)

    def _open(self, name, mode='rb'):
        headers, content = swiftclient.get_object(self.storage_url, self.token,
                                                  self.container_name, name,
                                                  http_conn=self.http_conn)
        buf = BytesIO(content)
        buf.name = basename(name)
        buf.mode = mode

        return File(buf)

    def _save(self, name, content):
        content_type = guess_type(name)[0]
        swiftclient.put_object(self.storage_url,
                               self.token,
                               self.container_name,
                               name,
                               content,
                               http_conn=self.http_conn,
                               content_type=content_type)
        return name

    def get_headers(self, name):
        if name != self.last_headers_name:
            self.last_headers_value = swiftclient.head_object(
                self.storage_url, self.token, self.container_name, name,
                http_conn=self.http_conn)
            self.last_headers_name = name
        return self.last_headers_value

    def exists(self, name):
        try:
            self.get_headers(name)
        except swiftclient.ClientException:
            return False
        return True

    def delete(self, name):
        try:
            swiftclient.delete_object(self.storage_url, self.token,
                                      self.container_name, name,
                                      http_conn=self.http_conn)
        except swiftclient.ClientException:
            pass

    def get_valid_name(self, name):
        s = name.strip().replace(' ', '_')
        return sub(r'(?u)[^-_\w./]', '', s)

    def get_available_name(self, name, max_length=None):
        if not self.auto_overwrite:
            name = super(SwiftStorage, self).get_available_name(name)

        return name

    def size(self, name):
        return int(self.get_headers(name)['content-length'])

    def modified_time(self, name):
        return datetime.fromtimestamp(
            float(self.get_headers(name)['x-timestamp']))

    def url(self, name):
        return urlparse.urljoin(self.storage_url, name)

    def path(self, name):
        return name

    def isdir(self, name):
        return '.' not in name

    def listdir(self, abs_path):
        container = swiftclient.get_container(self.storage_url,
                                              self.token,
                                              self.container_name)
        files = []
        dirs = []
        for obj in container[1]:
            if not obj['name'].startswith(abs_path):
                continue

            path = obj['name'][len(abs_path):].split('/')
            key = path[0] if path[0] else path[1]

            if not self.isdir(key):
                files.append(key)
            elif key not in dirs:
                dirs.append(key)

        return dirs, files

    def makedir(self, dir):
        swiftclient.put_object(self.storage_url,
                               token=self.token,
                               container=self.container_name,
                               name='%s/.' % dir,
                               contents='')

    def rm_tree(self, abs_path):
        container = swiftclient.get_container(self.storage_url,
                                              self.token,
                                              self.container_name)

        for obj in container[1]:
            if obj['name'].startswith(abs_path):
                swiftclient.delete_object(self.storage_url,
                                          token=self.token,
                                          container=self.container_name,
                                          name=obj['name'])
