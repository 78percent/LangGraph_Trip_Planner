from contextlib import asynccontextmanager
from types import SimpleNamespace
from uuid import uuid4

import httpx

from app.api.main import create_app
from app.agents.trip_planner_agent import MultiAgentTripPlanner
from test_workflow import FakeAmap, FakeModel, FakeRepository, draft


@asynccontextmanager
async def services():
    yield SimpleNamespace(planner=MultiAgentTripPlanner(FakeModel([draft()]), FakeAmap(), FakeRepository()))


async def test_invalid_request_is_rejected_without_external_calls():
    app = create_app(services)
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
            response = await client.post('/api/trip/plan', json={'city': '杭州'})
            assert response.status_code == 422


async def test_stream_has_real_node_updates_and_final_result():
    import json
    app = create_app(services)
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
            response = await client.post('/api/trip/plan/stream', json={
                'city': '杭州', 'start_date': '2026-10-01', 'end_date': '2026-10-01', 'travel_days': 1})
            assert response.status_code == 200
            events = [json.loads(line) for line in response.text.splitlines()]
            assert events[-1]['type'] == 'result'
            assert events[-1]['data']['days'][0]['attractions'][0]['poi_id'] == 'p1'
            assert sum(event['type'] == 'progress' for event in events) >= 6
