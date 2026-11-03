"""Our local MCP server: protocol boundary between agents and Amap HTTP APIs.

Use SDK 1.30.0, not an unpinned v2 example. Only bind to the local machine.
"""
#本地 MCP Server 是一层「协议化的服务边界」：对内封装高德 HTTP 细节、密钥、重试、清洗，对外用标准 MCP 协议暴露工具，让 Agent 只关心「调什么工具、传什么参数」，不关心背后怎么实现。
import logging
import os
from mcp.server.fastmcp import FastMCP

from app.config import get_settings
from app.services.amap_http import AmapHTTP
from app.services.errors import ServiceError

logging.getLogger('httpx').setLevel(logging.WARNING)  # httpx 这个库默认会在 INFO/DEBUG 级别打印每次请求的日志（发往哪个 URL、用什么方法、返回什么状态码, 把 httpx 的 logger 调到 WARNING，意味着只有警告及以上才输出，正常的请求日志被静音了。这是生产环境的常见做法。
mcp = FastMCP('amap-travel', host='127.0.0.1',
              port=int(os.environ.get('TRIP_MCP_PORT', '8001')), json_response=True)  # 创建了一个本地的MCP Server
amap = AmapHTTP(get_settings().amap_api_key.get_secret_value())    # amap就是一个已经配置好高德Key的 AmapHTTP对象， AmapHTTP中的调用链: 先取出Settings里的高德api, 然后用get_secret_value()把api key密文取出来, 本质上相当于AmapHTTP(amap_api_key)
                                                                   # 把这个 key 存为实例属性，之后所有 search、weather、detail、route 请求都自动带上它。调用方不用每次传 key。高德 API 的认证方式就是「URL 里带 key」
                                                                   # 这个url会在AmapHTTP.request中被拼接, httpx把完整请求报文发送到高德服务器, 返回JSON后再清洗，异常处理，序列化等
async def safe_call(operation):    #  统一给所有地图工具套一层异常保护, MCP 层负责把内部异常转换成 Agent 能安全读取的工具结果
    try:
        return await operation
    except ServiceError as exc:
        return {'error': str(exc)}
    except Exception:
        return {'error': '地图数据处理失败，请稍后重试'}


@mcp.tool()   # 这个装饰器把下面的py函数注册成 MCP Server 对外提供的工具, 加了以后，MCP Client / Agent 才能发现：有一个工具叫：maps_text_search
async def maps_text_search(keywords: str, city: str, kind: str = '') -> dict:
    """搜索真实 POI，返回 id、名称、地址、坐标。景点 kind=110000，酒店 kind=100000。"""     # docstring告知Tool Calling模型这个工具有什么用
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


if __name__ == '__main__':  # 直接运行这个文件时，启动 MCP Server。
    mcp.run(transport='streamable-http')
