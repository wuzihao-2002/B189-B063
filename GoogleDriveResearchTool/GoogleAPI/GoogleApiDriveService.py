import queue
import re
from time import sleep

import requests
from google.api_core import retry, exceptions
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.auth import exceptions as auth_exceptions


class LimitException(Exception):
    """
       When there is an exception in the limit, try to execute it again
    """

    def __init__(self, message):
        self.message = message


class GoogleApiDriveService:

    def __init__(self, creds):
        self.creds = creds
        self.service_queue = queue.LifoQueue()
        self.suspend = False

    def _authorize(self):
        """
            create google drive service instance
        :return:
        """
        service = build('drive', 'v3', credentials=self.creds, cache_discovery=False)
        # service.timeout = 20
        return service

    def get_service(self):
        if self.service_queue.empty():
            self.service_queue.put(self._authorize())
        return self.service_queue.get()

    def release_service(self, service):
        self.service_queue.put(service)

    def about(self, fields=None, allow_suspend=True):
        """
            get information about current user
        :param fields:
        :param allow_suspend:
        :return:
        """

        def _about(service):
            about = service.about().get(fields=fields).execute()
            return about

        return self.method_wrapper(_about, allow_suspend)

    def get_file_metadata(self, file_id, fields=None, allow_suspend=True):
        """
            get file's information
        :param file_id:
        :param fields:
        :param allow_suspend:
        :return:
        """

        def _get_file_metadata(service):
            file = service.files().get(fileId=file_id, fields=fields).execute()
            return file

        return self.method_wrapper(_get_file_metadata, allow_suspend)

    def get_media(self, file_id, allow_suspend=True):
        """
            get google drive file's content
        :param file_id:
        :param allow_suspend:
        :return:
        """

        def _get_media(service):
            media = service.files().get_media(fileId=file_id).execute()
            return media

        return self.method_wrapper(_get_media, allow_suspend)

    def export(self, file_id, mime_type='text/plain', allow_suspend=True):
        """
            export google document
        :param file_id:
        :param mime_type:
        :param allow_suspend:
        :return:
        """

        def _export(service):
            response = service.files().export(fileId=file_id, mimeType=mime_type).execute()
            return response

        return self.method_wrapper(_export, allow_suspend)

    def create_file(self, body, fd, mimetype, fields=None, allow_suspend=True):
        """
            create a file by body
             body = {
                        "name": "xxx",
                        "mimeType": "xxxx",
                        "parents": [
                            "xxxxxxxxxxxxx"
                        ]
                    }
        :param body:
        :param fd:
        :param mimetype:
        :param fields:
        :param allow_suspend:
        :return:
        """

        def _create_file(service):
            media = MediaIoBaseUpload(fd, mimetype=mimetype)
            file = service.files().create(body=body, fields=fields, media_body=media).execute()
            return file

        return self.method_wrapper(_create_file, allow_suspend)

    def update_file(self, file_id, param=None, allow_suspend=True):
        """
            update file metadata
        :param file_id:
        :param param:
        :param allow_suspend:
        :return:
        """

        def _update_file(service):
            _param = {}
            if param is not None:
                _param = param
            response = service.files().update(fileId=file_id, body=_param).execute()
            return response

        return self.method_wrapper(_update_file, allow_suspend)

    def update_file_content(self, file_id, fd, mimetype, allow_suspend=True):
        """
            update file content by io
        :param file_id:
        :param fd:
        :param mimetype:
        :param allow_suspend:
        :return:
        """

        def _update_file_content(service):
            media = MediaIoBaseUpload(fd, mimetype=mimetype)
            file = service.files().update(fileId=file_id, media_body=media).execute()
            return file

        return self.method_wrapper(_update_file_content, allow_suspend)

    def list_file(self, param=None, allow_suspend=True):
        """
            retrieve a file list
        :param param:
        :param allow_suspend:
        :return:
        """

        def _list_file(service):
            result = []
            page_token = None
            _param = {}
            if param is not None:
                _param = param

            while True:
                if page_token:
                    _param["pageToken"] = page_token
                files = service.files().list(**_param).execute()

                result.extend(files["files"])
                page_token = files.get("nextPageToken")
                if not page_token:
                    break

            return result

        return self.method_wrapper(_list_file, allow_suspend)

    @retry.Retry(predicate=retry.if_exception_type(LimitException,
                                                   exceptions.InternalServerError,
                                                   exceptions.TooManyRequests,
                                                   exceptions.ServiceUnavailable,
                                                   requests.exceptions.ConnectionError,
                                                   requests.exceptions.ChunkedEncodingError,
                                                   auth_exceptions.TransportError, ))
    def retry(self, target, *args):
        service = None
        try:
            allow_suspend = args[0]
            while self.suspend and allow_suspend:
                sleep(1)

            service = self.get_service()
            return target(service)
        except Exception as e:
            ex_message = e.__str__()
            if re.search(r"LIMIT|QUOTA|RATE|TIMED OUT", ex_message, re.I):
                raise LimitException(e)
            else:
                raise e
        finally:
            if service is not None:
                self.release_service(service)

    def method_wrapper(self, target, *args):
        return self.retry(target, *args)

    def set_suspend(self, suspend):
        self.suspend = suspend
