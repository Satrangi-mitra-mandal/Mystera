"""
DetectiveOS — Test Suite
Run: pytest backend/tests/ -v
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.database import Base, get_db
from app.config import settings

# Use SQLite for testing
TEST_DATABASE_URL = "sqlite:///./test_detectiveos.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def registered_user(client):
    res = client.post("/api/auth/register", json={
        "email": "test@test.com",
        "username": "testdetective",
        "password": "password123",
        "avatar": "🕵️"
    })
    return res.json()


@pytest.fixture
def auth_headers(registered_user):
    return {"Authorization": f"Bearer {registered_user['access_token']}"}


# ── Auth tests ─────────────────────────────────────
class TestAuth:
    def test_register(self, client):
        res = client.post("/api/auth/register", json={
            "email": "new@test.com",
            "username": "newdetective",
            "password": "password123",
            "avatar": "🔍"
        })
        assert res.status_code == 201
        data = res.json()
        assert "access_token" in data
        assert data["user"]["username"] == "newdetective"

    def test_register_duplicate_email(self, client, registered_user):
        res = client.post("/api/auth/register", json={
            "email": "test@test.com",
            "username": "other",
            "password": "password123"
        })
        assert res.status_code == 400

    def test_login(self, client, registered_user):
        res = client.post("/api/auth/login", json={
            "email": "test@test.com",
            "password": "password123"
        })
        assert res.status_code == 200
        assert "access_token" in res.json()

    def test_login_wrong_password(self, client, registered_user):
        res = client.post("/api/auth/login", json={
            "email": "test@test.com",
            "password": "wrongpassword"
        })
        assert res.status_code == 401

    def test_me(self, client, auth_headers):
        res = client.get("/api/auth/me", headers=auth_headers)
        assert res.status_code == 200
        assert res.json()["username"] == "testdetective"

    def test_me_no_token(self, client):
        res = client.get("/api/auth/me")
        assert res.status_code == 401


# ── Cases tests ────────────────────────────────────
class TestCases:
    def test_list_cases_empty(self, client):
        res = client.get("/api/cases")
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    def test_get_nonexistent_case(self, client):
        res = client.get("/api/cases/no-such-case")
        assert res.status_code == 404

    def test_start_case_requires_auth(self, client):
        res = client.post("/api/cases/some-case/start")
        assert res.status_code == 401


# ── Health check ───────────────────────────────────
class TestHealth:
    def test_health(self, client):
        res = client.get("/api/health")
        assert res.status_code == 200
        assert res.json()["status"] == "ok"
