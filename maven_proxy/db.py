# 修改 db.py 文件
# !/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: qicongsheng
import sqlite3
import threading
import time
from queue import Queue


class DBConnectionPool:
    def __init__(self, database_file_path, pool_size=5):
        self.database_file_path = database_file_path
        self.pool_size = pool_size
        self.connections = Queue(pool_size)
        self.lock = threading.Lock()

        # 初始化连接池
        for _ in range(pool_size):
            conn = sqlite3.connect(database_file_path, check_same_thread=False)
            self.connections.put(conn)

    def get_connection(self):
        return self.connections.get()

    def return_connection(self, conn):
        self.connections.put(conn)

    def close_all(self):
        while not self.connections.empty():
            conn = self.connections.get()
            conn.close()


class DB:
    def __init__(self, database_file_path='./database.db'):
        self.pool = DBConnectionPool(database_file_path)
        self.init_tables()

    def _execute(self, query, params=None):
        """执行SQL语句的通用方法"""
        conn = self.pool.get_connection()
        try:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            result = cursor.fetchall() if query.strip().upper().startswith('SELECT') else None
            conn.commit()
            return result
        finally:
            self.pool.return_connection(conn)

    def init_tables(self):
        self._execute(
            'CREATE TABLE IF NOT EXISTS fetch_errors (id INTEGER PRIMARY KEY AUTOINCREMENT, remote_url TEXT NOT NULL, error_message TEXT, timestamp INTEGER NOT NULL)')

    def record_fetch_error(self, file_path, error_message):
        self._execute('INSERT INTO fetch_errors (remote_url, error_message, timestamp)VALUES (?, ?, ?)',
                      (file_path, error_message, int(time.time())))

    def has_fetch_failed_before(self, remote_url):
        """
        检查指定的URL是否之前抓取失败过
        """
        result = self._execute('SELECT COUNT(*) FROM fetch_errors WHERE remote_url = ?', (remote_url,))
        return result[0][0] > 0 if result else False

    def close(self):
        """关闭所有数据库连接"""
        self.pool.close_all()
