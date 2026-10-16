def test_only_admin_can_access(client, make_user):
    _, user_headers = make_user()
    _, advisor_headers = make_user("asesor")
    assert client.get("/api/admin/users", headers=user_headers).status_code == 403
    assert client.get("/api/admin/stats", headers=advisor_headers).status_code == 403


def test_list_and_filter_users(client, admin, make_user):
    advisor, _ = make_user("asesor")
    page = client.get("/api/admin/users?role=asesor", headers=admin).json()
    assert advisor["id"] in [u["id"] for u in page["items"]]
    assert all(u["role"] == "asesor" for u in page["items"])

    found = client.get(f"/api/admin/users?search={advisor['username']}", headers=admin).json()
    assert found["total"] == 1


def test_change_role_status_and_delete(client, admin, make_user):
    user, headers = make_user()
    assert client.patch(f"/api/admin/users/{user['id']}/role", json={"role": "asesor"}, headers=admin).json()["role"] == "asesor"
    assert client.patch(f"/api/admin/users/{user['id']}", json={"full_name": "Editado"}, headers=admin).json()["full_name"] == "Editado"

    assert client.patch(f"/api/admin/users/{user['id']}/status", json={"is_active": False}, headers=admin).status_code == 200
    assert client.get("/api/users/me", headers=headers).status_code == 403
    login = client.post("/api/auth/login", data={"username": user["username"], "password": "secret123"})
    assert login.status_code == 403

    assert client.delete(f"/api/admin/users/{user['id']}", headers=admin).status_code == 204
    assert client.get(f"/api/admin/users/{user['id']}", headers=admin).status_code == 404


def test_admin_cannot_lock_themselves_out(client, admin):
    me = client.get("/api/users/me", headers=admin).json()
    assert client.patch(f"/api/admin/users/{me['id']}/role", json={"role": "usuario"}, headers=admin).status_code == 403
    assert client.patch(f"/api/admin/users/{me['id']}/status", json={"is_active": False}, headers=admin).status_code == 403
    assert client.delete(f"/api/admin/users/{me['id']}", headers=admin).status_code == 403
    assert client.delete("/api/users/me", headers=admin).status_code == 409


def test_stats(client, admin):
    stats = client.get("/api/admin/stats", headers=admin).json()
    assert stats["users"]["by_role"]["admin"] >= 1
    assert set(stats["advisories_by_status"]) == {"pendiente", "en_progreso", "completada", "cancelada"}


def test_reports_moderation(client, admin, make_user):
    _, author = make_user()
    _, reporter = make_user()
    post = client.post("/api/posts", json={"title": "Post polémico", "content": "..."}, headers=author).json()
    comment = client.post(f"/api/posts/{post['id']}/comments", json={"content": "spam"}, headers=author).json()

    report = client.post(f"/api/posts/{post['id']}/report", json={"reason": "Contenido ofensivo"}, headers=reporter)
    assert report.status_code == 201
    assert client.post(f"/api/posts/{post['id']}/report", json={"reason": "Otra vez"}, headers=reporter).status_code == 409
    comment_report = client.post(f"/api/comments/{comment['id']}/report", json={"reason": "Es spam"}, headers=reporter).json()

    pending = client.get("/api/admin/reports?status=pendiente", headers=admin).json()
    assert {report.json()["id"], comment_report["id"]} <= {r["id"] for r in pending["items"]}
    assert client.get("/api/admin/stats", headers=admin).json()["pending_reports"] >= 2

    dismissed = client.patch(f"/api/admin/reports/{report.json()['id']}", json={"status": "descartado"}, headers=admin).json()
    assert dismissed["status"] == "descartado" and dismissed["resolved_by"]["username"] == "admin"

    # Al eliminar el contenido reportado también se eliminan sus reportes
    assert client.delete(f"/api/comments/{comment['id']}", headers=admin).status_code == 204
    remaining = client.get("/api/admin/reports", headers=admin).json()
    assert comment_report["id"] not in {r["id"] for r in remaining["items"]}


def test_list_all_comments(client, admin, make_user):
    _, headers = make_user()
    post = client.post("/api/posts", json={"title": "Comentarios", "content": "..."}, headers=headers).json()
    client.post(f"/api/posts/{post['id']}/comments", json={"content": "texto-unico-moderacion"}, headers=headers)
    found = client.get("/api/admin/comments?search=texto-unico-moderacion", headers=admin).json()
    assert found["total"] == 1
