from fastapi import Request
from ..services.runtime import ApplicationServices


def get_services(request: Request) -> ApplicationServices:
    return request.app.state.services
