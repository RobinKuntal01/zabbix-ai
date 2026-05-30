import redis.asyncio as aioredis

def connect_redis():
    redis_client = aioredis.from_url("redis://localhost:6379", decode_responses=True)
    return redis_client
