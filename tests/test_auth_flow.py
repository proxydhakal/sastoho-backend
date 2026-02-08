import pytest
from httpx import AsyncClient
from app.main import app

# We need a proper DB setup for tests override, but for now we test against local DB if we can, or just minimal contract.
# Warning: Testing against local DB adds data!
# Ideally we use a test db or override dependency.
# For this verify step, assume we test against the running env but careful with data.

@pytest.mark.asyncio
async def test_register_and_login():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        email = "testuser_unique@example.com"
        password = "strongpassword123"
        
        # 1. Register
        # Note: If user exists, this fails (400). We handle that or use random email.
        import random
        rand_id = random.randint(1000, 9999)
        email = f"testuser_{rand_id}@example.com"

        response = await ac.post("/api/v1/users/", json={
            "email": email,
            "password": password,
            "full_name": "Test User"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == email
        assert "id" in data
        assert "hashed_password" not in data # Ensure security

        # 2. Login
        login_data = {
            "username": email,
            "password": password
        }
        response = await ac.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200
        tokens = response.json()
        assert "access_token" in tokens
        token = tokens["access_token"]

        # 3. Get Me
        response = await ac.get("/api/v1/users/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        me_data = response.json()
        assert me_data["email"] == email
