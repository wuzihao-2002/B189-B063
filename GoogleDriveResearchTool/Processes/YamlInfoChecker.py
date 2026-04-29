import os
import re
import traceback

from Common import LogHelper, YamlHelper

# SETTINGS YAML CHECK ERR
SETTINGS_NOT_EXISTS_ERR = "settings.yamlが存在しないです。"
SETTINGS_CREDENTIALS_NOT_SPECIFIED_ERR = "Googleアカウント認証ファイルがありません、Googleアカウント認証ファイル作成手順を参照し作成してください。"
SETTINGS_CREDENTIALS_NOT_EXISTS_ERR = "yamlファイルに設定したGoogleアカウント認証ファイルが見つかりませんでした、Googleアカウント認証ファイル作成手順を参照し作成してください。"
SETTINGS_CREDENTIALS_KEY_NOT_SPECIFIED_ERR = "Googleアカウント認証ファイル復号化キーがありません、Googleアカウント認証ファイル作成手順を参照し作成してください。"
SETTINGS_CREDENTIALS_KEY_NOT_EXISTS_ERR = "yamlファイルに設定したGoogleアカウント認証ファイル復号化キーが見つかりませんでした、Google" \
                                          "アカウント認証ファイル作成手順を参照し作成してください。"

# CONFIG YAML CHECK ERR
RESEARCH_NOT_EXISTS_ERR = "調査対象の設定ファイル「GoogleDriveResearchTool.yaml」が見つかりませんでした。調査対象フォルダの情報を設定してください。"
RESEARCH_URI_NOT_SPECIFIED_ERR = "調査対象フォルダのGoogle File URIをyamlファイルに設定してください。"
RESEARCH_URI_FORMAT_ERR = "設定された「GoogleFileURI」はGoogle Drive ファイルIDではありません。ご確認ください。"
RESEARCH_URI_NOT_EXISTS_ERR = "「GoogleFileURI」が存在しない。"
RESEARCH_URI_TRASHED_ERR = "「GoogleFileURI」はゴミ箱にある。"
RESEARCH_USER_ACCOUNT_FORMAT_ERR = "調査対象アカウント「%s」はメール形式ではないです。"
RESEARCH_USER_ACCOUNT_NOT_SPECIFIED_ERR = "調査対象アカウント限定なしの場合、[All]を指定してください。"
RESEARCH_USER_ACCOUNT_SPECIFIED_ERR = "All(調査対象アカウント限定なし)で設定ありけど、他のアカウント設定もありました。調査対象アカウント限定なしにすると、[All]だけを指定してください。"
RESEARCH_OUTPUT_FILE_FORMAT_ERR = "調査結果出力バス設定に間違いがあります。ご確認ください。"
RESEARCH_TERMINAL_FOLDER_URI_NOT_SPECIFIED_ERR = "「GoogleDriveResearchTool.yaml」に「IP_X.TXT」の保存場所「RunningTerminalFile_URI」を設定してください。"
RESEARCH_TERMINAL_FOLDER_URI_FORMAT_ERR = "「GoogleDriveResearchTool.yaml」に設定された「IP_X.TXT」の保存場所「RunningTerminalFile_URI」が不正です。ご確認ください。"
RESEARCH_TERMINAL_FOLDER_URI_NOT_EXISTS = "「RunningTerminalFile_URI」が存在しない。"
RESEARCH_TERMINAL_FOLDER_URI_TRASHED_ERR = "「RunningTerminalFile_URI」はゴミ箱にある。"
RESEARCH_TERMINAL_FOLDER_URI_MIMETYPE_ERR = "「RunningTerminalFile_URI」にGoogle フォルダのURIを設定してください。"
RESEARCH_TERMINAL_FOLDER_URI_PERMISSION_ERR = "Googleアカウントを「RunningTerminalFile_URI」の編集権限に追加してください。"

NETWORK_TIMEOUT_ERR = "タイムアウトが発生しました。"

