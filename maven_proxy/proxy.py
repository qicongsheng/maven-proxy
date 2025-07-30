#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: qicongsheng
import os
import uuid

from flask import request, send_from_directory, abort, Response, \
    render_template, redirect, session
from flask_httpauth import HTTPBasicAuth

from maven_proxy import help
from maven_proxy import job
from maven_proxy import utils
from maven_proxy.config import app_config as config

auth = HTTPBasicAuth()
# 创建全局配置对象
app = config.app
repo_context_path = app.config['REPO_CONTEXT_PATH']
browse_context_path = app.config['BROWSE_CONTEXT_PATH']


# 验证用户
@auth.verify_password
def verify_password(username, password):
    if 'user_id' in session:
        return session['user_id']
    if username in app.config['USERS'] and app.config['USERS'][username] == password:
        return username
    return None


@auth.error_handler
def auth_error(status):
    if request.path.startswith(browse_context_path) and status == 401:
        return redirect('/login')  # 重定向到登录页面的路由
    return "Authentication failed", status, {'X-Custom': 'Header', 'Content-Type': 'text/plain'}


# 处理域名路径请求
@app.route(f'/', methods=['GET'])
def handle_domain():
    return redirect('/browse')


# 处理根路径请求
@app.route(f'{browse_context_path}', methods=['GET'])
@auth.login_required
def handle_root():
    return generate_directory_listing('')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if verify_password(username, password):
            session['user_id'] = str(uuid.uuid4())
            session.permanent = True  # 启用超时设置
            return redirect('/browse')
        return "无效的凭据", 401
    return render_template("login.html", version=help.get_version())


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
    local_path = utils.get_local_path(path)
    if os.path.isfile(local_path):
        return send_from_directory(os.path.dirname(local_path), os.path.basename(local_path))
    else:
        # 如果是 maven-metadata.xml，特殊处理
        if path.endswith("maven-metadata.xml"):
            return handle_metadata(path)
        # 尝试从远程仓库获取
        if utils.fetch_from_remote(path):
            return send_from_directory(os.path.dirname(local_path), os.path.basename(local_path))
        abort(404)


# 处理 HEAD 请求
def handle_head(path):
    local_path = utils.get_local_path(path)
    if os.path.exists(local_path):
        return Response(headers={'Content-Length': os.path.getsize(local_path)})
    abort(404)


# 处理 PUT 请求（需要认证）
def handle_put(path):
    local_path = utils.get_local_path(path)
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    try:
        with open(local_path, 'wb') as f:
            f.write(request.data)
        # 如果是 maven-metadata.xml，生成校验文件
        if path.endswith("maven-metadata.xml"):
            sha1_content = utils.generate_sha1(request.data)
            with open(local_path + ".sha1", 'w') as f:
                f.write(sha1_content)
            md5_content = utils.generate_md5(request.data)
            with open(local_path + ".md5", 'w') as f:
                f.write(md5_content)
        return Response("Deployment successful", 201)
    except Exception as e:
        return Response(f"Deployment failed: {str(e)}", 500)


# 生成文件列表的 HTML 页面（Nginx 风格）
def generate_directory_listing(path):
    local_path = utils.get_local_path(path)
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
        get_last_modified=utils.get_last_modified,
        get_file_size=utils.get_file_size
    )


# 处理 maven-metadata.xml 请求
def handle_metadata(path):
    local_path = utils.get_local_path(path)
    if os.path.isfile(local_path):
        return send_from_directory(
            os.path.dirname(local_path),
            os.path.basename(local_path))

    if utils.fetch_from_remote(path):
        return send_from_directory(
            os.path.dirname(local_path),
            os.path.basename(local_path))

    # 如果远程仓库也不存在，生成一个空的 maven-metadata.xml
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    empty_metadata = utils.generate_empty_metadata(path)
    with open(local_path, 'wb') as f:
        f.write(empty_metadata)

    # 生成 maven-metadata.xml.sha1
    sha1_content = utils.generate_sha1(empty_metadata)
    with open(local_path + ".sha1", 'w') as f:
        f.write(sha1_content)

    # 生成 maven-metadata.xml.md5
    md5_content = utils.generate_md5(empty_metadata)
    with open(local_path + ".md5", 'w') as f:
        f.write(md5_content)

    return send_from_directory(
        os.path.dirname(local_path),
        os.path.basename(local_path))


def startup():
    print(f"Maven Proxy {help.get_version()}")
    print(f"repo_context_path={app.config['REPO_CONTEXT_PATH']}")
    print(f"browse_context_path={app.config['BROWSE_CONTEXT_PATH']}")
    print(f"local_repo_dir={config.REPO_ROOT}")
    print(f"remote_repo={config.REMOTE_REPO}")
    # 初始化定时任务
    job.start()
    app.run(host='0.0.0.0', port=config.PORT, threaded=True)


# 启动服务
if __name__ == '__main__':
    startup()
