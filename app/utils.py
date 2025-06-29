from typing import List, Dict
import httpx
import asyncio

#– Helper Functions (Pagination, Filtering, Retry)

async def fetch_with_retries(url, retries=3, delay=2):
    for attempt in range(retries):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            if attempt == retries - 1:
                raise
            await asyncio.sleep(delay)

def filter_characters(data: List[dict], name_filter: str) -> List[dict]:
    return [char for char in data if name_filter.lower() in char["name"].lower()]
