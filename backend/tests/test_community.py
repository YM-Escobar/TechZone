def test_post_crud_and_permissions(client, admin, make_user):
    _, author = make_user()
    _, other = make_user()
    post = client.post("/api/posts", json={"title": "Mi primera build", "content": "¿Qué opinan?"}, headers=author)
    assert post.status_code == 201
    post_id = post.json()["id"]

    assert client.get(f"/api/posts/{post_id}").json()["author"]["id"] == post.json()["author"]["id"]
    assert client.patch(f"/api/posts/{post_id}", json={"title": "Hackeado"}, headers=other).status_code == 403
    assert client.patch(f"/api/posts/{post_id}", json={"title": "Editado"}, headers=author).json()["title"] == "Editado"
    assert client.delete(f"/api/posts/{post_id}", headers=other).status_code == 403
    # El admin puede moderar
    assert client.delete(f"/api/posts/{post_id}", headers=admin).status_code == 204
    assert client.get(f"/api/posts/{post_id}").status_code == 404


def test_post_search(client, make_user):
    _, headers = make_user()
    client.post("/api/posts", json={"title": "Refrigeración líquida", "content": "texto-busqueda-xyz"}, headers=headers)
    assert client.get("/api/posts?search=texto-busqueda-xyz").json()["total"] == 1


def test_only_public_builds_can_be_shared(client, make_user, make_product):
    _, headers = make_user()
    gpu = make_product()
    private = client.post("/api/builds", json={"name": "Privada", "items": [{"product_id": gpu["id"]}]}, headers=headers).json()
    data = {"title": "Miren mi build", "content": "...", "build_id": private["id"]}
    assert client.post("/api/posts", json=data, headers=headers).status_code == 400

    client.patch(f"/api/builds/{private['id']}", json={"is_public": True}, headers=headers)
    assert client.post("/api/posts", json=data, headers=headers).status_code == 201


def test_comments_and_likes(client, admin, make_user):
    _, author = make_user()
    _, other = make_user()
    post_id = client.post("/api/posts", json={"title": "Likes", "content": "..."}, headers=author).json()["id"]

    comment = client.post(f"/api/posts/{post_id}/comments", json={"content": "¡Buena build!"}, headers=other).json()
    assert client.patch(f"/api/comments/{comment['id']}", json={"content": "x"}, headers=author).status_code == 403
    assert client.patch(f"/api/comments/{comment['id']}", json={"content": "¡Muy buena!"}, headers=other).json()["content"] == "¡Muy buena!"
    assert client.get(f"/api/posts/{post_id}/comments").json()["total"] == 1

    client.post(f"/api/posts/{post_id}/like", headers=other)
    liked = client.post(f"/api/posts/{post_id}/like", headers=other).json()  # un segundo like no suma
    assert liked["like_count"] == 1 and liked["comment_count"] == 1
    assert client.delete(f"/api/posts/{post_id}/like", headers=other).json()["like_count"] == 0

    assert client.delete(f"/api/comments/{comment['id']}", headers=author).status_code == 403
    assert client.delete(f"/api/comments/{comment['id']}", headers=admin).status_code == 204


def test_deleting_user_removes_their_content(client, make_user):
    _, headers = make_user()
    post_id = client.post("/api/posts", json={"title": "Se borrará", "content": "..."}, headers=headers).json()["id"]
    client.delete("/api/users/me", headers=headers)
    assert client.get(f"/api/posts/{post_id}").status_code == 404
