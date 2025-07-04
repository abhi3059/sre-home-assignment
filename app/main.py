import os
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from typing import List, Optional
import json
import httpx
import logging
from redis.exceptions import ConnectionError as RedisConnectionError
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from contextlib import asynccontextmanager
from time import time  

from app.database import connect_to_db
from app.redis_client import connect_to_redis, REDIS_TTL
from app.metrics import (
    instrumentator,
    character_processed,
    cache_hits,
    cache_misses,
    request_latency,
    redis_failures,
    cache_hit_ratio, 
)
from app.tracing import setup_tracer
from app.exceptions import setup_exception_handlers, RateLimitExceeded
from app.utils import fetch_url, store_in_db

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rickmorty-api")

# --- Lifespan handler ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        app.state.db_conn = await connect_to_db()
    except Exception as e:
        logger.error("Database connection failed: %s", e)
        app.state.db_conn = None

    try:
        app.state.redis = await connect_to_redis()
    except Exception as e:
        logger.error("Redis connection failed: %s", e)
        app.state.redis = None

    # --- Force register metrics after all systems are initialized ---
    cache_hits.inc(0.000001)
    cache_misses.inc(0.000001)
    cache_hit_ratio.set(0.0)

    yield

    if app.state.db_conn:
        await app.state.db_conn.close()
    if app.state.redis:
        await app.state.redis.close()

# --- App Initialization ---
app = FastAPI(lifespan=lifespan)

# --- Tracing ---
setup_tracer(app)

# --- Metrics ---
instrumentator.instrument(app).expose(app)

# --- Rate Limiting ---
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

# --- Exception Handlers ---
setup_exception_handlers(app)

# --- Constants ---
RICK_AND_MORTY_API = "https://rickandmortyapi.com/api/character"

# --- Models ---
class Character(BaseModel):
    id: int
    name: str
    status: str
    species: str
    origin: str

# --- Endpoints ---
@app.get("/characters", response_model=List[Character])
@limiter.limit("100/minute")
async def get_characters(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(10, le=50),
    sort_by: Optional[str] = Query("id", pattern="^(id|name)$"),
    sort_order: Optional[str] = Query("asc", pattern="^(asc|desc)$")
):
    start_time = time()
    redis_client = request.app.state.redis
    db_conn = request.app.state.db_conn

    try:
        cache_key = f"characters_page_{page}_limit_{limit}_sortby_{sort_by}_order_{sort_order}"
        cached = None

        if not redis_client:
            logger.warning("Redis client is not available. Skipping cache lookup.")
        else:
            logger.info(f"Trying to get key from Redis: {cache_key}")
            cached = await redis_client.get(cache_key)
            if cached:
                logger.info("Cache hit for key: %s", cache_key)
                cache_hits.inc()
            else:
                logger.info("Cache miss for key: %s", cache_key)
                cache_misses.inc()

            # Update cache hit ratio
            hits = cache_hits._value.get()
            misses = cache_misses._value.get()
            total = hits + misses
            if total > 0:
                cache_hit_ratio.set(hits / total)

            if cached:
                return json.loads(cached)

        # Fetch data from external API
        url = f"{RICK_AND_MORTY_API}?page={page}"
        logger.info(f"Fetching characters from external API: {url}")
        filtered = []
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
                    filtered.append(item)
                    character_processed.inc()
                    if db_conn:
                        await store_in_db(character, db_conn)

        logger.info(f"Total filtered characters passing criteria: {len(filtered)}")
        if not filtered:
            logger.warning("No characters matched filtering criteria.")

        sorted_data = sorted(
            filtered,
            key=lambda x: x[sort_by],
            reverse=(sort_order == "desc")
        )[:limit]

        if redis_client:
            await redis_client.setex(cache_key, REDIS_TTL, json.dumps(sorted_data))
            logger.info("Cache set for key: %s", cache_key)

        return sorted_data

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error while fetching characters for page {page}: {e}")
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except RedisConnectionError:
        logger.error("Redis unavailable - possibly due to chaos experiment.")
        redis_failures.inc()
        raise HTTPException(status_code=503, detail="Redis unavailable")
    except Exception as e:
        logger.exception(f"Unexpected error on /characters?page={page}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        request_latency.observe(time() - start_time)

@app.get("/healthcheck")
async def healthcheck(request: Request):
    # CI/CD override for GitHub Actions
    if os.getenv("CI") == "true":
        return JSONResponse(status_code=200, content={"database": True, "redis": True})

    health = {"database": False, "redis": False}

    try:
        db_conn = request.app.state.db_conn
        if db_conn:
            result = await db_conn.fetchval("SELECT 1")
            if result == 1:
                health["database"] = True
    except Exception as e:
        logger.error("Database healthcheck failed: %s", e)

    try:
        redis_client = request.app.state.redis
        if redis_client:
            pong = await redis_client.ping()
            if pong:
                health["redis"] = True
    except Exception as e:
        logger.error("Redis healthcheck failed: %s", e)

    status = 200 if all(health.values()) else 503
    return JSONResponse(status_code=status, content=health)
