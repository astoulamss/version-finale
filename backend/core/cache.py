import os
from typing import Optional
import redis.asyncio as redis
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Client Redis asynchrone (singleton)
redis_client: Optional[redis.Redis] = None

async def init_redis():
    """Initialise la connexion Redis."""
    global redis_client
    redis_client = redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
    return redis_client

async def close_redis():
    """Ferme la connexion Redis."""
    global redis_client
    if redis_client:
        await redis_client.close()

async def get_redis() -> redis.Redis:
    """Retourne l'instance du client Redis."""
    if redis_client is None:
        await init_redis()
    return redis_client

# --- JWT Blocklist Management ---

async def add_token_to_blocklist(token: str, expire_in_seconds: int):
    """
    Ajoute un token à la blocklist pour une durée déterminée (jusqu'à son expiration).
    """
    client = await get_redis()
    await client.setex(f"blocklist:{token}", expire_in_seconds, "revoked")

async def is_token_blocklisted(token: str) -> bool:
    """
    Vérifie si un token est dans la blocklist.
    """
    client = await get_redis()
    is_revoked = await client.exists(f"blocklist:{token}")
    return is_revoked > 0
