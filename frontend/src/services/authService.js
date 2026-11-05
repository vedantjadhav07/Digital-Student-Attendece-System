import api from './api';

export const authService = {
  login: async (username, password, remember = false) => {
    const res = await api.post('/api/auth/login', { username, password, remember });
    return res.data;
  },

  logout: async () => {
    const res = await api.post('/api/auth/logout');
    return res.data;
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

