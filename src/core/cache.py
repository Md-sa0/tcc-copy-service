from redis.asyncio import Redis


def create_cache(url: str) -> Redis:
    return Redis.from_url(url, decode_responses=True, socket_connect_timeout=3, socket_timeout=3)
