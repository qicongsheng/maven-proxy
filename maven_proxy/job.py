#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: qicongsheng
import os
import threading
import time
import traceback

import maven_proxy.task as task
from maven_proxy import utils
from maven_proxy.config import app_config as config

app = config.app


# 定时随机补全sources.jar/javadoc.jar
def auto_download_remote_files_by_dirs():
    time.sleep(5)
    while True:
        app.logger.info("Starting auto download remote files...")
        # 遍历 REPO_ROOT 目录，收集所有任务
        tasks = []
        for root, dirs, files in os.walk(app.config['REPO_ROOT'], topdown=False):
            for pom_file_name in files:
                pom_file_path = os.path.join(root, pom_file_name)
                if pom_file_path.lower().endswith('.pom'):
                    try:
                        group_id, artifact_id, version, packaging = utils.parse_pom_xml(pom_file_path)
                        file_types = ['.pom.sha1', '.pom.md5', '.module', '.module.sha1', '.module.md5']
                        if packaging in ('jar', 'bundle'):
                            file_types += ['.jar', '.jar.sha1', '.jar.md5',
                                           '-sources.jar', '-sources.jar.sha1', '-sources.jar.md5',
                                           '-javadoc.jar', '-javadoc.jar.sha1', '-javadoc.jar.md5']
                        for file_type in file_types:
                            target_file = utils.replace_last_occurrence(pom_file_name, '.pom', file_type)
                            if not os.path.exists(os.path.join(root, target_file)):
                                tasks.append(lambda _root=root, _pom=pom_file_name, _ft=file_type: auto_download_remote_file(_root, _pom, _ft))
                    except:
                        traceback.print_exc()
        # 批量执行，每批10个线程
        app.logger.info(f"Collected {len(tasks)} download tasks, executing in batches of 2000...")
        task.run_tasks_in_batches(tasks, batch_size=2000, logger=app.logger)
        app.logger.info("Auto download remote files end.")
        time.sleep(app.config['AUTO_DOWNLOAD_INTERVAL'])


# 自动下载指定文件
def auto_download_remote_file(root, pom_file_name, file_type):
    try:
        pom_file_path = os.path.join(root, pom_file_name)
        group_id, artifact_id, version, packaging = utils.parse_pom_xml(pom_file_path)
        remote_path = utils.build_remote_path(group_id, artifact_id, version, file_type)
        utils.fetch_from_remote(remote_path)
    except Exception as e:
        app.logger.error(f"Failed to auto download remote file {pom_file_name}: {e}")


# 定时清理空文件夹
def cleanup_empty_folders():
    time.sleep(5)
    while True:
        try:
            app.logger.info("Starting cleanup of empty folders...")
            cutoff_time = time.time() - app.config['CLEANUP_AGE']
            deleted_folders = []
            # 遍历 REPO_ROOT 目录
            for root, dirs, files in os.walk(app.config['REPO_ROOT'], topdown=False):
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    try:
                        # 检查是否为空文件夹
                        if len(os.listdir(dir_path)) == 0:
                            dir_mtime = os.path.getmtime(dir_path)
                            # 检查是否超过清理时间
                            if dir_mtime < cutoff_time:
                                os.rmdir(dir_path)
                                deleted_folders.append(dir_path)
                                app.logger.info(f"Deleted empty folder: {dir_path}")
                    except Exception as e:
                        app.logger.error(f"Failed to delete {dir_path}: {e}")
            # 如果删除了文件夹，记录日志
            if deleted_folders:
                app.logger.info(f"Deleted {len(deleted_folders)} empty folders.")
            else:
                app.logger.info("No empty folders to delete.")
        except:
            traceback.print_exc()
        time.sleep(app.config['CLEANUP_INTERVAL'])


def start():
    threading.Thread(target=auto_download_remote_files_by_dirs).start()
    threading.Thread(target=cleanup_empty_folders).start()
