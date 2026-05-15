// DOM Elements
const sections = {
    login: document.getElementById('login-section'),
    register: document.getElementById('register-section'),
    dashboard: document.getElementById('dashboard-section'),
    sessions: document.getElementById('sessions-section')
};

const navLinks = document.getElementById('nav-links');
let countdownInterval;

// Helper: Decode JWT
function parseJwt(token) {
    try {
        const base64Url = token.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        return JSON.parse(window.atob(base64));
    } catch (e) {
        return null;
    }
}

// Navigation Logic
function showSection(name) {
    Object.values(sections).forEach(s => {
        if (s) s.classList.remove('active');
    });
    
    if (sections[name]) {
        sections[name].classList.add('active');
        updateNav(name);
        
        if (name === 'sessions') loadSessions();
    }
}

function updateNav(currentSection) {
    const isLoggedIn = !!authService.getAccessToken();
    if (isLoggedIn) {
        navLinks.innerHTML = `
            <button class="nav-btn" onclick="showSection('dashboard')">Profile</button>
            <button class="nav-btn" onclick="showSection('sessions')">Users List</button>
            <button class="btn-primary" onclick="handleLogout()">Logout</button>
        `;
    } else {
        navLinks.innerHTML = `
            <button class="nav-btn" onclick="showSection('login')">Login</button>
            <button class="btn-primary" onclick="showSection('register')">Get Started</button>
        `;
    }
}

// UI Feedback
function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span>${type === 'success' ? '✓' : '✕'}</span> ${message}`;
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// Auth Handlers
document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;

    try {
        await authService.login(email, password);
        showToast('Successfully logged in!');
        loadDashboard();
    } catch (err) {
        showToast(err.message, 'error');
    }
});

document.getElementById('register-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('reg-email').value;
    const password = document.getElementById('reg-password').value;

    try {
        await authService.register(email, password);
        showToast('Account created! You can now login.');
        showSection('login');
    } catch (err) {
        showToast(err.message, 'error');
    }
});

async function handleLogout() {
    try {
        await authService.logout();
        showToast('Logged out successfully');
    } catch (err) {
        authService.clearTokens();
    }
    clearInterval(countdownInterval);
    showSection('login');
}

async function handleRefresh() {
    try {
        await authService.refresh();
        showToast('Session extended!');
        startCountdown();
        if (sections.sessions.classList.contains('active')) loadSessions();
    } catch (err) {
        showToast('Refresh failed. Session expired.', 'error');
        handleLogout();
    }
}

function startCountdown() {
    if (countdownInterval) clearInterval(countdownInterval);
    
    const token = authService.getAccessToken();
    const payload = parseJwt(token);
    if (!payload) return;

    const expiryElement = document.getElementById('session-countdown');
    
    countdownInterval = setInterval(() => {
        const now = Math.floor(Date.now() / 1000);
        const remaining = payload.exp - now;

        if (remaining <= 0) {
            clearInterval(countdownInterval);
            expiryElement.textContent = "00:00";
            handleLogout();
            return;
        }

        const mins = Math.floor(remaining / 60).toString().padStart(2, '0');
        const secs = (remaining % 60).toString().padStart(2, '0');
        expiryElement.textContent = `${mins}:${secs}`;
        
        // Visual warning
        if (remaining < 60) {
            expiryElement.style.color = '#ff4b4b';
            expiryElement.classList.add('pulse');
        } else {
            expiryElement.style.color = 'var(--primary)';
            expiryElement.classList.remove('pulse');
        }
    }, 1000);
}

async function loadDashboard() {
    try {
        const user = await authService.getCurrentUser();
        document.getElementById('user-greeting').textContent = `Hello, ${user.email.split('@')[0]}`;
        document.getElementById('display-email').textContent = user.email;
        document.getElementById('display-id').textContent = user.id;
        document.getElementById('user-initials').textContent = user.email[0].toUpperCase();
        
        const date = new Date(user.created_at);
        document.getElementById('display-last-login').textContent = date.toLocaleString();
        
        startCountdown();
        showSection('dashboard');
    } catch (err) {
        showSection('login');
    }
}

async function loadSessions() {
    const tableBody = document.getElementById('user-table-body');
    tableBody.innerHTML = '<tr><td colspan="4" class="loading">Loading user sessions...</td></tr>';
    
    try {
        const users = await authService.getAllUsers();
        tableBody.innerHTML = '';
        
        users.forEach(u => {
            const row = document.createElement('tr');
            const statusClass = u.is_active ? 'badge-success' : 'badge-neutral';
            
            row.innerHTML = `
                <td>
                    <div class="user-row">
                        <div class="user-row-avatar">${u.email[0].toUpperCase()}</div>
                        <div class="user-row-info">
                            <div class="user-row-email">${u.email}</div>
                            <div class="user-row-id">${u.id.substring(0, 8)}...</div>
                        </div>
                    </div>
                </td>
                <td>${new Date(u.created_at).toLocaleDateString()}</td>
                <td>${u.is_active ? 'Active' : 'Offline'}</td>
                <td><span class="status-badge ${statusClass}">● ${u.is_active ? 'Online' : 'Offline'}</span></td>
            `;
            tableBody.appendChild(row);
        });
    } catch (err) {
        tableBody.innerHTML = `<tr><td colspan="4" class="error-cell">Error: ${err.message}</td></tr>`;
    }
}

// Global Auth Failure Listener
window.addEventListener('auth-failed', () => {
    showToast('Session expired. Please login again.', 'error');
    handleLogout();
});

// Initial Load
window.addEventListener('DOMContentLoaded', () => {
    if (authService.getAccessToken()) {
        loadDashboard();
    } else {
        showSection('login');
    }
});
