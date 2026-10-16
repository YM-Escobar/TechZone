from tests.conftest import PASSWORD, auth_headers

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


def test_read_and_update_profile(client, make_user):
    user, headers = make_user()
    me = client.get("/api/users/me", headers=headers).json()
    assert me["id"] == user["id"]

    updated = client.patch("/api/users/me", json={"full_name": "Nombre Nuevo", "bio": "Me gustan las PCs"}, headers=headers)
    assert updated.status_code == 200 and updated.json()["bio"] == "Me gustan las PCs"

    public = client.get(f"/api/users/{user['id']}").json()
    assert "email" not in public and public["full_name"] == "Nombre Nuevo"


def test_username_must_be_unique(client, make_user):
    other, _ = make_user()
    _, headers = make_user()
    assert client.patch("/api/users/me", json={"username": other["username"]}, headers=headers).status_code == 409


def test_change_password(client, make_user):
    user, headers = make_user()
    wrong = client.put("/api/users/me/password", json={"current_password": "mala", "new_password": "nueva12345"}, headers=headers)
    assert wrong.status_code == 400
    ok = client.put("/api/users/me/password", json={"current_password": PASSWORD, "new_password": "nueva12345"}, headers=headers)
    assert ok.status_code == 200
    auth_headers(client, user["username"], "nueva12345")


def test_avatar_upload_and_delete(client, make_user):
    _, headers = make_user()
    uploaded = client.put("/api/users/me/avatar", files={"file": ("foto.png", PNG, "image/png")}, headers=headers)
    assert uploaded.status_code == 200
    avatar_url = uploaded.json()["avatar_url"]
    assert avatar_url.startswith("/uploads/avatars/") and avatar_url.endswith(".png")
    assert client.get(avatar_url).content == PNG

    removed = client.delete("/api/users/me/avatar", headers=headers)
    assert removed.json()["avatar_url"] is None
    assert client.get(avatar_url).status_code == 404


def test_avatar_rejects_non_images(client, make_user):
    _, headers = make_user()
    fake = client.put("/api/users/me/avatar", files={"file": ("virus.png", b"MZ\x90\x00 no soy imagen", "image/png")}, headers=headers)
    assert fake.status_code == 400


def test_delete_own_account(client, make_user):
    user, headers = make_user()
    assert client.delete("/api/users/me", headers=headers).status_code == 204
    assert client.get(f"/api/users/{user['id']}").status_code == 404
