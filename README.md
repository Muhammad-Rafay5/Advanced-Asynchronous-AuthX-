# 🚀 Advanced Asynchronous Auth System

Welcome to the **AuthX** – a high-performance, enterprise-grade authentication system built with **FastAPI** and **Vanilla JavaScript**. This project demonstrates a secure, "Zero-Trust" architecture featuring asynchronous database operations, dual-token security (JWT), and real-time session revocation using Redis.

---

## 🌟 Overview

This system is designed for developers who want to understand how a modern, production-ready authentication backend works. It moves away from traditional "stateful" cookies and embraces a modern "stateless" but "revocable" JWT approach.

### **Key Highlights:**
- **Fully Asynchronous**: Every database query is non-blocking for maximum speed.
- **Dual-Token System**: Uses a short-lived `Access Token` for security and a long-lived `Refresh Token` for convenience.
- **Session Revocation**: Real-time "Logout" capability using a Redis-backed blacklist.
- **Premium Frontend**: A stunning, glassmorphic UI built with pure HTML, CSS, and JS.

---

## 🛠️ Tech Stack

### **Backend (Python)**
- **FastAPI**: Modern, high-performance web framework.
- **SQLAlchemy (Async)**: Advanced SQL Toolkit with non-blocking DB drivers.
- **PostgreSQL / SQLite**: Flexible database support.
- **Redis**: Ultra-fast in-memory store for session management.
- **Passlib (Bcrypt)**: Industry-standard password hashing.

### **Frontend (Vanilla)**
- **HTML5 & CSS3**: Modern layouts using Flexbox, Grid, and Glassmorphism.
- **JavaScript (ES6+)**: Dynamic UI updates and secure token management.
- **Google Fonts**: "Outfit" typography for a premium feel.

---

## 📂 Project Structure

```text
├── app/
│   ├── core/           # Security & Configuration
│   ├── db/             # Models & Database Setup
│   ├── dependencies/   # Auth & DB dependencies
│   ├── redis/          # Token Blacklisting logic
│   ├── routes/         # API Endpoints (Auth, Users)
│   ├── schemas/        # Pydantic Data Validation
│   └── services/       # Business Logic
├── frontend/           # The Web UI
├── alembic/            # Database Migrations
├── .env                # Sensitive Credentials (Ignored by Git)
├── .env.example        # Template for Credentials
└── requirements.txt    # Project Dependencies
```

---

## 🚀 Installation & Setup

### **1. Prerequisites**
- Python 3.9+
- Redis (Optional but recommended for Logout feature)
- PostgreSQL (Optional, defaults to SQLite)

### **2. Clone & Setup Environment**
```bash
# Create a virtual environment
python -m venv venv

# Activate it (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### **3. Configuration**
Copy the `.env.example` file to `.env` and fill in your details:
```bash
cp .env.example .env
```

---

## 🏃 Running the Project

### **Step 1: Start the Backend**
```bash
uvicorn app.main:app --reload
```
The API will be available at: `http://127.0.0.1:8000`
Documentation: `http://127.0.0.1:8000/docs`

### **Step 2: Start the Frontend**
You can use any simple server to host the `frontend` folder:
```bash
python -m http.server 3000 --directory frontend
```
The UI will be available at: `http://127.0.0.1:3000`

---

## 🔐 Core Workflows

### **1. Registration**
User sends `email` and `password`. The password is hashed using **Bcrypt** before being stored.

### **2. Login & Tokens**
Upon login, the system issues two tokens:
- **Access Token (15 mins)**: Used for every API call.
- **Refresh Token (7 days)**: Used only to get a new Access Token.

### **3. The "Silent" Refresh**
The frontend includes logic in `auth.js` that watches for a `401 Unauthorized` error. If your access token expires, it automatically uses the Refresh Token to get a new one without interrupting your experience.

### **4. Secure Logout**
When you log out, your current token is sent to **Redis**. The system will reject any further requests using that token, even if it hasn't technically expired yet.

---

## 🛡️ Security Features
- **Password Salting**: Prevents rainbow table attacks.
- **CORS Configuration**: Restricts which domains can talk to your API.
- **Zero-Trust**: No data is shown on the dashboard until the backend confirms the token is valid AND not blacklisted.

---

## 👨‍💻 Contributing
This project is open for educational purposes! Feel free to fork it, add new features (like Email Verification or Role-Based Access Control), and experiment.

**Built with ❤️ for the Developer Community.**
