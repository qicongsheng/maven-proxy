#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: qicongsheng
from setuptools import setup, find_packages

setup(
    name="maven-proxy",
    version="1.0.69",
    author="qicongsheng",
    author_email="qicongsheng@outlook.com",
    description="Maven Repository Proxy with caching and authentication",
    url="https://github.com/qicongsheng/maven-proxy",
    packages=find_packages(),
    package_data={
        "maven_proxy": ["templates/*.html"]
    },
    install_requires=[
        "flask",
        "requests",
        "flask_httpauth",
        "apscheduler"
    ],
    entry_points={
        "console_scripts": [
            "maven-proxy=maven_proxy.app:main"
        ]
    }
)
