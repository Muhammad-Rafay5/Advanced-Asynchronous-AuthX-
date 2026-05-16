# 🔐 Advanced Asynchronous AuthX

![CI/CD](https://github.com/Muhammad-Rafay5/Advanced-Asynchronous-AuthX-/actions/workflows/main.yml/badge.svg)
![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green?logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue?logo=postgresql)
![Redis](https://img.shields.io/badge/Redis-7-red?logo=redis)
![License](https://img.shields.io/badge/License-MIT-yellow)

A **production-grade, fully asynchronous authentication system** built with FastAPI. Implements a Zero-Trust security architecture featuring dual-token JWT management, real-time session revocation via Redis, and a glassmorphic vanilla JavaScript frontend.

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Architecture](#-architecture)
- [API Endpoints](#-api-endpoints)
- [Authentication Flows](#-authentication-flows)
- [Getting Started](#-getting-started)
- [Environment Variables](#-environment-variables)
- [Running Tests](#-running-tests)
- [CI/CD Pipeline](#-cicd-pipeline)
- [Security Design](#-security-design)
- [Contributors](#-contributors)

---

## 🌟 Overview

AuthX is designed for developers who want to understand how a modern, production-ready authentication backend works. It moves away from traditional stateful cookies and embraces a **stateless but revocable JWT approach** — meaning tokens carry no server-side state, yet can be invalidated instantly using a Redis blacklist.

Every database operation is **non-blocking** using SQLAlchemy 2.0's async engine, making the system capable of handling high concurrency without thread-blocking I/O.

---

## ✨ Features

- **Fully Asynchronous** — Every DB query and Redis operation is non-blocking using `async/await`
- **Dual-Token System** — Short-lived Access Tokens (15 min) + long-lived Refresh Tokens (7 days)
- **Real-Time Logout** — Tokens are blacklisted in Redis on logout, invalidating them instantly even before expiry
- **Zero-Trust Security** — Every protected endpoint validates the token signature AND checks the Redis blacklist
- **Silent Token Refresh** — Frontend automatically refreshes expired access tokens using the refresh token
- **Password Security** — Bcrypt hashing with automatic salting to prevent rainbow table attacks
- **Rate Limiting** — SlowAPI integration to protect against brute-force attacks
- **CORS Protection** — Configurable allowed origins to prevent unauthorized cross-origin requests
- **Database Migrations** — Alembic-managed schema versioning
- **CI/CD Pipeline** — Automated linting (flake8), security scanning (Bandit), and async testing on every push
- **Glassmorphic UI** — Premium frontend built with pure HTML, CSS, and JavaScript

---

## 🛠️ Tech Stack

### Backend
| Technology | Version | Purpose |
|---|---|---|
| FastAPI | 0.111.0 | Async web framework |
| SQLAlchemy (Async) | ≥2.0.40 | ORM with non-blocking DB driver |
| PostgreSQL + asyncpg | 16 / 0.29.0 | Primary database |
| Redis | 5.0.4 | Token blacklist & session store |
| PyJWT | 2.8.0 | JWT creation and validation (HS256) |
| Passlib + Bcrypt | 1.7.4 / 3.2.2 | Password hashing |
| Alembic | 1.13.1 | Database migrations |
| SlowAPI | 0.1.9 | Rate limiting |
| Pydantic Settings | 2.2.1 | Environment config validation |
| Uvicorn / Gunicorn | 0.30.1 / 22.0.0 | ASGI server |

### Frontend
| Technology | Purpose |
|---|---|
| HTML5 + CSS3 | Structure and Glassmorphism styling |
| Vanilla JavaScript (ES6+) | Token management and API calls |
| Google Fonts (Outfit) | Typography |

### Dev & CI/CD
| Technology | Purpose |
|---|---|
| pytest + pytest-asyncio | Async test suite |
| httpx | Async HTTP test client |
| flake8 | PEP8 linting |
| Bandit | Security vulnerability scanning |
| GitHub Actions | Automated CI/CD pipeline |

---

## 📂 Project Structure

```
Advanced-Asynchronous-AuthX-/
│
├── .github/
│   └── workflows/
│       └── main.yml              # CI/CD pipeline definition
│
├── app/
│   ├── core/
│   │   ├── config.py             # Pydantic settings — secrets, DB URLs, token lifetimes
│   │   └── security.py           # Bcrypt hashing + JWT creation/validation (HS256)
│   │
│   ├── db/
│   │   ├── database.py           # Async SQLAlchemy engine + get_db session dependency
│   │   └── models.py             # User model (email, hashed_password, is_active)
│   │
│   ├── schemas/
│   │   ├── user.py               # UserCreate, UserResponse Pydantic models
│   │   └── auth.py               # TokenResponse, MessageResponse schemas
│   │
│   ├── routes/
│   │   ├── auth.py               # /register, /login, /logout, /refresh endpoints
│   │   └── users.py              # /me endpoint (protected)
│   │
│   ├── services/
│   │   └── auth.py               # Business logic — credential verification, registration
│   │
│   ├── dependencies/
│   │   └── auth.py               # get_current_user — Zero-Trust request interceptor
│   │
│   ├── redis/
│   │   └── blacklist.py          # Redis token blacklist — add_to_blacklist, is_blacklisted
│   │
│   └── tests/
│       ├── conftest.py           # Async test fixtures (DB, client setup)
│       └── test_auth.py          # E2E auth flow tests
│
├── alembic/
│   ├── env.py                    # Alembic async migration environment
│   └── versions/                 # Auto-generated migration scripts
│
├── frontend/
│   ├── index.html                # Landing / Login page
│   ├── register.html             # Registration page
│   ├── dashboard.html            # Protected dashboard
│   ├── style.css                 # Glassmorphism styles
│   └── auth.js                   # Token management + silent refresh logic
│
├── .env.example                  # Environment variable template
├── .flake8                       # Flake8 linting configuration
├── .gitignore                    # Git ignore rules
├── alembic.ini                   # Alembic configuration
├── pytest.ini                    # Pytest asyncio_mode=auto configuration
├── requirements.txt              # Python dependencies
├── Makefile                      # Docker convenience commands
└── README.md                     # This file
```

---

## 🏗️ Architecture

The project follows a **Modular Clean Architecture** with strict separation between layers:

```
Client / Frontend
       │
       ▼ HTTP Request
┌─────────────────────────────────┐
│     Interface Layer             │
│  app/routes/auth.py             │  ← /register, /login, /logout, /refresh
│  app/routes/users.py            │  ← /me
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│     Security Layer              │
│  app/dependencies/auth.py       │  ← get_current_user (Zero-Trust interceptor)
│  app/core/security.py           │  ← JWT verify + Bcrypt
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│     Business Logic Layer        │
│  app/services/auth.py           │  ← Credential verification, registration
│  app/redis/blacklist.py         │  ← Token blacklist operations
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│     Data Layer                  │
│  app/db/database.py             │  ← Async SQLAlchemy engine
│  app/db/models.py               │  ← User schema
└─────────────────────────────────┘
       │                 │
       ▼                 ▼
  PostgreSQL           Redis
  (persistent)      (in-memory blacklist)
```

---

## 📡 API Endpoints

Base URL: `http://127.0.0.1:8000`  
Interactive Docs: `http://127.0.0.1:8000/docs`

### Auth Routes — `/auth`

| Method | Endpoint | Auth Required | Description |
|---|---|---|---|
| `POST` | `/auth/register` | No | Create a new user account |
| `POST` | `/auth/login` | No | Login and receive access + refresh tokens |
| `POST` | `/auth/logout` | Yes (Bearer) | Blacklist the current token, ending the session |
| `POST` | `/auth/refresh` | Yes (Refresh Token) | Exchange a refresh token for a new access token |

### User Routes — `/users`

| Method | Endpoint | Auth Required | Description |
|---|---|---|---|
| `GET` | `/users/me` | Yes (Bearer) | Get the currently authenticated user's profile |

### Request / Response Examples

**POST `/auth/register`**
```json
// Request Body
{
  "email": "user@example.com",
  "password": "StrongPassword123!"
}

// Response 201
{
  "id": 1,
  "email": "user@example.com",
  "is_active": true
}
```

**POST `/auth/login`**
```json
// Request Body
{
  "email": "user@example.com",
  "password": "StrongPassword123!"
}

// Response 200
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

**POST `/auth/logout`**
```
// Header: Authorization: Bearer <access_token>

// Response 200
{
  "message": "Successfully logged out"
}
```

---

## 🔄 Authentication Flows

### 1. Registration & Login
```
User ──POST /register──► Validate schema ──► Hash password (Bcrypt) ──► Save to DB
User ──POST /login─────► Verify password ──► Issue Access Token (15min) + Refresh Token (7d) ──► Return tokens
```

### 2. Protected Resource Access (Zero-Trust)
```
Request ──► get_current_user interceptor
              │
              ├── Verify JWT signature (HS256) ──✗──► 401 Unauthorized
              │
              ├── Check Redis blacklist ──────✗──► 401 Unauthorized (logged out token)
              │
              └──✓──► Inject user into route ──► Return protected data
```

### 3. Silent Token Refresh
```
Frontend request ──► 401 Unauthorized (access token expired)
                       │
                       └──► POST /auth/refresh with refresh_token
                                │
                                ├── Validate refresh token type claim
                                ├── Check blacklist
                                └──► Issue new access_token ──► Retry original request
```

### 4. Secure Logout
```
POST /auth/logout ──► Extract token JTI/fingerprint ──► Store in Redis with TTL = token's remaining lifetime
                                                           │
                                                           └──► All future requests with this token ──► 401 (blacklisted)
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- PostgreSQL 16 (running locally or via Docker)
- Redis 7 (running locally or via Docker)

### 1. Clone the Repository

```bash
git clone https://github.com/Muhammad-Rafay5/Advanced-Asynchronous-AuthX-.git
cd Advanced-Asynchronous-AuthX-
```

### 2. Create and Activate a Virtual Environment

```bash
# Create
python -m venv venv

# Activate — Windows
venv\Scripts\activate

# Activate — macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
cp .env.example .env
```

Open `.env` and fill in your values (see [Environment Variables](#-environment-variables) below).

### 5. Run Database Migrations

```bash
alembic upgrade head
```

### 6. Start the Backend

```bash
uvicorn app.main:app --reload
```

The API will be available at: `http://127.0.0.1:8000`  
Swagger UI docs: `http://127.0.0.1:8000/docs`

### 7. Start the Frontend

```bash
python -m http.server 3000 --directory frontend
```

The UI will be available at: `http://127.0.0.1:3000`

---

## ⚙️ Environment Variables

Copy `.env.example` to `.env` and configure the following:

```env
# --- Security & Core ---
PROJECT_NAME="Advanced Asynchronous Backend"
ACCESS_TOKEN_SECRET="your_long_random_access_secret_here"
REFRESH_TOKEN_SECRET="your_different_long_random_refresh_secret_here"
ALGORITHM="HS256"

# --- Token Lifetimes ---
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# --- PostgreSQL Database ---
DATABASE_URL="postgresql+asyncpg://postgres:password@localhost:5432/auth_system"

# --- Connection Pool ---
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10

# --- Redis ---
REDIS_HOST="localhost"
REDIS_PORT=6379

# --- CORS ---
CORS_ORIGINS="http://localhost:5500,http://127.0.0.1:5500,http://localhost:3000"
```

> ⚠️ **Never commit your `.env` file.** It is already listed in `.gitignore`.

---

## 🧪 Running Tests

The test suite uses `pytest-asyncio` for fully async end-to-end tests.

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run a specific test file
pytest app/tests/test_auth.py -v
```

Tests automatically use an in-memory SQLite database (via `aiosqlite`) so no PostgreSQL instance is required to run them locally.

---

## 🔁 CI/CD Pipeline

Every push to `main` or `develop` triggers the GitHub Actions pipeline defined in `.github/workflows/main.yml`.

### Pipeline Steps

```
Push to main
     │
     ▼
1. Checkout code
2. Set up Python 3.12
3. Install dependencies (pip install -r requirements.txt)
     │
     ▼
4. Lint with flake8 ──────────── Fails on PEP8 violations (max line length 120)
     │
     ▼
5. Security scan with Bandit ─── Fails on high-severity issues in app/ code
     │
     ▼
6. Run async tests with pytest ─ Spins up PostgreSQL 16 + Redis 7 service containers
     │                           Runs full E2E test suite
     ▼
✅ All green → Pipeline passes
```

### Services Used in CI

The pipeline spins up real service containers:
- **PostgreSQL 16** on port `5432` with health checks
- **Redis 7** on port `6379` with health checks

### CI Environment Variables

Set automatically in the workflow (no secrets needed for tests):

```
ACCESS_TOKEN_SECRET  → ci_test_access_secret_do_not_use_in_prod
REFRESH_TOKEN_SECRET → ci_test_refresh_secret_do_not_use_in_prod
ALGORITHM            → HS256
DATABASE_URL         → postgresql+asyncpg://postgres:password@localhost:5432/auth_test
REDIS_HOST           → localhost
REDIS_PORT           → 6379
```

---

## 🛡️ Security Design

### Why Two Tokens?

| Token | Lifetime | Purpose |
|---|---|---|
| Access Token | 15 minutes | Sent with every API request. Short-lived to limit damage if stolen. |
| Refresh Token | 7 days | Only used to get a new access token. Never sent to data endpoints. |

Both tokens carry a `type` claim (`access` or `refresh`) so they cannot be used interchangeably — a refresh token cannot be used to access `/users/me`.

### Why Redis for Logout?

JWTs are stateless by design — once issued, they are valid until they expire. Without a blacklist, there is no way to invalidate a token on logout. By storing a "dead" token's identifier in Redis with a TTL equal to the token's remaining lifetime, the system achieves **real-time revocation** without any permanent storage overhead.

### Password Security

- Passwords are hashed using **Bcrypt** via Passlib
- Bcrypt automatically generates a unique salt per password, preventing rainbow table attacks
- Raw passwords are never stored or logged anywhere in the system

### CORS & Rate Limiting

- CORS is restricted to explicitly listed origins via `CORS_ORIGINS` in `.env`
- SlowAPI rate limiting protects authentication endpoints from brute-force attempts

---

## 👨‍💻 Contributors

| Name | Role |
|---|---|
| [Muhammad-Rafay5](https://github.com/Muhammad-Rafay5) | Lead Developer |

---

## 📄 License

This project is open source and available for educational purposes.

---

> Built with ❤️ using FastAPI, PostgreSQL, and Redis.
