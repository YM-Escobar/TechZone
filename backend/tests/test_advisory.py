REQUEST = {"title": "PC para edición", "purpose": "edicion_video", "budget": 1500, "preferences": "Silenciosa"}


def test_full_advisory_flow(client, outbox, make_user, make_product):
    user, user_headers = make_user()
    _, advisor = make_user("asesor")
    gpu = make_product(price=800)

    advisory = client.post("/api/advisories", json=REQUEST, headers=user_headers)
    assert advisory.status_code == 201 and advisory.json()["status"] == "pendiente"
    advisory_id = advisory.json()["id"]

    assert client.patch(f"/api/advisories/{advisory_id}", json={"budget": 1800}, headers=user_headers).json()["budget"] == 1800
    unassigned = client.get("/api/advisories?unassigned=true", headers=advisor).json()
    assert advisory_id in [a["id"] for a in unassigned["items"]]

    assigned = client.post(f"/api/advisories/{advisory_id}/assign", headers=advisor).json()
    assert assigned["status"] == "en_progreso"
    assert client.patch(f"/api/advisories/{advisory_id}", json={"budget": 2000}, headers=user_headers).status_code == 409

    build = client.post("/api/builds", json={"name": "Recomendada", "items": [{"product_id": gpu["id"]}]}, headers=advisor).json()
    assert client.get(f"/api/builds/{build['id']}", headers=user_headers).status_code == 404

    answered = client.post(f"/api/advisories/{advisory_id}/respond", json={
        "advisor_notes": "Te recomiendo esta configuración", "recommended_build_id": build["id"],
    }, headers=advisor).json()
    assert answered["status"] == "completada" and answered["recommended_build"]["id"] == build["id"]
    assert any(mail["to"] == user["email"] and "asesoría" in mail["subject"] for mail in outbox)

    # El usuario ya puede ver y copiar la build recomendada
    assert client.get(f"/api/builds/{build['id']}", headers=user_headers).status_code == 200
    assert client.post(f"/api/builds/{build['id']}/clone", headers=user_headers).status_code == 201
    assert client.post(f"/api/advisories/{advisory_id}/cancel", headers=user_headers).status_code == 409


def test_advisory_permissions(client, admin, make_user):
    _, owner = make_user()
    _, stranger = make_user()
    _, advisor = make_user("asesor")
    _, other_advisor = make_user("asesor")
    advisory_id = client.post("/api/advisories", json=REQUEST, headers=owner).json()["id"]

    assert client.get("/api/advisories", headers=owner).status_code == 403
    assert client.get(f"/api/advisories/{advisory_id}", headers=stranger).status_code == 404
    assert client.post(f"/api/advisories/{advisory_id}/assign", headers=owner).status_code == 403

    client.post(f"/api/advisories/{advisory_id}/assign", headers=advisor)
    taken = client.post(f"/api/advisories/{advisory_id}/assign", headers=other_advisor)
    assert taken.status_code == 409
    response = client.post(f"/api/advisories/{advisory_id}/respond", json={"advisor_notes": "x"}, headers=other_advisor)
    assert response.status_code == 403

    assert client.delete(f"/api/advisories/{advisory_id}", headers=advisor).status_code == 403
    assert client.delete(f"/api/advisories/{advisory_id}", headers=admin).status_code == 204


def test_admin_assigns_reopens_and_user_cancels(client, admin, make_user):
    _, owner = make_user()
    advisor, _ = make_user("asesor")
    plain_user, _ = make_user()
    advisory_id = client.post("/api/advisories", json=REQUEST, headers=owner).json()["id"]

    invalid = client.post(f"/api/advisories/{advisory_id}/assign", json={"advisor_id": plain_user["id"]}, headers=admin)
    assert invalid.status_code == 400
    assigned = client.post(f"/api/advisories/{advisory_id}/assign", json={"advisor_id": advisor["id"]}, headers=admin).json()
    assert assigned["advisor"]["id"] == advisor["id"]

    reopened = client.patch(f"/api/advisories/{advisory_id}/status", json={"status": "pendiente"}, headers=admin).json()
    assert reopened["status"] == "pendiente" and reopened["advisor"] is None

    assert client.post(f"/api/advisories/{advisory_id}/cancel", headers=owner).json()["status"] == "cancelada"
    mine = client.get("/api/advisories/me?status=cancelada", headers=owner).json()
    assert [a["id"] for a in mine["items"]] == [advisory_id]
