# AuthX — Full Codebase Fix Prompt

You are an expert Python and JavaScript developer. Below is a complete list of bugs, security vulnerabilities, and code quality issues found in the **Advanced-Asynchronous-AuthX-** project (a FastAPI + Vanilla JS authentication system). Fix **every single issue listed** in the exact files and locations specified. Do not change anything that is not mentioned. After all fixes are applied, the project must be fully functional, secure, and ready for production.

---

## PROJECT STRUCTURE (for reference)

```
├── app/
│   ├── core/config.py
│   ├── core/security.py
│   ├── core/rate_limit.py
│   ├── db/database.py
│   ├── db/models.py
│   ├── dependencies/auth.py
│   ├── redis/blacklist.py
│   ├── routes/auth.py
│   ├── routes/users.py
│   ├── schemas/auth.py
│   ├── schemas/user.py
│   ├── services/auth.py
│   ├── tests/test_main.py
│   └── main.py
├── alembic/env.py
├── frontend/
│   ├── auth.js
│   ├── main.js
│   └── index.html
├── requirements.txt
├── docker-compose.yml
└── entrypoint.sh
```

---

## 🔴 CRITICAL FIXES (Security / Runtime Failures)

---

### FIX 1 — `frontend/auth.js`: Stop storing tokens in localStorage

**Problem:** Both `access_token` and `refresh_token` are stored in `localStorage`. Any XSS script can read `localStorage.getItem('access_token')` and steal both tokens permanently.

**Fix:** Store the access token only in a JavaScript module-level variable (in-memory, lost on tab close). Store the refresh token in an `httpOnly`, `Secure`, `SameSite=Strict` cookie set by the backend. Remove all `localStorage` calls for tokens.

Change `saveTokens`, `getAccessToken`, `getRefreshToken`, and `clearTokens` in `auth.js` to:

```javascript
// In-memory store for access token
let _accessToken = null;

const authService = {
    saveTokens(access) {
        _accessToken = access;
        // refresh token is set as httpOnly cookie by the backend — do not touch it here
    },

    getAccessToken() {
        return _accessToken;
    },

    clearTokens() {
        _accessToken = null;
        // The backend clears the cookie on logout via Set-Cookie with Max-Age=0
    },

    // ... rest of the methods unchanged, but remove all localStorage.getItem/setItem/removeItem calls
};
```

Update `login()` to call `this.saveTokens(data.access_token)` (no second argument).
Update `refresh()` to call `this.saveTokens(data.access_token)` (no second argument).
Update `logout()` — no token argument needed for cookie; the cookie is sent automatically by the browser.

---

### FIX 2 — `app/routes/auth.py`: Logout must also blacklist the refresh token

**Problem:** The `logout()` endpoint only blacklists the access token's JTI. The refresh token is never revoked. A stolen refresh token can be used to generate new access tokens indefinitely even after the user logs out.

**Fix:** Accept the refresh token in the logout request body and blacklist its JTI too.

Replace the existing `logout` route with:

```python
@router.post("/logout", response_model=StandardActionResponse)
async def logout(
    token: str = Depends(oauth2_scheme),
    refresh_token: str = Body(..., embed=True)
):
    # Blacklist the access token
    try:
        payload = decode_token(token, settings.ACCESS_TOKEN_SECRET)
        token_data = TokenPayload(**payload)
        remaining = token_data.exp - int(datetime.now(timezone.utc).timestamp())
        await blacklist_service.add(token_data.jti, max(remaining, 0))
    except Exception:
        pass  # Already expired — nothing to blacklist

    # Blacklist the refresh token
    try:
        r_payload = decode_token(refresh_token, settings.REFRESH_TOKEN_SECRET)
        r_data = TokenPayload(**r_payload)
        r_remaining = r_data.exp - int(datetime.now(timezone.utc).timestamp())
        await blacklist_service.add(r_data.jti, max(r_remaining, 0))
    except Exception:
        pass  # Already expired — nothing to blacklist

    return StandardActionResponse(detail="Revocation complete")
```

Also update the `Body` import at the top of `app/routes/auth.py` — it is already imported, so no change needed there.

---

