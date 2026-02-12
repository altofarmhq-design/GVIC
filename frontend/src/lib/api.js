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
