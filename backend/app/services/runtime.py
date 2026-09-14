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
    settings = get_settings()
    settings.validate_required()
    async with AsyncConnectionPool(
        settings.database_url.get_secret_value(), min_size=1, max_size=8,
        kwargs={'autocommit': True, 'prepare_threshold': 0, 'row_factory': dict_row},
        open=False, timeout=10,
    ) as pool:
        await pool.wait(timeout=10)
        repository = Repository(pool)
        await repository.setup()
        saver = AsyncPostgresSaver(pool)
        await saver.setup()
        async with AmapService.connect() as amap:
            llm = get_llm(settings)
            yield ApplicationServices(
                repository=repository, amap=amap,
                planner=MultiAgentTripPlanner(llm, amap, repository),
                chat=ChatAgent(llm, list(amap.tools.values()), saver, repository),
                photos=UnsplashService(settings.unsplash_access_key.get_secret_value()),
            )
