/* ============================================
   RAKSHANA 24/7 — API Service Layer
   ============================================ */

const API_BASE = (window.RAKSHANA_API_BASE || (
  window.location.protocol === 'file:' ||
  (window.location.hostname === 'localhost' && window.location.port === '80')
    ? 'http://localhost:5000/api'
    : `${window.location.origin}/api`
)).replace(/\/+$/, '');

const RakshanaAPI = {
  token: localStorage.getItem('rakshana_token') || null,
  refreshToken: localStorage.getItem('rakshana_refresh') || null,
  user: (() => {
    try {
      return JSON.parse(localStorage.getItem('rakshana_user') || 'null');
    } catch (error) {
      console.error('Stored user data is invalid; clearing saved authentication.', error);
      localStorage.removeItem('rakshana_user');
      return null;
    }
  })(),

  headers(body) {
    const headers = {};
    if (!(body instanceof FormData)) headers['Content-Type'] = 'application/json';
    if (this.token) headers.Authorization = `Bearer ${this.token}`;
    return headers;
  },

  saveAuth(data) {
    this.token = data.access_token;
    this.refreshToken = data.refresh_token;
    this.user = data.user;
    localStorage.setItem('rakshana_token', data.access_token);
    localStorage.setItem('rakshana_refresh', data.refresh_token);
    localStorage.setItem('rakshana_user', JSON.stringify(data.user));
  },

  clearAuth() {
    this.token = null;
    this.refreshToken = null;
    this.user = null;
    localStorage.removeItem('rakshana_token');
    localStorage.removeItem('rakshana_refresh');
    localStorage.removeItem('rakshana_user');
  },

  isLoggedIn() {
    return Boolean(this.token);
  },

  async request(endpoint, options = {}, retry = true) {
    const headers = { ...this.headers(options.body), ...options.headers };
    if (options.body instanceof FormData) delete headers['Content-Type'];

    let response;
    try {
      response = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });
    } catch (error) {
      if (error instanceof TypeError) {
        throw new Error(`Cannot connect to the API at ${API_BASE}.`);
      }
      throw error;
    }

    const contentType = response.headers.get('content-type') || '';
    const data = contentType.includes('application/json')
      ? await response.json()
      : await response.text();

    if (!response.ok) {
      if (response.status === 401 && retry && this.refreshToken &&
          await this.refreshAuth()) {
        return this.request(endpoint, options, false);
      }
      const message = data && typeof data === 'object' && data.error
        ? data.error
        : `API request failed (${response.status})`;
      throw new Error(message);
    }
    return data;
  },

  async login(email, password) {
    const data = await this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    this.saveAuth(data);
    return data;
  },

  async biometricLogin(biometricData) {
    const data = await this.request('/auth/biometric-login', {
      method: 'POST',
      body: JSON.stringify(biometricData),
    });
    this.saveAuth(data);
    return data;
  },

  async registerBiometrics(registrationData) {
    return this.request('/auth/register-biometrics', {
      method: 'POST',
      body: JSON.stringify(registrationData),
    });
  },

  async register(userData) {
    const isFormData = userData instanceof FormData;
    const data = await this.request('/auth/register', {
      method: 'POST',
      body: isFormData ? userData : JSON.stringify(userData),
    });
    this.saveAuth(data);
    return data;
  },

  async refreshAuth() {
    const refreshToken = this.refreshToken;
    if (!refreshToken) return false;
    try {
      const response = await fetch(`${API_BASE}/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${refreshToken}`,
        },
      });
      if (!response.ok) {
        this.clearAuth();
        return false;
      }
      const data = await response.json();
      this.token = data.access_token;
      this.refreshToken = data.refresh_token;
      localStorage.setItem('rakshana_token', data.access_token);
      localStorage.setItem('rakshana_refresh', data.refresh_token);
      return true;
    } catch (error) {
      this.clearAuth();
      return false;
    }
  },

  async getMe() { return this.request('/auth/me'); },
  async getDashboard() { return this.request('/dashboard/'); },
  async getTimeline(days = 7) { return this.request(`/dashboard/timeline?days=${days}`); },
  async getStats() { return this.request('/dashboard/stats'); },

  async getAlerts(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.request(`/alerts/${query ? `?${query}` : ''}`);
  },
  async getAlertsSummary() { return this.request('/alerts/summary'); },
  async markAlertRead(alertId) {
    return this.request(`/alerts/${encodeURIComponent(alertId)}/read`, { method: 'PUT' });
  },
  async takeAlertAction(alertId, action) {
    return this.request(`/alerts/${encodeURIComponent(alertId)}/action`, {
      method: 'PUT',
      body: JSON.stringify({ action }),
    });
  },

  async triggerScan() { return this.request('/scan/trigger', { method: 'POST' }); },
  async getScanStatus() { return this.request('/scan/status'); },
  async getScanHistory() { return this.request('/scan/history'); },
  async getDemoScan() { return this.request('/scan/demo'); },
  async analyzeContent(text) {
    return this.request('/scan/analyze', {
      method: 'POST',
      body: JSON.stringify({ text }),
    });
  },
  async analyzeFile(file, additionalText = '') {
    const formData = new FormData();
    formData.append('file', file);
    if (additionalText) formData.append('text', additionalText);
    return this.request('/scan/analyze', { method: 'POST', body: formData });
  },

  async submitReport(reportData) {
    return this.request('/reports/submit', {
      method: 'POST',
      body: JSON.stringify(reportData),
    });
  },
  async getReportStatus(token) {
    return this.request(`/reports/status/${encodeURIComponent(token)}`);
  },
  async getReportTypes() { return this.request('/reports/types'); },
  async getLaws(query = '') {
    const params = new URLSearchParams();
    if (query) params.set('q', query);
    const search = params.toString();
    return this.request(`/legal/laws${search ? `?${search}` : ''}`);
  },
  async getRights() { return this.request('/legal/rights'); },
  async getHelplines() { return this.request('/legal/helplines'); },
  async getStrings(lang = 'en') {
    return this.request(`/i18n/strings?lang=${encodeURIComponent(lang)}`);
  },
  async healthCheck() { return this.request('/health'); },
  async exportData() { return this.request('/users/export'); },
};
