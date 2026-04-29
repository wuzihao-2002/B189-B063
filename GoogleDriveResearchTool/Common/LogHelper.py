import datetime
import logging
import os

logger: logging.Logger
warnLogger: logging.Logger
errorLogger: logging.Logger


def logger_init():
    """
        create logging instance
    :return:
    """
    global logger, warnLogger, errorLogger

    str_date = datetime.datetime.now().strftime('%Y%m%d')
    logger = _logger_init(str_date, logging.DEBUG)
    warnLogger = _logger_init(f"warn_{str_date}", logging.WARNING, "ResearchTool_warn")
    errorLogger = _logger_init(f"error_{str_date}", logging.ERROR, "ResearchTool_error")


def _logger_init(file_suffix_name, level, logger_name=None):
    log_path = os.path.join(os.path.abspath("."), "Log")
    os.makedirs(log_path, exist_ok=True)

    _logger = logging.getLogger(logger_name)
    fh = logging.FileHandler("Log\\GoogleDriveResearchTool_%s.log" % file_suffix_name,
                             encoding="utf-8", mode="a")
    formatter = logging.Formatter('%(asctime)s  %(name)s ThreadID(%(thread)s) %(levelname)s: %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')
    fh.setFormatter(formatter)
    _logger.addHandler(fh)
    _logger.setLevel(level)
    _logger.name = "ResearchTool"

    return _logger


def set_level(level):
    if str(level) == "0":
        logger.setLevel(logging.INFO)
    elif str(level) == "1":
        logger.setLevel(logging.DEBUG)


def error(msg):
    logger.error(msg)


def err_logger_error(msg):
    errorLogger.error(msg)


def warn(msg):
    warnLogger.warning(msg)


def info(msg):
    logger.info(msg)


def debug(msg):
    logger.debug(msg)
