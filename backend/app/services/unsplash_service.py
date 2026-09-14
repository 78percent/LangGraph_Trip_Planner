"""Optional image lookup. Missing credentials or photos do not fail a trip."""

import httpx


class UnsplashService:
    def __init__(self, access_key: str):
        self.access_key = access_key

    async def get_photo_url(self, query: str) -> str | None:
        if not self.access_key:
            return None
        try:
            async with httpx.AsyncClient(timeout=8) as client:
                response = await client.get('https://api.unsplash.com/search/photos',
                    headers={'Authorization': f'Client-ID {self.access_key}'},
                    params={'query': query, 'per_page': 1})
                response.raise_for_status()
                results = response.json().get('results', [])
                return results[0]['urls']['small'] if results else None
        except (httpx.HTTPError, ValueError, KeyError):
            return None
