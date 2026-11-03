"""High-level Amap HTTP operations, called only by our MCP server."""

import asyncio
import httpx

from ..models.schemas import Location, POIInfo, WeatherInfo
from .errors import ServiceError


class AmapHTTP:   # transport 是httpx 的底层网络传输对象，主要方便测试或自定义网络行为,正常业务里大概是None。不重要
    def __init__(self, api_key: str, transport: httpx.AsyncBaseTransport | None = None):
        self.api_key = api_key      # 存放高德api_key
        self.transport = transport

    async def request(self, path: str, **params) -> dict:  #参数提供“高德接口路径 + 查询参数”，我负责发送请求并把 JSON 返回给你
        # All operations are read-only GETs. Retry transient transport/5xx failures
        # once; do not retry invalid credentials or ordinary client errors.
        for attempt in range(2):   # 最多尝试2次，防止工具无限调用or网络卡死死循环
            try:
                async with httpx.AsyncClient(timeout=httpx.Timeout(15, connect=5), # 创建异步HTTP客户端，连接阶段最多等 5 秒
                                             transport=self.transport) as client:         # httpx.AsyncClient 是 异步版“发 HTTP 请求的工具”
                    response = await client.get('https://restapi.amap.com/v3/' + path,   # 拼接url向高德发送请求
                                                params={'key': self.api_key, **params})
                    response.raise_for_status()     # 检查 HTTP 状态
                    data = response.json()          # 把 HTTP 返回的 JSON 转成 Python 数据
                break
            except (httpx.HTTPError, ValueError) as exc:  # 捕获HTTP 网络 / 状态错误 或者 JSON 解析等 ValueError
                transient = isinstance(exc, httpx.TransportError) or (
                    isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code >= 500)
                if transient and attempt == 0:      # 判断这个错误是不是“临时错误，值得重试一次
                    await asyncio.sleep(0.4)        # TransportError 例如断网、连接失败、超时； HTTP >= 500 例如高德服务器暂时炸了
                    continue                        # 如果是临时错误, 并且这是第一次失败, 那就重新进入 for 再请求一次
                raise ServiceError('高德服务连接失败或返回异常，请稍后重试') from exc   #  如果第二次还失败：
        if data.get('status') != '1':               # 高德 API 有个特点：HTTP 状态码是 200，但业务上可能失败，靠响应体里的 status 字段区分：
            # Only the documented numeric status is forwarded, never the request URL.  #status == '1'：成功。其他：失败，infocode 里是具体错误码。
            code = str(data.get('infocode', 'unknown'))
            safe_code = code if code.isdigit() else 'unknown'
            raise ServiceError(f'高德查询未成功，错误码 {safe_code}')
        return data

    @staticmethod
    def parse_poi(item: dict) -> POIInfo | None:   # 数据清洗, 输入高德返回的一个 POI 字典, 输出POIInfo或者None
        try:                                       # POI 就是 一个地图兴趣点，例如景点、酒店、餐厅
            lon, lat = str(item.get('location', '')).split(',')   # 拆解坐标 例如:"location": "121.490317,31.241701"
            return POIInfo(
                id=item['id'], name=item['name'], address=item.get('address') or '',   # 返回一个POIInfo对象, 已经在schemas.py中定义了POIInfo类
                location=Location(longitude=float(lon), latitude=float(lat)),
                type=item.get('type') or '',
                photos=[p['url'] for p in item.get('photos', []) if p.get('url')],
            )
        except (ValueError, KeyError, TypeError):   #ValueError：坐标拆分失败、float() 转换失败、 KeyError：缺 id 或 name、 TypeError：字段类型不对（比如 photos 不是列表）
            # A point without valid coordinates cannot become a map marker.
            return None     #只要出问题就返回 None，不抛异常， 这是防御式解析——单个 POI 脏数据不应该让整个搜索失败，过滤掉即可

    async def search(self, keywords: str, city: str, kind: str = '') -> dict:  #
        data = await self.request('place/text', keywords=keywords, city=city,
                                  citylimit='true', types=kind, offset=20, extensions='all')
        points = [point for item in data.get('pois', []) if (point := self.parse_poi(item))]  # 先执行 parse_poi(item)，把结果赋给 point，然后再判断 point 有没有值
        return {'pois': [point.model_dump() for point in points]}       # 把 POIInfo 对象转回字典, 因为上游是 LangGraph 的 ToolNode，工具返回值需要是可序列化的内容（最终会变成 ToolMessage 的 content）
                                                                        # Pydantic 对象不能直接当 ToolMessage 内容，转成字典后就能被 JSON 序列化，模型也能读懂
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
                 'transit': 'direction/transit/integrated'}                         # 三种交通方式映射到不同 path
        if route_type not in paths:
            raise ServiceError('不支持的交通方式', 422)           # 不支持的类型抛 422
        params = {'origin': origin, 'destination': destination, 'extensions': 'all'}
        if route_type == 'transit':
            info = await self.city_info(city)                                       # transit 需要先查 city_info 拿 citycode，因为公交接口要城市编码
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