### FIX 3 — `app/redis/blacklist.py`: Fix the broken Redis connection check

**Problem:** `BlacklistService.__init__` tries to detect Redis failures at construction time, but `redis.asyncio.Redis()` **never raises on construction** — it only raises on the first I/O call. So `_use_redis` is always `True`, the in-memory fallback is never activated, and a Redis outage causes `is_blacklisted()` to silently return `False` — blacklisted tokens are silently accepted.

**Fix:** Add an async `initialize()` method that pings Redis and sets the flag correctly. Call it during app startup in `main.py`.

Replace `blacklist.py` with:

```python
import redis.asyncio as redis
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class BlacklistService:
    def __init__(self):
        self.redis = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            decode_responses=True
        )
        self._use_redis = False  # Will be set to True only after a successful ping
        self._internal_blacklist = set()

    async def initialize(self):
        """Call this during app startup to verify Redis connectivity."""
        try:
            await self.redis.ping()
            self._use_redis = True
            logger.info("Redis blacklist service: connected.")
        except Exception as e:
            self._use_redis = False
            logger.warning(f"Redis unavailable, using in-memory blacklist fallback: {e}")

    async def add(self, token_jti: str, expires_in_seconds: int):
        if self._use_redis:
            try:
                await self.redis.setex(token_jti, expires_in_seconds, "blacklisted")
                return
            except Exception as e:
                logger.error(f"Redis add error: {e}")
        self._internal_blacklist.add(token_jti)

    async def is_blacklisted(self, token_jti: str) -> bool:
        if self._use_redis:
            try:
                return await self.redis.exists(token_jti) > 0
            except Exception as e:
                logger.error(f"Redis check error, denying token to be safe: {e}")
                return True  # Fail-safe: deny if Redis is down
        return token_jti in self._internal_blacklist


blacklist_service = BlacklistService()
```

Then in `app/main.py`, update the `lifespan` function to call `initialize()`:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Database...")
    await init_db()
    logger.info("Initializing Redis Blacklist Service...")
    await blacklist_service.initialize()
    yield
    logger.info("Shutting down application...")
```

Add the import at the top of `main.py`:
```python
from app.redis.blacklist import blacklist_service
```

---

### FIX 4 — `app/routes/auth.py`: Refresh endpoint must check the blacklist

**Problem:** The `/auth/refresh` endpoint decodes the refresh token and immediately issues new tokens without checking if the JTI is already blacklisted. A revoked refresh token can still be used to mint new access tokens.

**Fix:** Add a blacklist check immediately after decoding the token. Add this block right after `token_data = TokenPayload(**payload)`:

```python
# Check if this refresh token has already been revoked
if await blacklist_service.is_blacklisted(token_data.jti):
    raise HTTPException(status_code=401, detail="Refresh token has been revoked")
```

Make sure `blacklist_service` is imported at the top of `app/routes/auth.py` — it already is.

---

## 🟡 WARNING FIXES (Bugs & Incorrect Behavior)

---

### FIX 5 — `requirements.txt`: Add missing `gunicorn` and `psycopg2-binary`

**Problem 1:** `entrypoint.sh` starts the server with `gunicorn`, but `gunicorn` is not in `requirements.txt`. The Docker image will build successfully, then crash at startup with `command not found: gunicorn`.

**Problem 2:** Alembic's `run_migrations_online()` uses `engine_from_config()` which defaults to the `psycopg2` driver. `psycopg2-binary` is not in `requirements.txt`, so `alembic upgrade head` in `entrypoint.sh` fails and migrations never apply.

**Fix:** Add these two lines to `requirements.txt`:

```
gunicorn==22.0.0
psycopg2-binary==2.9.9
```

---

### FIX 6 — `docker-compose.yml`: Expose the backend port

**Problem:** The `app` service has no `ports` mapping. Developers cannot access `http://localhost:8000` from their machine to test the API or view Swagger docs.

**Fix:** Add a `ports` section to the `app` service in `docker-compose.yml`:

