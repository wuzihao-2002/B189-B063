class ResearchFolder(object):
    id = None  # 自増id
    gid = None  # Google ファイル id
    parent_gid = None  # 親フォルダgid
    name = None  # Google フォルダ名
    uri = None  # フォルダURI

    def __init__(self):
        pass

    def set_values(self, record, mapper):
        """
            mapper: [field1 name: record index1, field2 name: record index2...]
        :param record:
        :param mapper:
        :return:
        """
        self.gid = record[mapper["gid"]]
        self.parent_gid = record[mapper["parent_gid"]]
        self.name = record[mapper["name"]]
        self.uri = record[mapper["uri"]]

    def get_values(self):
        values = [self.gid, self.parent_gid, self.name, self.uri]
        return values
