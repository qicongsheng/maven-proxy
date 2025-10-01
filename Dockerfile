# =================================
# REMOTE_REPOS='[{"url":"https://repo1.maven.org/maven2/","user":"","passwd":""},{"url":"https://plugins.gradle.org/m2/","user":"","passwd":""}]'
# =================================
FROM registry.mozu.eu.org/qics/python:3.9.21-alpine3.20
MAINTAINER qicongsheng

ENV PORT=8081 \
    AUTH_USER=user \
    AUTH_PASSWORD=passwd \
    REMOTE_REPOS='[{"url":"https://repo1.maven.org/maven2/"},{"url":"https://plugins.gradle.org/m2/"}]' \
    REPO_CONTEXT_PATH=/maven2 \
    BROWSE_CONTEXT_PATH=/browse \
    LOCAL_REPO_DIR=/data \
    SKIPLOG_ENABLE=false \
    TZ=Asia/Shanghai

RUN pip install --no-cache-dir maven-proxy -U && mkdir -p /data/repository

CMD ["maven-proxy"]