```yaml
app:
  build:
    context: .
    dockerfile: Dockerfile
  restart: always
  env_file:
    - .env
  environment:
    - DATABASE_URL=postgresql+asyncpg://postgres:password@db:5432/auth_system
    - REDIS_HOST=redis
  ports:
    - "8000:8000"       # ← ADD THIS
  depends_on:
    db:
      condition: service_healthy
    redis:
      condition: service_healthy
```

---

### FIX 7 — `app/tests/test_main.py`: Fix test isolation — inject the DB fixture

**Problem:** `test_full_workflow` doesn't use the `db_session` fixture. It creates its own app client sharing the global engine without resetting tables. Residual data from a prior run causes the duplicate-email check to fail registration with a 400.

**Fix:** Pass `db_session` into the test and override the app's DB dependency:

```python
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.db.database import Base, engine, AsyncSessionLocal, get_db


@pytest_asyncio.fixture(scope="function")
async def db_session():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_full_workflow(db_session):
    # Override DB dependency to use the isolated test session
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Registration
        reg_response = await ac.post("/auth/register", json={
            "email": "test@example.com",
            "password": "SecurePassword123"
        })
        assert reg_response.status_code == 201

        # 2. Authentication
        login_response = await ac.post("/auth/login", data={
            "username": "test@example.com",
            "password": "SecurePassword123"
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

        # 5. Session Revocation (now also sends refresh token)
        logout_response = await ac.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {new_access_token}"},
            json={"refresh_token": new_tokens["refresh_token"]}
        )
        assert logout_response.status_code == 200

        # 6. Zero-Trust Post-Validation
        blocked_response = await ac.get("/users/me", headers={"Authorization": f"Bearer {new_access_token}"})
        assert blocked_response.status_code == 401

    app.dependency_overrides.clear()
```

---

### FIX 8 — `app/main.py`: Fix CORS wildcard incompatibility with credentials

**Problem:** `allow_methods=["*"]` and `allow_headers=["*"]` combined with `allow_credentials=True` violates the browser CORS spec. Browsers reject wildcard values when credentials are included. Preflight requests for non-simple methods (PATCH, DELETE, etc.) will fail.

