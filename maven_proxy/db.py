#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: qicongsheng
import sqlite3

class DB:
    def __init__(self, data_file_path='./data.db'):
        self.conn = sqlite3.connect(data_file_path)

db = DB()
