from tests.test_profile import PNG


def test_products_crud_admin_only(client, admin, make_user, make_product):
    _, headers = make_user()
    data = {"name": "Ryzen 5", "brand": "AMD", "category": "cpu", "price": 150}
    assert client.post("/api/products", json=data, headers=headers).status_code == 403

    product = make_product(name="Ryzen 7 7800X3D", category="cpu", price="449.99", specs={"cores": 8})
    assert product["price"] == 449.99 and product["specs"] == {"cores": 8}

    updated = client.patch(f"/api/products/{product['id']}", json={"price": 399, "stock": 2}, headers=admin).json()
    assert updated["price"] == 399 and updated["stock"] == 2

    assert client.delete(f"/api/products/{product['id']}", headers=admin).status_code == 204
    assert client.get(f"/api/products/{product['id']}").status_code == 404


def test_product_filters_and_inactive(client, admin, make_product):
    product = make_product(name="Monitor curvo 34", category="monitor", price=300)
    by_category = client.get("/api/products?category=monitor&search=curvo").json()
    assert [p["id"] for p in by_category["items"]] == [product["id"]]
    assert client.get("/api/products?category=monitor&max_price=100").json()["total"] == 0

    client.patch(f"/api/products/{product['id']}", json={"is_active": False}, headers=admin)
    assert client.get(f"/api/products/{product['id']}").status_code == 404
    assert client.get(f"/api/products/{product['id']}", headers=admin).status_code == 200
    with_inactive = client.get("/api/products?category=monitor&include_inactive=true", headers=admin).json()
    assert product["id"] in [p["id"] for p in with_inactive["items"]]


def test_product_image_upload(client, admin, make_product):
    product = make_product()
    response = client.put(f"/api/products/{product['id']}/image", files={"file": ("gpu.png", PNG, "image/png")}, headers=admin)
    assert response.status_code == 200
    assert response.json()["image_url"].startswith("/uploads/products/")


def test_build_crud_and_totals(client, make_user, make_product):
    _, headers = make_user()
    cpu = make_product(category="cpu", price="449.99")
    gpu = make_product(category="gpu", price=599)

    build = client.post("/api/builds", json={
        "name": "Mi PC gamer",
        "items": [{"product_id": cpu["id"]}, {"product_id": gpu["id"]}, {"product_id": cpu["id"]}],
    }, headers=headers)
    assert build.status_code == 201
    assert build.json()["total_price"] == round(449.99 * 2 + 599, 2)

    build_id = build.json()["id"]
    updated = client.patch(f"/api/builds/{build_id}", json={
        "items": [{"product_id": cpu["id"]}, {"product_id": gpu["id"], "quantity": 2}],
        "is_public": True,
    }, headers=headers).json()
    assert updated["total_price"] == round(449.99 + 1198, 2) and updated["is_public"] is True

    assert client.get("/api/builds/me", headers=headers).json()["total"] == 1
    assert build_id in [b["id"] for b in client.get("/api/builds/public").json()["items"]]
    assert client.delete(f"/api/builds/{build_id}", headers=headers).status_code == 204


def test_build_visibility_and_permissions(client, make_user, make_product):
    _, owner = make_user()
    _, other = make_user()
    gpu = make_product()
    build = client.post("/api/builds", json={"name": "Privada", "items": [{"product_id": gpu["id"]}]}, headers=owner).json()

    assert client.get(f"/api/builds/{build['id']}").status_code == 404
    assert client.get(f"/api/builds/{build['id']}", headers=other).status_code == 404
    assert client.patch(f"/api/builds/{build['id']}", json={"name": "Hack"}, headers=other).status_code in (403, 404)
    assert client.delete(f"/api/builds/{build['id']}", headers=other).status_code == 403


def test_build_rejects_inactive_products_and_protects_used_products(client, admin, make_user, make_product):
    _, headers = make_user()
    inactive = make_product(is_active=False)
    assert client.post("/api/builds", json={"name": "Mala", "items": [{"product_id": inactive["id"]}]}, headers=headers).status_code == 400

    used = make_product()
    client.post("/api/builds", json={"name": "Usa producto", "items": [{"product_id": used["id"]}]}, headers=headers)
    assert client.delete(f"/api/products/{used['id']}", headers=admin).status_code == 409


def test_clone_public_build(client, make_user, make_product):
    _, owner = make_user()
    _, other = make_user()
    gpu = make_product(price=500)
    build = client.post("/api/builds", json={"name": "Pública", "is_public": True, "items": [{"product_id": gpu["id"]}]}, headers=owner).json()

    clone = client.post(f"/api/builds/{build['id']}/clone", headers=other)
    assert clone.status_code == 201
    assert clone.json()["is_public"] is False and clone.json()["total_price"] == 500
