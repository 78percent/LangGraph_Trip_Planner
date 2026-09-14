"""Explicit integration check. This makes paid model calls and saves demo records.

Run manually: python tests/live_smoke.py --run
Not collected by pytest. Credentials are read only from backend/.env.
"""

import asyncio
import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ['LANGSMITH_TRACING'] = 'false'
os.environ['LANGCHAIN_TRACING_V2'] = 'false'

from app.models.schemas import TripRequest, RouteRequest
from app.services.runtime import build_services
from app.services.event_loop import run_async


async def main():
    records = {}
    async with build_services() as services:
        points = await services.amap.search_poi('西湖', '杭州市', '110000')
        assert points and points[0].location.longitude > 100
        detail = await services.amap.get_poi_detail(points[0].id)
        assert detail['id'] == points[0].id
        weather = await services.amap.get_weather('杭州市')
        assert weather
        records['mcp'] = {'tools': list(services.amap.tools), 'poi_count': len(points),
                          'first_poi': points[0].name, 'forecast_dates': [str(item.date) for item in weather]}
        print(json.dumps({'mcp': records['mcp']}, ensure_ascii=True), flush=True)
        if len(points) > 1:
            route = await services.amap.plan_route(RouteRequest(
                origin=points[0].location, destination=points[1].location, city='杭州市', route_type='driving'))
            assert route['distance'] > 0 and route['polyline']
            records['route'] = {'distance': route['distance'], 'coordinates': len(route['polyline'])}
            print(json.dumps({'route': records['route']}), flush=True)
        start = date.today() + timedelta(days=1)
        request = TripRequest(city='杭州市', start_date=start, end_date=start + timedelta(days=1),
                              travel_days=2, preferences=['历史文化'], free_text_input='每天只安排两个景点，轻松游览。')
        plan = await services.planner.plan_trip(request)
        assert len(plan.days) == 2 and plan.days[0].hotel and plan.days[-1].hotel is None
        assert (await services.repository.get_plan(plan.id))['plan']['id'] == str(plan.id)
        records['plan'] = {'id': str(plan.id), 'days': len(plan.days), 'budget': plan.budget.model_dump()}
        print(json.dumps({'plan': records['plan']}, ensure_ascii=True), flush=True)
        result = await services.chat.send('请记住我的目的地是杭州市，并调用地图工具查询当地天气，只简短总结真实结果。', None)
        from uuid import UUID
        session_id = UUID(result['session_id'])
        snapshot = await services.chat.graph.aget_state(services.chat.config(session_id))
        calls = [call['name'] for m in snapshot.values['messages'] for call in getattr(m, 'tool_calls', [])]
        assert 'maps_weather' in calls
        records['chat'] = {'session_id': str(session_id), 'tool_calls': calls}
        print(json.dumps({'chat': records['chat']}), flush=True)
    # Recreate the whole runtime: messages must come from PostgreSQL, not Python memory.
    async with build_services() as services:
        history = await services.chat.history(session_id)
        assert history['messages'] and not history['pending']
        reply = await services.chat.send('我刚才说的目的地是哪座城市？只回复城市名称。', session_id)
        assert '杭州' in reply['reply']
        records['checkpoint_reconnect'] = True
    destination = Path(__file__).resolve().parents[2] / 'artifacts'
    destination.mkdir(exist_ok=True)
    (destination / 'live-smoke.json').write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')
    print('LIVE_SMOKE_PASSED', flush=True)


if __name__ == '__main__':
    if '--run' not in sys.argv:
        raise SystemExit('Pass --run to make real API calls and save demo records.')
    try:
        run_async(main())
    except Exception as exc:
        print('LIVE_SMOKE_FAILED:', type(exc).__name__, flush=True)
        def show_failure(error):
            import traceback
            print(type(error).__name__, flush=True)
            for frame in traceback.extract_tb(error.__traceback__):
                print(f'  {Path(frame.filename).name}:{frame.lineno} {frame.name}', flush=True)
            if type(error).__name__ == 'ServiceError':
                print(str(error), flush=True)
            if type(error).__name__ == 'HTTPStatusError':
                print('http_status:', error.response.status_code, flush=True)
                if error.request.url.host in ('localhost', '127.0.0.1'):
                    print('local_response:', error.response.text[:300], flush=True)
            for child in getattr(error, 'exceptions', []):
                show_failure(child)
            if error.__cause__:
                show_failure(error.__cause__)
        show_failure(exc)
        raise SystemExit(1)
