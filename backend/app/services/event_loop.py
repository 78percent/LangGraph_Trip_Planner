"""Windows psycopg async connections require a selector loop.

MCP uses HTTP and a regular Popen child, so no async subprocess support is needed.
"""

import asyncio
import sys


def run_async(coroutine):  # 传入一个协程对象coroutine
    factory = asyncio.SelectorEventLoop if sys.platform == 'win32' else None  # Windows：强制用 SelectorEventLoop 其他系统：用默认事件循环
    with asyncio.Runner(loop_factory=factory) as runner:    # 创建一个事件循环，然后把这个 async 协程真正跑起来，跑完再自动清理。
        return runner.run(coroutine)

"""
原因就是文件顶部写的：
psycopg 的异步连接在 Windows 下需要 selector loop。
# 统一运行异步协程；Windows 下使用 SelectorEventLoop，
# 以兼容 psycopg 的异步数据库连接
"""