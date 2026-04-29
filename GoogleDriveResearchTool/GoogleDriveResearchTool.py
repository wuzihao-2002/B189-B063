import os
import signal
import sys
from sys import exit

import psutil
from rich.prompt import Confirm

from Common import TsvHelper
from GoogleAPI.GoogleApiAuth import GoogleApiAuth
from Processes import YamlInfoChecker, DriveFilesInfoGet
from Processes.DriveFilesInfoGet import *
from Processes.ThreadPool.MaxThreadsAutoStat import MaxThreadsAutoStat

# MSG
LAUNCH_PARAMETER_COUNT_NG_MSG = "起動引数をご指定お願いいたします。"
LAUNCH_PARAMETER_GET_NG_MSG = "起動引数2（何番目）は正の整数で設定してください。"
OTHER_PROGRAM_LAUNCH_PARAMETER_GET_NG_MSG = "全体プログラムの起動引数の取得が失敗しました。"
HANDLER_FOLDER_IS_USED_MSG = "調査対象フォルダ「%s」は使用中です。"
RESEARCH_OK_END_MSG = "正常終了"
RESEARCH_NG_END_MSG = "異常終了"
RESEARCH_ABORT_END_MSG = "処理中止"
MULTIPLE_START_NG_MSG = "番号「%d」は使用中です。"
RESEARCHING_MSG = "ファイル情報取得中..."
RESEARCH_ABORTING_END_MSG = "処理中止中..."

# LOG
RESEARCH_START_LOG = "GoogleDriveファイル情報取得を開始します"
FOLDER_RESEARCH_START_LOG = "GoogleDriveにYAML指定したフォルダ情報を取得します"
FOLDER_RESEARCH_END_LOG = "GoogleDriveにYAML指定したフォルダ情報を取得しました。"
RESEARCH_OK_END_LOG = "GoogleDriveファイル情報取得が正常終了しました。"
RESEARCH_NG_END_LOG = "GoogleDriveファイル情報取得が異常終了しました。"
RESEARCH_ERR_LOG = "エラー情報: %s"

# TITLE
TITLE_TIPS = "提示"

SETTINGS_PATH = "AuthenticationConfig/settings.yaml"
DB_PATH = "GoogleDriveResearch.db"

gDrive: GoogleApiDriveService
creds = None
login_user = None

researchThreadPool = None
researchSqlite = None
researcher = None

signal_interrupt = False


def google_account_login():
    """
    Google authentication
    """
    global gDrive, creds, login_user
    auth = GoogleApiAuth(settings_info_dic[YamlInfoChecker.SETTINGS_PARAM_CREDENTIALS],
                         settings_info_dic[YamlInfoChecker.SETTINGS_PARAM_CREDENTIALS_KEY])
    creds = auth.login()

    gDrive = GoogleApiDriveService(creds)

    login_user = gDrive.about("user")


def drive_file_info_get():
    """
        Get the URL specified file structure
    """
    # 開始ログ出力
    LogHelper.info(FOLDER_RESEARCH_START_LOG)

    print()
    print(RESEARCHING_MSG)

    # global gid
    # Get the GID of the URL
    gid = yaml_checker.get_gid(google_folder_uri, True)

    # 調査結果ファイルにヘッダ行出力
    TsvHelper.write_title(output_path)

    # 調査対象フォルダの構造とアクセスユーザー情報取得
    researcher.file_structure_info_get(gid, google_user_list, permissions_output_flg, struct_output_flg)
    LogHelper.info(FOLDER_RESEARCH_END_LOG)

    LogHelper.debug("save to tsv begin")
    # 調査対象フォルダの構造とアクセスユーザー情報出力
    researcher.file_structure_info_save(gid, output_path)
    LogHelper.debug("save to tsv end")


def yaml_info_chk():
    """
        check settings.yaml and GoogleDriveResearchTool.yaml
    :return:
    """
    global yaml_checker, settings_info_dic, google_folder_info_dic
    yaml_checker = YamlInfoChecker.YamlInfoChecker(SETTINGS_PATH, google_folder_info_path)
    yaml_checker.exists_chk()
    settings_info_dic, google_folder_info_dic = yaml_checker.read()
    yaml_checker.info_chk(settings_info_dic, google_folder_info_dic)


