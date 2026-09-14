"""High-level Amap HTTP operations, called only by our MCP server."""

import asyncio
import httpx

from ..models.schemas import Location, POIInfo, WeatherInfo
from .errors import ServiceError


class AmapHTTP:
    def __init__(self, api_key: str, transport: httpx.AsyncBaseTransport | None = None):
        self.api_key = api_key
        self.transport = transport

    async def request(self, path: str, **params) -> dict:
        # All operations are read-only GETs. Retry transient transport/5xx failures
        # once; do not retry invalid credentials or ordinary client errors.
        for attempt in range(2):
            try:
                async with httpx.AsyncClient(timeout=httpx.Timeout(15, connect=5),
                                             transport=self.transport) as client:
                    response = await client.get('https://restapi.amap.com/v3/' + path,
                                                params={'key': self.api_key, **params})
                    response.raise_for_status()
                    data = response.json()
                break
            except (httpx.HTTPError, ValueError) as exc:
                transient = isinstance(exc, httpx.TransportError) or (
                    isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code >= 500)
                if transient and attempt == 0:
                    await asyncio.sleep(0.4)
                    continue
                raise ServiceError('高德服务连接失败或返回异常，请稍后重试') from exc
        if data.get('status') != '1':
            # Only the documented numeric status is forwarded, never the request URL.
            code = str(data.get('infocode', 'unknown'))
            safe_code = code if code.isdigit() else 'unknown'
            raise ServiceError(f'高德查询未成功，错误码 {safe_code}')
        return data

    @staticmethod
    def parse_poi(item: dict) -> POIInfo | None:
        try:
            lon, lat = str(item.get('location', '')).split(',')
            return POIInfo(
                id=item['id'], name=item['name'], address=item.get('address') or '',
                location=Location(longitude=float(lon), latitude=float(lat)),
                type=item.get('type') or '',
                photos=[p['url'] for p in item.get('photos', []) if p.get('url')],
            )
        except (ValueError, KeyError, TypeError):
            # A point without valid coordinates cannot become a map marker.
            return None

    async def search(self, keywords: str, city: str, kind: str = '') -> dict:
        data = await self.request('place/text', keywords=keywords, city=city,
                                  citylimit='true', types=kind, offset=20, extensions='all')
        points = [point for item in data.get('pois', []) if (point := self.parse_poi(item))]
        return {'pois': [point.model_dump() for point in points]}

    async def detail(self, poi_id: str) -> dict:
        data = await self.request('place/detail', id=poi_id, extensions='all')
        points = [point for item in data.get('pois', []) if (point := self.parse_poi(item))]
        if not points:
            raise ServiceError('没有找到可用的景点详情', 404)
        return points[0].model_dump()

    async def city_info(self, city: str) -> dict:
        data = await self.request('geocode/geo', address=city, city=city)
        matches = data.get('geocodes', [])
        if not matches:
            raise ServiceError('未能识别目的地城市，请输入完整城市名称', 422)
        return matches[0]

    async def weather(self, city: str) -> dict:
        info = await self.city_info(city)
        data = await self.request('weather/weatherInfo', city=info['adcode'], extensions='all')
        forecasts = data.get('forecasts', [])
        if not forecasts:
            return {'forecasts': []}
        def temperature(value):
            try:
                return int(value)
            except (TypeError, ValueError):
                return None
        items = [WeatherInfo(
            date=item['date'], day_weather=item['dayweather'], night_weather=item['nightweather'],
            day_temp=temperature(item.get('daytemp')), night_temp=temperature(item.get('nighttemp')),
            wind_direction=item.get('daywind', ''), wind_power=item.get('daypower', ''),
        ).model_dump(mode='json') for item in forecasts[0].get('casts', [])]
        return {'forecasts': items, 'report_time': forecasts[0].get('reporttime', '')}

    async def route(self, origin: str, destination: str, city: str, route_type: str) -> dict:
        paths = {'walking': 'direction/walking', 'driving': 'direction/driving',
                 'transit': 'direction/transit/integrated'}
        if route_type not in paths:
            raise ServiceError('不支持的交通方式', 422)
        params = {'origin': origin, 'destination': destination, 'extensions': 'all'}
        if route_type == 'transit':
            info = await self.city_info(city)
            params.update(city=info.get('citycode') or info['adcode'], cityd=info.get('citycode') or info['adcode'])
        data = await self.request(paths[route_type], **params)
        route = data.get('route', {})
        choices = route.get('transits' if route_type == 'transit' else 'paths', [])
        if not choices:
            raise ServiceError('当前起终点没有可用路线', 404)
        choice = choices[0]
        steps = choice.get('steps', [])
        if route_type == 'transit':
            steps = []
            for segment in choice.get('segments', []):
                steps.extend(segment.get('walking', {}).get('steps', []))
                steps.extend(segment.get('bus', {}).get('buslines', []))
        coordinates = []
        for step in steps:
            for point in str(step.get('polyline', '')).split(';'):
                try:
                    lon, lat = point.split(',')
                    coordinates.append([float(lon), float(lat)])
                except ValueError:
                    continue
        return {'distance': float(choice.get('distance') or 0),
                'duration': int(choice.get('duration') or 0), 'route_type': route_type,
                'polyline': coordinates, 'description': '高德实际路线查询结果'}
