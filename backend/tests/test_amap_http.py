"""Retry only transient failures; keep keys out of surfaced errors."""

import httpx
import pytest

from app.services.amap_http import AmapHTTP
from app.services.errors import ServiceError


async def test_one_transient_failure_is_retried():
    calls = 0

    def handle(request):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise httpx.ReadTimeout('temporary timeout', request=request)
        return httpx.Response(200, json={'status': '1', 'pois': []})

    service = AmapHTTP('test-only-key', transport=httpx.MockTransport(handle))
    result = await service.search('西湖', '杭州')
    assert result == {'pois': []}
    assert calls == 2


async def test_invalid_credentials_are_not_retried():
    calls = 0

    def handle(_request):
        nonlocal calls
        calls += 1
        return httpx.Response(200, json={'status': '0', 'infocode': '10001'})

    service = AmapHTTP('test-only-key', transport=httpx.MockTransport(handle))
    with pytest.raises(ServiceError, match='10001') as caught:
        await service.search('西湖', '杭州')
    assert calls == 1
    assert 'test-only-key' not in str(caught.value)


async def test_repeated_timeout_stops_after_two_attempts():
    calls = 0

    def handle(request):
        nonlocal calls
        calls += 1
        raise httpx.ReadTimeout('https://example.test/?key=test-only-key', request=request)

    service = AmapHTTP('test-only-key', transport=httpx.MockTransport(handle))
    with pytest.raises(ServiceError) as caught:
        await service.search('西湖', '杭州')
    assert calls == 2
    assert 'test-only-key' not in str(caught.value)
