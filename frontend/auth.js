const API_URL = 'http://127.0.0.1:8000';

const authService = {
    saveTokens(access, refresh) {
        localStorage.setItem('access_token', access);
        localStorage.setItem('refresh_token', refresh);
    },

    getAccessToken() {
        return localStorage.getItem('access_token');
    },

    getRefreshToken() {
        return localStorage.getItem('refresh_token');
    },

    clearTokens() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
    },

    async register(email, password) {
        const response = await fetch(`${API_URL}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Registration failed');
        }
        return response.json();
    },

    async login(email, password) {
        // FastAPI OAuth2PasswordRequestForm expects form data
        const formData = new URLSearchParams();
        formData.append('username', email);
        formData.append('password', password);

        const response = await fetch(`${API_URL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Login failed');
        }

        const data = await response.json();
        this.saveTokens(data.access_token, data.refresh_token);
        return data;
    },

    async refresh() {
        const refreshToken = this.getRefreshToken();
        if (!refreshToken) throw new Error('No refresh token available');

        const response = await fetch(`${API_URL}/auth/refresh`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: refreshToken })
        });

        if (!response.ok) {
            this.clearTokens();
            throw new Error('Session expired');
        }

        const data = await response.json();
        this.saveTokens(data.access_token, data.refresh_token);
        return data.access_token;
    },

    async fetchWithAuth(url, options = {}) {
        let token = this.getAccessToken();
        
        const headers = {
            ...options.headers,
            'Authorization': `Bearer ${token}`
        };

        let response = await fetch(`${API_URL}${url}`, { ...options, headers });

        if (response.status === 401) {
            try {
                const newToken = await this.refresh();
                headers['Authorization'] = `Bearer ${newToken}`;
                response = await fetch(`${API_URL}${url}`, { ...options, headers });
            } catch (e) {
                window.dispatchEvent(new CustomEvent('auth-failed'));
                throw e;
            }
        }

        return response;
    },

    async getCurrentUser() {
        const response = await this.fetchWithAuth('/users/me');
        if (!response.ok) throw new Error('Failed to fetch user');
        return response.json();
    },

    async logout() {
        const token = this.getAccessToken();
        try {
            await fetch(`${API_URL}/auth/logout`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` }
            });
        } finally {
            this.clearTokens();
        }
    },

    async getAllUsers() {
        const response = await this.fetchWithAuth('/users/');
        if (!response.ok) throw new Error('Failed to fetch users');
        return response.json();
    }
};
