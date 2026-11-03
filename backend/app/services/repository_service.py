"""PostgreSQL business records, separate from LangGraph's internal checkpoints."""

from uuid import UUID, uuid4

from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from psycopg_pool import AsyncConnectionPool

from ..models.schemas import TripPlan, TripRequest


class Repository:
    def __init__(self, pool: AsyncConnectionPool):
        self.pool = pool

    async def setup(self) -> None:      # 最初的建表语句
        async with self.pool.connection() as conn:
            await conn.execute('''CREATE TABLE IF NOT EXISTS travel_sessions (
                id UUID PRIMARY KEY, title TEXT NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now())''')
            await conn.execute('''CREATE TABLE IF NOT EXISTS travel_plans (
                id UUID PRIMARY KEY, request JSONB NOT NULL, plan JSONB NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now())''')

    async def create_session(self, title: str) -> UUID:   # 创建一个新的对话session
        session_id = uuid4()
        async with self.pool.connection() as conn:
            await conn.execute('INSERT INTO travel_sessions (id, title) VALUES (%s, %s)',
                               (session_id, title[:60]))
        return session_id

    async def session_exists(self, session_id: UUID) -> bool:   # 检查某个 session_id 在数据库里到底存不存在
        async with self.pool.connection() as conn:
            result = await conn.execute('SELECT 1 FROM travel_sessions WHERE id = %s', (session_id,))   # 不关心整条会话数据，只想知道“有没有”，所以查个 1 就够
            return await result.fetchone() is not None

    async def touch_session(self, session_id: UUID) -> None:   # 更新session内容上次修改的时间
        async with self.pool.connection() as conn:
            await conn.execute('UPDATE travel_sessions SET updated_at = now() WHERE id = %s', (session_id,))

    async def list_sessions(self) -> list[dict]:    # 列出所有对话记录, 这是出现在agent自由对话窗口的位置
        async with self.pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cursor:
                await cursor.execute('SELECT id, title, updated_at FROM travel_sessions ORDER BY updated_at DESC LIMIT 100')
                return await cursor.fetchall()

    async def save_plan(self, request: TripRequest, plan: TripPlan) -> TripPlan:   # 把这次规划完成的旅行计划存入travel_plans表中
        saved = plan.model_copy(update={'id': uuid4()})
        async with self.pool.connection() as conn:
            await conn.execute('INSERT INTO travel_plans (id, request, plan) VALUES (%s, %s, %s)',
                (saved.id, Jsonb(request.model_dump(mode='json')), Jsonb(saved.model_dump(mode='json'))))
        return saved

    async def get_plan(self, plan_id: UUID) -> dict | None:  # 找出我想要的那条旅行计划，从travel_plans表中按照plan_id去找
        async with self.pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cursor:
                await cursor.execute('SELECT request, plan FROM travel_plans WHERE id = %s', (plan_id,))
                return await cursor.fetchone()

    async def list_plans(self) -> list[dict]:     # # 列出最近 100 条已保存旅行计划的摘要信息
        async with self.pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cursor:
                await cursor.execute('''SELECT id, created_at, plan->>'city' AS city,
                    plan->>'start_date' AS start_date, plan->>'end_date' AS end_date
                    FROM travel_plans ORDER BY created_at DESC LIMIT 100''')
                return await cursor.fetchall()
