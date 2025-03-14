from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
  long_description = fh.read()

setup(
    name="maven-proxy",
    version="0.0.1",
    author="qicongsheng",
    author_email="qicongsheng@outlook.com",
    description="Maven Repository Proxy with caching and authentication",
    url="https://github.com/yourusername/maven-proxy",
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