#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: qicongsheng
import os
import threading
import time
import traceback

from maven_proxy import utils
from maven_proxy.config import app_config as config

app = config.app


# 定时随机补全sources.jar/javadoc.jar
def auto_download_remote_files_by_dirs():
    while True:
        try:
            print("Starting auto download remote files...")
            # 遍历 REPO_ROOT 目录
            for root, dirs, files in os.walk(app.config['REPO_ROOT'], topdown=False):
                for pom_file_name in files:
                    pom_file_path = os.path.join(root, pom_file_name)
                    if pom_file_path.lower().endswith('.pom'):
                        group_id, artifact_id, version, packaging = utils.parse_pom_xml(pom_file_path)
                        # 文件不存在，从远程下载
                        if packaging == 'jar':
                            auto_download_remote_file(root, pom_file_name, '.pom.sha1')
                            auto_download_remote_file(root, pom_file_name, '.jar')
                            auto_download_remote_file(root, pom_file_name, '.jar.sha1')
                            auto_download_remote_file(root, pom_file_name, '-sources.jar')
                            auto_download_remote_file(root, pom_file_name, '-sources.jar.sha1')
                            auto_download_remote_file(root, pom_file_name, '-javadoc.jar')
                            auto_download_remote_file(root, pom_file_name, '-javadoc.jar.sha1')
            print("Auto download remote files end.")
        except:
            traceback.print_exc()
        time.sleep(app.config['AUTO_DOWNLOAD_INTERVAL'])


# 自动下载指定文件
def auto_download_remote_file(root, pom_file_name, file_type):
    pom_file_path = os.path.join(root, pom_file_name)
    try:
        if not pom_file_path.lower().endswith('.pom'):
            return
        group_id, artifact_id, version, packaging = utils.parse_pom_xml(pom_file_path)
        # 文件不存在，从远程下载
        if packaging == 'jar':
            jar_file = utils.replace_last_occurrence(pom_file_name, '.pom', file_type)
            # 不存在jar文件，则下载
            if not os.path.exists(os.path.join(root, jar_file)):
                remote_path = utils.build_remote_path(group_id, artifact_id, version, file_type)
                utils.fetch_from_remote(remote_path)
    except Exception as e:
        print(f"Failed to auto download remote file {pom_file_name}: {e}")


# 定时清理空文件夹
def cleanup_empty_folders():
    while True:
        try:
            print("Starting cleanup of empty folders...")
            cutoff_time = time.time() - app.config['CLEANUP_AGE']
            deleted_folders = []
            # 遍历 REPO_ROOT 目录
            for root, dirs, files in os.walk(app.config['REPO_ROOT'], topdown=False):
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    try:
                        # 检查是否为空文件夹
                        if not os.listdir(dir_path):
                            dir_mtime = os.path.getmtime(dir_path)
                            # 检查是否超过清理时间
                            if dir_mtime < cutoff_time:
                                os.rmdir(dir_path)
                                deleted_folders.append(dir_path)
                                print(f"Deleted empty folder: {dir_path}")
                    except Exception as e:
                        print(f"Failed to delete {dir_path}: {e}")
            # 如果删除了文件夹，记录日志
            if deleted_folders:
                print(f"Deleted {len(deleted_folders)} empty folders.")
            else:
                print("No empty folders to delete.")
        except:
            traceback.print_exc()
        time.sleep(app.config['CLEANUP_INTERVAL'])


def start():
    threading.Thread(target=auto_download_remote_files_by_dirs).start()
    threading.Thread(target=cleanup_empty_folders).start()
