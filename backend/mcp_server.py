"""Our local MCP server: protocol boundary between agents and Amap HTTP APIs.

Use SDK 1.30.0, not an unpinned v2 example. Only bind to the local machine.
"""

import logging
import os
from mcp.server.fastmcp import FastMCP

from app.config import get_settings
from app.services.amap_http import AmapHTTP
from app.services.errors import ServiceError

logging.getLogger('httpx').setLevel(logging.WARNING)
mcp = FastMCP('amap-travel', host='127.0.0.1',
              port=int(os.environ.get('TRIP_MCP_PORT', '8001')), json_response=True)
amap = AmapHTTP(get_settings().amap_api_key.get_secret_value())


async def safe_call(operation):
    try:
        return await operation
    except ServiceError as exc:
        return {'error': str(exc)}
    except Exception:
        return {'error': '地图数据处理失败，请稍后重试'}


@mcp.tool()
async def maps_text_search(keywords: str, city: str, kind: str = '') -> dict:
    """搜索真实 POI，返回 id、名称、地址、坐标。景点 kind=110000，酒店 kind=100000。"""
    return await safe_call(amap.search(keywords, city, kind))


@mcp.tool()
async def maps_weather(city: str) -> dict:
    """查询城市当前可用的天气预报；只有返回的日期存在预报，不能外推其他日期。"""
    return await safe_call(amap.weather(city))


@mcp.tool()
async def maps_search_detail(poi_id: str) -> dict:
    """通过搜索结果中的真实 POI ID 查询详情和照片。"""
    return await safe_call(amap.detail(poi_id))


@mcp.tool()
async def maps_route(origin: str, destination: str, city: str, route_type: str = 'walking') -> dict:
    """查询实际路线。起终点格式为 经度,纬度；route_type 为 walking/driving/transit。"""
    return await safe_call(amap.route(origin, destination, city, route_type))


if __name__ == '__main__':
    mcp.run(transport='streamable-http')
