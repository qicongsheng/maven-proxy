# 修改 db.py 文件
#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: qicongsheng
import sqlite3
import time

class DB:
    def __init__(self, data_file_path='./data.db'):
        self.conn = sqlite3.connect(data_file_path, check_same_thread=False)
        self.init_tables()

    def init_tables(self):
        # 创建错误记录表
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS fetch_errors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                remote_url TEXT NOT NULL,
                error_message TEXT,
                timestamp INTEGER NOT NULL
            )
        ''')
        self.conn.commit()

    def record_fetch_error(self, remote_url, error_message):
        self.conn.execute('''
            INSERT INTO fetch_errors (remote_url, error_message, timestamp)
            VALUES (?, ?, ?)
        ''', (remote_url, error_message, int(time.time())))
        self.conn.commit()

    def has_fetch_failed_before(self, remote_url):
        """
        检查指定的URL是否之前抓取失败过
        """
        cursor = self.conn.execute('SELECT COUNT(*) FROM fetch_errors WHERE remote_url = ?', (remote_url,))
        count = cursor.fetchone()[0]
        return count > 0

