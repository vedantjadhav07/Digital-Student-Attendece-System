import api from './api';

export const authService = {
  login: async (username, password, remember = true) => {
    const res = await api.post('/api/auth/login', { username, password, remember });
    if (res.data?.access_token) {
      localStorage.setItem('lab_access_token', res.data.access_token);
    }
    if (res.data?.refresh_token) {
      localStorage.setItem('lab_refresh_token', res.data.refresh_token);
    }
    if (res.data?.user) {
      localStorage.setItem('lab_user', JSON.stringify(res.data.user));
    }
    return res.data;
  },

  logout: async () => {
    try {
      const res = await api.post('/api/auth/logout');
      return res.data;
    } finally {
      localStorage.removeItem('lab_access_token');
      localStorage.removeItem('lab_refresh_token');
      localStorage.removeItem('lab_user');
    }
  },

  refreshToken: async () => {
    const refreshToken = localStorage.getItem('lab_refresh_token');
    if (!refreshToken) throw new Error('No refresh token available');
    const res = await api.post('/api/auth/refresh', { refresh_token: refreshToken });
    if (res.data?.access_token) {
      localStorage.setItem('lab_access_token', res.data.access_token);
    }
    if (res.data?.refresh_token) {
      localStorage.setItem('lab_refresh_token', res.data.refresh_token);
    }
    if (res.data?.user) {
      localStorage.setItem('lab_user', JSON.stringify(res.data.user));
    }
    return res.data;
  },

  getStoredUser: () => {
    try {
      const u = localStorage.getItem('lab_user');
      return u ? JSON.parse(u) : null;
    } catch {
      return null;
    }
  },

  getMe: async () => {
    const res = await api.get('/api/auth/me');
    return res.data;
  },

  changePassword: async (newPassword, confirmPassword) => {
    const res = await api.post('/api/auth/change_password', {
      new_password: newPassword,
      confirm_password: confirmPassword,
    });
    return res.data;
  },
};