def yaml_info_get():
    """
        get information
    :return:
    """
    global google_folder_uri, google_user_list, permissions_output_flg, \
        struct_output_flg, output_path, log_level, max_threads_projectid, \
        max_threads_terminal, max_threads_terminal, update_schedule, \
        running_terminal_file_uri, terminal_folder_gid

    # 調査対象フォルダのGoogle Folder URI:
    google_folder_uri = str(google_folder_info_dic[YamlInfoChecker.PARAM_GOOGLE_FILE_URI]).strip()
    # 調査対象ユーザーリスト　ALL/リスト
    google_user_list = google_folder_info_dic[YamlInfoChecker.PARAM_USER_ACCOUNT]
    # アクセスユーザー一覧出力か否か
    permissions_output_flg = str(google_folder_info_dic[YamlInfoChecker.PARAM_ACCESS_USER_EXPORT]).strip()
    # フォルダだけか、ファイルも出力するかのフラグ
    struct_output_flg = str(google_folder_info_dic[YamlInfoChecker.PARAM_STRUCT_OUTPUT_MODE]).strip()
    # 調査結果出力パス
    output_path = str(google_folder_info_dic[YamlInfoChecker.PARAM_OUTPUT_FILE_PATH]).strip()
    # ログレベル
    log_level = google_folder_info_dic[YamlInfoChecker.PARAM_LOG_LEVEL]
    # すべての端末で使用可能なスレッド数と制限
    max_threads_projectid = google_folder_info_dic[YamlInfoChecker.PARAM_MAX_THREADS_PROJECTID]
    # 当の端末で使用可能な最大スレッド数
    max_threads_terminal = google_folder_info_dic[YamlInfoChecker.PARAM_MAX_THREADS_TERMINAL]
    # 「IP_X.TXT」更新計画
    update_schedule = google_folder_info_dic[YamlInfoChecker.PARAM_TERMINAL_FILE_UPDATE_SCHEDULE]
    # 端末ファイル(IP_X.TXT)の保存場所(Google Folder URI)
    running_terminal_file_uri = str(google_folder_info_dic[YamlInfoChecker.PARAM_RUNNING_TERMINAL_FILE_URI]).strip()
    # 端末ファイル(IP_X.TXT)の保存場所(Google Folder URI)のgid
    terminal_folder_gid = yaml_checker.get_gid(running_terminal_file_uri, True)


def int_parse(value):
    _parse_flg = True
    _parse_value = -1
    try:
        _parse_value = int(value)
    except ValueError:
        _parse_flg = False

    return _parse_flg, _parse_value


def launch_parameter_chk():
    """
    入力パラメータを取得する
    :rtype: object
    """
    # check the number of parameters
    len_argv = len(sys.argv)
    if len_argv == 2 or len_argv == 3:
        for argv in sys.argv:
            print(argv, end=" ")
        print()

        # check terminal order
        _terminal_order = 1
        if len_argv == 3:
            _terminal_order = sys.argv[2]
            parse_flg, parse_value = int_parse(_terminal_order)
            if not parse_flg or parse_value <= 0:
                raise Exception(LAUNCH_PARAMETER_GET_NG_MSG)
            _terminal_order = parse_value

        return sys.argv[1], _terminal_order
    else:
        raise Exception(LAUNCH_PARAMETER_COUNT_NG_MSG)


def other_program_launch_parameter_get():
    """
        retrieve the launch parameter of other program
    :return:
    """
    launch_param_set = set()

    try:
        for proc in psutil.process_iter(['name', 'pid', 'cmdline']):
            try:
                proc_info = proc.info
                proc_pid = proc_info['pid']
                proc_name = proc_info['name']
                proc_cmdline = proc_info['cmdline']

                if proc_pid == pid or proc_pid == ppid:
                    continue

                if proc_cmdline is not None and proc_name in ["GoogleDriveResearchTool.exe",
                                                              "GoogleDrivePermissionSettingTool.exe"]:
                    launch_param_set.add(tuple(proc_cmdline))
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        return launch_param_set
    except Exception as ex:
        LogHelper.error(ex)
        LogHelper.error(traceback.format_exc())
        raise Exception(OTHER_PROGRAM_LAUNCH_PARAMETER_GET_NG_MSG)


def is_continue_execution(_terminal_order):
    """
        if there is already a program with the same launch parameter order num in the current terminal,
            terminate the current program
        otherwise
            continue execution
    :param _terminal_order:
    :return:
    """
    launch_param_set = other_program_launch_parameter_get()

    for launch_param in launch_param_set:
        # get order num
        if len(launch_param) == 2:
            order_num = 1
        elif len(launch_param) == 3:
            parse_flg, order_num = int_parse(launch_param[2])
            if not parse_flg:
                continue
        else:
            continue

        # check if the order num has already been used
        if _terminal_order == order_num:
            return False

    return True