# CONFIG YAML INFO CHECK
FOLDER_URI_CHECK_REGEX = r"^https://drive\.google\.com/drive/(\S*)folders/(.+)$"
FILE_URI_CHECK_REGEX = r"^^https://(drive\.google\.com/file|docs\.google\.com/document)/d/(.+)$"
EMAIL_CHECK_REGEX = r"^\w+([-+.]\w+)*@\w+([-.]\w+)*\.\w+([-.]\w+)*$"
TSV_FILE_CHECK_REGEX = r"(.+)\.tsv$"

# YAML INFO GET
INFO_GET_START_LOG = "YAMLファイル設定情報を取得します"
INFO_GET_END_LOG = "YAMLファイル設定情報を取得しました"

# YAML INFO SHOW MSG
RESEARCH_INFO_SHOW_MSG = "実行情報:"
RESEARCH_INFO_URI_SHOW_MSG = "・調査対象フォルダ:"
RESEARCH_INFO_USER_SHOW_MSG = "・調査対象ユーザー:"
RESEARCH_INFO_ACCESS_USER_EXPORT_MSG = "・フォルダアクセスユーザー情報出力:"
RESEARCH_INFO_ACCESS_USER_EXPORT_SHOW_MSG = "   アクセスユーザー情報出力"
RESEARCH_INFO_ACCESS_USER_NOT_EXPORT_SHOW_MSG = "   アクセスユーザー情報出力しない"
RESEARCH_INFO_STRUCT_OUTPUT_MSG = "・出力対象:"
RESEARCH_INFO_FOLDER_FILE_OUTPUT_SHOW_MSG = "   フォルダとファイル共に"
RESEARCH_INFO_FOLDER_OUTPUT_SHOW_MSG = "   フォルダだけ"
RESEARCH_INFO_OUTPUT_FILE_SHOW_MSG = "・調査結果ファイル出力バス:"
RESEARCH_INFO_MAX_THREADS_PROJECTID_MSG = "・合計スレッド数制限:"
RESEARCH_INFO_RUNNING_TERMINAL_FILE_URI_MSG = "・「IP_n.txt」を保存URI:"
RESEARCH_INFO_MAX_THREADS_TERMINAL_MSG = "・最大スレッド数制限:"
RESEARCH_INFO_TERMINAL_FILE_UPDATE_SCHEDULE_MSG = "・「IP_n.txt」更新計画(min):"

# YAML PARAMETER
PARAM_GOOGLE_FILE_URI = "GoogleFileURI"
PARAM_USER_ACCOUNT = "UserAccount"
PARAM_ACCESS_USER_EXPORT = "AccessUserExport"
PARAM_STRUCT_OUTPUT_MODE = "StructOutputMode"
PARAM_OUTPUT_FILE_PATH = "OutPutFilePath"
PARAM_LOG_LEVEL = "log_level"
# PARAM_MAX_USER_ACCOUNTS_URI = "MaxUserAccountsURI"
PARAM_MAX_THREADS_TERMINAL = "MaxThreads_Terminal"
PARAM_MAX_THREADS_PROJECTID = "MaxThreads_ProjectID"
PARAM_RUNNING_TERMINAL_FILE_URI = "RunningTerminalFile_URI"
PARAM_TERMINAL_FILE_UPDATE_SCHEDULE = "TerminalFileUpdateSchedule"

# DEFAULT VALUE
RESEARCH_DEFAULT_USER_ACCOUNT = "ALL"
RESEARCH_DEFAULT_ACCESS_USER_EXPORT = "0"
RESEARCH_DEFAULT_STRUCT_OUTPUT_MODE = "0"
RESEARCH_DEFAULT_OUTPUT_FILE_PATH = "調査結果.tsv"
BROADLEAF_EMAIL_SUFFIX = "@broadleaf.co.jp"

