"""Deterministic regression tests: no model requests, API keys or database needed."""

import asyncio
from datetime import date
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.agents.trip_planner_agent import MultiAgentTripPlanner
from app.models.schemas import TripRequest, POIInfo, PlanDraft, Location
from app.services.errors import ServiceError
from app.services.plan_service import validate_draft, assemble_plan


def request(days=1):
    return TripRequest(city='杭州', start_date='2026-10-01', end_date=f'2026-10-{days:02d}', travel_days=days)


def point(poi_id='p1', name='真实景点'):
    return POIInfo(id=poi_id, name=name, address='真实地址', location=Location(longitude=120.1, latitude=30.2))


def draft(days=1, poi_id='p1'):
    return PlanDraft.model_validate({'days': [{
        'date': f'2026-10-{index + 1:02d}', 'description': '轻松游览',
        'attractions': [{'poi_id': poi_id, 'visit_duration': 90, 'description': '游览建议', 'ticket_price': 40}],
        'hotel_id': 'h1' if index < days - 1 else None, 'hotel_cost': 300,
        'meals': [{'type': kind, 'name': '餐饮建议', 'estimated_cost': 20}
                  for kind in ('breakfast', 'lunch', 'dinner')], 'transportation_cost': 10,
    } for index in range(days)], 'overall_suggestions': '提前核实营业时间'})


class FakeModel:
    def __init__(self, outputs):
        self.outputs = iter(outputs)
        self.calls = 0

    def with_structured_output(self, *_args, **_kwargs):
        return self

    async def ainvoke(self, _messages):
        self.calls += 1
        return next(self.outputs)


class FakeAmap:
    async def search_poi(self, _keyword, _city, kind):
        return [point('h1', '真实酒店')] if kind == '100000' else [point()]

    async def get_weather(self, _city):
        return []


class FakeRepository:
    def __init__(self):
        self.saved = []

    async def save_plan(self, req, plan):
        self.saved.append(plan)
        return plan.model_copy(update={'id': uuid4()})


def test_dates_rejected():
    with pytest.raises(ValidationError):
        TripRequest(city='杭州', start_date='2026-10-02', end_date='2026-10-01', travel_days=1)


def test_ids_dates_and_meals_are_checked():
    item = draft(poi_id='invented')
    item.days[0].date = date(2026, 10, 2)
    item.days[0].meals[0].type = 'lunch'
    errors = validate_draft(request(), item, [point()], [])
    assert len(errors) == 3


def test_costs_count_nights_and_use_canonical_coordinates():
    req, plan = request(2), draft(2)
    result = assemble_plan(req, plan, [point()], [point('h1')], [], [])
    assert result.budget.total_hotels == 300
    assert result.days[-1].hotel is None
    assert result.budget.total == 80 + 300 + 120 + 20
    assert result.days[0].attractions[0].location == point().location
    assert result.days[0].attractions[0].name == point().name
    assert result.weather_info == [] and result.warnings


async def test_invalid_draft_gets_one_repair():
    model = FakeModel([draft(poi_id='invented'), draft()])
    repo = FakeRepository()
    planner = MultiAgentTripPlanner(model, FakeAmap(), repo)
    result = await planner.plan_trip(request())
    assert result.city == '杭州' and model.calls == 2
    assert len(repo.saved) == 1


async def test_repeated_invalid_output_never_saves_fake_plan():
    model = FakeModel([draft(poi_id='invented'), draft(poi_id='invented')])
    repo = FakeRepository()
    planner = MultiAgentTripPlanner(model, FakeAmap(), repo)
    with pytest.raises(ServiceError):
        await planner.plan_trip(request())
    assert model.calls == 2 and not repo.saved


async def test_no_attractions_stops_before_model_call():
    class EmptyAmap(FakeAmap):
        async def search_poi(self, *_args):
            return []
    model, repo = FakeModel([draft()]), FakeRepository()
    planner = MultiAgentTripPlanner(model, EmptyAmap(), repo)
    with pytest.raises(ServiceError):
        await planner.plan_trip(request())
    assert model.calls == 0 and not repo.saved


async def test_optional_failures_are_visible_and_parallel_branches_join_once():
    class BarrierAmap(FakeAmap):
        def __init__(self):
            self.started = set()
            self.ready = asyncio.Event()

        async def wait(self, name):
            self.started.add(name)
            if len(self.started) == 3:
                self.ready.set()
            await asyncio.wait_for(self.ready.wait(), timeout=2)

        async def search_poi(self, _keyword, _city, kind):
            if kind == '100000':
                await self.wait('hotels')
                raise ServiceError('酒店故障')
            await self.wait('attractions')
            return [point()]

        async def get_weather(self, _city):
            await self.wait('weather')
            raise ServiceError('天气故障')
    output = draft(2)
    output.days[0].hotel_id = None
    model = FakeModel([output])
    planner = MultiAgentTripPlanner(model, BarrierAmap(), FakeRepository())
    result = await planner.plan_trip(request(2))
    assert model.calls == 1
    assert any('天气查询失败' in item for item in result.warnings)
    assert any('酒店查询失败' in item for item in result.warnings)
    assert result.budget.total_hotels == 0
