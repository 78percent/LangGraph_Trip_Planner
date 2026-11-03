"""MCP client shared by graph nodes, chat tools and HTTP routes."""

import asyncio
import json
import os
import socket
import subprocess
import sys
from contextlib import asynccontextmanager

import httpx

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools

from ..config import BACKEND_DIR
from ..models.schemas import POIInfo, WeatherInfo
from .errors import ServiceError


class AmapService:
    def __init__(self, tools):
        self.tools = {tool.name: tool for tool in tools}

    @classmethod
    @asynccontextmanager      #启动时类似 async with AmapService.connect() as amap:
    async def connect(cls):   #启动 MCP Server → 连上它 → 加载工具 → 创建 AmapService → 用完以后关闭 MCP Server
        with socket.socket() as listener:
            listener.bind(('127.0.0.1', 0))     # 让操作系统替我找一个当前空闲端口
            port = listener.getsockname()[1]
        process = subprocess.Popen(             # 把刚找到的端口塞进环境变量
            [sys.executable, str(BACKEND_DIR / 'mcp_server.py')],
            env={**os.environ, 'TRIP_MCP_PORT': str(port)},
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0,
        )
        url = f'http://127.0.0.1:{port}/mcp'
        def local_http_client(**kwargs):
            # Windows system proxy settings must not redirect the local MCP channel.
            return httpx.AsyncClient(**kwargs, trust_env=False, follow_redirects=True)
        client = MultiServerMCPClient({'amap': {
            'transport': 'streamable_http', 'url': url, 'timeout': 40,
            'httpx_client_factory': local_http_client,
        }})             # 创建 MCP Client, MultiServerMCPClient是LangChain 这一边用于连接 MCP Server 的客户端
        try:
            async with httpx.AsyncClient(timeout=1, trust_env=False) as http:
                for _ in range(80):                     # MCP Server 就绪检测
                    if process.poll() is not None:      # 子进程直接死了
                        raise ServiceError('本机 MCP 服务启动失败，请检查依赖和配置')
                    try:
                        await http.get(url)
                        break
                    except httpx.HTTPError:
                        await asyncio.sleep(0.25)
                else:                                   # 一直起不来
                    raise ServiceError('本机 MCP 服务启动超时')
            async with client.session('amap') as session:   # 和名叫 amap 的 MCP Server 建立一次 session
                yield cls(await load_mcp_tools(session))    # 去 MCP Server 问 “你那里有哪些工具？” 即mcp_server.py里的4工具加载回来, 返回MCP Tools列表
        finally:
            if process.poll() is None:
                process.terminate()                     # 让 MCP 子进程退出
                try:
                    await asyncio.to_thread(process.wait, timeout=5)    # 最多等 5 秒
                except subprocess.TimeoutExpired:
                    process.kill()                      # 如果它还赖着不走, 就杀掉进程
                    await asyncio.to_thread(process.wait)

    async def call(self, name: str, arguments: dict) -> dict:  # 统一调用所有 MCP Tool
        try:
            async with asyncio.timeout(40):                      # MCP Tool 40 秒还没回来，就别无限等
                raw = await self.tools[name].ainvoke(arguments)  # 真正调用工具
            if isinstance(raw, dict):                          # MCP 工具返回结果有时已经是dict, 所以这一层做统一处理
                data = raw
            else:
                text = raw if isinstance(raw, str) else '\n'.join(
                    block.get('text', '') for block in raw if isinstance(block, dict))
                data = json.loads(text)
            if not isinstance(data, dict):                  # 进一步保证AmapService 往上层交的数据必须是字典
                raise ValueError('Expected an object')
        except Exception as exc:
            raise ServiceError('地图工具超时或返回格式异常') from exc
        if data.get('error'):
            raise ServiceError(str(data['error']))
        return data

    async def search_poi(self, keywords: str, city: str, kind: str = '') -> list[POIInfo]:
        data = await self.call('maps_text_search', {'keywords': keywords, 'city': city, 'kind': kind})
        return [POIInfo.model_validate(item) for item in data.get('pois', [])]

    async def get_weather(self, city: str) -> list[WeatherInfo]:
        data = await self.call('maps_weather', {'city': city})
        return [WeatherInfo.model_validate(item) for item in data.get('forecasts', [])]

    async def get_poi_detail(self, poi_id: str) -> dict:
        return await self.call('maps_search_detail', {'poi_id': poi_id})

    async def plan_route(self, request) -> dict:
        def coordinates(location):
            return f'{location.longitude},{location.latitude}'
        return await self.call('maps_route', {
            'origin': coordinates(request.origin), 'destination': coordinates(request.destination),
            'city': request.city, 'route_type': request.route_type,
        })

#AmapService 是主 Backend 里的 MCP 客户端服务：负责启动本地 MCP Server、连上它、加载 MCP Tools、
#统一调用 Tool，并把结果整理成项目自己的 Pydantic 数据。


"""
connect()的整个生命周期：
找端口
↓
启动 MCP
↓
等 MCP ready
↓
连接
↓
加载 tools
↓
给业务代码使用
↓
关闭 MCP
"""