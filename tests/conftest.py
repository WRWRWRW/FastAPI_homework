import pytest_asyncio
from uvicorn import Config, Server
from main import app
import socket
import asyncio

def get_free_port():
    with socket.socket() as s:
        s.bind(('', 0))
        return s.getsockname()[1]

@pytest_asyncio.fixture
async def live_server():
    port = get_free_port()
    config = Config(app=app, host="127.0.0.1", port=port, log_level="error", lifespan="off")
    server = Server(config)
    server_task = asyncio.create_task(server.serve())

    for _ in range(20):
        try:
            reader, writer = await asyncio.open_connection("127.0.0.1", port)
            writer.close()
            await writer.wait_closed()
            break
        except:
            await asyncio.sleep(0.2)
    else:
        raise RuntimeError("unable to start server")

    yield {
        "base_url": f"http://127.0.0.1:{port}",
        "ws_url": f"ws://127.0.0.1:{port}/ws"
    }

    server.should_exit = True
    await server_task
