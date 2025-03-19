#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: qicongsheng
import hashlib
import os
import time
from datetime import datetime
from xml.etree import ElementTree as ET

import requests
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, request, send_from_directory, abort, Response, render_template, redirect
from flask_httpauth import HTTPBasicAuth

from maven_proxy import help
from maven_proxy.config import Config

app = Flask(__name__)
auth = HTTPBasicAuth()

# 创建全局配置对象
config = Config()
app.config.from_object(config)
app.url_map.strict_slashes = False
repo_context_path = app.config['REPO_CONTEXT_PATH']
browse_context_path = app.config['BROWSE_CONTEXT_PATH']


# 获取本地路径
def get_local_path(path):
    return os.path.join(app.config['REPO_ROOT'], path)


# 从远程仓库获取文件
def fetch_from_remote(path):
    remote_url = app.config['REMOTE_REPO'] + path
    try:
        auth = None
        if app.config['REMOTE_REPO_USERNAME'] and app.config['REMOTE_REPO_PASSWORD']:
            auth = (app.config['REMOTE_REPO_USERNAME'], app.config['REMOTE_REPO_PASSWORD'])

        resp = requests.get(remote_url, auth=auth, timeout=10)
        if resp.status_code == 200:
            local_path = get_local_path(path)
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, 'wb') as f:
                f.write(resp.content)

            return True
        return False
    except Exception as e:
        print(f"Remote fetch failed: {e}")
        return False


# 生成空的 maven-metadata.xml
def generate_empty_metadata(path):
    metadata = ET.Element("metadata")
    group_id, artifact_id = path.split("/")[-3:-1]
    ET.SubElement(metadata, "groupId").text = group_id
    ET.SubElement(metadata, "artifactId").text = artifact_id
    ET.SubElement(metadata, "versioning")
    return ET.tostring(metadata, encoding="utf-8", xml_declaration=True)


# 生成文件的 SHA1 校验值
def generate_sha1(content):
    sha1 = hashlib.sha1()
    sha1.update(content)
    return sha1.hexdigest()


# 生成文件的 MD5 校验值
def generate_md5(content):
    md5 = hashlib.md5()
    md5.update(content)
    return md5.hexdigest()


# 辅助函数：获取文件的最后修改时间
def get_last_modified(file_path):
    timestamp = os.path.getmtime(file_path)
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


# 辅助函数：获取文件大小
def get_file_size(file_path):
    size = os.path.getsize(file_path)
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.2f} KB"
    else:
        return f"{size / (1024 * 1024):.2f} MB"


# 生成文件列表的 HTML 页面（Nginx 风格）
def generate_directory_listing(path):
    local_path = get_local_path(path)
    if not os.path.exists(local_path):
        return None

    # 获取目录下的文件和子目录
    items = os.listdir(local_path)
    items.sort()
    files = []
    dirs = []
    for item in items:
        item_path = os.path.join(local_path, item)
        if os.path.isdir(item_path):
            dirs.append(item + "/")
        else:
            files.append(item)
    # 计算父路径
    if path == "/":
        parent_path = "/"
    else:
        parent_path = os.path.dirname(path.rstrip("/"))
        if not parent_path:
            parent_path = "/"
        else:
            parent_path = "/" + parent_path + "/"

    return render_template(
        "directory_listing.html",
        path=path,
        repo_context_path=repo_context_path,
        browse_context_path=browse_context_path,
        parent_path=parent_path,
        local_path=local_path,
        dirs=dirs,
        files=files,
        os=os,
        get_last_modified=get_last_modified,
        get_file_size=get_file_size
    )


