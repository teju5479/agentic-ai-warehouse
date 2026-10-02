import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 120000, // 2 min for LLM calls
});

export const dashboardApi = {
  get: () => api.get('/dashboard'),
};

export const ordersApi = {
  list: () => api.get('/orders'),
  get: (id) => api.get(`/orders/${id}`),
};

export const inventoryApi = {
  list: () => api.get('/inventory'),
};

export const shipmentsApi = {
  list: () => api.get('/shipments'),
};

export const pickersApi = {
  list: () => api.get('/pickers'),
  get: (id) => api.get(`/pickers/${id}`),
  update: (id, data) => api.patch(`/pickers/${id}`, data),
};

export const exceptionsApi = {
  list: (status) => api.get('/exceptions', { params: status ? { status } : {} }),
  get: (id) => api.get(`/exceptions/${id}`),
  resolve: (id) => api.post(`/exceptions/${id}/resolve`),
  approve: (id) => api.post(`/exceptions/${id}/approve`),
  reject: (id) => api.post(`/exceptions/${id}/reject`),
};

export const plannerApi = {
  run: () => api.post('/planner/run'),
  listPlans: () => api.get('/planner/plans'),
  getPlan: (id) => api.get(`/planner/plans/${id}`),
  replan: (data) => api.post('/planner/replan', data),
};

export const auditApi = {
  list: (params) => api.get('/audit', { params }),
};

export const policiesApi = {
  list: () => api.get('/policies'),
};

export const scenariosApi = {
  list: () => api.get('/scenarios'),
  reset: () => api.post('/scenarios/reset'),
  run: (id) => api.post(`/scenarios/${id}/run`),
};

export default api;
