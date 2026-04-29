import datetime
import re
import threading
import traceback
import unicodedata
from collections import defaultdict

from pytz import timezone

from Common import LogHelper
# err msg
from Common.TsvItemEnum import TsvItemEnum
from DTO.FileDetail import FileDetail
from DTO.ResearchFolder import ResearchFolder
from GoogleAPI.GoogleApiDriveService import GoogleApiDriveService
from Processes.SqliteDB.ResearchSQLite import ResearchSQLite
from Processes.ThreadPool.ResearchThreadPool import ResearchThreadPool

ITEM_ACCESS_PERMISSION = "アクセス権限"
ERR_SIGN = "×"

# error msg
GET_FILE_INFO_SUCCESS_LOG = "「処理ファイル名:\"%s\",URL:\"%s\"」の情報を取得しました。"
GET_FILE_INFO_FAILED = "属性「%s」が取得できませんでした。"
GET_FILE_INFO_FAILED_LOG = "「処理ファイル名:\"%s\",URL:\"%s\"」の属性「%s」が取得できませんでした。"
GET_FILE_INFO_ERROR_LOG = "「処理ファイル名:\"%s\",URL:\"%s\"」の情報取得が失敗しました。\nエラー情報:%s"
GET_SUB_FILE_INFO_ERROR_LOG = "「処理ファイル名:\"%s\",URL:\"%s\"」のサブファイル情報取得が失敗しました。\nエラー情報:%s"
GET_LOGIN_USER_EMAIL_ERROR_LOG = "ログインユーザーのメールアドレスの取得が失敗しました。"
PERMISSION_DENIED_ERROR = "「共有設定」がfalseで、ログインユーザーは権限設定の権限がありません。"
PERMISSION_DENIED_ERROR_LOG = "「処理ファイル名:\"%s\",URL:\"%s\"」は「共有設定」がfalseで、ログインユーザーは権限設定の権限がありません。"

# recursive deep length
dir_series_count = 0

# get fields info
PARAM = "id, name, mimeType, webViewLink, writersCanShare, parents," \
        " owners, permissions, modifiedTime, lastModifyingUser"

# research result
RESEARCH_RESULT = "調査結果情報:"
RESEARCH_TOTAL_COUNT = "  総件数: %s"
RESEARCH_FOLDER_COUNT = "    フォルダ件数  : %s"
RESEARCH_FILE_COUNT = "    ファイル件数  : %s"
RESEARCH_WARN_COUNT = "    ワーニング件数: %s"
RESEARCH_ERR_COUNT = "    エラー件数    : %s"
ACCOUNT_SET_COUNT = "  アカウント設定件数: %s"
ACCOUNT_FILE_COUNT = "    %s件数: %s"

BROADLEAF_EMAIL_SUFFIX = "@broadleaf.co.jp"

exception_interrupt = False


