from fastapi import APIRouter, Depends, Query
from ...models.schemas import RouteRequest
from ...services.runtime import ApplicationServices
from ..dependencies import get_services

router = APIRouter(prefix='/map', tags=['地图'])


@router.get('/poi')
async def search_poi(keywords: str = Query(min_length=1, max_length=100),
                     city: str = Query(min_length=1, max_length=60),
                     services: ApplicationServices = Depends(get_services)):
    return {'success': True, 'data': await services.amap.search_poi(keywords, city)}


@router.get('/weather')
async def weather(city: str = Query(min_length=1, max_length=60),
                  services: ApplicationServices = Depends(get_services)):
    return {'success': True, 'data': await services.amap.get_weather(city)}


@router.post('/route')
async def route(request: RouteRequest, services: ApplicationServices = Depends(get_services)):
    return {'success': True, 'data': await services.amap.plan_route(request)}


@router.get('/health')
async def health(services: ApplicationServices = Depends(get_services)):
    return {'status': 'connected', 'tools': list(services.amap.tools)}
