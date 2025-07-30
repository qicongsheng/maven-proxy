#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: qicongsheng
import hashlib
import os
from datetime import datetime
from xml.etree import ElementTree as ET

import requests

from maven_proxy.config import app_config as config

app = config.app


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


# 替换最后一个字符串
def replace_last_occurrence(str_value, old, new):
    parts = str_value.rsplit(old, 1)  # 从右侧分割一次
    if len(parts) == 1:
        return str_value  # 未找到则返回原字符串
    return new.join(parts)


# 获取本地路径
def get_local_path(path):
    return os.path.join(app.config['REPO_ROOT'], path)


# 根据坐标拼接相对路径目录
def build_remote_path(group_id, artifact_id, version, type):
    return group_id.replace('.', '/') + '/' + artifact_id + '/' + version + '/' + artifact_id + '-' + version + type


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
            print(f'fetched from remote: {remote_url}')
            return True
        return False
    except Exception as e:
        print(f"Remote fetch failed: {e}")
        return False


# 尝试将XML文件解析为POM并提取坐标信息
def parse_pom_xml(xml_file):
    ns = {'mvn': 'http://maven.apache.org/POM/4.0.0'}
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # 检查是否是有效的POM文件
        if root.tag not in ['{http://maven.apache.org/POM/4.0.0}project', 'project']:
            print(f"跳过非POM文件: {xml_file} (根元素: {root.tag})")
            return None

        # 提取当前项目信息
        group_id = None
        artifact_id = None
        version = None
        packaging = "jar"  # Maven默认打包类型是jar

        # 处理带命名空间的POM
        if root.tag.startswith('{'):
            group_id = root.findtext('mvn:groupId', namespaces=ns)
            artifact_id = root.findtext('mvn:artifactId', namespaces=ns)
            version = root.findtext('mvn:version', namespaces=ns)
            # 解析packaging字段
            packaging_elem = root.find('mvn:packaging', namespaces=ns)
            if packaging_elem is not None and packaging_elem.text:
                packaging = packaging_elem.text

            # 检查父项目信息
            parent = root.find('mvn:parent', namespaces=ns)
            if parent is not None:
                if group_id is None:
                    group_id = parent.findtext('mvn:groupId', namespaces=ns)
                if version is None:
                    version = parent.findtext('mvn:version', namespaces=ns)
        else:
            # 处理不带命名空间的POM
            group_id = root.findtext('groupId')
            artifact_id = root.findtext('artifactId')
            version = root.findtext('version')
            # 解析packaging字段
            packaging_elem = root.find('packaging')
            if packaging_elem is not None and packaging_elem.text:
                packaging = packaging_elem.text

            # 检查父项目信息
            parent = root.find('parent')
            if parent is not None:
                if group_id is None:
                    group_id = parent.findtext('groupId')
                if version is None:
                    version = parent.findtext('version')

        # 尝试从properties中查找版本
        if version is None:
            properties = root.find('mvn:properties', namespaces=ns) if root.tag.startswith('{') else root.find(
                'properties')
            if properties is not None:
                version_properties = [
                    ('revision', ns if root.tag.startswith('{') else None),
                    ('project.version', ns if root.tag.startswith('{') else None),
                    ('version', ns if root.tag.startswith('{') else None)
                ]

                for prop, ns_dict in version_properties:
                    if ns_dict:
                        version = properties.findtext(f'mvn:{prop}', namespaces=ns)
                    else:
                        version = properties.findtext(prop)
                    if version:
                        break

        # 确保关键字段存在
        if artifact_id is None:
            artifact_id = "UNKNOWN_ARTIFACT_ID"
        if group_id is None:
            group_id = "UNKNOWN_GROUP_ID"
        if version is None:
            version = "UNKNOWN_VERSION"

        return group_id, artifact_id, version, packaging
    except ET.ParseError:
        print(f"XML解析错误: {xml_file} - 可能不是有效的XML文件")
        return None, None, None, None
    except Exception as e:
        print(f"解析 {xml_file} 时出错: {str(e)}")
        return None, None, None, None