# 处理 maven-metadata.xml 请求
def handle_metadata(path):
    local_path = get_local_path(path)
    if os.path.isfile(local_path):
        return send_from_directory(
            os.path.dirname(local_path),
            os.path.basename(local_path))

    if fetch_from_remote(path):
        return send_from_directory(
            os.path.dirname(local_path),
            os.path.basename(local_path))

    # 如果远程仓库也不存在，生成一个空的 maven-metadata.xml
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    empty_metadata = generate_empty_metadata(path)
    with open(local_path, 'wb') as f:
        f.write(empty_metadata)

    # 生成 maven-metadata.xml.sha1
    sha1_content = generate_sha1(empty_metadata)
    with open(local_path + ".sha1", 'w') as f:
        f.write(sha1_content)

    # 生成 maven-metadata.xml.md5
    md5_content = generate_md5(empty_metadata)
    with open(local_path + ".md5", 'w') as f:
        f.write(md5_content)

    return send_from_directory(
        os.path.dirname(local_path),
        os.path.basename(local_path))


# 验证用户
@auth.verify_password
def verify_password(username, password):
    if username in app.config['USERS'] and app.config['USERS'][username] == password:
        return username
    return None


# 处理域名路径请求
@app.route(f'/', methods=['GET'])
@auth.login_required
def handle_domain():
    return redirect('/browse')


# 处理根路径请求
@app.route(f'{browse_context_path}', methods=['GET'])
@auth.login_required
def handle_root():
    return generate_directory_listing('')


# 处理browse路径请求
@app.route(f'{browse_context_path}/<path:path>', methods=['GET'])
@auth.login_required
def handle_browse(path):
    return generate_directory_listing(path)


@app.route(f'{repo_context_path}/<path:path>', methods=['GET', 'PUT', 'HEAD'])
@auth.login_required
def handle_path(path):
    if request.method == 'GET':
        return handle_get(path)
    elif request.method == 'PUT':
        return handle_put(path)
    elif request.method == 'HEAD':
        return handle_head(path)


# 处理 GET 请求
def handle_get(path):
    local_path = get_local_path(path)
    if os.path.isfile(local_path):
        return send_from_directory(os.path.dirname(local_path), os.path.basename(local_path))
    else:
        # 如果是 maven-metadata.xml，特殊处理
        if path.endswith("maven-metadata.xml"):
            return handle_metadata(path)
        # 尝试从远程仓库获取
        if fetch_from_remote(path):
            return send_from_directory(os.path.dirname(local_path), os.path.basename(local_path))
        abort(404)


# 处理 HEAD 请求
def handle_head(path):
    local_path = get_local_path(path)
    if os.path.exists(local_path):
        return Response(headers={'Content-Length': os.path.getsize(local_path)})
    abort(404)


# 处理 PUT 请求（需要认证）
def handle_put(path):
    local_path = get_local_path(path)
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    try:
        with open(local_path, 'wb') as f:
            f.write(request.data)
        # 如果是 maven-metadata.xml，生成校验文件
        if path.endswith("maven-metadata.xml"):
            sha1_content = generate_sha1(request.data)
            with open(local_path + ".sha1", 'w') as f:
                f.write(sha1_content)
            md5_content = generate_md5(request.data)
            with open(local_path + ".md5", 'w') as f:
                f.write(md5_content)
        return Response("Deployment successful", 201)
    except Exception as e:
        return Response(f"Deployment failed: {str(e)}", 500)


def cleanup_empty_folders():
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


def startup():
    print(f"Maven Proxy {help.get_version()}")
    print(f"repo_context_path={app.config['REPO_CONTEXT_PATH']}")
    print(f"browse_context_path={app.config['BROWSE_CONTEXT_PATH']}")
    print(f"local_repo_dir={config.REPO_ROOT}")
    print(f"remote_repo={config.REMOTE_REPO}")
    # 初始化定时任务
    print("Job of cleanup of empty folders starting...")
    scheduler = BackgroundScheduler()
    scheduler.add_job(cleanup_empty_folders, 'interval', seconds=app.config['CLEANUP_INTERVAL'])
    scheduler.start()
    print("Job of cleanup of empty folders started")
    app.run(host='0.0.0.0', port=config.PORT, threaded=True)


# 启动服务
if __name__ == '__main__':
    startup()
