import asyncio
from uuid import UUID
from fastapi import APIRouter, Depends
from ...models.schemas import ChatRequest
from ...services.runtime import ApplicationServices
from ..dependencies import get_services

router = APIRouter(prefix='/chat', tags=['持久化对话'])


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
