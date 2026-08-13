"""
Rate limiter shared across routers.

Keyed on the real client IP: Render sits behind a proxy, so we read
X-Forwarded-For (set by the proxy) instead of request.client.host, which
would otherwise be the proxy's address for every user.
"""
from slowapi import Limiter


def _client_key(request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


limiter = Limiter(key_func=_client_key)
