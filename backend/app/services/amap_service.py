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
    @asynccontextmanager
    async def connect(cls):
        with socket.socket() as listener:
            listener.bind(('127.0.0.1', 0))
            port = listener.getsockname()[1]
        process = subprocess.Popen(
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
        }})
        try:
            async with httpx.AsyncClient(timeout=1, trust_env=False) as http:
                for _ in range(80):
                    if process.poll() is not None:
                        raise ServiceError('本机 MCP 服务启动失败，请检查依赖和配置')
                    try:
                        await http.get(url)
                        break
                    except httpx.HTTPError:
                        await asyncio.sleep(0.25)
                else:
                    raise ServiceError('本机 MCP 服务启动超时')
            async with client.session('amap') as session:
                yield cls(await load_mcp_tools(session))
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    await asyncio.to_thread(process.wait, timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    await asyncio.to_thread(process.wait)

    async def call(self, name: str, arguments: dict) -> dict:
        try:
            async with asyncio.timeout(40):
                raw = await self.tools[name].ainvoke(arguments)
            if isinstance(raw, dict):
                data = raw
            else:
                text = raw if isinstance(raw, str) else '\n'.join(
                    block.get('text', '') for block in raw if isinstance(block, dict))
                data = json.loads(text)
            if not isinstance(data, dict):
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