**Fix:** Replace the wildcard values with explicit lists:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)
```

---

### FIX 9 — `frontend/main.js`: Fix the non-functional "Apply" button

**Problem:** Every row in the identity table renders an "Apply" button with no click handler attached. Clicking it does nothing.

**Fix:** Either remove the button entirely (safest, since no backend endpoint exists for user management actions), or add a placeholder. Remove this line from the `row.innerHTML` template inside `loadSessions()`:

```javascript
// REMOVE this td:
<td><button class="btn btn-outline" style="padding: 0.3rem 0.8rem; font-size: 0.7rem;">Apply</button></td>
```

Also update the `colspan` on the loading and error rows from `7` to `6` to match the reduced column count.

---

## 🔵 IMPROVEMENT FIXES (Code Quality & Reliability)

---

### FIX 10 — `app/routes/auth.py`: Clean up the logout fallback — don't use raw token as JTI

**Problem:** When token decode fails in the `except` branch of `logout()`, the code does `jti = token` and passes the full raw JWT string (~300 chars) to `blacklist_service.add()` as the key. This wastes Redis memory and is semantically wrong. After applying FIX 2, this fallback no longer exists, so no additional change is needed here. Just confirm the new `logout()` from FIX 2 is in place.

---

### FIX 11 — `frontend/main.js`: Restart the countdown after a silent token refresh

**Problem:** After `fetchWithAuth()` triggers a silent token refresh, new tokens are saved but `startCountdown()` is never called. The UI countdown continues from the old token's expiry and shows "Expired" even though the session is still valid.

**Fix:** In `auth.js`, after saving the new access token in `refresh()`, dispatch a custom event:

```javascript
async refresh() {
    const refreshToken = this.getRefreshToken();  // This will come from the cookie after FIX 1; adjust accordingly
    if (!refreshToken) throw new Error('No refresh token available');

    const response = await fetch(`${API_URL}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',  // Sends the httpOnly cookie
        body: JSON.stringify({ refresh_token: refreshToken })
    });

    if (!response.ok) {
        this.clearTokens();
        throw new Error('Session expired');
    }

    const data = await response.json();
    this.saveTokens(data.access_token);

    // Notify the UI that a new token is available so it can restart the countdown
    window.dispatchEvent(new CustomEvent('tokens-refreshed'));

    return data.access_token;
},
```

In `main.js`, add this listener near the other global event listeners:

```javascript
window.addEventListener('tokens-refreshed', startCountdown);
```

---

### FIX 12 — `frontend/index.html` + `frontend/main.js`: Add client-side password validation

**Problem:** The backend enforces password rules (min 8 chars, one uppercase, one digit), but the frontend has no inline validation. Users only learn about requirements after a failed network call.

**Fix:** Add an `input` event listener to the password field in `main.js` (after the DOM is ready):

```javascript
const regPassword = document.getElementById('reg-password');
if (regPassword) {
    regPassword.addEventListener('input', () => {
        const v = regPassword.value;
        const ok = v.length >= 8 && /[A-Z]/.test(v) && /[0-9]/.test(v);
        regPassword.style.borderColor = v.length === 0 ? '' : ok ? 'var(--accent-green)' : 'var(--accent-red)';
    });
}
```

Add a hint element in `index.html` below the register password input:

```html
<p style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.25rem;">
    Min 8 characters, one uppercase letter, one number.
</p>
```

---

### FIX 13 — `requirements.txt`: Fix bcrypt version to stop passlib deprecation warning

**Problem:** `bcrypt==4.0.1` introduced a breaking API change that causes passlib 1.7.4 to emit `AttributeError: module 'bcrypt' has no attribute '__about__'` on every startup, polluting logs.

**Fix:** Downgrade bcrypt in `requirements.txt`:

```
# Change this:
bcrypt==4.0.1

# To this:
bcrypt==3.2.2
```

---

### FIX 14 — `frontend/main.js`: Replace hardcoded session TTL of `15` with dynamic value

**Problem:** The "Token TTL" column in the identity table always shows the hardcoded number `15`, regardless of the actual configured expiry.

**Fix:** Replace the hardcoded `<td>15</td>` inside `loadSessions()` with a dynamic value derived from the JWT for the current user, and a dash for others:

```javascript
// Add this before building row.innerHTML:
let ttlDisplay = '—';
if (isMe) {
    const token = authService.getAccessToken();
    const payload = parseJwt(token);
    if (payload && payload.iat && payload.exp) {
        ttlDisplay = Math.ceil((payload.exp - payload.iat) / 60) + ' min';
    }
}

// Then in row.innerHTML replace:
//   <td>15</td>
// with:
//   <td>${ttlDisplay}</td>
```

---

## SUMMARY OF ALL FILES TO CHANGE

| File | Changes |
|---|---|
| `frontend/auth.js` | FIX 1, FIX 11 — remove localStorage, use in-memory token, dispatch tokens-refreshed event |
| `frontend/main.js` | FIX 9, FIX 11, FIX 12, FIX 14 — remove Apply button, listen tokens-refreshed, password hint, dynamic TTL |
| `frontend/index.html` | FIX 12 — add password hint paragraph |
| `app/routes/auth.py` | FIX 2, FIX 4 — logout blacklists refresh token too; refresh checks blacklist |
| `app/redis/blacklist.py` | FIX 3 — async initialize() ping check; fail-safe deny on Redis error |
| `app/main.py` | FIX 3 — call blacklist_service.initialize() in lifespan; FIX 8 — explicit CORS lists |
| `app/tests/test_main.py` | FIX 7 — inject db_session fixture, override get_db dependency |
| `requirements.txt` | FIX 5, FIX 13 — add gunicorn, psycopg2-binary; downgrade bcrypt |
| `docker-compose.yml` | FIX 6 — expose port 8000 for the app service |

---

## CONSTRAINTS

- Do not rename any files, endpoints, or environment variable names.
- Do not change the project structure.
- Do not alter any functionality that is not mentioned above.
- After all fixes, `pytest` must pass, `docker-compose up` must build and run without errors, and the `/auth/register`, `/auth/login`, `/auth/refresh`, `/auth/logout`, and `/users/me` endpoints must all work correctly end-to-end.
