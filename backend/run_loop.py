"""Terminal interface to the same chat graph used by FastAPI."""
import asyncio
from app.services.runtime import build_services
from app.services.event_loop import run_async


async def main():
    async with build_services() as services:
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
                result = await services.chat.send(message, session_id)
                from uuid import UUID
                session_id = UUID(result['session_id'])
                print('助手：', result['reply'])
            except Exception as exc:
                print('本轮未完成：', type(exc).__name__, '；可使用网页恢复或 /new 新建会话')


if __name__ == '__main__':
    run_async(main())
