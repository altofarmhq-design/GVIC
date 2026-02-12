import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const api = {
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
  generateReport: (options = {}) => axios.post(`${API}/report/generate`, options, { responseType: 'blob' })
};

export default api;
