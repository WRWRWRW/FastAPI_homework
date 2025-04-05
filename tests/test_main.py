import pytest
import asyncio
import socket 
import time
from httpx import AsyncClient 
from main import app


def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

@pytest.mark.asyncio
async def test_register_and_login():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # 1. Register
        resp = await ac.post("/register", data={"email": "test@example.com", "password": "password"})
        assert resp.status_code == 303  # Redirect to /login

        # 2. Try login with pw
        resp = await ac.post("/login", data={"email": "test@example.com", "password": "password"})
        assert resp.status_code == 303  # Redirect to /welcome

        # 3. Try login with wrong pw
        resp = await ac.post("/login", data={"email": "test@example.com", "password": "wrong pw lol"})
        assert "Incorrect password" in resp.text

        # 4. Login with unregistered user
        resp = await ac.post("/login", data={"email": "this is not an email", "password": "lol"})
        assert "This email is not registered" in resp.text

@pytest.mark.asyncio
async def test_welcome_requires_login():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.get("/welcome", follow_redirects=False)
        assert resp.status_code == 303  # Redirect to login
