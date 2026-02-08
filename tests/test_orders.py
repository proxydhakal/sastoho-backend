import pytest
from httpx import AsyncClient
from app.main import app
from app.core.security import create_access_token
import uuid

# Helper to create admin token (reuse if possible or mock)
async def get_admin_token(ac):
    email = "admin_order_test@example.com"
    password = "adminpassword"
    # Try login first
    login_res = await ac.post("/api/v1/auth/login", data={"username": email, "password": password})
    if login_res.status_code == 200:
        return login_res.json()["access_token"]
        
    await ac.post("/api/v1/users/", json={"email": email, "password": password, "full_name": "Admin Order"})
    res = await ac.post("/api/v1/auth/login", data={"username": email, "password": password})
    return res.json()["access_token"]

@pytest.mark.asyncio
async def test_order_creation_flow():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        email = f"user_order_{uuid.uuid4().hex[:6]}@example.com"
        password = "testpassword"

        # 1. Setup Product (Admin)
        admin_token = await get_admin_token(ac)
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create Category
        cat_res = await ac.post("/api/v1/catalog/categories", json={"name": f"OrderCat-{uuid.uuid4().hex[:6]}"}, headers=admin_headers)
        cat_id = cat_res.json()["id"]

        # Create Product
        prod_res = await ac.post("/api/v1/catalog/products", json={
            "name": f"OrderProd-{uuid.uuid4().hex[:6]}",
            "category_id": cat_id,
            "variants": [{"sku": f"O-SKU-{uuid.uuid4().hex}", "price": 100, "stock_quantity": 50}]
        }, headers=admin_headers)
        product = prod_res.json()
        variant_id = product["variants"][0]["id"]

        # 2. User Setup
        # Register
        await ac.post("/api/v1/users/", json={"email": email, "password": password, "full_name": "Order User"})
        # Login
        login_res = await ac.post("/api/v1/auth/login", data={"username": email, "password": password})
        user_token = login_res.json()["access_token"]
        user_headers = {"Authorization": f"Bearer {user_token}"}

        # 3. Add to Cart
        await ac.post("/api/v1/cart/items", json={"variant_id": variant_id, "quantity": 2}, headers=user_headers)
        
        # 4. Create Order
        order_payload = {
            "shipping_address": {"street": "123 Main St", "city": "Test City", "country": "Test Country"},
            "payment_method_id": "tok_visa" # Mock token
        }
        
        # Mock Stripe
        from unittest.mock import MagicMock, patch
        
        mock_intent = MagicMock()
        mock_intent.id = "pi_mock_123456"
        
        with patch("app.services.payment_service.payment_service.create_payment_intent", return_value=mock_intent):
            res = await ac.post("/api/v1/orders/", json=order_payload, headers=user_headers)
            
        assert res.status_code == 200
        order = res.json()
        assert order["status"] == "pending"
        assert order["stripe_payment_id"] == "pi_mock_123456"
        assert float(order["total_amount"]) == 200.0 # 100 * 2
        assert len(order["items"]) == 1
        assert order["items"][0]["product_variant_id"] == variant_id
        
        # 5. Verify Cart Empty
        cart_res = await ac.get("/api/v1/cart/", headers=user_headers)
        assert cart_res.status_code == 200
        assert len(cart_res.json()["items"]) == 0
        
        # 6. Verify Stock Deduction
        # Get product again
        prod_get = await ac.get(f"/api/v1/catalog/products/{product['id']}")
        assert prod_get.json()["variants"][0]["stock_quantity"] == 48 # 50 - 2

        # 7. Get Order List
        orders_res = await ac.get("/api/v1/orders/", headers=user_headers)
        assert orders_res.status_code == 200
        assert len(orders_res.json()) >= 1
