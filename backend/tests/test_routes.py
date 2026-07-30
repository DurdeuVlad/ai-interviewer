import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import Base
from app.routes import interviews as interviews_module


@pytest.fixture()
def client(monkeypatch):
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)

    # main.py wires init_db() via app lifespan against the real configured DATABASE_URL -
    # importing just the router and overriding its get_db dependency avoids touching that
    # engine or the on-disk interviews.db at all.
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(interviews_module.router)

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[interviews_module.get_db] = override_get_db
    return TestClient(app)


def test_full_happy_path(client):
    start = client.post("/interviews", json={"topic": "remote work"})
    assert start.status_code == 201
    interview_id = start.json()["interview_id"]
    assert start.json()["status"] == "in_progress"

    done = False
    for _ in range(10):
        answer = client.post(f"/interviews/{interview_id}/answer", json={"answer": "it's fine"})
        assert answer.status_code == 200
        done = answer.json()["done"]
        if done:
            break
    assert done is True

    summary = client.get(f"/interviews/{interview_id}/summary")
    assert summary.status_code == 200
    body = summary.json()
    assert "themes" in body and "key_points" in body

    detail = client.get(f"/interviews/{interview_id}")
    assert detail.status_code == 200
    assert detail.json()["status"] == "completed"


def test_get_unknown_interview_is_404(client):
    resp = client.get("/interviews/999999")
    assert resp.status_code == 404


def test_answer_after_completion_is_409(client):
    start = client.post("/interviews", json={"topic": "topic"})
    interview_id = start.json()["interview_id"]
    for _ in range(10):
        answer = client.post(f"/interviews/{interview_id}/answer", json={"answer": "a"})
        if answer.json()["done"]:
            break

    resp = client.post(f"/interviews/{interview_id}/answer", json={"answer": "one more"})
    assert resp.status_code == 409
    assert "already ended" in resp.json()["detail"]


def test_list_interviews_reflects_created_ones(client):
    client.post("/interviews", json={"topic": "topic A"})
    client.post("/interviews", json={"topic": "topic B"})

    resp = client.get("/interviews")
    assert resp.status_code == 200
    topics = [item["topic"] for item in resp.json()["interviews"]]
    assert topics == ["topic B", "topic A"]
