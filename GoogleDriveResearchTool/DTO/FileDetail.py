class FileDetail(object):
    id = None  # 自増id
    gid = None  # ファイル/フォルダgid
    parent_gid = None  # 親フォルダgid
    file = None  # ファイル
    type = None  # 種類
    last_update_date = None  # 最終更新年月日
    last_update_time = None  # 最終更新時間
    last_updater = None  # 最終更新者
    uri = None  # URI
    parent_folder = None  # 親フォルダ
    parent_uri = None  # 親URI
    writers_can_share = None  # 共有設定
    domain = None  # リンク設定
    owner = None  # Owner
    writer = None  # Editor
    reader = None  # Reader
    check_result = None  # 権限ﾁｪｯｸ結果
    setting_result = None  # 権限設定結果
    err_info = None  # ErrInfo

    def __init__(self):
        pass

    def set_values(self, record, mapper):
        """
            mapper: [field1 name: record index1, field2 name: record index2...]
        :param record:
        :param mapper:
        :return:
        """
        self.id = record[mapper["id"]]
        self.gid = record[mapper["gid"]]
        self.parent_gid = record[mapper["parent_gid"]]
        self.file = record[mapper["file"]]
        self.type = record[mapper["type"]]
        self.last_update_date = record[mapper["last_update_date"]]
        self.last_update_time = record[mapper["last_update_time"]]
        self.last_updater = record[mapper["last_updater"]]
        self.uri = record[mapper["uri"]]
        self.parent_folder = record[mapper["parent_folder"]]
        self.parent_uri = record[mapper["parent_uri"]]
        self.writers_can_share = record[mapper["writers_can_share"]]
        self.domain = record[mapper["domain"]]
        self.owner = record[mapper["owner"]]
        self.writer = record[mapper["writer"]]
        self.reader = record[mapper["reader"]]
        self.check_result = record[mapper["check_result"]]
        self.setting_result = record[mapper["setting_result"]]
        self.err_info = record[mapper["err_info"]]

    def get_values(self):
        values = [self.gid, self.parent_gid, self.file, self.type, self.last_update_date, self.last_update_time,
                  self.last_updater, self.uri, self.parent_folder, self.parent_uri, self.writers_can_share, self.domain,
                  self.owner, self.writer, self.reader, self.check_result, self.setting_result, self.err_info]
        return values
