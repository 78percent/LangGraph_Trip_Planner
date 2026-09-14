from fastapi import APIRouter, Depends, Query
from ...services.runtime import ApplicationServices
from ..dependencies import get_services

router = APIRouter(prefix='/poi', tags=['兴趣点'])


@router.get('/detail/{poi_id}')
async def detail(poi_id: str, services: ApplicationServices = Depends(get_services)):
    return {'success': True, 'data': await services.amap.get_poi_detail(poi_id)}


@router.get('/search')
async def search(keywords: str = Query(min_length=1, max_length=100),
                  city: str = Query(min_length=1, max_length=60),
                  services: ApplicationServices = Depends(get_services)):
    return {'success': True, 'data': await services.amap.search_poi(keywords, city)}


@router.get('/photo')
async def photo(name: str = Query(min_length=1, max_length=100),
                 services: ApplicationServices = Depends(get_services)):
    return {'success': True, 'data': {'photo_url': await services.photos.get_photo_url(name)}}
