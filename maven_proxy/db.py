# 修改 db.py 文件
# !/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: qicongsheng
import sqlite3
import time
from datetime import datetime


class DB:
    def __init__(self, database_file_path='./database.db'):
        self.conn = sqlite3.connect(database_file_path, check_same_thread=False)
        self.init_tables()

    def init_tables(self):
        # 创建错误记录表
        self.conn.execute(
            'CREATE TABLE IF NOT EXISTS fetch_errors (id INTEGER PRIMARY KEY AUTOINCREMENT, remote_url TEXT NOT NULL, error_message TEXT, timestamp INTEGER NOT NULL)')
        self.conn.commit()

    def record_fetch_error(self, file_path, error_message):
        self.conn.execute('INSERT INTO fetch_errors (remote_url, error_message, timestamp)VALUES (?, ?, ?)',
                          (file_path, error_message, int(time.time())))
        self.conn.commit()

    def has_fetch_failed_before(self, remote_url):
        """
        检查指定的URL是否之前抓取失败过
        """
        cursor = self.conn.execute('SELECT COUNT(*) FROM fetch_errors WHERE remote_url = ?', (remote_url,))
        count = cursor.fetchone()[0]
        return count > 0

    def get_fetch_errors(self, limit=100):
        """
        获取抓取错误记录，时间戳已格式化为 yyyy-MM-dd HH:mm:ss
        :param limit: 限制返回记录数，默认100条
        :return: 格式化后的错误记录列表
        """
        cursor = self.conn.execute(
            'SELECT id, remote_url, error_message, timestamp FROM fetch_errors ORDER BY id DESC LIMIT ?', (limit,))
        result = []
        for row in cursor.fetchall():
            # 将时间戳转换为 yyyy-MM-dd HH:mm:ss 格式
            timestamp_formatted = datetime.fromtimestamp(row[3]).strftime('%Y-%m-%d %H:%M:%S')
            result.append((row[0], row[1], row[2], timestamp_formatted))
        return result

    def clear_fetch_errors(self):
        """
        清空所有抓取错误记录
        """
        self.conn.execute('DELETE FROM fetch_errors')
        self.conn.commit()