class GoogleDriveFolderIterator:
    set_account_record_dic = {}

    account_record_lock = threading.RLock()
    atomic_lock = threading.RLock()

    def __init__(self, login_user, g_drive: GoogleApiDriveService, thread_pool: ResearchThreadPool,
                 research_sqlite: ResearchSQLite):
        self.total_count = 0
        self.folder_count = 0
        self.file_count = 0
        self.err_count = 0
        self.failed_count = 0
        self.warn_count = 0
        self.login_email, self.login_name = self.get_login_username(login_user)
        self.drive = g_drive
        self.threadPool = thread_pool
        self.research_sqlite = research_sqlite
        self.google_user_list = None
        self.permissions_output_flg = None
        self.struct_output_flg = None

    def get_login_username(self, login_user):
        user = self.get_json_item(login_user, "user")
        login_email = self.get_json_item(user, "emailAddress")
        login_name = self.get_json_item(user, "displayName")
        if self.is_none_or_empty(login_email) or self.is_none_or_empty(login_name):
            LogHelper.debug(login_user)
            raise Exception(GET_LOGIN_USER_EMAIL_ERROR_LOG)

        login_email = str(login_email).replace(BROADLEAF_EMAIL_SUFFIX, "")

        return login_email, login_name

    def file_structure_info_get(self, sel_gid, google_user_list, permissions_output_flg, struct_output_flg):
        """
            use multi thread save google file info to sqlite
        :param sel_gid:
        :param google_user_list:
        :param permissions_output_flg:
        :param struct_output_flg:
        :return:
        """
        self.google_user_list = google_user_list
        self.permissions_output_flg = permissions_output_flg
        self.struct_output_flg = struct_output_flg

        # save folder info
        self.save_root_folder_info_to_db(sel_gid)

        # binding threadPool task method
        self.threadPool.set_target(self.save_file_info_to_db)

        # begin task handle loop
        self.threadPool.run()

        record_index = 0
        record_count = 1

        # loop: research Google Drive info
        while True:
            if record_count > record_index:
                folder_info_iterator = self.research_sqlite.research_folder_iterator(record_index)

                for research_folder in folder_info_iterator:
                    record_index += 1
                    self.threadPool.add_work(research_folder)
            # sleep(0.1)
            record_count = self.research_sqlite.research_folder_record_count()

            if not self.threadPool.state():
                if self.research_sqlite.research_exit:
                    break

                record_count = self.research_sqlite.research_folder_record_count()
                if record_count == record_index:
                    break

        self.threadPool.shutdown()
        self.research_sqlite.commit()

        # close task thread
        self.threadPool.stop_task()
        self.research_sqlite.close()

    def file_structure_info_save(self, sel_gid, output_path):
        """
            write sqlite save file info to tsv
        :param sel_gid:
        :param output_path:
        :return:
        """
        self.research_sqlite.re_init()

        with open(output_path, 'a', encoding='UTF-8', newline="", errors='ignore') as output_file:
            self.research_sqlite.file_info_to_tsv(sel_gid, output_file)

        self.research_sqlite.close()

    def save_root_folder_info_to_db(self, gid):
        """

        :param gid:
        :return:
        """
        file = self.drive.get_file_metadata(gid, PARAM)
        parent_id = None
        parent_name = None
        parent_uri = None

        parents = self.get_json_item(file, "parents")
        if not self.is_none_or_empty(parents):
            parent_id = parents[0]
            parent_file = self.drive.get_file_metadata(parent_id, "name,webViewLink")
            parent_name = self.get_json_item(parent_file, "name")
            parent_uri = self.get_json_item(parent_file, "webViewLink")

        self.total_count += 1

        # add task
        research_folder = ResearchFolder()
        research_folder.gid = gid
        research_folder.parent_gid = parent_id
        research_folder.name = self.get_json_item(file, "name")
        research_folder.uri = self.get_json_item(file, "webViewLink")
        self.research_sqlite.save_data(research_folder)

        # add task
        self.files_detail_to_sqlite(file, parent_id, parent_name, parent_uri, gid)

    def save_file_info_to_db(self, research_work):
        """
            threadPool handle method
            google drive file type:
                file: save to table [FileDetail]
                folder: save to table [FileDetail]、[ResearchFolder]
        :param research_work:
        :return:
        """
        try:
            # get sub file
            children = self.get_children(research_work.gid)
            with self.atomic_lock:
                self.total_count += len(children)

            # get sub file info and save to sqlite
            for child_file in children:
                name = self.get_json_item(child_file, "name")
                link = self.get_json_item(child_file, "webViewLink")
                mime_type = self.get_json_item(child_file, "mimeType")
                gid = self.get_json_item(child_file, "id")

                try:
                    if mime_type is not None and mime_type == "application/vnd.google-apps.folder" \
                            and not self.is_none_or_empty(gid):
                        research_folder = ResearchFolder()
                        research_folder.gid = gid
                        research_folder.parent_gid = research_work.gid
                        research_folder.name = name
                        research_folder.uri = link
                        self.research_sqlite.save_data(research_folder)

                    # parse file info and save to SQLite
                    self.files_detail_to_sqlite(child_file, research_work.gid, research_work.name, research_work.uri)

                except Exception as e:
                    with self.atomic_lock:
                        self.err_count += 1
                    LogHelper.err_logger_error(GET_FILE_INFO_ERROR_LOG % (name, link, e))
                    LogHelper.err_logger_error(traceback.format_exc())
        except Exception as e:
            with self.atomic_lock:
                self.err_count += 1
            LogHelper.err_logger_error(GET_SUB_FILE_INFO_ERROR_LOG % (research_work.name, research_work.uri, e))
            LogHelper.err_logger_error(traceback.format_exc())

    def files_detail_to_sqlite(self, file, parent_gid, parent_title, parent_uri, gid=None):
        """
            Get all information about a file or folder
        :param file:
        :param parent_gid:
        :param parent_title:
        :param parent_uri:
        :param gid:
        :return:
        """
        file_detail = FileDetail()

        if gid is None:
            gid = self.get_json_item(file, "id")
        file_detail.gid = gid
        file_detail.parent_gid = parent_gid

        warn_info_list = []
        err_info_list = []

        # ファイル
        file_name = self.get_json_item(file, "name")
        if self.is_none_or_empty(file_name):
            file_detail.file = ERR_SIGN
            err_info_list.append(TsvItemEnum.FILE.value)
        else:
            file_detail.file = file_name

        # 種類
        mime_type = self.get_json_item(file, "mimeType")
        if self.is_none_or_empty(mime_type):
            file_detail.type = ERR_SIGN
            err_info_list.append(TsvItemEnum.TYPE.value)
        else:
            file_type = re.sub("application/vnd.google-apps.", "", mime_type)
            if file_type == "folder":
                file_detail.type = "D"
                with self.atomic_lock:
                    self.folder_count += 1
            elif file_type == "shortcut":
                file_detail.type = "S"
                with self.atomic_lock:
                    self.file_count += 1
            else:
                file_detail.type = "F"
                with self.atomic_lock:
                    self.file_count += 1

        # 更新年月日、更新時間、更新者
        self.modify_info_get(file, file_detail, warn_info_list, err_info_list)

        # URI
        uri = self.get_json_item(file, "webViewLink")
        if self.is_none_or_empty(uri):
            file_detail.uri = ERR_SIGN
            err_info_list.append(TsvItemEnum.URI.value)
        else:
            file_detail.uri = uri

        # 親フォルダ
        if self.is_none_or_empty(parent_title):
            file_detail.parent_folder = ERR_SIGN
            warn_info_list.append(TsvItemEnum.PARENT_FOLDER.value)
        else:
            file_detail.parent_folder = parent_title

        # 親URI
        if self.is_none_or_empty(parent_uri):
            file_detail.parent_uri = ERR_SIGN
            warn_info_list.append(TsvItemEnum.PARENT_URI.value)
        else:
            file_detail.parent_uri = parent_uri

        # 共有設定
        writer_can_share = self.get_json_item(file, "writersCanShare")
        if self.is_none_or_empty(writer_can_share):
            file_detail.writers_can_share = ERR_SIGN
            err_info_list.append(TsvItemEnum.WRITERS_CAN_SHARE.value)
        else:
            file_detail.writers_can_share = writer_can_share

        # 共有情報
        self.permissions_info_get(file, file_detail, err_info_list)

        # 共有設定=false、ownedByMe=false
        permission_denied = self.check_permission_denied(file_detail)

        # 権限ﾁｪｯｸ結果:調査ツールで使ってない項目なので、-付き
        file_detail.check_result = "-"
        # 権限設定結果:調査ツールで使ってない項目なので、-付き
        file_detail.setting_result = "-"

        # ErrInfo
        err_info = ""
        warn_err_info_list = warn_info_list + err_info_list
        if warn_err_info_list:
            err_info = GET_FILE_INFO_FAILED % "、".join(warn_err_info_list)

        if permission_denied:
            err_info += PERMISSION_DENIED_ERROR

        if err_info == "":
            err_info = "-"

        file_detail.err_info = err_info

        self.research_sqlite.save_data(file_detail)

        # success
        if not warn_info_list and not err_info_list and not permission_denied:
            LogHelper.info(GET_FILE_INFO_SUCCESS_LOG % (file_name, uri))
        else:
            # some items were not retrieved
            if warn_info_list:
                LogHelper.warn(GET_FILE_INFO_FAILED_LOG % (file_name, uri, '、'.join(warn_info_list)))
                with self.atomic_lock:
                    self.warn_count += 1

            if err_info_list or permission_denied:
                if err_info_list:
                    LogHelper.err_logger_error(GET_FILE_INFO_FAILED_LOG % (file_name, uri, '、'.join(err_info_list)))
                if permission_denied:
                    LogHelper.err_logger_error(PERMISSION_DENIED_ERROR_LOG % (file_name, uri))
                with self.atomic_lock:
                    self.err_count += 1

    def modify_info_get(self, file, file_detail, warn_info_list, err_info_list):
        """
            get last modified time and last modifying user
        :param file:
        :param file_detail:
        :param warn_info_list:
        :param err_info_list:
        :return:
        """
        # 最終更新日時
        modified_time = self.get_json_item(file, "modifiedTime")
        if self.is_none_or_empty(modified_time):
            # 最終更新年月日
            file_detail.last_update_date = ERR_SIGN
            # 最終更新時間
            file_detail.last_update_time = ERR_SIGN
            err_info_list.append(TsvItemEnum.LAST_UPDATE_DATE.value)
            err_info_list.append(TsvItemEnum.LAST_UPDATE_TIME.value)
        else:
            format_datetime = datetime.datetime.strptime(modified_time, "%Y-%m-%dT%H:%M:%S.%fZ").replace(
                tzinfo=timezone("UTC"))
            convert_datetime = datetime.datetime.fromtimestamp(format_datetime.timestamp())

            # 最終更新年月日
            last_modify_date = convert_datetime.strftime("%Y/%m/%d")
            file_detail.last_update_date = last_modify_date
            # 最終更新時間
            last_modify_time = convert_datetime.strftime("%H:%M:%S")
            file_detail.last_update_time = last_modify_time

        # 最終更新者
        modify_user = self.get_json_item(file, "lastModifyingUser")
        email = self.get_json_item(modify_user, "emailAddress")
        display_name = self.get_json_item(modify_user, "displayName")
        if self.is_none_or_empty(email):
            file_detail.last_updater = ERR_SIGN
            warn_info_list.append(TsvItemEnum.LAST_UPDATER.value)
        else:
            email = str(email).replace(BROADLEAF_EMAIL_SUFFIX, "")
            display_name = display_name if display_name is not None else ""
            file_detail.last_updater = "%s(%s)" % (email, display_name)

    def permissions_info_get(self, file, file_detail, err_info_list):
        """
            get file permissions (owner, writer, reader)
        :param file:
        :param file_detail:
        :param err_info_list:
        :return:
        """
        # 共有情報
        if self.permissions_output_flg == '1':
            per_list = defaultdict(list)
            is_contain_owner = False

            owners = self.get_json_item(file, "owners")
            if not self.is_none_or_empty(owners):
                for owner in owners:
                    email = self.get_json_item(owner, "emailAddress")
                    display_name = self.get_json_item(owner, "displayName")
                    if email is not None and len(email) > 0:
                        is_contain_owner = True
                        if "ALL" in self.google_user_list or email in self.google_user_list:
                            email = str(email).replace(BROADLEAF_EMAIL_SUFFIX, "").lower()
                            per_list["owner"].append("%s(%s)" % (email, "" if display_name is None else display_name))

            permissions = self.get_json_item(file, "permissions")
            if self.is_none_or_empty(permissions):
                file_detail.domain = ERR_SIGN
                file_detail.writer = ERR_SIGN
                file_detail.reader = ERR_SIGN
                if not is_contain_owner:
                    file_detail.owner = ERR_SIGN
                    err_info_list.append(TsvItemEnum.OWNER.value)
                else:
                    file_detail.owner = ",".join(per_list["owner"])
                err_info_list.append(TsvItemEnum.DOMAIN.value)
                err_info_list.append(ITEM_ACCESS_PERMISSION)
                self.set_account_record(self.login_email, self.login_name)
            else:
                for permission in permissions:
                    permission_type = self.get_json_item(permission, "type")
                    email = self.get_json_item(permission, "emailAddress")
                    display_name = self.get_json_item(permission, "displayName")
                    role = self.get_json_item(permission, "role")
                    view = self.get_json_item(permission, "view")
                    if role == "owner":
                        is_contain_owner = True

                    if view == "metadata":
                        continue

                    if not self.is_none_or_empty(email):
                        if permission_type != "anyone":
                            email = str(email).lower()
                            # record set account file count
                            self.set_account_record(email, display_name)

                            if "ALL" in self.google_user_list or email in self.google_user_list:
                                email = str(email).replace(BROADLEAF_EMAIL_SUFFIX, "")
                                user_info = "%s(%s)" % (email, "" if display_name is None else display_name)
                                if role == "owner":
                                    if user_info not in per_list["owner"]:
                                        per_list["owner"].append(user_info)
                                elif role == "writer":
                                    per_list["writer"].append(user_info)
                                elif role in ["reader", "commenter"]:
                                    per_list["reader"].append(user_info)

                    if permission_type == "domain":
                        per_list["domain"].append(display_name)

                if per_list.__contains__("domain"):
                    file_detail.domain = ",".join(per_list['domain'])
                else:
                    file_detail.domain = "制限付き"

                if len(per_list["owner"]) > 0 or is_contain_owner:
                    file_detail.owner = ",".join(per_list["owner"])
                else:
                    file_detail.owner = ERR_SIGN
                    err_info_list.append(TsvItemEnum.OWNER.value)
                file_detail.writer = ",".join(per_list["writer"])
                file_detail.reader = ",".join(per_list["reader"])

    def set_account_record(self, email, display_name):
        """
            record set account file count
        :param email:
        :param display_name:
        :return:
        """
        # set account is ALL, do not record set account
        if "ALL" in self.google_user_list or email is None:
            return

        with self.account_record_lock:
            # init dic
            if len(self.set_account_record_dic) == 0:
                for user in self.google_user_list:
                    self.set_account_record_dic[user] = {"count": 0, "name": None}

            # record set account
            if not email.__contains__("@"):
                email += BROADLEAF_EMAIL_SUFFIX
            if email in self.google_user_list:
                if not self.is_none_or_empty(display_name):
                    self.set_account_record_dic[email]["name"] = display_name
                self.set_account_record_dic[email]["count"] += 1

    def check_permission_denied(self, file_detail):
        if file_detail.owner is not None and str(file_detail.owner) != ERR_SIGN \
                and str(file_detail.writers_can_share).upper() == "FALSE":
            owned_by_me = False
            owner_list = re.split(',', file_detail.owner)
            for owner in owner_list:
                if self.is_none_or_empty(owner):
                    continue
                if '(' in owner:
                    index = owner.index('(')
                    owner = owner[:index]
                if self.login_email == owner:
                    owned_by_me = True
                    break
            if not owned_by_me:
                return True
        return False

    def get_children(self, parent_gid):
        """
        Get information under a folder by ID
        :param parent_gid:
        :return:Return information about the next level of the found folder
        """
        if self.struct_output_flg == '1':
            child_query = "\"" + parent_gid + "\"" + " in parents and trashed=false"
        else:
            child_query = "\"" + parent_gid + "\"" + \
                          " in parents and mimeType = 'application/vnd.google-apps.folder' and trashed=false"
        file_list = self.drive.list_file({"q": child_query, "fields": "nextPageToken,files(%s)" % PARAM})

        return file_list

    def research_result_display(self):
        """
            display google drive research result
        :return:
        """
        print()
        print(RESEARCH_RESULT)
        LogHelper.info(RESEARCH_RESULT)

        print(RESEARCH_TOTAL_COUNT % self.total_count)
        LogHelper.info(RESEARCH_TOTAL_COUNT % self.total_count)

        print(RESEARCH_FOLDER_COUNT % self.folder_count)
        LogHelper.info(RESEARCH_FOLDER_COUNT % self.folder_count)

        print(RESEARCH_FILE_COUNT % self.file_count)
        LogHelper.info(RESEARCH_FILE_COUNT % self.file_count)

        print(RESEARCH_WARN_COUNT % self.warn_count)
        LogHelper.info(RESEARCH_WARN_COUNT % self.warn_count)

        print(RESEARCH_ERR_COUNT % self.err_count)
        LogHelper.info(RESEARCH_ERR_COUNT % self.err_count)

        # (set account) is ALL
        if len(self.set_account_record_dic) == 0:
            return

        # (set account) research info display
        print(ACCOUNT_SET_COUNT % len(self.set_account_record_dic))
        LogHelper.info(ACCOUNT_SET_COUNT % len(self.set_account_record_dic))

        format_account_info_list, max_length = self.get_format_set_account_list()
        for account_info in format_account_info_list:
            account_research_info = ACCOUNT_FILE_COUNT % (
                account_info["account"] + " " * (max_length - account_info["name_len"]), account_info["file_count"])
            print(account_research_info)
            LogHelper.info(account_research_info)

    def get_format_set_account_list(self):
        max_length = 0
        format_account_info_list = []

        for email in self.set_account_record_dic:
            count = self.set_account_record_dic[email]["count"]
            name = self.set_account_record_dic[email]["name"]
            format_account = "%s(%s)" % (email, "????" if name is None else name)
            length = self.display_width(format_account)
            format_account_info_list.append({"account": format_account, "file_count": count, "name_len": length})
            max_length = max(length, max_length)

        return format_account_info_list, max_length

    @staticmethod
    def display_width(text):
        width = 0
        for ch in text:
            width += 2 if unicodedata.east_asian_width(ch) in ("F", "W") else 1
        return width

    @staticmethod
    def get_json_item(json_dic, item_name):
        """
        get the item of specified {item_name} in the {json_dic}
        :param json_dic:
        :param item_name:
        :return:
        """
        if json_dic is None or item_name not in json_dic:
            return None

        return json_dic[item_name]

    @staticmethod
    def is_none_or_empty(data):
        """
        check the {data} if {None} or {empty}
        :param data:
        :return:
        """
        if data is None:
            return True

        if isinstance(data, (str, list, dict, set, tuple)) and len(data) == 0:
            return True

        return False
