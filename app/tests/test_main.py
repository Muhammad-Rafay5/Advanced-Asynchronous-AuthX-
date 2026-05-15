import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.db.database import Base, engine, AsyncSessionLocal

@pytest_asyncio.fixture(scope="function")
async def db_session():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.mark.asyncio
async def test_full_workflow():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Registration
        reg_response = await ac.post("/auth/register", json={
            "email": "test@example.com",
            "password": "securepassword123"
        })
        assert reg_response.status_code == 201

        # 2. Authentication
        login_response = await ac.post("/auth/login", data={
            "username": "test@example.com",
            "password": "securepassword123"
        })
        assert login_response.status_code == 200
        tokens = login_response.json()
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]

        # 3. Security Access
        me_response = await ac.get("/users/me", headers={"Authorization": f"Bearer {access_token}"})
        assert me_response.status_code == 200

        # 4. Rotation
        refresh_response = await ac.post("/auth/refresh", json={"refresh_token": refresh_token})
        assert refresh_response.status_code == 200
        new_tokens = refresh_response.json()
        new_access_token = new_tokens["access_token"]

        # 5. Session Revocation
        logout_response = await ac.post("/auth/logout", headers={"Authorization": f"Bearer {new_access_token}"})
        assert logout_response.status_code == 200

        # 6. Zero-Trust Post-Validation
        blocked_response = await ac.get("/users/me", headers={"Authorization": f"Bearer {new_access_token}"})
        assert blocked_response.status_code == 401
