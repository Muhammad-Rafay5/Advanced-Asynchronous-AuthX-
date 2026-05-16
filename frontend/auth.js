const API_URL = 'http://127.0.0.1:8000';

let _accessToken = null;
let _refreshToken = null;

const authService = {
    saveTokens(access, refresh = null) {
        _accessToken = access;
        if (refresh !== null) _refreshToken = refresh;
    },

    getAccessToken() {
        return _accessToken;
    },

    getRefreshToken() {
        return _refreshToken;
    },

    clearTokens() {
        _accessToken = null;
        _refreshToken = null;
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
        const formData = new URLSearchParams();
        formData.append('username', email);
        formData.append('password', password);

        const response = await fetch(`${API_URL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: formData,
            credentials: 'include'
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
        
        window.dispatchEvent(new CustomEvent('tokens-refreshed'));
        
        return data.access_token;
    },

    async fetchWithAuth(url, options = {}) {
        let token = this.getAccessToken();
        
        const headers = {
            ...options.headers,
            'Authorization': `Bearer ${token}`
        };

        let response = await fetch(`${API_URL}${url}`, { ...options, headers, credentials: 'include' });

        if (response.status === 401) {
            try {
                const newToken = await this.refresh();
                headers['Authorization'] = `Bearer ${newToken}`;
                response = await fetch(`${API_URL}${url}`, { ...options, headers, credentials: 'include' });
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
        const refreshToken = this.getRefreshToken();
        try {
            await fetch(`${API_URL}/auth/logout`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ refresh_token: refreshToken })
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
