import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Configure axios defaults
axios.defaults.withCredentials = true;

// Add token to requests
axios.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const api = {
  // Auth APIs
  register: (email, password, passwordConfirm, name) => axios.post(`${API}/auth/register`, { email, password, password_confirm: passwordConfirm, name }),
  login: (email, password) => axios.post(`${API}/auth/login`, { email, password }),
  googleSession: (sessionId) => axios.post(`${API}/auth/google/session`, { session_id: sessionId }),
  getMe: () => axios.get(`${API}/auth/me`),
  logout: () => axios.post(`${API}/auth/logout`),
  changePassword: (currentPassword, newPassword) => axios.put(`${API}/auth/password`, { current_password: currentPassword, new_password: newPassword }),
  getRoles: () => axios.get(`${API}/auth/roles`),
  // User Management (Admin)
  getUsers: () => axios.get(`${API}/auth/users`),
  getUser: (userId) => axios.get(`${API}/auth/users/${userId}`),
  updateUser: (userId, data) => axios.put(`${API}/auth/users/${userId}`, data),
  deleteUser: (userId) => axios.delete(`${API}/auth/users/${userId}`),
  getPendingUsers: () => axios.get(`${API}/auth/pending`),
  approveUser: (userId) => axios.post(`${API}/auth/users/${userId}/approve`),
  rejectUser: (userId) => axios.post(`${API}/auth/users/${userId}/reject`),
  // Dashboard APIs
  getDashboard: () => axios.get(`${API}/dashboard`),
  process: (value) => axios.post(`${API}/process`, { value }),
  getProcessHistory: (limit = 20) => axios.get(`${API}/process/history?limit=${limit}`),
  getSigma: () => axios.get(`${API}/config/sigma`),
  updateSigma: (sigma) => axios.put(`${API}/config/sigma`, { sigma }),
  getOmega: () => axios.get(`${API}/config/omega`),
  updateOmega: (omega) => axios.put(`${API}/config/omega`, omega),
  processIO: (data, format) => axios.post(`${API}/io/process`, { data, format }),
  getLogs: (count = 10) => axios.get(`${API}/logs?count=${count}`),
  clearLogs: () => axios.delete(`${API}/logs`),
  getAlerts: () => axios.get(`${API}/alerts`),
  runHealthCheck: () => axios.post(`${API}/health-check`),
  resolveAlert: (alertId) => axios.post(`${API}/alerts/resolve`, { alert_id: alertId }),
  getModules: () => axios.get(`${API}/modules`),
  getStatus: () => axios.get(`${API}/status`),
  // Integration APIs
  getIntegrationStatus: () => axios.get(`${API}/integration/status`),
  executeExchange: (data, source_domain, message_type) => 
    axios.post(`${API}/integration/exchange`, { data, source_domain, message_type }),
  getAdapters: () => axios.get(`${API}/integration/adapters`),
  getMappings: () => axios.get(`${API}/integration/mappings`),
  getRoutingRules: () => axios.get(`${API}/integration/routing`),
  // Report APIs
  getReportSummary: () => axios.get(`${API}/report/summary`),
  generateReport: (options = {}) => axios.post(`${API}/report/generate`, options, { responseType: 'blob' }),
  // Monitoring APIs
  getRealtimeMonitoring: () => axios.get(`${API}/monitor/realtime`),
  getDistributionMonitor: () => axios.get(`${API}/monitor/distribution`),
  // Dynamic Adjustment APIs
  getAdjustmentConfig: () => axios.get(`${API}/adjustment/config`),
  updateAdjustmentConfig: (config) => axios.put(`${API}/adjustment/config`, config),
  executeAdjustment: () => axios.post(`${API}/adjustment/execute`),
  getAdjustmentHistory: (limit = 20) => axios.get(`${API}/adjustment/history?limit=${limit}`),
  // Multi-Model APIs
  getAllModels: () => axios.get(`${API}/models`),
  getModel: (modelId) => axios.get(`${API}/models/${modelId}`),
  createModel: (model) => axios.post(`${API}/models`, model),
  activateModel: (modelId) => axios.post(`${API}/models/${modelId}/activate`),
  deleteModel: (modelId) => axios.delete(`${API}/models/${modelId}`),
  // Prediction APIs
  getPredictionConfig: () => axios.get(`${API}/prediction/config`),
  updatePredictionConfig: (config) => axios.put(`${API}/prediction/config`, config),
  analyzePrediction: () => axios.post(`${API}/prediction/analyze`),
  applyPrediction: () => axios.post(`${API}/prediction/apply`),
  getPredictionHistory: (limit = 10) => axios.get(`${API}/prediction/history?limit=${limit}`),
  // Pareto APIs
  getParetoConfig: () => axios.get(`${API}/pareto/config`),
  updateParetoConfig: (config) => axios.put(`${API}/pareto/config`, config),
  runParetoOptimization: () => axios.post(`${API}/pareto/optimize`),
  applyParetoSolution: (index) => axios.post(`${API}/pareto/apply/${index}`),
  // Comparison APIs
  analyzeComparison: (options = {}) => axios.post(`${API}/comparison/analyze`, options),
  getComparisonRecords: (limit = 20) => axios.get(`${API}/comparison/records?limit=${limit}`),
  // Data Sources APIs
  getDataSources: () => axios.get(`${API}/datasources`),
  createDataSource: (config) => axios.post(`${API}/datasources`, config),
  getDataSource: (sourceId) => axios.get(`${API}/datasources/${sourceId}`),
  updateDataSource: (sourceId, config) => axios.put(`${API}/datasources/${sourceId}`, config),
  deleteDataSource: (sourceId) => axios.delete(`${API}/datasources/${sourceId}`),
  fetchDataSource: (sourceId) => axios.post(`${API}/datasources/${sourceId}/fetch`),
  processDataSource: (sourceId) => axios.post(`${API}/datasources/${sourceId}/process`),
  getCollectedData: (limit = 50) => axios.get(`${API}/datasources/collected?limit=${limit}`),
  startDataSource: (sourceId) => axios.post(`${API}/datasources/${sourceId}/start`),
  stopDataSource: (sourceId) => axios.post(`${API}/datasources/${sourceId}/stop`)
};

export default api;
