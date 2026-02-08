import pytest
from httpx import AsyncClient
from app.main import app
import uuid

@pytest.mark.asyncio
async def test_cart_and_wishlist_flow():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        email = f"user_cart_{uuid.uuid4().hex[:6]}@example.com"
        password = "testpassword"
        
        # 1. Create Product & Variant (Admin)
        # Using a new admin user logic would be verbose, let's reuse/create one
        admin_token = await get_admin_token(ac)
        
        # Create Category
        cat_res = await ac.post("/api/v1/catalog/categories", json={"name": f"CartCat-{uuid.uuid4().hex[:6]}"}, headers={"Authorization": f"Bearer {admin_token}"})
        cat_id = cat_res.json()["id"]
        
        # Create Product
        prod_res = await ac.post("/api/v1/catalog/products", json={
            "name": f"CartProd-{uuid.uuid4().hex[:6]}",
            "category_id": cat_id,
            "variants": [{"sku": f"C-SKU-{uuid.uuid4().hex}", "price": 50, "stock_quantity": 100}]
        }, headers={"Authorization": f"Bearer {admin_token}"})
        product = prod_res.json()
        variant_id = product["variants"][0]["id"]
        
        # 2. Guest Cart Flow
        session_id = str(uuid.uuid4())
        headers_guest = {"X-Session-ID": session_id}
        
        # Add to cart
        add_res = await ac.post("/api/v1/cart/items", json={"variant_id": variant_id, "quantity": 2}, headers=headers_guest)
        assert add_res.status_code == 200
        cart = add_res.json()
        assert cart["session_id"] == session_id
        assert len(cart["items"]) == 1
        assert cart["items"][0]["quantity"] == 2
        item_id = cart["items"][0]["id"]
        
        # Update qty
        upd_res = await ac.patch(f"/api/v1/cart/items/{item_id}", json={"quantity": 3}, headers=headers_guest)
        assert upd_res.status_code == 200
        assert upd_res.json()["items"][0]["quantity"] == 3
        
        # 3. User Registration & Login
        await ac.post("/api/v1/users/", json={"email": email, "password": password, "full_name": "Cart User"})
        login_res = await ac.post("/api/v1/auth/login", data={"username": email, "password": password})
        user_token = login_res.json()["access_token"]
        headers_user = {"Authorization": f"Bearer {user_token}"}
        
        # 4. Merge Cart
        merge_res = await ac.post("/api/v1/cart/merge", json={"session_id": session_id}, headers=headers_user)
        assert merge_res.status_code == 200
        merged_cart = merge_res.json()
        assert merged_cart["user_id"] is not None
        # Check items merged
        assert len(merged_cart["items"]) == 1
        assert merged_cart["items"][0]["product_variant_id"] == variant_id
        assert merged_cart["items"][0]["quantity"] == 3 # Should preserve qty from session
        
        # 5. Wishlist Flow
        # Add to wishlist
        w_add = await ac.post("/api/v1/wishlist/items", json={"variant_id": variant_id}, headers=headers_user)
        assert w_add.status_code == 200
        wishlist = w_add.json()
        assert len(wishlist["items"]) == 1
        assert wishlist["items"][0]["variant"]["id"] == variant_id
        
        # Get wishlist
        w_get = await ac.get("/api/v1/wishlist/", headers=headers_user)
        assert w_get.status_code == 200
        
        # Remove from wishlist
        w_del = await ac.delete(f"/api/v1/wishlist/items/{variant_id}", headers=headers_user)
        assert w_del.status_code == 200
        assert len(w_del.json()["items"]) == 0

async def get_admin_token(ac):
    email = "admin_cart_test@example.com"
    password = "adminpassword"
    # Register/Login
    await ac.post("/api/v1/users/", json={"email": email, "password": password, "full_name": "Admin Cart"})
    res = await ac.post("/api/v1/auth/login", data={"username": email, "password": password})
    return res.json()["access_token"]
