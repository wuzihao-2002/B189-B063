import queue
import sqlite3
import threading
import traceback
from time import sleep

from Common import TsvHelper, LogHelper
from Common.TsvItemEnum import TsvItemEnum
from DTO.FileDetail import FileDetail
from DTO.ResearchFolder import ResearchFolder
from Processes import DriveFilesInfoGet
from Processes.SqliteDB import SqlCommand


class ResearchSQLite:

    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.research_exit = False
        self.commit_thread = None
        self.research_folder_mapper = None

    def init_db(self):
        init_command = SqlCommand.drop_tbl_file_detail_sql
        init_command += SqlCommand.create_tbl_file_detail_sql
        init_command += SqlCommand.drop_tbl_research_folder_sql
        init_command += SqlCommand.create_tbl_research_folder_sql
        init_command += SqlCommand.vacuum_sql

        self.conn.executescript(init_command)

    def re_init(self):
        self.conn.close()
        self.__init__(db_path=self.db_path)

    def save_data(self, data):
        """
            save google drive file info to sqlite
        :param data:
        :return:
        """
        try:
            if data is not None:
                if isinstance(data, FileDetail):
                    insert_sql = SqlCommand.insert_file_detail_sql
                else:
                    insert_sql = SqlCommand.insert_research_folder_sql
                self.conn.execute(insert_sql, data.get_values())
        except Exception as e:
            LogHelper.error("Sqlite insert Err:%s" % e)
            LogHelper.error(traceback.format_exc())
            DriveFilesInfoGet.exception_interrupt = True

    def research_folder_iterator(self, gt_id):
        """
            get google folder info
        :param gt_id:
        :return:
        """
        try:
            gt_id_select_sql = SqlCommand.select_research_folder_by_id_gt_sql
            cursor = self.conn.execute(gt_id_select_sql, [gt_id])
            if self.research_folder_mapper is None and cursor.description is not None:
                self.research_folder_mapper = self.get_cursor_mapper(cursor.description)

            for record in cursor:
                if self.research_exit:
                    return
                research_folder = ResearchFolder()
                research_folder.set_values(record, self.research_folder_mapper)
                yield research_folder
        except Exception as e:
            LogHelper.error("Sqlite research Err:%s" % e)
            LogHelper.error(traceback.format_exc())
            DriveFilesInfoGet.exception_interrupt = True

    def research_folder_record_count(self):
        max_id_select_sql = SqlCommand.select_research_folder_max_id_sql
        cursor = self.conn.execute(max_id_select_sql)
        record = cursor.fetchone()
        return record[0]

    def commit(self):
        self.conn.commit()

    def _auto_commit(self, second):
        """
            interval point second commit
        :param second:
        :return:
        """
        try:
            while True:
                sleep(second)
                if self.research_exit:
                    return

                self.commit()
        except Exception as e:
            LogHelper.error("Sqlite commit Err:%s" % e)
            LogHelper.error(traceback.format_exc())
            DriveFilesInfoGet.exception_interrupt = True

    def auto_commit(self):
        """
            task [save_worker] [research_worker] begin
        :return:
        """
        self.commit_thread = threading.Thread(target=self._auto_commit, args={10})
        self.commit_thread.setDaemon(True)
        self.commit_thread.start()

    def stop_task(self):
        """
            stop task
        :return:
        """
        self.research_exit = True

    def close(self):
        """
            close
        :return:
        """
        self.stop_task()

        self.conn.close()

    def file_info_to_tsv(self, gid, output_file):
        """
            write google file info to tsv
        :param gid:
        :param output_file:
        :return:
        """
        series_queue = queue.LifoQueue()
        # get folder info
        cursor = self.conn.execute(SqlCommand.select_file_detail_by_gid_eq_sql, [gid])
        mapper = self.get_cursor_mapper(cursor.description)
        folder_info_record = cursor.fetchone()

        if folder_info_record is None:
            return

        folder_info_dict = self.record_to_write_dict(folder_info_record, mapper, 0)
        TsvHelper.write_to_tsv(output_file, folder_info_dict)

        # folder structure series down
        parent_gid = folder_info_record[mapper["parent_gid"]]
        # queue item: (gid, parent_gid, output order in parent folder)
        series_queue.put((gid, parent_gid, 0))

        # loop folder series queue
        while series_queue.qsize() > 0:
            folder_info = series_queue.get()
            series_queue.put(folder_info)

            folder_gid = folder_info[0]

            # output sub file info
            cursor = self.conn.execute(SqlCommand.select_subFileInfo_by_parentGid_sql, [folder_gid])
            for file_info in cursor:
                file_info_dict = self.record_to_write_dict(file_info, mapper, series_queue.qsize())
                TsvHelper.write_to_tsv(output_file, file_info_dict)

            # get sub folder info
            cursor = self.conn.execute(SqlCommand.select_subFolderInfo_by_parentGid_sql, [folder_gid])
            folder_info_record = cursor.fetchone()
            if folder_info_record:
                # output sub folder info
                sub_folder_info_dic = self.record_to_write_dict(folder_info_record, mapper, series_queue.qsize())
                TsvHelper.write_to_tsv(output_file, sub_folder_info_dic)

                # put sub folder
                sub_gid = folder_info_record[mapper["gid"]]
                # series_queue.put((sub_gid, folder_gid, output order in parent folder))
                series_queue.put((sub_gid, folder_gid, 0))
            else:
                # get next folder
                while series_queue.qsize() > 0:
                    # pop current folder
                    item = series_queue.get()
                    # get next folder in same series of the current folder
                    cursor = self.conn.execute(SqlCommand.select_nextFolderInfo_by_parentGid_sql,
                                               [item[1], item[2] + 1])
                    folder_info_record = cursor.fetchone()

                    if folder_info_record:
                        # output folder info
                        folder_info_dic = self.record_to_write_dict(folder_info_record, mapper, series_queue.qsize())
                        TsvHelper.write_to_tsv(output_file, folder_info_dic)

                        # put next folder
                        sub_gid = folder_info_record[mapper["gid"]]
                        parent_gid = folder_info_record[mapper["parent_gid"]]
                        series_queue.put((sub_gid, parent_gid, item[2] + 1))
                        break

    @staticmethod
    def record_to_write_dict(record, mapper, dir_series_count):
        """
            convert db line to dict
        :param record:
        :param mapper:
        :param dir_series_count:
        :return:
        """

        prefix = "｜" * dir_series_count + "└── "
        file_name = record[mapper["file"]]
        if dir_series_count > 0:
            file_name = prefix + record[mapper["file"]]

        record_dict = {
            TsvItemEnum.FILE.value: file_name,
            TsvItemEnum.TYPE.value: record[mapper["type"]],
            TsvItemEnum.LAST_UPDATE_DATE.value: record[mapper["last_update_date"]],
            TsvItemEnum.LAST_UPDATE_TIME.value: record[mapper["last_update_time"]],
            TsvItemEnum.LAST_UPDATER.value: record[mapper["last_updater"]],
            TsvItemEnum.URI.value: record[mapper["uri"]],
            TsvItemEnum.PARENT_FOLDER.value: record[mapper["parent_folder"]],
            TsvItemEnum.PARENT_URI.value: record[mapper["parent_uri"]],
            TsvItemEnum.WRITERS_CAN_SHARE.value: (
                True if record[mapper["writers_can_share"]] == 1 else
                False if record[mapper["writers_can_share"]] == 0 else
                record[mapper["writers_can_share"]]
            ),
            TsvItemEnum.DOMAIN.value: record[mapper["domain"]],
            TsvItemEnum.OWNER.value: record[mapper["owner"]],
            TsvItemEnum.WRITER.value: record[mapper["writer"]],
            TsvItemEnum.READER.value: record[mapper["reader"]],
            TsvItemEnum.CHECK_RESULT.value: record[mapper["check_result"]],
            TsvItemEnum.SETTING_RESULT.value: record[mapper["setting_result"]],
            TsvItemEnum.ERR_INFO.value: record[mapper["err_info"]]
        }

        return record_dict

    @staticmethod
    def get_cursor_mapper(cursor_description):
        """
            record select fields index
        :param cursor_description:
        :return:
        """
        mapper = {}
        cursor_description_len = len(cursor_description)
        for index in range(cursor_description_len):
            mapper[cursor_description[index][0]] = index

        return mapper
