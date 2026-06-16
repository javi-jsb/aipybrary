from httpx import ASGITransport, AsyncClient

from app.config import settings
from app.main import app

ALLOWED_ORIGIN = settings.CORS_ALLOW_ORIGINS[0]
DISALLOWED_ORIGIN = "http://evil.example"


async def test_preflight_allows_configured_origin() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.options(
            "/auth/login",
            headers={
                "Origin": ALLOWED_ORIGIN,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Authorization",
            },
        )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == ALLOWED_ORIGIN
    assert "POST" in response.headers["access-control-allow-methods"]
    assert "authorization" in response.headers["access-control-allow-headers"].lower()


async def test_simple_request_echoes_allowed_origin() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health", headers={"Origin": ALLOWED_ORIGIN})

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == ALLOWED_ORIGIN


async def test_disallowed_origin_gets_no_cors_header() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health", headers={"Origin": DISALLOWED_ORIGIN})

    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers
