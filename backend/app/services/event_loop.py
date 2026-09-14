"""Windows psycopg async connections require a selector loop.

MCP uses HTTP and a regular Popen child, so no async subprocess support is needed.
"""

import asyncio
import sys


def run_async(coroutine):
    factory = asyncio.SelectorEventLoop if sys.platform == 'win32' else None
    with asyncio.Runner(loop_factory=factory) as runner:
        return runner.run(coroutine)
