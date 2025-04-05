import pytest
import asyncio
import websockets
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_notification_broadcast(live_server):
    base_url = live_server["base_url"]
    ws_url = live_server["ws_url"]
    received = []
    ws_ready = asyncio.Event()

    async def ws_client():
        async with websockets.connect(ws_url) as ws:
            await ws.send("ping")
            ws_ready.set()
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=10)
                received.append(msg)
            except asyncio.TimeoutError:
                pytest.fail("WebSocket did not receive message in time")

    task = asyncio.create_task(ws_client())

    await asyncio.wait_for(ws_ready.wait(), timeout=3)

    async with AsyncClient(base_url=base_url) as ac:
        await ac.post("/register", data={
            "email": "aaa@example.com",
            "password": "123456"
        })

    await asyncio.wait_for(task, timeout=10)

    assert any("aaa@example.com" in m for m in received)
