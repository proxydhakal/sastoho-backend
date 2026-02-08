import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
from app.main import app
from app.core import security

@pytest.mark.asyncio
async def test_password_reset_flow():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        email = "reset_test@example.com"
        password = "oldpassword123"
        new_password = "newpassword456"
        
        # 1. Register User
        await ac.post("/api/v1/users/", json={
            "email": email,
            "password": password,
            "full_name": "Reset Tester"
        })

        # 2. Request Password Reset (Mocking email sending)
        with patch("app.core.email.fastmail.send_message", new_callable=AsyncMock) as mock_send:
            response = await ac.post(f"/api/v1/users/password-recovery/{email}") # Wait, prefix is /auth or /users? 
            # In api.py: api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
            # The endpoints are in auth.py.
            # Endpoint logic: @router.post("/password-recovery/{email}"...)
            # So URL is /api/v1/auth/password-recovery/{email}
            
            response = await ac.post(f"/api/v1/auth/password-recovery/{email}")
            assert response.status_code == 200
            assert response.json() == {"msg": "Password recovery email sent"}
            assert mock_send.called

            # 3. Extract token (In real test we'd intercept the mock call args, but here we can just generate one manually for verification of the reset endpoint specifically, OR we intercept the token from the mock call)
            # Let's generate a valid token manually to test the reset endpoint safely
            from app.core.reset_token import create_password_reset_token
            token = create_password_reset_token(email)
        
        # 4. Reset Password
        response = await ac.post("/api/v1/auth/reset-password/", json={
            "token": token,
            "new_password": new_password
        })
        assert response.status_code == 200
        assert response.json() == {"msg": "Password updated successfully"}

        # 5. Login with NEW password
        login_data = {"username": email, "password": new_password}
        response = await ac.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200
        assert "access_token" in response.json()

        # 6. Login with OLD password (should fail)
        login_data_old = {"username": email, "password": password}
        response = await ac.post("/api/v1/auth/login", data=login_data_old)
        assert response.status_code == 400