# SETTINGS YAML PARAMETER
SETTINGS_PARAM_CREDENTIALS = "save_credentials_file"
SETTINGS_PARAM_CREDENTIALS_KEY = "save_credentials_privatekey_file"
# SETTINGS YAML DEFAULT VALUE
SETTINGS_DEFAULT_CREDENTIALS_FILE = "saved_credentials.json"
SETTINGS_DEFAULT_CREDENTIALS_KEY_FILE = "privatekey_saved_credentials.bin"


class YamlInfoChecker:

    def __init__(self, settings_path, research_path):
        self.settings_path = settings_path
        self.research_path = research_path

    def exists_chk(self):
        """
            settings.yaml and GoogleDriveResearchTool.yaml exists check
        :return:
        """
        chk_result = []
        # settings.yaml exists check
        if not YamlHelper.yaml_exists(self.settings_path):
            chk_result.append(SETTINGS_NOT_EXISTS_ERR)
        # GoogleDriveResearchTool.yaml check
        if not YamlHelper.yaml_exists(self.research_path):
            chk_result.append(RESEARCH_NOT_EXISTS_ERR)

        if len(chk_result):
            raise Exception("\n".join(chk_result))

    def read(self):
        """
            read settings.yaml and GoogleDriveResearchTool.yaml content
        :return:
        """
        LogHelper.info(INFO_GET_START_LOG)

        settings_info_dic = YamlHelper.yaml_read(self.settings_path)
        if settings_info_dic is None:
            settings_info_dic = {}

        google_folder_info_dic = YamlHelper.yaml_read(self.research_path)
        if google_folder_info_dic is None:
            google_folder_info_dic = {}

        LogHelper.info(INFO_GET_END_LOG)

        return settings_info_dic, google_folder_info_dic

    def info_chk(self, settings_info_dic, research_info_dic):
        """
            check settings.yaml and GoogleDriveResearchTool.yaml content
        :return:
        """
        self.settings_info_chk(settings_info_dic)
        self.google_folder_info_chk(research_info_dic)

    def settings_info_chk(self, settings_info_dic):
        """
            settings.yaml and GoogleDriveResearchTool.yaml content check
        :param settings_info_dic:
        :return:
        """
        chk_result = []

        credentials_chk_result = self.credentials_chk(settings_info_dic)
        if credentials_chk_result is not None:
            chk_result.append(credentials_chk_result)

        secrets_chk_result = self.secrets_chk(settings_info_dic)
        if secrets_chk_result is not None:
            chk_result.append(secrets_chk_result)

        if len(chk_result) > 0:
            raise Exception("\n".join(chk_result))

    def google_folder_info_chk(self, google_folder_info_dic):
        """
            check config yaml
        :param google_folder_info_dic
        :return:
        """
        chk_result = []

        # 調査対象フォルダ
        uri_chk_result = self.google_file_uri_chk(google_folder_info_dic)
        if len(uri_chk_result) > 0:
            chk_result.extend(uri_chk_result)

        # 調査対象ユーザー
        account_chk_result = self.user_account_chk(google_folder_info_dic)
        if len(account_chk_result) > 0:
            chk_result.extend(account_chk_result)

        # フォルダアクセスユーザー情報出力
        self.output_mode_chk(google_folder_info_dic, PARAM_ACCESS_USER_EXPORT)
        # 出力対象
        self.output_mode_chk(google_folder_info_dic, PARAM_STRUCT_OUTPUT_MODE)

        # 調査結果ファイル出力バス
        output_file_chk_result = self.output_file_path_chk(google_folder_info_dic)
        if len(output_file_chk_result) > 0:
            chk_result.extend(output_file_chk_result)

        # ログレベル
        self.log_level_chk(google_folder_info_dic)

        # すべての端末で使用可能なスレッド数と制限
        self.max_threads_projectid_chk(google_folder_info_dic)

        # 端末ファイル「IP_n.txt」の保存場所
        terminal_folder_uri_chk_result = self.terminal_folder_uri_chk(google_folder_info_dic)
        if len(terminal_folder_uri_chk_result) > 0:
            chk_result.extend(terminal_folder_uri_chk_result)

        # 自端末で使用可能な最大スレッド数
        self.max_threads_terminal_chk(google_folder_info_dic)

        # 「IP_n.txt」更新計画(min)
        self.terminal_file_update_schedule_chk(google_folder_info_dic)

        if len(chk_result) > 0:
            raise Exception("\n".join(chk_result))

    @staticmethod
    def credentials_chk(settings_info_dic):
        """
            Googleｱｶｳﾝﾄ認証ﾌｧｲﾙ exists check
        :param settings_info_dic:
        :return:
        """
        chk_result = None
        specified = True

        if not settings_info_dic.__contains__(SETTINGS_PARAM_CREDENTIALS) \
                or settings_info_dic[SETTINGS_PARAM_CREDENTIALS] is None \
                or len(str(settings_info_dic[SETTINGS_PARAM_CREDENTIALS]).strip()) == 0:
            specified = False
            # default value
            settings_info_dic[SETTINGS_PARAM_CREDENTIALS] = SETTINGS_DEFAULT_CREDENTIALS_FILE

        # exists check
        if not os.path.exists(settings_info_dic[SETTINGS_PARAM_CREDENTIALS]):
            if specified:
                chk_result = SETTINGS_CREDENTIALS_NOT_EXISTS_ERR
            else:
                chk_result = SETTINGS_CREDENTIALS_NOT_SPECIFIED_ERR

        return chk_result

    @staticmethod
    def secrets_chk(settings_info_dic):
        """
            Googleｱｶｳﾝﾄ認証ﾌｧｲﾙ復号化キー  exists check
        :param settings_info_dic:
        :return:
        """
        chk_result = None
        specified = True

        if not settings_info_dic.__contains__(SETTINGS_PARAM_CREDENTIALS_KEY) \
                or settings_info_dic[SETTINGS_PARAM_CREDENTIALS_KEY] is None \
                or len(str(settings_info_dic[SETTINGS_PARAM_CREDENTIALS_KEY]).strip()) == 0:
            specified = False
            # default value
            settings_info_dic[SETTINGS_PARAM_CREDENTIALS_KEY] = SETTINGS_DEFAULT_CREDENTIALS_KEY_FILE

        # exists check
        if not os.path.exists(settings_info_dic[SETTINGS_PARAM_CREDENTIALS_KEY]):
            if specified:
                chk_result = SETTINGS_CREDENTIALS_KEY_NOT_EXISTS_ERR
            else:
                chk_result = SETTINGS_CREDENTIALS_KEY_NOT_SPECIFIED_ERR

        return chk_result

    @staticmethod
    def google_file_uri_chk(google_folder_info_dic):
        """
            check 調査対象フォルダ
            :specified,format,exists,google info
        :param google_folder_info_dic:
        :return:
        """
        chk_result = []
        # check format
        if not google_folder_info_dic.__contains__(PARAM_GOOGLE_FILE_URI) \
                or google_folder_info_dic[PARAM_GOOGLE_FILE_URI] is None \
                or len(str(google_folder_info_dic[PARAM_GOOGLE_FILE_URI])) == 0:
            chk_result.append(RESEARCH_URI_NOT_SPECIFIED_ERR)
        else:
            value = google_folder_info_dic[PARAM_GOOGLE_FILE_URI]
            if isinstance(value, list):
                value = value[0]
                google_folder_info_dic[PARAM_GOOGLE_FILE_URI] = value

            if not re.match(FOLDER_URI_CHECK_REGEX, value.strip(), re.I):
                chk_result.append(RESEARCH_URI_FORMAT_ERR)

        return chk_result

    def user_account_chk(self, google_folder_info_dic):
        """
            check 調査対象ユーザー
        :param google_folder_info_dic:
        :return:
        """
        chk_result = []

        if not google_folder_info_dic.__contains__(PARAM_USER_ACCOUNT) \
                or google_folder_info_dic[PARAM_USER_ACCOUNT] is None:
            # default value
            chk_result.append(RESEARCH_USER_ACCOUNT_NOT_SPECIFIED_ERR)
        else:
            user_account_value = google_folder_info_dic[PARAM_USER_ACCOUNT]

            # user_account_value add to list
            user_account_list = self.user_account_list_get(user_account_value)

            # user account format check
            if len(user_account_list) == 0:
                chk_result.append(RESEARCH_USER_ACCOUNT_NOT_SPECIFIED_ERR)
            elif len(user_account_list) == 1 and str(user_account_list[0]).strip().upper() == "ALL":
                google_folder_info_dic[PARAM_USER_ACCOUNT] = "ALL"
            else:
                user_list = []
                for user in user_account_list:
                    if user is None or str(user).strip().upper() == "ALL":
                        chk_result.append(RESEARCH_USER_ACCOUNT_SPECIFIED_ERR)
                        continue

                    user_temp = str(user).strip()
                    if not re.match(EMAIL_CHECK_REGEX, user_temp, re.I):
                        chk_result.append(RESEARCH_USER_ACCOUNT_FORMAT_ERR % user_temp)

                    if len(chk_result) == 0:
                        user_list.append(user_temp)
                if len(chk_result) == 0:
                    google_folder_info_dic[PARAM_USER_ACCOUNT] = user_list

        return chk_result

    def user_account_list_get(self, user_account_value):
        user_account_list = []
        # get user account list
        if isinstance(user_account_value, list):
            for users in user_account_value:
                self.user_add_to_list(users, user_account_list)
        else:
            self.user_add_to_list(user_account_value, user_account_list)

        return user_account_list

    @staticmethod
    def user_add_to_list(users, user_account_list):
        """
            user_list add to user_account_list
        :param users:
        :param user_account_list:
        :return:
        """
        if users is None:
            return

        user_split_list = re.split(r'[,，]', str(users))
        for user in user_split_list:
            user_temp = str(user).strip().lower()
            if user_temp == "":
                continue

            if user_temp.upper() != "ALL" and not user_temp.__contains__("@"):
                user_temp += BROADLEAF_EMAIL_SUFFIX

            if not user_account_list.__contains__(user_temp):
                user_account_list.append(user_temp)

    @staticmethod
    def output_mode_chk(google_folder_info_dic, chk_key):
        """
            check フォルダアクセスユーザー情報出力 and 出力対象
        :param google_folder_info_dic:
        :param chk_key:
        :return:
        """
        if not google_folder_info_dic.__contains__(chk_key):
            google_folder_info_dic[chk_key] = "0"
        else:
            mode = google_folder_info_dic[chk_key]
            mode_value = "1"
            if isinstance(mode, list):
                if len(mode) == 0 or str(mode[0]).strip() != "1":
                    mode_value = "0"
            else:
                if str(mode).strip() != "1":
                    mode_value = "0"
            google_folder_info_dic[chk_key] = mode_value

    @staticmethod
    def output_file_path_chk(google_folder_info_dic):
        """
            check 調査結果ファイル出力バス
        :return:
        """
        chk_result = []

        # check specified
        if not google_folder_info_dic.__contains__(PARAM_OUTPUT_FILE_PATH) \
                or google_folder_info_dic[PARAM_OUTPUT_FILE_PATH] is None \
                or len(str(google_folder_info_dic[PARAM_OUTPUT_FILE_PATH]).strip()) == 0:
            google_folder_info_dic[PARAM_OUTPUT_FILE_PATH] = RESEARCH_DEFAULT_OUTPUT_FILE_PATH

        # check format
        output_file_path = str(google_folder_info_dic[PARAM_OUTPUT_FILE_PATH]).strip()
        if not re.match(TSV_FILE_CHECK_REGEX, output_file_path, re.I):
            chk_result.append(RESEARCH_OUTPUT_FILE_FORMAT_ERR)

        if len(chk_result) == 0:
            if not os.path.isabs(output_file_path):
                output_file_path = os.path.join(os.path.abspath("."), output_file_path)
            if not os.path.exists(output_file_path):
                try:
                    folder, file = os.path.split(output_file_path)
                    os.makedirs(folder, exist_ok=True)

                    f = open(output_file_path, "a")
                    f.close()
                except Exception as e:
                    LogHelper.error(e)
                    LogHelper.error(traceback.format_exc())
                    chk_result.append(RESEARCH_OUTPUT_FILE_FORMAT_ERR)

        return chk_result

    @staticmethod
    def log_level_chk(google_folder_info_dic):
        log_level = "1"
        # ログレベル
        if not google_folder_info_dic.__contains__(PARAM_LOG_LEVEL) \
                or google_folder_info_dic[PARAM_LOG_LEVEL] is None \
                or str(google_folder_info_dic[PARAM_LOG_LEVEL]).strip() != "1":
            log_level = "0"
        google_folder_info_dic[PARAM_LOG_LEVEL] = log_level

    def max_threads_terminal_chk(self, google_folder_info_dic):
        self.num_chk(google_folder_info_dic, PARAM_MAX_THREADS_TERMINAL, 32)

    def max_threads_projectid_chk(self, google_folder_info_dic):
        self.num_chk(google_folder_info_dic, PARAM_MAX_THREADS_PROJECTID, 100)

    def terminal_file_update_schedule_chk(self, google_folder_info_dic):
        self.num_chk(google_folder_info_dic, PARAM_TERMINAL_FILE_UPDATE_SCHEDULE, 30)

    def num_chk(self, google_folder_info_dic, chk_key, default_value):
        """
            check the number settings
        :param google_folder_info_dic:
        :param chk_key:
        :param default_value:
        :return:
        """
        if not google_folder_info_dic.__contains__(chk_key) \
                or google_folder_info_dic[chk_key] is None \
                or len(str(google_folder_info_dic[chk_key]).strip()) == 0:
            google_folder_info_dic[chk_key] = default_value
        else:
            value = google_folder_info_dic[chk_key]

            if isinstance(value, list):
                value = str(value[0]).strip()

            parse_flg, parse_value = self.int_parse(str(value).strip())
            if parse_flg and parse_value > 0:
                google_folder_info_dic[chk_key] = parse_value
            else:
                google_folder_info_dic[chk_key] = default_value

    @staticmethod
    def terminal_folder_uri_chk(google_folder_info_dic):
        """
            check the content set for [RunningTerminalFile_URI]
        :param google_folder_info_dic:
        :return:
        """
        chk_result = []
        # check format
        if not google_folder_info_dic.__contains__(PARAM_RUNNING_TERMINAL_FILE_URI) \
                or google_folder_info_dic[PARAM_RUNNING_TERMINAL_FILE_URI] is None \
                or len(str(google_folder_info_dic[PARAM_RUNNING_TERMINAL_FILE_URI]).strip()) == 0:
            # not specified
            chk_result.append(RESEARCH_TERMINAL_FOLDER_URI_NOT_SPECIFIED_ERR)
        else:
            value = google_folder_info_dic[PARAM_RUNNING_TERMINAL_FILE_URI]
            if isinstance(value, list):
                value = value[0]
                google_folder_info_dic[PARAM_RUNNING_TERMINAL_FILE_URI] = value

            if not re.match(FOLDER_URI_CHECK_REGEX, value.strip(), re.I):
                # does not match the regular expression
                chk_result.append(RESEARCH_TERMINAL_FOLDER_URI_FORMAT_ERR)

        return chk_result

    @staticmethod
    def int_parse(value):
        """
            convert value to integer
        :param value:
        :return:
        """
        parse_flg = True
        parse_value = -1

        try:
            parse_value = int(value)
        except ValueError:
            parse_flg = False

        return parse_flg, parse_value

    @staticmethod
    def google_folder_info_display(google_folder_info_dic):
        """
            display config yaml details
        :param google_folder_info_dic:
        """
        print()
        print(RESEARCH_INFO_SHOW_MSG)

        # 調査対象フォルダ
        print(RESEARCH_INFO_URI_SHOW_MSG)
        LogHelper.info(RESEARCH_INFO_URI_SHOW_MSG)
        print("   %s" % google_folder_info_dic[PARAM_GOOGLE_FILE_URI])
        LogHelper.info("   %s" % google_folder_info_dic[PARAM_GOOGLE_FILE_URI])

        # 調査対象ユーザー
        print(RESEARCH_INFO_USER_SHOW_MSG)
        LogHelper.info(RESEARCH_INFO_USER_SHOW_MSG)
        if 'ALL' in google_folder_info_dic[PARAM_USER_ACCOUNT]:
            print(" " * 3 + "ALL")
            LogHelper.info(" " * 3 + "ALL")
        else:
            for email in google_folder_info_dic[PARAM_USER_ACCOUNT]:
                print(" " * 3 + "\"%s\"" % email)
                LogHelper.info(" " * 3 + "\"%s\"" % email)

        # フォルダアクセスユーザー情報出力
        print(RESEARCH_INFO_ACCESS_USER_EXPORT_MSG)
        LogHelper.info(RESEARCH_INFO_ACCESS_USER_EXPORT_MSG)
        if str(google_folder_info_dic[PARAM_ACCESS_USER_EXPORT]).strip() == '0':
            print(RESEARCH_INFO_ACCESS_USER_NOT_EXPORT_SHOW_MSG)
            LogHelper.info(RESEARCH_INFO_ACCESS_USER_NOT_EXPORT_SHOW_MSG)
        else:
            print(RESEARCH_INFO_ACCESS_USER_EXPORT_SHOW_MSG)
            LogHelper.info(RESEARCH_INFO_ACCESS_USER_EXPORT_SHOW_MSG)

        # 出力対象
        print(RESEARCH_INFO_STRUCT_OUTPUT_MSG)
        LogHelper.info(RESEARCH_INFO_STRUCT_OUTPUT_MSG)
        if str(google_folder_info_dic[PARAM_STRUCT_OUTPUT_MODE]).strip() == '0':
            print(RESEARCH_INFO_FOLDER_OUTPUT_SHOW_MSG)
            LogHelper.info(RESEARCH_INFO_FOLDER_OUTPUT_SHOW_MSG)
        else:
            print(RESEARCH_INFO_FOLDER_FILE_OUTPUT_SHOW_MSG)
            LogHelper.info(RESEARCH_INFO_FOLDER_FILE_OUTPUT_SHOW_MSG)

        # 調査結果ファイル出力バス
        print(RESEARCH_INFO_OUTPUT_FILE_SHOW_MSG)
        LogHelper.info(RESEARCH_INFO_OUTPUT_FILE_SHOW_MSG)
        print("   %s" % google_folder_info_dic[PARAM_OUTPUT_FILE_PATH])
        LogHelper.info("   %s" % google_folder_info_dic[PARAM_OUTPUT_FILE_PATH])

        # すべての端末で使用可能なスレッド数と制限
        print(RESEARCH_INFO_MAX_THREADS_PROJECTID_MSG)
        LogHelper.info(RESEARCH_INFO_MAX_THREADS_PROJECTID_MSG)
        print("   %s" % google_folder_info_dic[PARAM_MAX_THREADS_PROJECTID])
        LogHelper.info("   %s" % google_folder_info_dic[PARAM_MAX_THREADS_PROJECTID])

        # 端末ファイル(IP_X.TXT)の保存場所
        print(RESEARCH_INFO_RUNNING_TERMINAL_FILE_URI_MSG)
        LogHelper.info(RESEARCH_INFO_RUNNING_TERMINAL_FILE_URI_MSG)
        print("   %s" % google_folder_info_dic[PARAM_RUNNING_TERMINAL_FILE_URI])
        LogHelper.info("   %s" % google_folder_info_dic[PARAM_RUNNING_TERMINAL_FILE_URI])

        # 当の端末で使用可能な最大スレッド数
        print(RESEARCH_INFO_MAX_THREADS_TERMINAL_MSG)
        LogHelper.info(RESEARCH_INFO_MAX_THREADS_TERMINAL_MSG)
        print("   %s" % google_folder_info_dic[PARAM_MAX_THREADS_TERMINAL])
        LogHelper.info("   %s" % google_folder_info_dic[PARAM_MAX_THREADS_TERMINAL])

        # (IP_X.TXT)更新計画(min)
        print(RESEARCH_INFO_TERMINAL_FILE_UPDATE_SCHEDULE_MSG)
        LogHelper.info(RESEARCH_INFO_TERMINAL_FILE_UPDATE_SCHEDULE_MSG)
        print("   %s" % google_folder_info_dic[PARAM_TERMINAL_FILE_UPDATE_SCHEDULE])
        LogHelper.info("   %s" % google_folder_info_dic[PARAM_TERMINAL_FILE_UPDATE_SCHEDULE])

    def research_folder_chk(self, folder_uri, google_drive):
        """
            check the research folder
        :param folder_uri:
        :param google_drive:
        :return:
        """
        gid = self.get_gid(folder_uri, True)

        try:
            file = google_drive.get_file_metadata(gid, "trashed")
            if file["trashed"]:
                raise Exception(RESEARCH_URI_TRASHED_ERR)
        except Exception as ex:
            ex_message = ex.__str__()
            if ex_message.upper().__contains__("NOT FOUND"):
                raise Exception(RESEARCH_URI_NOT_EXISTS_ERR)
            elif ex_message.upper().__contains__("TIMEOUT") or ex_message.upper().__contains__("応答しなかったため"):
                raise Exception(NETWORK_TIMEOUT_ERR)
            else:
                raise Exception(ex_message)

    def terminal_folder_chk(self, folder_uri, google_drive):
        """
            check the terminal folder
        :param folder_uri:
        :param google_drive:
        :return:
        """
        gid = self.get_gid(folder_uri, True)

        try:
            file = google_drive.get_file_metadata(gid, "trashed, mimeType, permissions")

            if file["trashed"]:
                raise Exception(RESEARCH_TERMINAL_FOLDER_URI_TRASHED_ERR)

            if file["mimeType"] != "application/vnd.google-apps.folder":
                raise Exception(RESEARCH_TERMINAL_FOLDER_URI_MIMETYPE_ERR)

            if not file.__contains__("permissions"):
                raise Exception(RESEARCH_TERMINAL_FOLDER_URI_PERMISSION_ERR)
        except Exception as ex:
            ex_message = ex.__str__()
            if ex_message.upper().__contains__("NOT FOUND"):
                raise Exception(RESEARCH_TERMINAL_FOLDER_URI_NOT_EXISTS)
            elif ex_message.upper().__contains__("TIMEOUT") or ex_message.upper().__contains__("応答しなかったため"):
                raise Exception(NETWORK_TIMEOUT_ERR)
            else:
                raise Exception(ex_message)

    @staticmethod
    def get_gid(google_uri, is_folder):
        """
            get google file id
        :param google_uri:
        :param is_folder:
        :return:
        """
        if is_folder:
            gid = re.findall(r"/folders/(.+)|$", google_uri.strip())[0]
        else:
            gid = re.findall(r'/d/(.+)|$', google_uri.strip())[0]

        if gid.__contains__("/"):
            gid = gid[: gid.index("/")]
        if gid.__contains__("?"):
            gid = gid[: gid.index("?")]
        return gid
