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


def create_app(service_factory=build_services) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app):
        async with service_factory() as services:
            app.state.services = services
            yield

    settings = get_settings()
    app = FastAPI(title=settings.app_name, version='1.0.0', lifespan=lifespan)
    app.add_middleware(CORSMiddleware, allow_origins=settings.allowed_origins,
                       allow_methods=['GET', 'POST'], allow_headers=['Content-Type'])
    for module in (trip, map, poi, chat):
        app.include_router(module.router, prefix='/api')

    @app.exception_handler(ServiceError)
    async def service_error(_request: Request, exc: ServiceError):
        return JSONResponse(status_code=exc.status_code, content={'success': False, 'detail': str(exc)})

    @app.exception_handler(Exception)
    async def unexpected_error(_request: Request, exc: Exception):
        logging.getLogger(__name__).error('Request failed: %s', type(exc).__name__)
        return JSONResponse(status_code=504 if isinstance(exc, TimeoutError) else 502,
                            content={'success': False, 'detail': '服务暂时不可用，请稍后重试'})

    @app.get('/health')
    async def health():
        return {'status': 'ready', 'service': settings.app_name}

    @app.get('/')
    async def root():
        return {'name': settings.app_name, 'docs': '/docs'}

    return app


app = create_app()
