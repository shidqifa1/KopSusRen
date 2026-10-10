"""Scaffold checks; BR/FR behavior tests start with their owning milestones."""

import asyncio
import subprocess

import httpx

from app.main import app


def test_m0_health_is_the_only_route() -> None:
    async def check_routes() -> None:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/health")
            assert response.status_code == 200
            assert response.json() == {"status": "ok"}
            for path in ("/", "/docs", "/redoc", "/openapi.json"):
                assert (await client.get(path)).status_code == 404

    asyncio.run(check_routes())
    assert [getattr(route, "path", None) for route in app.routes] == ["/health"]


def test_nfr_3_private_artifacts_are_ignored() -> None:
    private_paths = [
        ".env",
        ".venv/example",
        "data/example.db",
        "data/example.db-wal",
        "data/example.db-shm",
        "data/example.sqlite3",
        "data/example.sqlite-wal",
        "logs/example.txt",
        "example.log",
        "backups/example.txt",
    ]
    result = subprocess.run(
        ["git", "check-ignore", "--no-index", "--stdin"],
        input="\n".join(private_paths) + "\n",
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.splitlines() == private_paths
    example = subprocess.run(
        ["git", "check-ignore", "--no-index", ".env.example"],
        capture_output=True,
        check=False,
    )
    assert example.returncode == 1
