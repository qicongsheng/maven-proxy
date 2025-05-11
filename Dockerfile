FROM python:3.9.21-alpine3.20
MAINTAINER qicongsheng

ENV PORT=8081 \
    AUTH_USER=user \
    AUTH_PASSWORD=passwd \
    REMOTE_REPO=https://repo.maven.apache.org/maven2/ \
    REMOTE_REPO_USERNAME= \
    REMOTE_REPO_PASSWORD= \
    REPO_CONTEXT_PATH=/maven2 \
    BROWSE_CONTEXT_PATH=/browse \
    LOCAL_REPO_DIR=/data/repository \
    TZ=Asia/Shanghai

RUN pip install --no-cache-dir maven-proxy -U && mkdir -p /data/repository

CMD ["maven-proxy"]
