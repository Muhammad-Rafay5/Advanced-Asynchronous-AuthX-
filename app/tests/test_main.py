import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.db.database import Base, engine, AsyncSessionLocal, get_db
from app.redis.blacklist import blacklist_service


@pytest_asyncio.fixture(scope="function", autouse=True)
async def reset_blacklist():
    """Force in-memory blacklist mode and clear it before/after every test."""
    blacklist_service._use_redis = False
    blacklist_service._internal_blacklist.clear()
    yield
    blacklist_service._internal_blacklist.clear()


@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Create all tables before the test, drop them after."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def test_full_workflow(db_session):
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    test_email = f"test_{unique_id}@example.com"
    test_password = "SecurePassword123"

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:

        # 1. Registration
        reg_response = await ac.post("/auth/register", json={
            "full_name": "Test User",
            "company_name": "Test Company",
            "email": test_email,
            "password": test_password,
            "confirm_password": test_password,
            "terms_accepted": True
        })
        assert reg_response.status_code == 201

        # 2. Login
        login_response = await ac.post("/auth/login", data={
            "username": test_email,
            "password": test_password
        })
        assert login_response.status_code == 200
        tokens = login_response.json()
        access_token = tokens["access_token"]
        refresh_token_val = tokens["refresh_token"]

        # 3. Access protected route
        me_response = await ac.get("/users/me", headers={"Authorization": f"Bearer {access_token}"})
        assert me_response.status_code == 200

        # 4. Token rotation
        refresh_response = await ac.post("/auth/refresh", json={"refresh_token": refresh_token_val})
        assert refresh_response.status_code == 200
        new_tokens = refresh_response.json()
        new_access_token = new_tokens["access_token"]
        new_refresh_token = new_tokens["refresh_token"]

        # 5. Logout (blacklists both tokens)
        logout_response = await ac.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {new_access_token}"},
            json={"refresh_token": new_refresh_token}
        )
        assert logout_response.status_code == 200

        # 6. Verify token is now blocked (zero-trust check)
        blocked_response = await ac.get("/users/me", headers={"Authorization": f"Bearer {new_access_token}"})
        assert blocked_response.status_code == 401

    app.dependency_overrides.clear()
