
import pytest
from httpx import AsyncClient
from app.api.v1.api import api_router
from app.main import app
import uuid

@pytest.mark.asyncio
async def test_advanced_product_features():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        email = "admin_adv@example.com"
        password = "adminpassword"
        
        # 1. Login
        await ac.post("/api/v1/users/", json={
            "email": email,
            "password": password,
            "full_name": "Admin Adv"
        })
        login_res = await ac.post("/api/v1/auth/login", data={"username": email, "password": password})
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        unique_id = str(uuid.uuid4())[:8]
        
        # 2. Create Category
        cat_res = await ac.post("/api/v1/catalog/categories", json={
            "name": f"Adv Cat {unique_id}",
            "description": "Category for advanced tests"
        }, headers=headers)
        cat_id = cat_res.json()["id"]

        # 3. Create Products for Search Test
        # Product A
        p1_res = await ac.post("/api/v1/catalog/products", json={
            "name": f"Alpha Phone {unique_id}",
            "description": "Premium device",
            "category_id": cat_id,
            "variants": [{"sku": f"A-SKU-{unique_id}", "price": 100, "stock_quantity": 10}]
        }, headers=headers)
        p1_id = p1_res.json()["id"]
        
        # Product B (different name)
        p2_res = await ac.post("/api/v1/catalog/products", json={
            "name": f"Beta Tablet {unique_id}",
            "description": "Large screen device",
            "category_id": cat_id,
            "variants": [{"sku": f"B-SKU-{unique_id}", "price": 200, "stock_quantity": 5}]
        }, headers=headers)
        p2_id = p2_res.json()["id"]
        
        # 4. Test Search
        # Search "Alpha"
        search_res = await ac.get(f"/api/v1/catalog/products?search=Alpha", headers=headers)
        assert search_res.status_code == 200
        results = search_res.json()
        assert len(results) >= 1
        assert any(p["name"] == f"Alpha Phone {unique_id}" for p in results)
        assert not any(p["name"] == f"Beta Tablet {unique_id}" for p in results)
        
        # 5. Test Inventory Update
        sku = f"A-SKU-{unique_id}"
        inv_res = await ac.patch(f"/api/v1/catalog/variants/{sku}/inventory", json={"quantity": 50}, headers=headers)
        assert inv_res.status_code == 200
        assert inv_res.json()["stock_quantity"] == 50
        
        # Verify persistence
        p1_get = await ac.get(f"/api/v1/catalog/products/{p1_id}", headers=headers)
        # Variant list might be unordered or we need to find the right one
        variants = p1_get.json()["variants"]
        variant = next(v for v in variants if v["sku"] == sku)
        assert variant["stock_quantity"] == 50
        
        # 6. Test Soft Delete
        del_res = await ac.delete(f"/api/v1/catalog/products/{p1_id}", headers=headers)
        assert del_res.status_code == 200
        
        # Verify it's gone from list
        list_res = await ac.get(f"/api/v1/catalog/products?search=Alpha", headers=headers)
        results = list_res.json()
        assert not any(p["id"] == p1_id for p in results)
        
        # Verify direct fetch gives 404 (or we might want to allow it for admin? currently logic filters it)
        # Service logic filters is_deleted=False in get_with_variants
        get_res = await ac.get(f"/api/v1/catalog/products/{p1_id}", headers=headers)
        # If get_with_variants returns None, router raises 404
        assert get_res.status_code == 404
