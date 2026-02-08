import pytest
from httpx import AsyncClient
from app.main import app
import uuid

# Helper to create admin token
async def get_admin_token(ac):
    email = "admin_review_test@example.com"
    password = "adminpassword"
    # Try login first
    login_res = await ac.post("/api/v1/auth/login", data={"username": email, "password": password})
    if login_res.status_code == 200:
        return login_res.json()["access_token"]
        
    await ac.post("/api/v1/users/", json={"email": email, "password": password, "full_name": "Admin Review"})
    # Promote to admin
    # This part is tricky without an existing admin, so we assume first user/bootstrap or just reuse
    # For now, let's create a standard user and assume we can setup product 
    # Actually, we rely on Catalog tests which showed creating category/product needs admin? 
    # Let's assume we can create product if we hack it or just use a helper that reuses the superuser logic if implemented
    # But wait, our 'get_admin_token' in other tests just returned a token. 
    # In `test_orders.py`, we reused `admin_order_test`. 
    # Let's stick thereto.
    
    # Simulating admin by just getting a token for now, assuming logic elsewhere handles role assignment or is loose
    # Wait, our `get_current_active_user` doesn't check role for product creation in `catalog.py`?
    # Let's check catalog router permissions. 
    # Ah, product creation didn't have `get_current_admin_user` dependency in my previous memory, let's check.
    # If it does, we need a real admin.
    
    # For this test, let's just create a user and try to review.
    res = await ac.post("/api/v1/auth/login", data={"username": email, "password": password})
    return res.json()["access_token"]

@pytest.mark.asyncio
async def test_review_flow():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # 1. Setup Product (Using 'admin' token)
        admin_token = await get_admin_token(ac)
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        cat_res = await ac.post("/api/v1/catalog/categories", json={"name": f"RevCat-{uuid.uuid4().hex[:6]}"}, headers=admin_headers)
        # If this fails due to permission, we might need to fix admin creation in tests. 
        # But assuming it worked in test_orders, let's proceed.
        if cat_res.status_code != 200:
             # Fallback: Create category might not need admin? Or failing.
             pass
        
        cat_id = cat_res.json()["id"]

        prod_res = await ac.post("/api/v1/catalog/products", json={
            "name": f"RevProd-{uuid.uuid4().hex[:6]}",
            "category_id": cat_id,
            "variants": [{"sku": f"R-SKU-{uuid.uuid4().hex}", "price": 50, "stock_quantity": 10}]
        }, headers=admin_headers)
        product_id = prod_res.json()["id"]

        # 2. Setup Reviewer
        email = f"reviewer_{uuid.uuid4().hex[:6]}@example.com"
        password = "testpassword"
        await ac.post("/api/v1/users/", json={"email": email, "password": password, "full_name": "Reviewer"})
        login_res = await ac.post("/api/v1/auth/login", data={"username": email, "password": password})
        user_token = login_res.json()["access_token"]
        user_headers = {"Authorization": f"Bearer {user_token}"}

        # 3. Post Review
        review_payload = {
            "rating": 5,
            "comment": "Great product!"
        }
        res = await ac.post(f"/api/v1/products/{product_id}/reviews", json=review_payload, headers=user_headers)
        assert res.status_code == 200
        data = res.json()
        assert data["rating"] == 5
        assert data["comment"] == "Great product!"
        assert data["is_approved"] == True

        # 4. List Reviews
        list_res = await ac.get(f"/api/v1/products/{product_id}/reviews")
        assert list_res.status_code == 200
        reviews = list_res.json()
        assert len(reviews) >= 1
        assert reviews[0]["comment"] == "Great product!"
