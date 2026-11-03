"""Terminal interface to the same chat graph used by FastAPI."""
import asyncio
import sys
from pathlib import Path

# Set the import path before importing app; IDE profilers may use runpy.
backend_dir = str(Path(__file__).resolve().parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.services.runtime import build_services
from app.services.event_loop import run_async


async def main():
    async with build_services() as services:  #  创建整个项目需要的服务对象
        session_id = None
        print('途间旅行助手：/new 新会话，/quit 退出')
        while True:
            message = await asyncio.to_thread(input, '你：')
            if message.strip() == '/quit':
                break
            if message.strip() == '/new':
                session_id = None
                continue
            if not message.strip():
                continue
            try:
                result = await services.chat.send(message, session_id)  # 服务对象services.chat.send发送消息给AI, 携带本次message和对话记录所属session_id, 返回结果result
                from uuid import UUID
                session_id = UUID(result['session_id'])     # 对于创建的新对话，分配一个 UUID session_id给他, 进行对话分开存储
                print('助手：', result['reply'])
            except Exception as exc:
                print('本轮未完成：', type(exc).__name__, '；可使用网页恢复或 /new 新建会话')


if __name__ == '__main__':
    run_async(main())
