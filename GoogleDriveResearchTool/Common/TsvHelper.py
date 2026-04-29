import csv

from Common.TsvItemEnum import TsvItemEnum

TSV_WRITE_ERR = "TSVファイル「%s」の書き込みに失敗しました,エラー情報:%s"
fieldnames = list(kv.value for kv in TsvItemEnum)


def write_to_tsv(file, line):
    """
        Write content to txt
    :param file:
    :param line:
    :return:
    """
    try:

        csv_writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter='\t',
                                    extrasaction='ignore')
        csv_writer.writerow(line)
    except Exception as e:
        raise Exception(TSV_WRITE_ERR % (file.name, e))


def write_title(file_path):
    """
        write
    :param file_path:
    :return:
    """
    try:
        with open(file_path, 'w', encoding='UTF-8', newline="", errors='ignore') as file:
            # csv_writer = csv.writer(file, delimiter='\t')
            # csv_writer.writerow(kv.value for kv in TsvItemEnum)
            csv_writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter='\t',
                                        extrasaction='ignore')
            csv_writer.writeheader()
    except Exception as e:
        raise Exception(TSV_WRITE_ERR % (file_path, e))
