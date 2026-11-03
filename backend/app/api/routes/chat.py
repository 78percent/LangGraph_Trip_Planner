import asyncio
from uuid import UUID
from fastapi import APIRouter, Depends
from ...models.schemas import ChatRequest
from ...services.runtime import ApplicationServices
from ..dependencies import get_services

router = APIRouter(prefix='/chat', tags=['持久化对话'])

# routes 里的 URL = 后端功能入口，不等于前端页面, 不是网页地址，而是后端接口地址
@router.post('/send')
async def send(request: ChatRequest, services: ApplicationServices = Depends(get_services)):
    async with asyncio.timeout(180):
        return {'success': True, 'data': await services.chat.send(request.message, request.session_id)}


@router.get('/sessions')
async def sessions(services: ApplicationServices = Depends(get_services)):
    return {'success': True, 'data': await services.repository.list_sessions()}


@router.get('/sessions/{session_id}')
async def history(session_id: UUID, services: ApplicationServices = Depends(get_services)):
    return {'success': True, 'data': await services.chat.history(session_id)}


@router.post('/sessions/{session_id}/resume')
async def resume(session_id: UUID, services: ApplicationServices = Depends(get_services)):
    async with asyncio.timeout(180):
        return {'success': True, 'data': await services.chat.resume(session_id)}


"""
routes 文件夹里的那些 URL，大多数不是网页地址，而是后端接口地址
例如 @router.post('/chat')
这些不是说“你有一个 /chat 网页”，而是说：
浏览器 / 前端 / 其他程序，可以向这个地址发 HTTP 请求。

前端把用户输入发给后端聊天接口, 然后后端执行：
接收请求
→ 调 ChatAgent
→ 拿到结果
→ 返回 JSON
"""



"""
后端 API URL
例如：
/api/chat
/api/trip
/api/poi
/api/map

作用：
接收数据、执行业务、返回 JSON
"""


"""
比如前端点“发送”按钮后，可能做：
Vue 页面
→ fetch/axios 请求 POST /api/chat
→ FastAPI route 接住
→ services.chat.send(...)
→ 返回 JSON
→ Vue 把 reply 显示出来

所以你虽然可能只有两三个实际页面，但后端完全可以有十几个、几十个 URL，因为：
一个页面会调用很多不同 API。
"""