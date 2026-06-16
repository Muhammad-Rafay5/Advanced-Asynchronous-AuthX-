// Global Auth State
let currentUser = null;
let countdownInterval;
let isLoadingSessions = false;

// DOM Elements - Lazy initialized
const getElements = () => ({
    sections: {
        login: document.getElementById('login-section'),
        register: document.getElementById('register-section'),
        dashboard: document.getElementById('dashboard-section'),
        'forgot-password': document.getElementById('forgot-password-section'),
        'reset-password': document.getElementById('reset-password-section')
    },
    sidebar: document.getElementById('sidebar'),
    mainContent: document.getElementById('main-content'),
    countdown: document.getElementById('session-countdown'),
    tableBody: document.getElementById('user-table-body'),
    countBadge: document.getElementById('user-count')
});

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

// Sanitize user content to prevent XSS
function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

// Navigation Logic
function showSection(name, skipDataLoad = false) {
    const el = getElements();
    if (!el.sections[name]) return;

    // Only hide others if not already active to prevent flickering/recursion
    if (!el.sections[name].classList.contains('active')) {
        Object.values(el.sections).forEach(s => {
            if (s) {
                s.classList.add('hidden');
                s.classList.remove('active');
            }
        });
        el.sections[name].classList.remove('hidden');
        el.sections[name].classList.add('active');
    }
    
    const isAuth = name === 'login' || name === 'register' || name === 'forgot-password' || name === 'reset-password';
    if (isAuth) {
        if (el.sidebar) el.sidebar.classList.add('hidden');
        if (el.mainContent) el.mainContent.style.marginLeft = '0';
    } else {
        if (el.sidebar) el.sidebar.classList.remove('hidden');
        if (el.mainContent) el.mainContent.style.marginLeft = '';
        
        // Load data ONLY if explicitly requested or on first show
        if (name === 'dashboard' && !skipDataLoad) loadDashboard();
    }
}

// UI Feedback
function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    if (!container) return;
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
const loginForm = document.getElementById('login-form');
if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-password').value;

        try {
            await authService.login(email, password);
            showToast('Access Authorized');
            await loadDashboard();
        } catch (err) {
            showToast(err.message, 'error');
        }
    });
}

const registerForm = document.getElementById('register-form');
if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const name = document.getElementById('reg-name').value;
        const company = document.getElementById('reg-company').value;
        const email = document.getElementById('reg-email').value;
        const password = document.getElementById('reg-password').value;
        const confirm = document.getElementById('reg-confirm').value;
        const terms = document.getElementById('reg-terms').checked;

        if (password !== confirm) {
            showToast('Passwords do not match', 'error');
            return;
        }
        if (!terms) {
            showToast('Please accept the terms', 'error');
            return;
        }

        try {
            await authService.register(name, company, email, password, confirm, terms);
            showToast('Workspace created successfully!');
            showSection('login');
        } catch (err) {
            showToast(err.message, 'error');
        }
    });
}

const forgotForm = document.getElementById('forgot-form');
if (forgotForm) {
    forgotForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('forgot-email').value;
        try {
            const result = await authService.forgotPassword(email);
            showToast(result.message);
            showSection('reset-password');
        } catch (err) {
            showToast(err.message, 'error');
        }
    });
}

const resetForm = document.getElementById('reset-form');
if (resetForm) {
    resetForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const token = document.getElementById('reset-token').value;
        const newPassword = document.getElementById('reset-password-input').value;
        const confirmNew = document.getElementById('reset-confirm').value;

        if (newPassword !== confirmNew) {
            showToast('Passwords do not match', 'error');
            return;
        }

        try {
            const result = await authService.resetPassword(token, newPassword, confirmNew);
            showToast(result.message);
            showSection('login');
        } catch (err) {
            showToast(err.message, 'error');
        }
    });
}

// Global UI Handlers
window.togglePasswordVisibility = function(inputId, iconElement) {
    const input = document.getElementById(inputId);
    if (input.type === 'password') {
        input.type = 'text';
        iconElement.style.color = '#f59e0b';
    } else {
        input.type = 'password';
        iconElement.style.color = '#9ca3af';
    }
};

window.checkPasswordStrength = function() {
    const password = document.getElementById('reg-password').value;
    const text = document.getElementById('strength-text');
    
    let strength = 0;
    if (password.length >= 8) strength += 25;
    if (/[A-Z]/.test(password)) strength += 25;
    if (/[0-9]/.test(password)) strength += 25;
    if (/[^A-Za-z0-9]/.test(password)) strength += 25;

    if (password.length === 0) {
        text.textContent = 'Too short';
        text.style.color = '#a1a1aa';
    } else if (strength <= 25) {
        text.textContent = 'Weak';
        text.style.color = '#ef4444';
    } else if (strength <= 50) {
        text.textContent = 'Fair';
        text.style.color = '#f59e0b';
    } else if (strength <= 75) {
        text.textContent = 'Good';
        text.style.color = '#10b981';
    } else {
        text.textContent = 'Strong';
        text.style.color = '#059669';
    }
};

