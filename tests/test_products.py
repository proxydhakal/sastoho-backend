import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_product_catalog_flow():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        email = "admin_catalog@example.com"
        password = "adminpassword"
        
        # 1. Register & Login as Admin (Assuming first user logic or we just authenticate)
        await ac.post("/api/v1/users/", json={
            "email": email,
            "password": password,
            "full_name": "Admin User"
        })
        
        login_res = await ac.post("/api/v1/auth/login", data={"username": email, "password": password})
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        
        # 2. Create Category
        cat_name = f"Electronics {unique_id}"
        slug_check = f"electronics-{unique_id}"
        
        cat_res = await ac.post("/api/v1/catalog/categories", json={
            "name": cat_name,
            "description": "Gadgets and devices"
        }, headers=headers)
        assert cat_res.status_code == 200
        category = cat_res.json()
        assert category["slug"] == slug_check
        cat_id = category["id"]
        
        # 3. Create Product with Variants
        prod_name = f"Smartphone {unique_id}"
        prod_slug = f"smartphone-{unique_id}"
        
        prod_res = await ac.post("/api/v1/catalog/products", json={
            "name": prod_name,
            "description": "Flagship phone",
            "category_id": cat_id,
            "variants": [
                {
                    "sku": f"PHONE-X-BLK-64-{unique_id}",
                    "price": 999.99,
                    "stock_quantity": 100,
                    "attributes": {"color": "black", "storage": "64GB"}
                },
                {
                    "sku": f"PHONE-X-WHT-128-{unique_id}",
                    "price": 1099.99,
                    "stock_quantity": 50,
                    "attributes": {"color": "white", "storage": "128GB"}
                }
            ]
        }, headers=headers)
        assert prod_res.status_code == 200
        product = prod_res.json()
        assert product["slug"] == prod_slug
        assert len(product["variants"]) == 2
        
        # 4. Fetch Products List
        list_res = await ac.get("/api/v1/catalog/products")
        assert list_res.status_code == 200
        data = list_res.json()
        assert len(data) >= 1
        # Check if our created product is in the list
        found = any(p["name"] == prod_name for p in data)
        assert found