def create_researcher(_thread_count):
    """
        initial google drive file info researcher
    :param _thread_count:
    :return:
    """
    global researchThreadPool, researchSqlite, researcher
    researchThreadPool = ResearchThreadPool(max_workers=_thread_count)
    researchSqlite = ResearchSQLite(DB_PATH)
    researchSqlite.init_db()
    researcher = GoogleDriveFolderIterator(login_user, gDrive, researchThreadPool, researchSqlite)


def on_exit(signum, frame):
    """
        catch [Ctrl + C] command
    :param signum:
    :param frame:
    :return:
    """
    global signal_interrupt

    if researchThreadPool is None or researchSqlite is None:
        return

    signal.signal(signal.SIGINT, signal.SIG_DFL)
    signal.signal(signal.SIGTERM, signal.SIG_DFL)
    ask_result = Confirm.ask("中止しますか?")
    if ask_result:
        signal_interrupt = True
        print(RESEARCH_ABORTING_END_MSG)
        if researchThreadPool is not None:
            researchThreadPool.stop_task()
        if researchSqlite is not None:
            researchSqlite.stop_task()
    else:
        print(RESEARCHING_MSG)
        signal_interrupt = False
        signal.signal(signal.SIGINT, on_exit)
        signal.signal(signal.SIGTERM, on_exit)


if __name__ == "__main__":
    threads_auto_stat = None

    try:
        # ログを出力する
        LogHelper.logger_init()
        LogHelper.info(RESEARCH_START_LOG)

        # 入力パラメータを取得する
        google_folder_info_path, terminal_order = launch_parameter_chk()
        pid = os.getpid()
        ppid = os.getppid()

        # 二重起動チェック
        if not is_continue_execution(terminal_order):
            print()
            print(MULTIPLE_START_NG_MSG % terminal_order)
            LogHelper.info(MULTIPLE_START_NG_MSG % terminal_order)
            exit(0)

        # signal [Ctrl+C] catch
        signal.signal(signal.SIGINT, on_exit)
        signal.signal(signal.SIGTERM, on_exit)

        # 配置ファイル、Google Driveに調査対象フォルダ設定Yamlファイルのチェック
        yaml_info_chk()
        yaml_info_get()

        # ログレベルの設定
        LogHelper.set_level(log_level)

        # Googleｱｶｳﾝﾄ認証ﾌｧｲﾙ
        google_account_login()

        # 調査対象フォルダはゴミ箱にあるかをチェック
        yaml_checker.research_folder_chk(google_folder_uri, gDrive)
        yaml_checker.terminal_folder_chk(running_terminal_file_uri, gDrive)

        # the console display yaml file's information
        yaml_checker.google_folder_info_display(google_folder_info_dic)

        # calculate thread count by google file
        threads_auto_stat = MaxThreadsAutoStat(gDrive, terminal_folder_gid, update_schedule,
                                               max_threads_terminal, max_threads_projectid, terminal_order,
                                               google_folder_uri)

        # remove the expired terminal files with same IP and create a new terminal file
        threads_auto_stat.init_terminal_file()

        # Verify if the handler folder is being used
        if threads_auto_stat.handler_folder_is_used():
            print()
            print(HANDLER_FOLDER_IS_USED_MSG % google_folder_uri)
            LogHelper.info(HANDLER_FOLDER_IS_USED_MSG % google_folder_uri)
            exit(0)

        # calculate the number of threads using terminal file
        thread_count = threads_auto_stat.init_thread_count()

        # create instance
        create_researcher(thread_count)

        # Scheduled thread pool update.
        threads_auto_stat.schedule_run(researchThreadPool)

        # google drive file info get
        drive_file_info_get()

        # research result
        researcher.research_result_display()

        print()

        if signal_interrupt:
            print(RESEARCH_ABORT_END_MSG)
            LogHelper.info(RESEARCH_ABORT_END_MSG)
        else:
            if researcher.err_count > 0 or researcher.failed_count > 0 or DriveFilesInfoGet.exception_interrupt:
                print(RESEARCH_NG_END_MSG)
                LogHelper.info(RESEARCH_NG_END_LOG)
            else:
                print(RESEARCH_OK_END_MSG)
                LogHelper.info(RESEARCH_OK_END_LOG)

    except Exception as e:
        print()
        print(e)
        print(RESEARCH_NG_END_MSG)
        LogHelper.error(RESEARCH_NG_END_LOG)
        LogHelper.error(RESEARCH_ERR_LOG % e)
        LogHelper.error(traceback.format_exc())

    finally:
        # after program end, remove the current terminal file
        if threads_auto_stat is not None:
            threads_auto_stat.remove_terminal_file()
