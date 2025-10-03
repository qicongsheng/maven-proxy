#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: qicongsheng
import threading
from typing import List, Callable, Any


def run_tasks_concurrently(tasks: List[Callable]) -> List[Any]:
    """
    简化版的并发任务执行器

    Args:
        tasks: 要执行的任务函数列表

    Returns:
        任务执行结果列表
    """
    results = [None] * len(tasks)
    threads = []
    lock = threading.Lock()

    def wrapper(func, index, *args, **kwargs):
        try:
            result = func(*args, **kwargs)
            with lock:
                results[index] = result
        except Exception as e:
            with lock:
                results[index] = e

    # 创建并启动所有线程
    for i, task in enumerate(tasks):
        thread = threading.Thread(target=wrapper, args=(task, i))
        threads.append(thread)
        thread.start()

    # 等待所有线程完成
    for thread in threads:
        thread.join()

    return results
