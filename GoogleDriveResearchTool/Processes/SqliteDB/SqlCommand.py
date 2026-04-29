create_tbl_file_detail_sql = """
                                CREATE TABLE FileDetail (
                                    id                INTEGER  PRIMARY KEY AUTOINCREMENT,
                                    gid               TEXT,
                                    parent_gid        TEXT,
                                    file              TEXT     COLLATE NOCASE,
                                    type              CHAR (1),
                                    last_update_date  TEXT,
                                    last_update_time  TEXT,
                                    last_updater      TEXT,
                                    uri               TEXT,
                                    parent_folder     TEXT,
                                    parent_uri        TEXT ,
                                    writers_can_share BOOLEAN,
                                    domain            TEXT,
                                    owner             TEXT,
                                    writer            TEXT,
                                    reader            TEXT,
                                    check_result      CHAR (1),
                                    setting_result    CHAR (1),
                                    err_info          TEXT
                                );
                                CREATE INDEX fileDetail_parent_gid ON FileDetail (
                                    parent_gid
                                );
                                CREATE INDEX fileDetail_type ON FileDetail (
                                    type
                                );
                                CREATE INDEX fileDetail_file ON FileDetail (
                                    file
                                );
                            """
create_tbl_research_folder_sql = """
                                    CREATE TABLE ResearchFolder (
                                        id         INTEGER PRIMARY KEY AUTOINCREMENT,
                                        gid        TEXT,
                                        parent_gid TEXT,
                                        name       TEXT    COLLATE NOCASE,
                                        uri        TEXT
                                    );
                                    CREATE INDEX researchFolder_parent_gid ON ResearchFolder (
                                        parent_gid
                                    );
                                """

drop_tbl_file_detail_sql = """
                              DROP TABLE IF EXISTS FileDetail;
                           """
drop_tbl_research_folder_sql = """
                                  DROP TABLE IF EXISTS ResearchFolder;
                               """

insert_file_detail_sql = """
                            INSERT INTO FileDetail (
                                  gid,
                                  parent_gid,
                                  file,
                                  type,
                                  last_update_date,
                                  last_update_time,
                                  last_updater,
                                  uri,
                                  parent_folder,
                                  parent_uri,
                                  writers_can_share,
                                  domain,
                                  owner,
                                  writer,
                                  reader,
                                  check_result,
                                  setting_result,
                                  err_info
                              )
                              VALUES (
                                  ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
                              );
                         """
insert_research_folder_sql = """
                                INSERT INTO ResearchFolder (
                                      gid,
                                      parent_gid,
                                      name,
                                      uri
                                  )
                                  VALUES (
                                      ?,?,?,?
                                  );
                             """
select_file_detail_by_gid_eq_sql = """
                                       SELECT id,
                                              gid,
                                              parent_gid,
                                              file,
                                              type,
                                              last_update_date,
                                              last_update_time,
                                              last_updater,
                                              uri,
                                              parent_folder,
                                              parent_uri,
                                              writers_can_share,
                                              domain,
                                              owner,
                                              writer,
                                              reader,
                                              check_result,
                                              setting_result,
                                              err_info
                                         FROM FileDetail
                                         WHERE gid = ?;
                                    """
select_research_folder_by_id_gt_sql = """
                                        SELECT id,
                                               gid,
                                               parent_gid,
                                               name,
                                               uri
                                          FROM ResearchFolder
                                          WHERE id > ?;
                                      """
select_research_folder_max_id_sql = """
                                        SELECT MAX(id) FROM ResearchFolder;
                                    """
select_subFileInfo_by_parentGid_sql = """
                                        SELECT * 
                                          FROM FileDetail 
                                          WHERE 
                                            parent_gid = ? 
                                            AND type IN ('F', 'S') 
                                          ORDER BY type, file ASC
                                      """
select_subFolderInfo_by_parentGid_sql = """
                                           SELECT * 
                                             FROM FileDetail 
                                             WHERE 
                                               parent_gid = ?
                                               AND type = 'D'
                                             ORDER BY file
                                             LIMIT 1
                                        """
select_nextFolderInfo_by_parentGid_sql = """
                                            SELECT * 
                                              FROM FileDetail 
                                              WHERE 
                                                parent_gid = ? 
                                                AND type = 'D' 
                                              ORDER BY file 
                                              LIMIT ?, 1
                                         """
vacuum_sql = "VACUUM;"
