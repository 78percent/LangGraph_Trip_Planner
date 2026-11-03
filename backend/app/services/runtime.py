"""Create and close shared resources in the same async lifespan task."""

from contextlib import asynccontextmanager
from dataclasses import dataclass

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from ..agents.chat_agent import ChatAgent
from ..agents.trip_planner_agent import MultiAgentTripPlanner
from ..config import get_settings
from .amap_service import AmapService
from .llm_service import get_llm
from .repository_service import Repository
from .unsplash_service import UnsplashService


@dataclass
class ApplicationServices:
    repository: Repository
    amap: AmapService
    planner: MultiAgentTripPlanner
    chat: ChatAgent
    photos: UnsplashService


@asynccontextmanager
async def build_services():
    settings = get_settings()           # 读取配置
    settings.validate_required()        # validate_required()检查必要项
    async with AsyncConnectionPool(     # 创建 PostgreSQL 连接池。后面的 Repository 和 AsyncPostgresSaver 都共用这个池。
        settings.database_url.get_secret_value(), min_size=1, max_size=8,
        kwargs={'autocommit': True, 'prepare_threshold': 0, 'row_factory': dict_row},
        open=False, timeout=10,
    ) as pool:
        await pool.wait(timeout=10)
        repository = Repository(pool)
        await repository.setup()        # 创建业务数据库层，顺便确保 travel_sessions / travel_plans 表存在。
        saver = AsyncPostgresSaver(pool)
        await saver.setup()             # 给 LangGraph 保存 checkpoint / messages 状态。
        async with AmapService.connect() as amap:   # 把高德/MCP 那一套连接建立起来，拿到可用的 amap 服务对象
            llm = get_llm(settings)     # 创建 LLM，然后把所有东西组装起来
            yield ApplicationServices(
                repository=repository, amap=amap,
                planner=MultiAgentTripPlanner(llm, amap, repository),
                chat=ChatAgent(llm, list(amap.tools.values()), saver, repository),
                photos=UnsplashService(settings.unsplash_access_key.get_secret_value()),
            )
"""
yield段做的事情:
repository → 数据库业务操作
amap       → 高德工具
planner    → 行程规划功能
chat       → 自由聊天 Agent
photos     → Unsplash 图片服务
"""

"""
这个 services 里面装的是一堆已经创建好的东西：
services.repository
services.amap
services.planner
services.chat
services.photos

后端启动时, build_services()
→ 创建所有服务
→ 打包成 ApplicationServices
→ 存到 app.state.services

接口收到请求时, get_services(request)就会把所有服务从工具箱里拿出来
拿到service, 再去调用service.amap services.planner...
"""