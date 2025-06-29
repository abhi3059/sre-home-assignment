from typing import List, Dict, Optional
import httpx
import asyncio
import logging

logger = logging.getLogger("rickmorty-api")

# Retry-capable fetcher for external API
async def fetch_with_retries(url: str, retries: int = 3, delay: float = 2.0) -> dict:
    for attempt in range(retries):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.warning("Fetch attempt %s failed: %s", attempt + 1, e)
            if attempt == retries - 1:
                raise
            await asyncio.sleep(delay)

# Fetch with external client (used by FastAPI endpoint)
async def fetch_url(client: httpx.AsyncClient, url: str, retries: int = 3, delay: float = 2.0) -> dict:
    for attempt in range(retries):
        try:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.warning("Fetch attempt %s failed via passed client: %s", attempt + 1, e)
            if attempt == retries - 1:
                raise
            await asyncio.sleep(delay)

# Stores character in DB if not already present
async def store_in_db(character: Dict, db_conn):
    try:
        await db_conn.execute(
            """
            INSERT INTO characters (id, name, status, species, origin)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (id) DO NOTHING
            """,
            character["id"],
            character["name"],
            character["status"],
            character["species"],
            character["origin"]["name"]
        )
        logger.debug("Stored character in DB: %s", character["name"])
    except Exception as e:
        logger.error("Failed to store character in DB: %s", e)

# Filter character list by name (optional)
def filter_characters(data: List[Dict], name_filter: Optional[str]) -> List[Dict]:
    if not name_filter:
        return data

    name_filter = name_filter.strip().lower()
    return [
        char for char in data
        if "name" in char and name_filter in char["name"].lower()
    ]
