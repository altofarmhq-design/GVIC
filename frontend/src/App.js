import { useState, useEffect, useCallback } from "react";
import "@/App.css";
import axios from "axios";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Slider } from "@/components/ui/slider";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Progress } from "@/components/ui/progress";
import { ScrollArea } from "@/components/ui/scroll-area";
import { 
  PieChart, Pie, Cell, ResponsiveContainer, 
  BarChart, Bar, XAxis, YAxis, Tooltip as RechartsTooltip,
  RadialBarChart, RadialBar, Legend
} from 'recharts';
import { 
  LayoutDashboard, Play, Database, Bell, Settings, 
  Activity, CheckCircle, AlertTriangle, Zap, RefreshCw,
  FileText, Trash2, Heart, Network, ArrowRightLeft, 
  GitBranch, Link2, Send
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// ==================== API Functions ====================
const api = {
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
  // Integration APIs
  getIntegrationStatus: () => axios.get(`${API}/integration/status`),
  executeExchange: (data, source_domain, message_type) => 
    axios.post(`${API}/integration/exchange`, { data, source_domain, message_type }),
  getAdapters: () => axios.get(`${API}/integration/adapters`),
  getMappings: () => axios.get(`${API}/integration/mappings`),
  getRoutingRules: () => axios.get(`${API}/integration/routing`)
};

// ==================== Metric Card Component ====================
const MetricCard = ({ icon: Icon, label, value, variant = "cyan" }) => {
  const variants = {
    cyan: "from-teal-600 to-teal-500 border-teal-400",
    teal: "from-emerald-700 to-emerald-600 border-emerald-500",
    amber: "from-amber-700 to-amber-600 border-amber-500",
    purple: "from-violet-700 to-violet-600 border-violet-500"
  };

  return (
    <div className={`rounded-xl p-5 bg-gradient-to-br ${variants[variant]} border relative overflow-hidden`}>
      <div className="absolute top-0 right-0 w-20 h-20 bg-white/5 rounded-full -mr-10 -mt-10" />
      <Icon className="w-6 h-6 text-white/80 mb-2" />
      <p className="text-white/70 text-sm mb-1">{label}</p>
      <p className="text-white text-2xl font-bold">{value}</p>
    </div>
  );
};

// ==================== Dashboard Tab ====================
const DashboardTab = ({ dashboard, onRefresh }) => {
  const pieData = dashboard?.charts?.distribution?.data || [
    { name: '공공', value: 33, color: '#3b82f6' },
    { name: '생산', value: 34, color: '#10b981' },
    { name: '개인', value: 33, color: '#f59e0b' }
  ];

  const balanceScore = dashboard?.balance_score || 0.85;
  const gaugeData = [{ name: '균형', value: balanceScore * 100, fill: '#10b981' }];
  const sigma = dashboard?.sigma || [0.33, 0.34, 0.33];

  return (
    <div className="space-y-6">
      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4" data-testid="metrics-row">
        <MetricCard 
          icon={Activity} 
          label="처리 건수" 
          value={dashboard?.metrics?.total_processed || 0}
          variant="cyan"
        />
        <MetricCard 
          icon={CheckCircle} 
          label="성공률" 
          value={`${((dashboard?.metrics?.success_rate || 0) * 100).toFixed(1)}%`}
          variant="teal"
        />
        <MetricCard 
          icon={AlertTriangle} 
          label="활성 알림" 
          value={dashboard?.metrics?.active_alerts || 0}
          variant="amber"
        />
        <MetricCard 
          icon={Zap} 
          label="시스템" 
          value={dashboard?.metrics?.system_status || "active"}
          variant="purple"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Distribution Chart */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-slate-100 flex items-center gap-2">
              <Activity className="w-5 h-5" /> 분배 비율
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64" data-testid="distribution-chart">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={90}
                    paddingAngle={2}
                    dataKey="value"
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <RechartsTooltip 
                    contentStyle={{ background: '#1e293b', border: '1px solid #475569', borderRadius: '8px' }}
                    labelStyle={{ color: '#f1f5f9' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="flex justify-center gap-6 mt-4">
              {pieData.map((item, idx) => (
                <div key={idx} className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full" style={{ background: item.color }} />
                  <span className="text-slate-300 text-sm">{item.name}: {item.value.toFixed(1)}%</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Balance Gauge */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-slate-100 flex items-center gap-2">
              <CheckCircle className="w-5 h-5" /> 균형 상태
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64" data-testid="balance-gauge">
              <ResponsiveContainer width="100%" height="100%">
                <RadialBarChart 
                  cx="50%" 
                  cy="50%" 
                  innerRadius="60%" 
                  outerRadius="100%" 
                  data={gaugeData}
                  startAngle={180}
                  endAngle={0}
                >
                  <RadialBar
                    background={{ fill: '#334155' }}
                    dataKey="value"
                    cornerRadius={10}
                  />
                </RadialBarChart>
              </ResponsiveContainer>
              <div className="text-center -mt-20">
                <span className="text-4xl font-bold text-slate-100">{(balanceScore * 100).toFixed(1)}%</span>
              </div>
            </div>
            <div className="mt-8 space-y-2 px-4">
              <p className="text-slate-400 text-sm">
                Σ 기준: [{sigma[0]?.toFixed(2)}, {sigma[1]?.toFixed(2)}, {sigma[2]?.toFixed(2)}]
              </p>
              <p className="text-slate-400 text-sm">
                수렴 상태: <span className="text-emerald-400 font-medium">active</span>
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

// ==================== Processing Tab ====================
const ProcessingTab = ({ onProcess }) => {
  const [inputValue, setInputValue] = useState(0.75);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleProcess = async () => {
    setLoading(true);
    try {
      const response = await api.process(inputValue);
      setResult(response.data);
      if (onProcess) onProcess();
    } catch (error) {
      console.error("Process error:", error);
    }
    setLoading(false);
  };

  const distData = result?.data?.distribution ? [
    { name: '공공', value: result.data.distribution.public, fill: '#3b82f6' },
    { name: '생산', value: result.data.distribution.productive, fill: '#10b981' },
    { name: '개인', value: result.data.distribution.individual, fill: '#f59e0b' }
  ] : [];

  return (
    <Card className="bg-slate-800/50 border-slate-700">
      <CardHeader>
        <CardTitle className="text-slate-100 flex items-center gap-2">
          <Play className="w-5 h-5" /> GVIC 엔진 처리
        </CardTitle>
        <CardDescription className="text-slate-400">
          값을 입력하고 처리 실행을 클릭하세요
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Input Section */}
          <div className="space-y-6">
            <div>
              <label className="text-slate-300 text-sm mb-2 block">처리할 값</label>
              <Input
                type="number"
                min={0}
                max={10}
                step={0.05}
                value={inputValue}
                onChange={(e) => setInputValue(parseFloat(e.target.value) || 0)}
                className="bg-slate-900 border-slate-600 text-slate-100"
                data-testid="process-input"
              />
            </div>
            <Button 
              onClick={handleProcess} 
              disabled={loading}
              className="w-full bg-emerald-600 hover:bg-emerald-500"
              data-testid="process-button"
            >
              {loading ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <Play className="w-4 h-4 mr-2" />}
              처리 실행
            </Button>
          </div>

          {/* Result Section */}
          <div className="space-y-4">
            {result?.success ? (
              <>
                <div className="grid grid-cols-3 gap-3" data-testid="process-result">
                  <div className="bg-slate-900/50 rounded-lg p-3 text-center">
                    <p className="text-slate-400 text-xs">자산 가치</p>
                    <p className="text-slate-100 text-lg font-bold">
                      {result.data?.asset?.value?.toFixed(3) || 0}
                    </p>
                  </div>
                  <div className="bg-slate-900/50 rounded-lg p-3 text-center">
                    <p className="text-slate-400 text-xs">균형 점수</p>
                    <p className="text-slate-100 text-lg font-bold">
                      {((result.data?.balance_score || 0) * 100).toFixed(1)}%
                    </p>
                  </div>
                  <div className="bg-slate-900/50 rounded-lg p-3 text-center">
                    <p className="text-slate-400 text-xs">수렴 상태</p>
                    <p className="text-emerald-400 text-lg font-bold">
                      {result.data?.convergence?.is_valid ? "✓ 유효" : "⚠ 조정됨"}
                    </p>
                  </div>
                </div>

                {distData.length > 0 && (
                  <div className="h-48">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={distData}>
                        <XAxis dataKey="name" stroke="#94a3b8" />
                        <YAxis stroke="#94a3b8" />
                        <RechartsTooltip 
                          contentStyle={{ background: '#1e293b', border: '1px solid #475569', borderRadius: '8px' }}
                        />
                        <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                          {distData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.fill} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                )}
              </>
            ) : (
              <div className="flex items-center justify-center h-48 text-slate-500">
                <p>왼쪽에서 값을 입력하고 '처리 실행'을 클릭하세요</p>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

// ==================== Data Tab ====================
const DataTab = ({ logs, onLogsRefresh }) => {
  const [ioFormat, setIoFormat] = useState("json");
  const [ioData, setIoData] = useState('{"value": 0.75, "type": "market"}');
  const [ioResult, setIoResult] = useState(null);

  const defaultInputs = {
    json: '{"value": 0.75, "type": "market"}',
    csv: "value,type\n0.75,market",
    key_value: "value=0.75\ntype=market"
  };

  const handleIOProcess = async () => {
    try {
      const response = await api.processIO(ioData, ioFormat);
      setIoResult(response.data);
    } catch (error) {
      console.error("IO process error:", error);
    }
  };

  const handleClearLogs = async () => {
    try {
      await api.clearLogs();
      onLogsRefresh();
    } catch (error) {
      console.error("Clear logs error:", error);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* IO Test */}
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader>
          <CardTitle className="text-slate-100 flex items-center gap-2">
            <Database className="w-5 h-5" /> 입출력 테스트
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-slate-300 text-sm mb-2 block">형식</label>
            <Select value={ioFormat} onValueChange={(v) => { setIoFormat(v); setIoData(defaultInputs[v]); }}>
              <SelectTrigger className="bg-slate-900 border-slate-600 text-slate-100" data-testid="io-format-select">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="json">JSON</SelectItem>
                <SelectItem value="csv">CSV</SelectItem>
                <SelectItem value="key_value">Key-Value</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <label className="text-slate-300 text-sm mb-2 block">데이터</label>
            <Textarea
              value={ioData}
              onChange={(e) => setIoData(e.target.value)}
              className="bg-slate-900 border-slate-600 text-slate-100 font-mono h-24"
              data-testid="io-data-input"
            />
          </div>
          <Button onClick={handleIOProcess} className="w-full" data-testid="io-process-button">
            <RefreshCw className="w-4 h-4 mr-2" /> 처리
          </Button>
          {ioResult && (
            <div className="bg-slate-900 rounded-lg p-3">
              <pre className="text-slate-300 text-xs overflow-auto">
                {JSON.stringify(ioResult, null, 2)}
              </pre>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Activity Logs */}
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-slate-100 flex items-center gap-2">
            <FileText className="w-5 h-5" /> 활동 로그
          </CardTitle>
          <Button variant="outline" size="sm" onClick={handleClearLogs} data-testid="clear-logs-button">
            <Trash2 className="w-4 h-4 mr-1" /> 초기화
          </Button>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-80" data-testid="logs-list">
            {logs && logs.length > 0 ? (
              <div className="space-y-2">
                {logs.map((log, idx) => (
                  <div key={idx} className="bg-slate-900/50 rounded-lg p-3">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-blue-400 text-xs">{log.timestamp?.slice(0, 16)}</span>
                      <Badge variant="outline" className="text-xs">{log.phase}</Badge>
                    </div>
                    <p className="text-slate-300 text-sm">{log.action}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-slate-500 text-center py-8">로그가 없습니다</p>
            )}
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
};

// ==================== Alerts Tab ====================
const AlertsTab = ({ alerts, onRefresh }) => {
  const [healthResults, setHealthResults] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleHealthCheck = async () => {
    setLoading(true);
    try {
      const response = await api.runHealthCheck();
      setHealthResults(response.data);
      onRefresh();
    } catch (error) {
      console.error("Health check error:", error);
    }
    setLoading(false);
  };

  const stats = alerts?.statistics || { total: 0, active: 0, resolved: 0 };

  return (
    <Card className="bg-slate-800/50 border-slate-700">
      <CardHeader>
        <CardTitle className="text-slate-100 flex items-center gap-2">
          <Bell className="w-5 h-5" /> 알림 센터
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Health Check Section */}
          <div className="lg:col-span-2 space-y-4">
            <h3 className="text-slate-200 font-medium">시스템 점검</h3>
            <Button 
              onClick={handleHealthCheck} 
              disabled={loading}
              className="bg-emerald-600 hover:bg-emerald-500"
              data-testid="health-check-button"
            >
              {loading ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <Heart className="w-4 h-4 mr-2" />}
              헬스체크 실행
            </Button>

            {healthResults && (
              <div className="space-y-2" data-testid="health-results">
                {Object.entries(healthResults.results || {}).map(([key, value]) => (
                  <div key={key} className="bg-slate-900/50 rounded-lg p-3 flex items-center justify-between">
                    <span className="text-slate-100 font-medium capitalize">{key}</span>
                    <Badge variant={value.status === 'healthy' ? 'default' : 'destructive'}>
                      {value.status === 'healthy' ? '정상' : '점검 필요'}
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Stats Section */}
          <div className="space-y-4">
            <h3 className="text-slate-200 font-medium">알림 통계</h3>
            <div className="space-y-3" data-testid="alert-stats">
              <div className="bg-slate-900/50 rounded-lg p-4">
                <p className="text-slate-400 text-sm">전체 알림</p>
                <p className="text-slate-100 text-2xl font-bold">{stats.total}</p>
              </div>
              <div className="bg-slate-900/50 rounded-lg p-4">
                <p className="text-slate-400 text-sm">활성 알림</p>
                <p className="text-amber-400 text-2xl font-bold">{stats.active}</p>
              </div>
              <div className="bg-slate-900/50 rounded-lg p-4">
                <p className="text-slate-400 text-sm">해결됨</p>
                <p className="text-emerald-400 text-2xl font-bold">{stats.resolved}</p>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

// ==================== Settings Tab ====================
const SettingsTab = ({ sigma, omega, modules, onUpdate }) => {
  const [sigmaValues, setSigmaValues] = useState(sigma || [0.33, 0.34, 0.33]);
  const [omegaValues, setOmegaValues] = useState(omega || {
    V_pub_min: 0.2, V_pub_max: 0.5,
    V_pro_min: 0.2, V_pro_max: 0.5,
    V_ind_min: 0.1, V_ind_max: 0.5,
    sum_constraint: 1.0
  });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (sigma) setSigmaValues(sigma);
    if (omega) setOmegaValues(omega);
  }, [sigma, omega]);

  const sigmaTotal = sigmaValues.reduce((a, b) => a + b, 0);

  const handleSaveSigma = async () => {
    if (Math.abs(sigmaTotal - 1.0) > 0.01) {
      alert("시그마 합계가 1이 되어야 합니다");
      return;
    }
    setSaving(true);
    try {
      await api.updateSigma(sigmaValues);
      onUpdate();
    } catch (error) {
      console.error("Save sigma error:", error);
    }
    setSaving(false);
  };

  const handleSaveOmega = async () => {
    setSaving(true);
    try {
      await api.updateOmega(omegaValues);
      onUpdate();
    } catch (error) {
      console.error("Save omega error:", error);
    }
    setSaving(false);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Sigma Settings */}
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader>
          <CardTitle className="text-slate-100 flex items-center gap-2">
            <span className="text-xl">Σ</span> 시그마 설정
          </CardTitle>
          <CardDescription className="text-slate-400">가치 분배 목표 비율</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div>
            <label className="text-slate-300 text-sm mb-2 flex justify-between">
              <span>공공 (V_pub)</span>
              <span className="text-blue-400">{(sigmaValues[0] * 100).toFixed(0)}%</span>
            </label>
            <Slider
              value={[sigmaValues[0] * 100]}
              onValueChange={([v]) => setSigmaValues([v/100, sigmaValues[1], sigmaValues[2]])}
              max={100}
              step={5}
              className="[&_[role=slider]]:bg-blue-500"
              data-testid="sigma-pub-slider"
            />
          </div>
          <div>
            <label className="text-slate-300 text-sm mb-2 flex justify-between">
              <span>생산 (V_pro)</span>
              <span className="text-emerald-400">{(sigmaValues[1] * 100).toFixed(0)}%</span>
            </label>
            <Slider
              value={[sigmaValues[1] * 100]}
              onValueChange={([v]) => setSigmaValues([sigmaValues[0], v/100, sigmaValues[2]])}
              max={100}
              step={5}
              className="[&_[role=slider]]:bg-emerald-500"
              data-testid="sigma-pro-slider"
            />
          </div>
          <div>
            <label className="text-slate-300 text-sm mb-2 flex justify-between">
              <span>개인 (V_ind)</span>
              <span className="text-amber-400">{(sigmaValues[2] * 100).toFixed(0)}%</span>
            </label>
            <Slider
              value={[sigmaValues[2] * 100]}
              onValueChange={([v]) => setSigmaValues([sigmaValues[0], sigmaValues[1], v/100])}
              max={100}
              step={5}
              className="[&_[role=slider]]:bg-amber-500"
              data-testid="sigma-ind-slider"
            />
          </div>

          <div className={`text-center p-2 rounded ${Math.abs(sigmaTotal - 1.0) <= 0.01 ? 'bg-emerald-900/30 text-emerald-400' : 'bg-amber-900/30 text-amber-400'}`}>
            합계: {sigmaTotal.toFixed(2)} {Math.abs(sigmaTotal - 1.0) <= 0.01 ? '✓' : '(1.0이 되어야 함)'}
          </div>

          <Button 
            onClick={handleSaveSigma} 
            disabled={saving || Math.abs(sigmaTotal - 1.0) > 0.01}
            className="w-full"
            data-testid="save-sigma-button"
          >
            💾 Σ 저장
          </Button>
        </CardContent>
      </Card>

      {/* Omega Settings */}
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader>
          <CardTitle className="text-slate-100 flex items-center gap-2">
            <span className="text-xl">Ω</span> 오메가 설정
          </CardTitle>
          <CardDescription className="text-slate-400">경계 조건 설정</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-slate-300 text-sm mb-1 block">V_pub 최소</label>
              <Input
                type="number"
                min={0}
                max={1}
                step={0.05}
                value={omegaValues.V_pub_min}
                onChange={(e) => setOmegaValues({...omegaValues, V_pub_min: parseFloat(e.target.value)})}
                className="bg-slate-900 border-slate-600 text-slate-100"
                data-testid="omega-pub-min"
              />
            </div>
            <div>
              <label className="text-slate-300 text-sm mb-1 block">V_pub 최대</label>
              <Input
                type="number"
                min={0}
                max={1}
                step={0.05}
                value={omegaValues.V_pub_max}
                onChange={(e) => setOmegaValues({...omegaValues, V_pub_max: parseFloat(e.target.value)})}
                className="bg-slate-900 border-slate-600 text-slate-100"
                data-testid="omega-pub-max"
              />
            </div>
            <div>
              <label className="text-slate-300 text-sm mb-1 block">V_ind 최대</label>
              <Input
                type="number"
                min={0}
                max={1}
                step={0.05}
                value={omegaValues.V_ind_max}
                onChange={(e) => setOmegaValues({...omegaValues, V_ind_max: parseFloat(e.target.value)})}
                className="bg-slate-900 border-slate-600 text-slate-100"
                data-testid="omega-ind-max"
              />
            </div>
          </div>

          <Button 
            onClick={handleSaveOmega} 
            disabled={saving}
            className="w-full"
            data-testid="save-omega-button"
          >
            💾 Ω 저장
          </Button>

          <div className="mt-6">
            <h4 className="text-slate-200 font-medium mb-3">모듈 상태</h4>
            <div className="space-y-2" data-testid="module-status">
              {(modules || []).map((mod, idx) => (
                <div key={idx} className="flex items-center justify-between py-2 border-b border-slate-700">
                  <span className="text-slate-100">{mod.name}</span>
                  <Badge variant={mod.status === 'active' ? 'default' : 'secondary'}>
                    {mod.status === 'active' ? '활성' : '비활성'}
                  </Badge>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// ==================== Integration Tab ====================
const IntegrationTab = ({ onRefresh }) => {
  const [integrationStatus, setIntegrationStatus] = useState(null);
  const [adapters, setAdapters] = useState([]);
  const [mappings, setMappings] = useState([]);
  const [routingRules, setRoutingRules] = useState([]);
  const [loading, setLoading] = useState(false);
  const [exchangeData, setExchangeData] = useState('{"order_id": "ORD-001", "customer_id": "CUST-100", "amount": 1500}');
  const [sourceDomain, setSourceDomain] = useState("erp");
  const [messageType, setMessageType] = useState("order");
  const [exchangeResult, setExchangeResult] = useState(null);

  useEffect(() => {
    fetchIntegrationData();
  }, []);

  const fetchIntegrationData = async () => {
    try {
      const [statusRes, adaptersRes, mappingsRes, rulesRes] = await Promise.all([
        api.getIntegrationStatus(),
        api.getAdapters(),
        api.getMappings(),
        api.getRoutingRules()
      ]);
      setIntegrationStatus(statusRes.data);
      setAdapters(adaptersRes.data.adapters || []);
      setMappings(mappingsRes.data.mappings || []);
      setRoutingRules(rulesRes.data.rules || []);
    } catch (error) {
      console.error("Fetch integration data error:", error);
    }
  };

  const handleExchange = async () => {
    setLoading(true);
    try {
      const data = JSON.parse(exchangeData);
      const response = await api.executeExchange(data, sourceDomain, messageType);
      setExchangeResult(response.data);
      fetchIntegrationData();
      onRefresh();
    } catch (error) {
      console.error("Exchange error:", error);
      setExchangeResult({ success: false, errors: [error.message] });
    }
    setLoading(false);
  };

  const monitor = integrationStatus?.monitor || {};

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <MetricCard 
          icon={Network} 
          label="어댑터" 
          value={integrationStatus?.adapters?.total || 0}
          variant="cyan"
        />
        <MetricCard 
          icon={Link2} 
          label="매핑" 
          value={integrationStatus?.semantic_mappings?.total_mappings || 0}
          variant="teal"
        />
        <MetricCard 
          icon={GitBranch} 
          label="라우팅 규칙" 
          value={integrationStatus?.routing?.total_rules || 0}
          variant="amber"
        />
        <MetricCard 
          icon={ArrowRightLeft} 
          label="총 교환" 
          value={integrationStatus?.total_exchanges || 0}
          variant="purple"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Exchange Test */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-slate-100 flex items-center gap-2">
              <Send className="w-5 h-5" /> 데이터 교환 테스트
            </CardTitle>
            <CardDescription className="text-slate-400">
              도메인 간 데이터 교환을 시뮬레이션합니다
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-slate-300 text-sm mb-1 block">소스 도메인</label>
                <Select value={sourceDomain} onValueChange={setSourceDomain}>
                  <SelectTrigger className="bg-slate-900 border-slate-600 text-slate-100" data-testid="source-domain-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="erp">ERP</SelectItem>
                    <SelectItem value="crm">CRM</SelectItem>
                    <SelectItem value="scm">SCM</SelectItem>
                    <SelectItem value="mes">MES</SelectItem>
                    <SelectItem value="finance">Finance</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-slate-300 text-sm mb-1 block">메시지 유형</label>
                <Select value={messageType} onValueChange={setMessageType}>
                  <SelectTrigger className="bg-slate-900 border-slate-600 text-slate-100" data-testid="message-type-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="order">주문</SelectItem>
                    <SelectItem value="customer">고객</SelectItem>
                    <SelectItem value="inventory">재고</SelectItem>
                    <SelectItem value="production">생산</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div>
              <label className="text-slate-300 text-sm mb-1 block">데이터 (JSON)</label>
              <Textarea
                value={exchangeData}
                onChange={(e) => setExchangeData(e.target.value)}
                className="bg-slate-900 border-slate-600 text-slate-100 font-mono h-24"
                data-testid="exchange-data-input"
              />
            </div>
            <Button 
              onClick={handleExchange} 
              disabled={loading}
              className="w-full bg-violet-600 hover:bg-violet-500"
              data-testid="exchange-button"
            >
              {loading ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <ArrowRightLeft className="w-4 h-4 mr-2" />}
              교환 실행
            </Button>
            
            {exchangeResult && (
              <div className={`mt-4 p-3 rounded-lg ${exchangeResult.success ? 'bg-emerald-900/30 border border-emerald-600' : 'bg-red-900/30 border border-red-600'}`}>
                <p className={`font-medium mb-2 ${exchangeResult.success ? 'text-emerald-400' : 'text-red-400'}`}>
                  {exchangeResult.success ? '✓ 교환 성공' : '✗ 교환 실패'}
                </p>
                {exchangeResult.target_domains && (
                  <p className="text-slate-300 text-sm">
                    대상 도메인: {exchangeResult.target_domains.join(', ')}
                  </p>
                )}
                {exchangeResult.transformations && (
                  <p className="text-slate-400 text-xs mt-1">
                    변환: {exchangeResult.transformations.length}건
                  </p>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Adapters & Monitor */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-slate-100 flex items-center gap-2">
              <Network className="w-5 h-5" /> 도메인 어댑터
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-60" data-testid="adapters-list">
              <div className="space-y-2">
                {adapters.map((adapter, idx) => (
                  <div key={idx} className="bg-slate-900/50 rounded-lg p-3 flex items-center justify-between">
                    <div>
                      <p className="text-slate-100 font-medium">{adapter.domain_id}</p>
                      <p className="text-slate-500 text-xs">{adapter.protocol} • {adapter.domain_type}</p>
                    </div>
                    <div className="text-right">
                      <Badge variant={adapter.health_score > 0.8 ? 'default' : 'destructive'}>
                        {(adapter.health_score * 100).toFixed(0)}%
                      </Badge>
                      <p className="text-slate-500 text-xs mt-1">
                        {adapter.message_count}건 처리
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>

            {/* Monitor Stats */}
            <div className="mt-4 pt-4 border-t border-slate-700">
              <h4 className="text-slate-300 text-sm mb-3">실시간 모니터</h4>
              <div className="grid grid-cols-3 gap-2">
                <div className="bg-slate-900/50 rounded p-2 text-center">
                  <p className="text-slate-500 text-xs">처리량</p>
                  <p className="text-slate-100 font-medium">{monitor.throughput?.toFixed(2) || 0}/s</p>
                </div>
                <div className="bg-slate-900/50 rounded p-2 text-center">
                  <p className="text-slate-500 text-xs">평균 지연</p>
                  <p className="text-slate-100 font-medium">{monitor.average_latency_ms?.toFixed(1) || 0}ms</p>
                </div>
                <div className="bg-slate-900/50 rounded p-2 text-center">
                  <p className="text-slate-500 text-xs">에러</p>
                  <p className="text-red-400 font-medium">{monitor.total_errors || 0}</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Mappings & Routing Rules */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Semantic Mappings */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-slate-100 flex items-center gap-2">
              <Link2 className="w-5 h-5" /> 의미 매핑
            </CardTitle>
            <CardDescription className="text-slate-400">
              도메인 간 필드 매핑 ({mappings.length}건)
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-48" data-testid="mappings-list">
              <div className="space-y-2">
                {mappings.map((mapping, idx) => (
                  <div key={idx} className="bg-slate-900/50 rounded-lg p-2 flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2">
                      <span className="text-blue-400">{mapping.source_domain}.{mapping.source_field}</span>
                      <ArrowRightLeft className="w-3 h-3 text-slate-500" />
                      <span className="text-emerald-400">{mapping.target_domain}.{mapping.target_field}</span>
                    </div>
                    <Badge variant="outline" className="text-xs">
                      {(mapping.similarity_score * 100).toFixed(0)}%
                    </Badge>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Routing Rules */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-slate-100 flex items-center gap-2">
              <GitBranch className="w-5 h-5" /> 라우팅 규칙
            </CardTitle>
            <CardDescription className="text-slate-400">
              메시지 라우팅 규칙 ({routingRules.length}건)
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-48" data-testid="routing-rules-list">
              <div className="space-y-2">
                {routingRules.map((rule, idx) => (
                  <div key={idx} className="bg-slate-900/50 rounded-lg p-3">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-slate-100 font-medium">{rule.name}</span>
                      <Badge variant={rule.enabled ? 'default' : 'secondary'}>
                        우선순위: {rule.priority}
                      </Badge>
                    </div>
                    <div className="text-slate-400 text-xs">
                      <span className="text-blue-400">{rule.source_domain}</span>
                      <span className="mx-1">→</span>
                      <span className="text-emerald-400">{rule.target_domains?.join(', ')}</span>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

// ==================== Main App ====================
function App() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [dashboard, setDashboard] = useState(null);
  const [logs, setLogs] = useState([]);
  const [alerts, setAlerts] = useState(null);
  const [modules, setModules] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const [dashRes, logsRes, alertsRes, modulesRes] = await Promise.all([
        api.getDashboard(),
        api.getLogs(10),
        api.getAlerts(),
        api.getModules()
      ]);
      setDashboard(dashRes.data);
      setLogs(logsRes.data.logs);
      setAlerts(alertsRes.data);
      setModules(modulesRes.data.modules);
    } catch (error) {
      console.error("Fetch error:", error);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Header */}
      <header className="bg-slate-800/80 border-b border-slate-700 px-6 py-4">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-gradient-to-br from-violet-500 to-purple-600 rounded-xl flex items-center justify-center">
            <Zap className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-100" data-testid="app-title">GVIC Engine</h1>
            <p className="text-slate-400 text-sm">통합 제어 대시보드</p>
          </div>
          <div className="ml-auto">
            <Button variant="outline" size="sm" onClick={fetchData} data-testid="refresh-button">
              <RefreshCw className="w-4 h-4 mr-1" /> 새로고침
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-6">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="bg-slate-800 border border-slate-700 mb-6" data-testid="main-tabs">
            <TabsTrigger value="dashboard" className="data-[state=active]:bg-slate-700">
              <LayoutDashboard className="w-4 h-4 mr-2" /> 대시보드
            </TabsTrigger>
            <TabsTrigger value="processing" className="data-[state=active]:bg-slate-700">
              <Play className="w-4 h-4 mr-2" /> 처리
            </TabsTrigger>
            <TabsTrigger value="data" className="data-[state=active]:bg-slate-700">
              <Database className="w-4 h-4 mr-2" /> 데이터
            </TabsTrigger>
            <TabsTrigger value="alerts" className="data-[state=active]:bg-slate-700">
              <Bell className="w-4 h-4 mr-2" /> 알림
            </TabsTrigger>
            <TabsTrigger value="settings" className="data-[state=active]:bg-slate-700">
              <Settings className="w-4 h-4 mr-2" /> 설정
            </TabsTrigger>
          </TabsList>

          <TabsContent value="dashboard">
            <DashboardTab dashboard={dashboard} onRefresh={fetchData} />
          </TabsContent>

          <TabsContent value="processing">
            <ProcessingTab onProcess={fetchData} />
          </TabsContent>

          <TabsContent value="data">
            <DataTab logs={logs} onLogsRefresh={fetchData} />
          </TabsContent>

          <TabsContent value="alerts">
            <AlertsTab alerts={alerts} onRefresh={fetchData} />
          </TabsContent>

          <TabsContent value="settings">
            <SettingsTab 
              sigma={dashboard?.sigma} 
              omega={dashboard?.omega}
              modules={modules}
              onUpdate={fetchData}
            />
          </TabsContent>
        </Tabs>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 py-6 text-center text-slate-500 text-sm">
        GVIC Engine v1.0.0 • 6개 특허 모듈 통합 시스템
      </footer>
    </div>
  );
}

export default App;
