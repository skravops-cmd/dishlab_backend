def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_readiness(client):
    res = client.get("/health/ready")
    assert res.status_code == 200
    assert res.json()["status"] == "ready"
