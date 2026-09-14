"""Trip endpoints: HTTP parsing here; graph execution and persistence elsewhere."""

import asyncio
import json
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from ...models.schemas import TripRequest, TripPlanResponse, RevisionRequest
from ...services.errors import ServiceError
from ...services.runtime import ApplicationServices
from ..dependencies import get_services

router = APIRouter(prefix='/trip', tags=['旅行规划'])


@router.post('/plan', response_model=TripPlanResponse)
async def plan_trip(request: TripRequest, services: ApplicationServices = Depends(get_services)):
    async with asyncio.timeout(240):
        return TripPlanResponse(data=await services.planner.plan_trip(request))


@router.post('/plan/stream')
async def stream_plan(request: TripRequest, services: ApplicationServices = Depends(get_services)):
    async def events():
        try:
            async with asyncio.timeout(240):
                async for event in services.planner.stream_trip(request):
                    yield json.dumps(event, ensure_ascii=False) + '\n'
        except ServiceError as exc:
            yield json.dumps({'type': 'error', 'message': str(exc)}, ensure_ascii=False) + '\n'
        except TimeoutError:
            yield json.dumps({'type': 'error', 'message': '规划超时，请减少天数后重试'}, ensure_ascii=False) + '\n'
        except Exception:
            yield json.dumps({'type': 'error', 'message': '模型或存储服务异常，本次未返回有效行程'}, ensure_ascii=False) + '\n'
    return StreamingResponse(events(), media_type='application/x-ndjson',
                             headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})


@router.get('/plans')
async def list_plans(services: ApplicationServices = Depends(get_services)):
    return {'success': True, 'data': await services.repository.list_plans()}


@router.get('/plans/{plan_id}')
async def get_plan(plan_id: UUID, services: ApplicationServices = Depends(get_services)):
    record = await services.repository.get_plan(plan_id)
    if record is None:
        raise ServiceError('行程不存在', 404)
    return {'success': True, 'data': record['plan']}


@router.post('/plans/{plan_id}/revise', response_model=TripPlanResponse)
async def revise_plan(plan_id: UUID, revision: RevisionRequest,
                      services: ApplicationServices = Depends(get_services)):
    record = await services.repository.get_plan(plan_id)
    if record is None:
        raise ServiceError('行程不存在', 404)
    request = TripRequest.model_validate({**record['request'], 'free_text_input': revision.instruction})
    async with asyncio.timeout(240):
        plan = await services.planner.plan_trip(request, previous_plan=record['plan'])
    return TripPlanResponse(message='已另存为新行程，原计划保留', data=plan)


@router.get('/health')
async def health(services: ApplicationServices = Depends(get_services)):
    return {'status': 'ready', 'workflow': 'parallel-search -> draft -> validate -> finalize',
            'tools_count': len(services.amap.tools)}
