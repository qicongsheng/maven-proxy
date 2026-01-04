<p align="center">
	<img src="https://raw.githubusercontent.com/qicongsheng/maven-proxy/refs/heads/main/screenshot/favicon.ico">
	<br>
</p>

A lightweight Maven repository(with proxy) implemented in Python. Supports downloading and uploading dependency jar packages. Dependency jar files and pom files are stored in disk folders, which is convenient for manually uploading local dependencies. Extremely low resource consumption.

## Example Usage
### Install
```
pip3 install maven-proxy
```
### Usage
```
usage: maven-proxy [-h] [--port PORT] [--local-repo-dir LOCAL_REPO_DIR] [--remote-repos REMOTE_REPOS] [--auth-user AUTH_USER] [--auth-password AUTH_PASSWORD] [--repo-context-path REPO_CONTEXT_PATH]
                       [--browse-context-path BROWSE_CONTEXT_PATH] [--cleanup-interval CLEANUP_INTERVAL] [--cleanup-age CLEANUP_AGE] [--auto-download-interval AUTO_DOWNLOAD_INTERVAL]
                       [--permanent-session-lifetime PERMANENT_SESSION_LIFETIME] [--msg-404 MSG_404] [--skiplog-enable SKIPLOG_ENABLE] [--skip-auth SKIP_AUTH]

Maven Proxy Configuration

options:
  -h, --help            show this help message and exit
  --port PORT
  --local-repo-dir LOCAL_REPO_DIR
  --remote-repos REMOTE_REPOS
  --auth-user AUTH_USER
  --auth-password AUTH_PASSWORD
  --repo-context-path REPO_CONTEXT_PATH
  --browse-context-path BROWSE_CONTEXT_PATH
  --cleanup-interval CLEANUP_INTERVAL
  --cleanup-age CLEANUP_AGE
  --auto-download-interval AUTO_DOWNLOAD_INTERVAL
  --permanent-session-lifetime PERMANENT_SESSION_LIFETIME
  --msg-404 MSG_404
  --skiplog-enable SKIPLOG_ENABLE
  --skip-auth SKIP_AUTH
```

## Screenshot
<br>
<img width="420px" src="https://raw.githubusercontent.com/qicongsheng/maven-proxy/refs/heads/main/screenshot/login.png"><br>
<img width="420px" src="https://raw.githubusercontent.com/qicongsheng/maven-proxy/refs/heads/main/screenshot/list.png">
