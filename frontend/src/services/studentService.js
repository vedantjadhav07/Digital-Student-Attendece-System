import api from './api';

export const studentService = {
  getDashboard: async () => {
    const res = await api.get('/api/student/dashboard');
    return res.data;
  },

  markAttendance: async ({ session_id, workstation_number, workstation_id }) => {
    const res = await api.post('/attendance/submit', {
      session_id,
      workstation_number,
      workstation_id,
    });
    return res.data;
  },

  submitAttendance: async (sessionId, workstationToken = null) => {
    const payload = {};
    if (sessionId) payload.session_id = sessionId;
    if (workstationToken) payload.workstation_token = workstationToken;

    const res = await api.post('/attendance/submit', payload, {
      headers: workstationToken ? { 'X-Workstation-Token': workstationToken } : {},
    });
    return res.data;
  },

  downloadExcel: async () => {
    const res = await api.get('/student/export_personal', {
      responseType: 'blob',
    });
    return res;
  },
};

export default studentService;
