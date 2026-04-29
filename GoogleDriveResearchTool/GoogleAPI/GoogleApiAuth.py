import json
import os
import traceback

from google.oauth2.credentials import Credentials

from Common import LogHelper
from GoogleAPI.Decryption import DecryptFile

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive']

DECRYPT_ERR = "Googleアカウント認証ファイルの復号化が失敗しました。Googleアカウント認証ファイル作成手順を参照し再作成してください"


class GoogleApiAuth:

    def __init__(self, saved_credentials, key_saved_credentials):
        """
            google drive login files,
            using key decrypt secrets/credentials file
        :param saved_credentials:
        :param key_saved_credentials:
        """
        self.saved_credentials = saved_credentials
        self.key_saved_credentials = key_saved_credentials

    def login(self):
        """
            login google account
        :return:
        """
        return self.read_saved_credentials()

    def read_saved_credentials(self):
        """
            read google account certify file
        :param self:
        :return:
        """
        json_credentials = self.read_decrypt_certify_file(self.saved_credentials, self.key_saved_credentials)
        credentials = Credentials.from_authorized_user_info(json_credentials, SCOPES)
        return credentials

    @staticmethod
    def read_decrypt_certify_file(certify_file, key_file):
        """
            using key_file decrypt certify_file
        :param certify_file:
        :param key_file:
        :return:
        """
        if not os.path.exists(certify_file):
            raise Exception("not found certify file 「%s」" % certify_file)

        if not os.path.exists(key_file):
            raise Exception("not found decrypt key file 「%s」" % key_file)

        try:
            decrypt_content = DecryptFile.decrypt(certify_file, key_file)
        except Exception:
            LogHelper.error(traceback.format_exc())
            raise Exception(DECRYPT_ERR)

        return json.loads(decrypt_content)
