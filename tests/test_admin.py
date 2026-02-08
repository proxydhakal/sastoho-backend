import pytest
from httpx import AsyncClient
from app.main import app
import uuid

async def create_superuser(ac, email, password):
    # This is a hack for testing. 
    # Real app would have a script or initial migration. 
    # Here we create a user and then manually update DB? 
    # No, we can't access DB easily here without session.
    # BUT, we implemented `update_user_role` in admin router.
    # Catch-22: Need admin to promote admin.
    
    # Solution: The first user created should be admin? 
    # Or, we can use a backdoor or just rely on manual seeding.
    # For integration test, we might check if `admin_review_test` from other tests persists and has role?
    # NO. 
    
    # Let's try to register a user.
    await ac.post("/api/v1/users/", json={"email": email, "password": password, "full_name": "Potential Admin"})
    
    # Login
    res = await ac.post("/api/v1/auth/login", data={"username": email, "password": password})
    token = res.json()["access_token"]
    
    # In `app/core/database.py` or `main.py` maybe we have a startup event to create SUPERUSER? 
    # If not, let's skip the "promote" part if blocked, but we CAN test stats via a mock or just fail if no admin.
    
    # Wait! In `test_auth_flow.py` maybe we verified superuser?
    # Let's assume for this test environment (clean DB per test maybe?) 
    # Actually, let's create a fixture or just try a known admin if one exists.
    
    # Hack: I'll manually set is_superuser=True in the code for a specific email just for this test? NO.
    
    # Better: I will use a dependency override in the test!
    return token

@pytest.mark.asyncio
async def test_admin_stats():
    # Override dependency to FORCE admin role without DB hack
    from app.api.v1.routers.admin import get_current_admin_user
    from app.models.user import User
    
    mock_admin = User(id=1, email="admin@test.com", is_superuser=True, role="admin")
    
    app.dependency_overrides[get_current_admin_user] = lambda: mock_admin
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Get Stats (with forced admin)
        res = await ac.get("/api/v1/admin/stats")
        assert res.status_code == 200
        stats = res.json()
        assert "total_users" in stats
        assert "total_orders" in stats
        assert "total_revenue" in stats
        
    app.dependency_overrides = {}
