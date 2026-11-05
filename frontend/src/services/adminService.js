import api from './api';

export const adminService = {
  getOverview: async () => {
    const res = await api.get('/api/admin/overview');
    return res.data;
  },

  getUsers: async (role = 'all', search = '') => {
    const params = {};
    if (role && role !== 'all') params.role = role;
    if (search) params.search = search;
    const res = await api.get('/api/admin/users', { params });
    return res.data;
  },

  createUser: async (userData) => {
    const res = await api.post('/api/admin/users', userData);
    return res.data;
  },

  updateUser: async (userId, userData) => {
    const res = await api.put(`/api/admin/users/${userId}`, userData);
    return res.data;
  },

  deleteUser: async (userId) => {
    const res = await api.delete(`/api/admin/users/${userId}`);
    return res.data;
  },

  bulkImportUsers: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await api.post('/api/admin/users/bulk_import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },

  bulkImportStudents: async (file) => {
    return adminService.bulkImportUsers(file);
  },

  getDepartments: async () => {
    const res = await api.get('/api/admin/departments');
    return res.data;
  },

  createDepartment: async (data) => {
    const res = await api.post('/api/admin/departments', data);
    return res.data;
  },

  updateDepartment: async (id, data) => {
    const res = await api.put(`/api/admin/departments/${id}`, data);
    return res.data;
  },

  deleteDepartment: async (id) => {
    const res = await api.delete(`/api/admin/departments/${id}`);
    return res.data;
  },

  getSubjects: async () => {
    const res = await api.get('/api/admin/subjects');
    return res.data;
  },

  createSubject: async (data) => {
    const res = await api.post('/api/admin/subjects', data);
    return res.data;
  },

  updateSubject: async (id, data) => {
    const res = await api.put(`/api/admin/subjects/${id}`, data);
    return res.data;
  },

  deleteSubject: async (id) => {
    const res = await api.delete(`/api/admin/subjects/${id}`);
    return res.data;
  },

  getAcademicStructure: async () => {
    const res = await api.get('/api/admin/academic_structure');
    return res.data;
  },

  getLaboratories: async () => {
    const res = await api.get('/api/admin/laboratories');
    return res.data;
  },

  createLaboratory: async (data) => {
    const res = await api.post('/api/admin/laboratories', data);
    return res.data;
  },

  updateLaboratory: async (id, data) => {
    const res = await api.put(`/api/admin/laboratories/${id}`, data);
    return res.data;
  },

  deleteLaboratory: async (id) => {
    const res = await api.delete(`/api/admin/laboratories/${id}`);
    return res.data;
  },
};

export default adminService;
