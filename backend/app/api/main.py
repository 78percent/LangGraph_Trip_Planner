"""FastAPI composition root. Resources are owned by lifespan, never by imports."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ..config import get_settings
from ..services.errors import ServiceError
from ..services.runtime import build_services
from .routes import trip, map, poi, chat


def create_app(service_factory=build_services) -> FastAPI:  # 创建fastapi对象
    @asynccontextmanager                                    # 定义lifespan,在fastapi启动时进入lifespan
    async def lifespan(app):
        async with service_factory() as services:           # 拿到build_services()创建的services
            app.state.services = services                   # 放进app.state.services
            yield

    settings = get_settings()
    app = FastAPI(title=settings.app_name, version='1.0.0', lifespan=lifespan)  # 此处真正创建了FastAPI对象, 后续若干参数对其进行配置，启动和关闭时，用这个 lifespan 管理资源。
    app.add_middleware(CORSMiddleware, allow_origins=settings.allowed_origins,  #CORS添加跨域配置
                       allow_methods=['GET', 'POST'], allow_headers=['Content-Type'])
    for module in (trip, map, poi, chat):                   # 这些模块都可以在/api/routes里找到
        app.include_router(module.router, prefix='/api')    # 把几个路由模块注册进 FastAPI

    @app.exception_handler(ServiceError)                    # 统一异常处理: 只要抛出你自定义的 ServiceError，FastAPI 都统一在这里接住，然后转成 JSON 返回给前端
    async def service_error(_request: Request, exc: ServiceError):
        return JSONResponse(status_code=exc.status_code, content={'success': False, 'detail': str(exc)})

    @app.exception_handler(Exception)                       # 不是 ServiceError 的其他未知错误，都来这里
    async def unexpected_error(_request: Request, exc: Exception):
        logging.getLogger(__name__).error('Request failed: %s', type(exc).__name__)
        return JSONResponse(status_code=504 if isinstance(exc, TimeoutError) else 502, # 如果是504超时错误就返回504， 其他时候返回502
                            content={'success': False, 'detail': '服务暂时不可用，请稍后重试'})

    @app.get('/health')
    async def health():             # 健康检查接口/health, 看看后端是不是活着
        return {'status': 'ready', 'service': settings.app_name}

    @app.get('/')                   # 这是根路径, 访问根路径iiu返回应用名name和文档地址/docs
    async def root():
        return {'name': settings.app_name, 'docs': '/docs'}

    return app                      #create_app() 前面配置了半天，最后把这个完整的 FastAPI 应用对象返回出去。


app = create_app()


"""
exception_handler会接住我自定义抛出的ServiceError，被FastAPI接住后转成JSON返回给前端
raise ServiceError('会话不存在', 404)

最后前端收到：
{
  "success": false,
  "detail": "会话不存在"
}
"""

"""
创建 FastAPI app
→ 配置 lifespan
→ 配置跨域
→ 注册 router
→ 注册异常处理
→ 注册基础接口
→ return app
"""