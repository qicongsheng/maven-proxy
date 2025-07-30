#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: qicongsheng
import argparse
import os
import uuid
from datetime import timedelta

from flask import Flask


class Config:
    def __init__(self):
        # 解析命令行参数
        parser = argparse.ArgumentParser(description="Maven Proxy Configuration")
        parser.add_argument("--port", type=int, default=int(os.getenv("PORT", 8081)))
        parser.add_argument("--local-repo-dir", type=str,
                            default=os.getenv("LOCAL_REPO_DIR", os.path.expanduser("~/.m2/repository")))
        parser.add_argument("--remote-repo", type=str,
                            default=os.getenv("REMOTE_REPO", "https://repo.maven.apache.org/maven2/"))
        parser.add_argument("--remote-repo-username", type=str, default=os.getenv("REMOTE_REPO_USERNAME", None))
        parser.add_argument("--remote-repo-password", type=str, default=os.getenv("REMOTE_REPO_PASSWORD", None))
        parser.add_argument("--auth-user", type=str, default=os.getenv("AUTH_USER", "user"))
        parser.add_argument("--auth-password", type=str, default=os.getenv("AUTH_PASSWORD", "passwd"))
        parser.add_argument("--repo-context-path", type=str, default=os.getenv("REPO_CONTEXT_PATH", "/maven2"))
        parser.add_argument("--browse-context-path", type=str, default=os.getenv("BROWSE_CONTEXT_PATH", "/browse"))
        parser.add_argument("--cleanup-interval", type=int, default=int(os.getenv("CLEANUP_INTERVAL", 300)))
        parser.add_argument("--cleanup-age", type=int, default=int(os.getenv("CLEANUP_AGE", 3600)))
        parser.add_argument("--auto-download-interval", type=int, default=int(os.getenv("AUTO_DOWNLOAD_INTERVAL", 300)))
        parser.add_argument("--permanent-session-lifetime", type=int,
                            default=int(os.getenv("PERMANENT_SESSION_LIFETIME", 30)))
        args = parser.parse_args()

        # 本地仓库端口
        self.PORT = args.port
        # 本地仓库路径
        self.REPO_ROOT = args.local_repo_dir
        # 远程Maven仓库
        self.REMOTE_REPO = args.remote_repo
        # 远程Maven仓库 认证（可选）
        self.REMOTE_REPO_USERNAME = args.remote_repo_username
        self.REMOTE_REPO_PASSWORD = args.remote_repo_password
        # 部署用户认证
        self.USERS = {args.auth_user: args.auth_password}
        # repo上下文路径（如 /maven2）
        self.REPO_CONTEXT_PATH = args.repo_context_path
        # 浏览器上下文路径（如 /browse）
        self.BROWSE_CONTEXT_PATH = args.browse_context_path
        # 定时任务配置
        self.CLEANUP_INTERVAL = args.cleanup_interval
        self.CLEANUP_AGE = args.cleanup_age
        self.AUTO_DOWNLOAD_INTERVAL = args.auto_download_interval
        self.PERMANENT_SESSION_LIFETIME = args.permanent_session_lifetime

        app = Flask(__name__)
        app.config.from_object(self)
        app.url_map.strict_slashes = False
        app.secret_key = str(uuid.uuid4())
        app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=self.PERMANENT_SESSION_LIFETIME)
        self.app = app


app_config = Config()
