# 使用官方Python Alpine镜像
FROM python:3.9-alpine

# 设置环境变量（可覆盖）
ENV AUTH_USER=user \
    AUTH_PASSWORD=passwd \
    REMOTE_REPO=https://repo1.maven.org/maven2/ \
    REMOTE_REPO_USERNAME= \
    REMOTE_REPO_PASSWORD= \
    CONTEXT_PATH=/maven2 \
    LOCAL_REPO_DIR=/data/repository

# 设置工作目录
WORKDIR /app

# 复制项目文件
COPY requirements.txt .
COPY templates/ ./templates/
COPY maven_proxy.py .
COPY config.py .

# 安装系统依赖
RUN apk add --no-cache \
    build-base \
    libffi-dev \
    openssl-dev \
    && pip install --no-cache-dir -r requirements.txt \
    && mkdir -p /data/repository

# 暴露端口
EXPOSE 8080

# 设置启动命令
CMD ["python", "nexus_proxy.py"]
