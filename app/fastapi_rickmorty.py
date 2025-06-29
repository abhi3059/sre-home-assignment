from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from typing import List, Optional
import httpx
from redis import Redis, ConnectionError as RedisConnectionError
import psycopg2
import os
import json
import logging
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rickmorty-api")

app = FastAPI()

# --- Rate Limiting ---
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- Configuration ---
RICK_AND_MORTY_API = "https://rickandmortyapi.com/api/character"
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_TTL = int(os.getenv("REDIS_TTL", 3600))

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_NAME = os.getenv("DB_NAME", "rickmorty")

# --- Redis client ---
redis_client = Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# --- PostgreSQL connection ---
try:
    db_conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        dbname=DB_NAME
    )
    db_cursor = db_conn.cursor()
    db_cursor.execute("""
        CREATE TABLE IF NOT EXISTS characters (
            id INT PRIMARY KEY,
            name TEXT,
            status TEXT,
            species TEXT,
            origin TEXT
        )
    """)
    db_conn.commit()
except Exception as e:
    logger.error("Database connection failed: %s", e)

# --- Models ---
class Character(BaseModel):
    id: int
    name: str
    status: str
    species: str
    origin: str

# --- Retry Decorator with backoff and 429 handling ---
@retry(
    wait=wait_exponential(multiplier=1, min=2, max=10),
    stop=stop_after_attempt(5),
    retry=retry_if_exception_type(httpx.HTTPStatusError)
)
async def fetch_url(client: httpx.AsyncClient, url: str) -> dict:
    response = await client.get(url)
    if response.status_code == 429:
        logger.warning("Received 429 from API, retrying...")
        raise httpx.HTTPStatusError("Too Many Requests", request=response.request, response=response)
    response.raise_for_status()
    return response.json()

# --- Helper ---
def store_in_db(character):
    try:
        db_cursor.execute(
            "INSERT INTO characters (id, name, status, species, origin) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING",
            (character["id"], character["name"], character["status"], character["species"], character["origin"]["name"])
        )
        db_conn.commit()
    except Exception as e:
        logger.error("Failed to store character in DB: %s", e)

@app.get("/characters", response_model=List[Character])
@limiter.limit("100/minute")
async def get_characters(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(10, le=50),
    sort_by: Optional[str] = Query("id", pattern="^(id|name)$"),
    sort_order: Optional[str] = Query("asc", pattern="^(asc|desc)$")
):
    try:
        cache_key = f"characters_page_{page}_limit_{limit}_sortby_{sort_by}_order_{sort_order}"
        cached = redis_client.get(cache_key)
        if cached:
            logger.info("Cache hit for key: %s", cache_key)
            return json.loads(cached)

        filtered = []
        url = f"{RICK_AND_MORTY_API}?page={page}"
        async with httpx.AsyncClient() as client:
            data = await fetch_url(client, url)
            for character in data.get("results", []):
                if (character["species"] == "Human" and
                    character["status"] == "Alive" and
                    character["origin"]["name"].startswith("Earth")):
                    item = {
                        "id": character["id"],
                        "name": character["name"],
                        "status": character["status"],
                        "species": character["species"],
                        "origin": character["origin"]["name"]
                    }
                    store_in_db(character)
                    filtered.append(item)

        sorted_data = sorted(
            filtered,
            key=lambda x: x[sort_by],
            reverse=(sort_order == "desc")
        )[:limit]

        redis_client.setex(cache_key, REDIS_TTL, json.dumps(sorted_data))
        logger.info("Cache set for key: %s", cache_key)
        return sorted_data

    except httpx.HTTPStatusError as e:
        logger.error("HTTP error: %s", e)
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except RedisConnectionError:
        logger.error("Redis unavailable")
        raise HTTPException(status_code=503, detail="Redis unavailable")
    except Exception as e:
        logger.exception("Unexpected error")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/healthcheck")
def healthcheck():
    health = {"database": False, "redis": False}
    try:
        db_cursor.execute("SELECT 1")
        db_conn.commit()
        health["database"] = True
    except Exception as e:
        logger.error("Database healthcheck failed: %s", e)

    try:
        redis_client.ping()
        health["redis"] = True
    except Exception as e:
        logger.error("Redis healthcheck failed: %s", e)

    status = 200 if all(health.values()) else 503
    return JSONResponse(status_code=status, content=health)