async function handleLogout() {
    try {
        await authService.logout();
        showToast('Identity de-authorized');
    } catch (err) {
        authService.clearTokens();
    }
    clearInterval(countdownInterval);
    currentUser = null;
    showSection('login');
}

async function handleRefresh() {
    try {
        await authService.refresh();
        showToast('Token Rotated');
        startCountdown();
        await loadSessions();
    } catch (err) {
        showToast('Re-authorization required', 'error');
        handleLogout();
    }
}

function startCountdown() {
    if (countdownInterval) clearInterval(countdownInterval);
    
    const token = authService.getAccessToken();
    const payload = parseJwt(token);
    if (!payload) return;

    const el = getElements();
    if (!el.countdown) return;
    
    countdownInterval = setInterval(() => {
        const now = Math.floor(Date.now() / 1000);
        const remaining = payload.exp - now;

        if (remaining <= 0) {
            clearInterval(countdownInterval);
            el.countdown.textContent = "Expired";
            el.countdown.classList.add('badge-expired');
            handleLogout();
            return;
        }

        const mins = Math.floor(remaining / 60).toString().padStart(2, '0');
        const secs = (remaining % 60).toString().padStart(2, '0');
        el.countdown.textContent = `${mins}:${secs} Remaining`;
        
        if (remaining < 60) {
            el.countdown.classList.add('pulse');
        } else {
            el.countdown.classList.remove('pulse');
        }
    }, 1000);
}

async function loadDashboard() {
    try {
        // Prevent recursive calls while loading
        if (currentUser) {
            showSection('dashboard', true); // Show without reloading everything
        } else {
            currentUser = await authService.getCurrentUser();
            startCountdown();
            showSection('dashboard', true); // Show the shell immediately
        }
        await loadSessions(); // This is the slow part, load it independently
    } catch (err) {
        console.error('Dashboard load failed:', err);
        showSection('login');
    }
}

async function loadSessions() {
    if (isLoadingSessions) return;
    isLoadingSessions = true;

    const el = getElements();
    if (!el.tableBody) {
        isLoadingSessions = false;
        return;
    }

    el.tableBody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 3rem;">Synchronizing with Identity Repository...</td></tr>';
    
    try {
        const users = await authService.getAllUsers();
        el.tableBody.innerHTML = '';
        if (el.countBadge) el.countBadge.textContent = `${users.length} Total Identities`;
        
        users.forEach((u, index) => {
            const row = document.createElement('tr');
            const isMe = currentUser && u.id === currentUser.id;
            
            const statusClass = u.is_active ? 'badge-active' : 'badge-neutral';
            const statusText = u.is_active ? 'Active' : 'Deactivated';
            const accessLevel = u.is_superuser ? 'Superuser' : 'Standard';
            const levelClass = u.is_superuser ? 'badge-superuser' : 'badge-standard';
            
            let sessionStatus = 'Offline';
            let sessionClass = 'badge-neutral';
            
            if (isMe) {
                const token = authService.getAccessToken();
                const payload = parseJwt(token);
                const now = Math.floor(Date.now() / 1000);
                if (payload && payload.exp > now) {
                    sessionStatus = 'Live';
                    sessionClass = 'badge-standard';
                } else {
                    sessionStatus = 'Expired';
                    sessionClass = 'badge-expired';
                }
            }

            let ttlDisplay = '—';
            if (isMe) {
                const token = authService.getAccessToken();
                const payload = parseJwt(token);
                if (payload && payload.iat && payload.exp) {
                    ttlDisplay = Math.ceil((payload.exp - payload.iat) / 60) + ' min';
                }
            }

            row.innerHTML = `
                <td style="color: var(--text-muted);">#${index + 1}</td>
                <td>
                    <div style="font-weight: 500;">${escapeHtml(u.email)} ${isMe ? '<span style="font-size:0.7rem; color:var(--primary);">(You)</span>' : ''}</div>
                    <div style="font-size: 0.75rem; color: var(--text-muted);">${escapeHtml(u.id.substring(0, 12))}...</div>
                </td>
                <td><span class="badge ${statusClass}">${statusText}</span></td>
                <td><span class="badge ${levelClass}">${accessLevel}</span></td>
                <td>${ttlDisplay}</td>
                <td><span class="badge ${sessionClass}" style="border: none;">${sessionStatus}</span></td>
            `;
            el.tableBody.appendChild(row);
        });
    } catch (err) {
        console.error('Session load failed:', err);
        el.tableBody.innerHTML = `<tr><td colspan="6" style="color: var(--accent-red); text-align: center;">Error: ${escapeHtml(err.message)}</td></tr>`;
    } finally {
        isLoadingSessions = false;
    }
}

// Global Auth Failure Listener
window.addEventListener('auth-failed', () => {
    showToast('Identity token expired', 'error');
    handleLogout();
});

window.addEventListener('tokens-refreshed', startCountdown);

// Initial Load
window.addEventListener('DOMContentLoaded', () => {
    // Access token is in-memory only — always cleared on page reload.
    // Users must log in again after a page refresh.
    showSection('login');

    // Initial Load - no longer checking old password strength element here since we do it inline
});
