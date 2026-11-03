from fastapi import Request
from ..services.runtime import ApplicationServices


def get_services(request: Request) -> ApplicationServices:      # 一个从 FastAPI 的 request 里把刚才存进去的 services 拿出来的小工具。
    return request.app.state.services

"""
前面你已经有：
app.state.services = services
这里就是反向取：
def get_services(request: Request) -> ApplicationServices:
    return request.app.state.services
所以链条是：
FastAPI 启动
→ build_services()
→ app.state.services = services

接口收到请求
→ get_services(request)
→ request.app.state.services
→ 拿到 repository / chat / planner / amap 等服务
"""