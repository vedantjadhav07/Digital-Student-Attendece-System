import api from './api';

export const teacherService = {
  getOverview: async () => {
    const res = await api.get('/api/teacher/overview');
    return res.data;
  },

  getSubjects: async () => {
    const res = await api.get('/api/teacher/subjects');
    return res.data;
  },

  getLaboratories: async () => {
    const res = await api.get('/api/teacher/laboratories');
    return res.data;
  },

  addSubject: async (data) => {
    const payload = typeof data === 'object' ? data : { subject_id: data };
    const res = await api.post('/api/teacher/add_subject', payload);
    return res.data;
  },

  startSession: async (sessionData) => {
    const res = await api.post('/api/teacher/start_session', sessionData);
    return res.data;
  },

  pauseSession: async (sessionId) => {
    const res = await api.post(`/api/teacher/pause_session/${sessionId}`);
    return res.data;
  },

  extendSession: async (sessionId, minutes = 10) => {
    const res = await api.post(`/api/teacher/extend_session/${sessionId}`, { minutes });
    return res.data;
  },

  stopSession: async (sessionId) => {
    const res = await api.post(`/api/teacher/stop_session/${sessionId}`);
    return res.data;
  },

  getSessionLive: async (sessionId) => {
    const res = await api.get(`/api/teacher/session/${sessionId}/live`);
    return res.data;
  },

  getStudentAnalysis: async (subjectId = null) => {
    const params = subjectId ? { subject_id: subjectId } : {};
    const res = await api.get('/api/teacher/student_analysis', { params });
    return res.data;
  },
};

export default teacherService;
