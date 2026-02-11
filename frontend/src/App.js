import { useState, useEffect, useCallback } from "react";
import "@/App.css";
import axios from "axios";
import { 
  Activity, Database, Settings, AlertTriangle, BarChart3, 
  RefreshCw, Play, Trash2, Download, ChevronRight, CheckCircle2,
  XCircle, Clock, Zap, TrendingUp, PieChart, Save
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Tab Components
const TabButton = ({ active, onClick, icon: Icon, label, badge }) => (
  <button
    data-testid={`tab-${label.toLowerCase().replace(/\s/g, '-')}`}
    onClick={onClick}
    className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-all border-b-2 ${
      active 
        ? 'border-cyan-400 text-cyan-400 bg-slate-800/50' 
        : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-800/30'
    }`}
  >
    <Icon size={18} />
    <span>{label}</span>
    {badge !== undefined && (
      <span className={`px-2 py-0.5 text-xs rounded-full ${
        badge > 0 ? 'bg-amber-500/20 text-amber-400' : 'bg-slate-700 text-slate-400'
      }`}>
        {badge}
      </span>
    )}
  </button>
);

// Card Components
const StatCard = ({ icon: Icon, label, value, subtext, color = "cyan" }) => {
  const colors = {
    cyan: "from-cyan-500/20 to-cyan-600/10 border-cyan-500/30 text-cyan-400",
    emerald: "from-emerald-500/20 to-emerald-600/10 border-emerald-500/30 text-emerald-400",
    amber: "from-amber-500/20 to-amber-600/10 border-amber-500/30 text-amber-400",
    rose: "from-rose-500/20 to-rose-600/10 border-rose-500/30 text-rose-400",
    violet: "from-violet-500/20 to-violet-600/10 border-violet-500/30 text-violet-400",
  };
  
  return (
    <div className={`bg-gradient-to-br ${colors[color]} border rounded-xl p-4`}>
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-lg bg-slate-900/50`}>
          <Icon size={20} />
        </div>
        <div>
          <p className="text-xs text-slate-400 uppercase tracking-wide">{label}</p>
          <p className="text-2xl font-bold text-white">{value}</p>
          {subtext && <p className="text-xs text-slate-500">{subtext}</p>}
        </div>
      </div>
    </div>
  );
};

// Distribution Pie Chart (SVG)
const DistributionChart = ({ data }) => {
  const total = data.public + data.productive + data.individual;
  const publicAngle = (data.public / total) * 360;
  const productiveAngle = (data.productive / total) * 360;
  
  const createArc = (startAngle, endAngle, color) => {
    const start = (startAngle - 90) * Math.PI / 180;
    const end = (endAngle - 90) * Math.PI / 180;
    const largeArc = endAngle - startAngle > 180 ? 1 : 0;
    const x1 = 50 + 40 * Math.cos(start);
    const y1 = 50 + 40 * Math.sin(start);
    const x2 = 50 + 40 * Math.cos(end);
    const y2 = 50 + 40 * Math.sin(end);
    
    return `M 50 50 L ${x1} ${y1} A 40 40 0 ${largeArc} 1 ${x2} ${y2} Z`;
  };

  return (
    <div className="flex items-center gap-6">
      <svg viewBox="0 0 100 100" className="w-32 h-32">
        <path d={createArc(0, publicAngle, "#3B82F6")} fill="#3B82F6" />
        <path d={createArc(publicAngle, publicAngle + productiveAngle, "#10B981")} fill="#10B981" />
        <path d={createArc(publicAngle + productiveAngle, 360, "#F59E0B")} fill="#F59E0B" />
        <circle cx="50" cy="50" r="25" fill="#0f172a" />
      </svg>
      <div className="space-y-2 text-sm">
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded-full bg-blue-500"></span>
          <span className="text-slate-300">공공: {(data.public * 100).toFixed(1)}%</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded-full bg-emerald-500"></span>
          <span className="text-slate-300">생산: {(data.productive * 100).toFixed(1)}%</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded-full bg-amber-500"></span>
          <span className="text-slate-300">개인: {(data.individual * 100).toFixed(1)}%</span>
        </div>
      </div>
    </div>
  );
};

// Balance Gauge
const BalanceGauge = ({ value }) => {
  const percentage = value * 100;
  const color = value >= 0.7 ? '#10B981' : value >= 0.3 ? '#F59E0B' : '#EF4444';
  
  return (
    <div className="flex flex-col items-center">
      <div className="relative w-32 h-16 overflow-hidden">
        <svg viewBox="0 0 100 50" className="w-full h-full">
          <path d="M 10 50 A 40 40 0 0 1 90 50" fill="none" stroke="#1e293b" strokeWidth="8" />
          <path 
            d="M 10 50 A 40 40 0 0 1 90 50" 
            fill="none" 
            stroke={color} 
            strokeWidth="8"
            strokeDasharray={`${percentage * 1.26} 126`}
          />
        </svg>
        <div className="absolute inset-0 flex items-end justify-center pb-1">
          <span className="text-xl font-bold text-white">{percentage.toFixed(0)}%</span>
        </div>
      </div>
      <span className="text-xs text-slate-400 mt-1">균형 지수</span>
    </div>
  );
};

// Main Dashboard Component
const Dashboard = ({ dashboard, onRefresh, loading }) => {
  const distribution = dashboard?.engine?.modules?.distributor?.current_ratio || [0.5, 0.3, 0.2];
  const distData = {
    public: distribution[0] || 0.5,
    productive: distribution[1] || 0.3,
    individual: distribution[2] || 0.2
  };
  
  return (
    <div className="space-y-6">
      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard 
          icon={Activity} 
          label="처리 건수" 
          value={dashboard?.engine?.total_processed || 0}
          color="cyan"
        />
        <StatCard 
          icon={CheckCircle2} 
          label="성공률" 
          value={`${((dashboard?.engine?.success_rate || 0) * 100).toFixed(1)}%`}
          color="emerald"
        />
        <StatCard 
          icon={AlertTriangle} 
          label="활성 알림" 
          value={dashboard?.summary?.active_alerts || 0}
          color="amber"
        />
        <StatCard 
          icon={Zap} 
          label="시스템" 
          value={dashboard?.summary?.system_status || 'unknown'}
          color="violet"
        />
      </div>
      
      {/* Charts Row */}
      <div className="grid md:grid-cols-2 gap-6">
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <PieChart size={20} className="text-cyan-400" />
            분배 비율
          </h3>
          <DistributionChart data={distData} />
        </div>
        
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <TrendingUp size={20} className="text-emerald-400" />
            균형 상태
          </h3>
          <div className="flex items-center justify-around">
            <BalanceGauge value={0.85} />
            <div className="space-y-3">
              <div className="text-sm">
                <span className="text-slate-400">Σ 기준:</span>
                <span className="text-white ml-2">[{dashboard?.engine?.sigma?.map(s => s.toFixed(2)).join(', ') || '0.50, 0.30, 0.20'}]</span>
              </div>
              <div className="text-sm">
                <span className="text-slate-400">수렴 상태:</span>
                <span className={`ml-2 ${dashboard?.engine?.modules?.convergence === 'active' ? 'text-emerald-400' : 'text-amber-400'}`}>
                  {dashboard?.engine?.modules?.convergence || 'active'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Process Tab Component
const ProcessTab = () => {
  const [inputValue, setInputValue] = useState(50);
  const [result, setResult] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [history, setHistory] = useState([]);

  const handleProcess = async () => {
    setProcessing(true);
    try {
      const res = await axios.post(`${API}/engine/process`, { value: inputValue });
      setResult(res.data);
      setHistory(prev => [{ input: inputValue, result: res.data, time: new Date() }, ...prev].slice(0, 10));
    } catch (e) {
      console.error(e);
    }
    setProcessing(false);
  };

  return (
    <div className="space-y-6">
      {/* Input Section */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-white mb-4">데이터 처리</h3>
        <div className="flex gap-4 items-end">
          <div className="flex-1">
            <label className="block text-sm text-slate-400 mb-2">입력 값 (0-100)</label>
            <input
              data-testid="process-input"
              type="range"
              min="0"
              max="100"
              value={inputValue}
              onChange={(e) => setInputValue(Number(e.target.value))}
              className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-cyan-500"
            />
            <div className="flex justify-between text-xs text-slate-500 mt-1">
              <span>0</span>
              <span className="text-cyan-400 font-bold text-lg">{inputValue}</span>
              <span>100</span>
            </div>
          </div>
          <button
            data-testid="process-btn"
            onClick={handleProcess}
            disabled={processing}
            className="px-6 py-3 bg-cyan-500 hover:bg-cyan-600 disabled:bg-slate-600 text-white rounded-lg font-medium flex items-center gap-2 transition-colors"
          >
            {processing ? <RefreshCw size={18} className="animate-spin" /> : <Play size={18} />}
            처리
          </button>
        </div>
      </div>

      {/* Result Section */}
      {result && (
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <CheckCircle2 size={20} className={result.success ? 'text-emerald-400' : 'text-rose-400'} />
            처리 결과
          </h3>
          <div className="grid md:grid-cols-3 gap-4">
            <div className="bg-slate-900/50 rounded-lg p-4">
              <p className="text-xs text-slate-400 mb-1">분배</p>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span className="text-blue-400">공공</span>
                  <span className="text-white">{result.data?.distribution?.public?.toFixed(4)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-emerald-400">생산</span>
                  <span className="text-white">{result.data?.distribution?.productive?.toFixed(4)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-amber-400">개인</span>
                  <span className="text-white">{result.data?.distribution?.individual?.toFixed(4)}</span>
                </div>
              </div>
            </div>
            <div className="bg-slate-900/50 rounded-lg p-4">
              <p className="text-xs text-slate-400 mb-1">수렴</p>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-400">유효</span>
                  <span className={result.data?.convergence?.is_valid ? 'text-emerald-400' : 'text-rose-400'}>
                    {result.data?.convergence?.is_valid ? 'Yes' : 'No'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">변환됨</span>
                  <span className="text-white">{result.data?.convergence?.was_transformed ? 'Yes' : 'No'}</span>
                </div>
              </div>
            </div>
            <div className="bg-slate-900/50 rounded-lg p-4">
              <p className="text-xs text-slate-400 mb-1">균형 점수</p>
              <p className="text-3xl font-bold text-cyan-400">
                {(result.data?.balance_score * 100)?.toFixed(1)}%
              </p>
            </div>
          </div>
        </div>
      )}

      {/* History */}
      {history.length > 0 && (
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">처리 이력</h3>
          <div className="space-y-2">
            {history.map((h, i) => (
              <div key={i} className="flex items-center justify-between bg-slate-900/50 rounded-lg px-4 py-2 text-sm">
                <span className="text-slate-400">입력: <span className="text-white">{h.input}</span></span>
                <span className={h.result.success ? 'text-emerald-400' : 'text-rose-400'}>
                  {h.result.success ? '성공' : '실패'}
                </span>
                <span className="text-slate-500">{h.time.toLocaleTimeString()}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// Settings Tab
const SettingsTab = () => {
  const [sigma, setSigma] = useState([0.5, 0.3, 0.2]);
  const [omega, setOmega] = useState({ V_pub_min: 0.2, V_pub_max: 0.8, V_ind_max: 0.5 });
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState(null);

  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const [sigmaRes, omegaRes] = await Promise.all([
          axios.get(`${API}/config/sigma`),
          axios.get(`${API}/config/omega`)
        ]);
        setSigma(sigmaRes.data.sigma);
        setOmega(omegaRes.data.omega);
      } catch (e) {
        console.error(e);
      }
    };
    fetchConfig();
  }, []);

  const handleSaveSigma = async () => {
    setSaving(true);
    try {
      await axios.put(`${API}/config/sigma`, { sigma });
      setMessage({ type: 'success', text: 'Σ 설정이 저장되었습니다' });
    } catch (e) {
      setMessage({ type: 'error', text: e.response?.data?.detail || '저장 실패' });
    }
    setSaving(false);
    setTimeout(() => setMessage(null), 3000);
  };

  const handleSaveOmega = async () => {
    setSaving(true);
    try {
      await axios.put(`${API}/config/omega`, omega);
      setMessage({ type: 'success', text: 'Ω 설정이 저장되었습니다' });
    } catch (e) {
      setMessage({ type: 'error', text: '저장 실패' });
    }
    setSaving(false);
    setTimeout(() => setMessage(null), 3000);
  };

  const updateSigma = (idx, val) => {
    const newSigma = [...sigma];
    newSigma[idx] = val;
    setSigma(newSigma);
  };

  const sigmaSum = sigma.reduce((a, b) => a + b, 0);
  const isValidSigma = Math.abs(sigmaSum - 1.0) < 0.01;

  return (
    <div className="space-y-6">
      {message && (
        <div className={`p-4 rounded-lg ${message.type === 'success' ? 'bg-emerald-500/20 border border-emerald-500/30 text-emerald-400' : 'bg-rose-500/20 border border-rose-500/30 text-rose-400'}`}>
          {message.text}
        </div>
      )}

      {/* Sigma Settings */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Σ (시그마) 설정</h3>
        <p className="text-sm text-slate-400 mb-4">기본 분배 비율을 설정합니다. 합계는 1.0이어야 합니다.</p>
        
        <div className="grid md:grid-cols-3 gap-4 mb-4">
          {['공공 (Public)', '생산 (Productive)', '개인 (Individual)'].map((label, idx) => (
            <div key={idx}>
              <label className="block text-sm text-slate-400 mb-2">{label}</label>
              <input
                data-testid={`sigma-${idx}`}
                type="number"
                step="0.01"
                min="0"
                max="1"
                value={sigma[idx]}
                onChange={(e) => updateSigma(idx, parseFloat(e.target.value) || 0)}
                className="w-full px-4 py-2 bg-slate-900 border border-slate-600 rounded-lg text-white focus:border-cyan-500 focus:outline-none"
              />
            </div>
          ))}
        </div>
        
        <div className="flex items-center justify-between">
          <div className={`text-sm ${isValidSigma ? 'text-emerald-400' : 'text-rose-400'}`}>
            합계: {sigmaSum.toFixed(2)} {isValidSigma ? '✓' : '(1.0 필요)'}
          </div>
          <button
            data-testid="save-sigma-btn"
            onClick={handleSaveSigma}
            disabled={saving || !isValidSigma}
            className="px-4 py-2 bg-cyan-500 hover:bg-cyan-600 disabled:bg-slate-600 text-white rounded-lg flex items-center gap-2"
          >
            <Save size={16} />
            저장
          </button>
        </div>
      </div>

      {/* Omega Settings */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Ω (오메가) 제약조건</h3>
        <p className="text-sm text-slate-400 mb-4">수렴 시 적용되는 제약조건을 설정합니다.</p>
        
        <div className="grid md:grid-cols-3 gap-4 mb-4">
          <div>
            <label className="block text-sm text-slate-400 mb-2">공공 최소 (V_pub_min)</label>
            <input
              data-testid="omega-pub-min"
              type="number"
              step="0.01"
              value={omega.V_pub_min}
              onChange={(e) => setOmega({...omega, V_pub_min: parseFloat(e.target.value) || 0})}
              className="w-full px-4 py-2 bg-slate-900 border border-slate-600 rounded-lg text-white focus:border-cyan-500 focus:outline-none"
            />
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-2">공공 최대 (V_pub_max)</label>
            <input
              data-testid="omega-pub-max"
              type="number"
              step="0.01"
              value={omega.V_pub_max}
              onChange={(e) => setOmega({...omega, V_pub_max: parseFloat(e.target.value) || 0})}
              className="w-full px-4 py-2 bg-slate-900 border border-slate-600 rounded-lg text-white focus:border-cyan-500 focus:outline-none"
            />
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-2">개인 최대 (V_ind_max)</label>
            <input
              data-testid="omega-ind-max"
              type="number"
              step="0.01"
              value={omega.V_ind_max}
              onChange={(e) => setOmega({...omega, V_ind_max: parseFloat(e.target.value) || 0})}
              className="w-full px-4 py-2 bg-slate-900 border border-slate-600 rounded-lg text-white focus:border-cyan-500 focus:outline-none"
            />
          </div>
        </div>
        
        <div className="flex justify-end">
          <button
            data-testid="save-omega-btn"
            onClick={handleSaveOmega}
            disabled={saving}
            className="px-4 py-2 bg-cyan-500 hover:bg-cyan-600 disabled:bg-slate-600 text-white rounded-lg flex items-center gap-2"
          >
            <Save size={16} />
            저장
          </button>
        </div>
      </div>
    </div>
  );
};

// 💾 Data Tab Component
const DataTab = () => {
  const [stats, setStats] = useState(null);
  const [selectedCollection, setSelectedCollection] = useState('processing_results');
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);

  const collections = [
    { id: 'processing_results', name: '처리 결과', icon: Activity },
    { id: 'alerts', name: '알림', icon: AlertTriangle },
    { id: 'metrics', name: '메트릭', icon: BarChart3 },
    { id: 'configs', name: '설정', icon: Settings },
  ];

  const fetchStats = async () => {
    try {
      const res = await axios.get(`${API}/data/stats`);
      setStats(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  const fetchData = async (collection) => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/data/${collection.replace('_', '-')}`);
      setData(res.data.results || res.data.alerts || res.data.metrics || res.data.configs || []);
    } catch (e) {
      console.error(e);
      setData([]);
    }
    setLoading(false);
  };

  const handleExport = async (collection) => {
    try {
      const res = await axios.post(`${API}/data/export?collection=${collection}`);
      const blob = new Blob([JSON.stringify(res.data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${collection}_export_${new Date().toISOString().split('T')[0]}.json`;
      a.click();
    } catch (e) {
      console.error(e);
    }
  };

  const handleClear = async (collection) => {
    if (!window.confirm(`정말 ${collection} 데이터를 삭제하시겠습니까?`)) return;
    try {
      await axios.delete(`${API}/data/clear/${collection}`);
      fetchStats();
      fetchData(collection);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  useEffect(() => {
    fetchData(selectedCollection);
  }, [selectedCollection]);

  return (
    <div className="space-y-6">
      {/* Stats Overview */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <Database size={20} className="text-cyan-400" />
            데이터베이스 상태
          </h3>
          <button
            data-testid="refresh-stats-btn"
            onClick={fetchStats}
            className="p-2 hover:bg-slate-700 rounded-lg transition-colors"
          >
            <RefreshCw size={18} className="text-slate-400" />
          </button>
        </div>
        
        <div className={`mb-4 px-3 py-2 rounded-lg inline-flex items-center gap-2 ${
          stats?.status === 'connected' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'
        }`}>
          {stats?.status === 'connected' ? <CheckCircle2 size={16} /> : <XCircle size={16} />}
          {stats?.status === 'connected' ? '연결됨' : '연결 안됨'}
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {collections.map(col => (
            <div key={col.id} className="bg-slate-900/50 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <col.icon size={16} className="text-slate-400" />
                <span className="text-sm text-slate-400">{col.name}</span>
              </div>
              <p className="text-2xl font-bold text-white">
                {stats?.collections?.[col.id] || 0}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Collection Browser */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-xl overflow-hidden">
        {/* Collection Tabs */}
        <div className="flex border-b border-slate-700 overflow-x-auto">
          {collections.map(col => (
            <button
              key={col.id}
              data-testid={`collection-${col.id}`}
              onClick={() => setSelectedCollection(col.id)}
              className={`flex items-center gap-2 px-4 py-3 text-sm whitespace-nowrap transition-colors ${
                selectedCollection === col.id 
                  ? 'bg-slate-700/50 text-cyan-400 border-b-2 border-cyan-400' 
                  : 'text-slate-400 hover:bg-slate-700/30'
              }`}
            >
              <col.icon size={16} />
              {col.name}
            </button>
          ))}
        </div>

        {/* Actions */}
        <div className="flex items-center justify-between p-4 border-b border-slate-700">
          <span className="text-sm text-slate-400">
            {data.length}개 레코드
          </span>
          <div className="flex gap-2">
            <button
              data-testid="export-btn"
              onClick={() => handleExport(selectedCollection)}
              className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-lg text-sm flex items-center gap-2"
            >
              <Download size={14} />
              내보내기
            </button>
            {selectedCollection !== 'configs' && (
              <button
                data-testid="clear-btn"
                onClick={() => handleClear(selectedCollection)}
                className="px-3 py-1.5 bg-rose-500/20 hover:bg-rose-500/30 text-rose-400 rounded-lg text-sm flex items-center gap-2"
              >
                <Trash2 size={14} />
                초기화
              </button>
            )}
          </div>
        </div>

        {/* Data Table */}
        <div className="max-h-96 overflow-auto">
          {loading ? (
            <div className="flex items-center justify-center p-8">
              <RefreshCw size={24} className="animate-spin text-cyan-400" />
            </div>
          ) : data.length === 0 ? (
            <div className="flex flex-col items-center justify-center p-8 text-slate-400">
              <Database size={32} className="mb-2 opacity-50" />
              <p>데이터가 없습니다</p>
            </div>
          ) : (
            <div className="divide-y divide-slate-700/50">
              {data.slice(0, 50).map((item, idx) => (
                <div key={idx} className="p-4 hover:bg-slate-700/20 transition-colors">
                  <pre className="text-xs text-slate-300 overflow-x-auto">
                    {JSON.stringify(item, null, 2)}
                  </pre>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Alerts Tab
const AlertsTab = () => {
  const [alerts, setAlerts] = useState({ active: [], statistics: {} });
  const [loading, setLoading] = useState(false);

  const fetchAlerts = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/control/alerts`);
      setAlerts(res.data);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  const resolveAlert = async (alertId) => {
    try {
      await axios.post(`${API}/control/alerts/${alertId}/resolve`);
      fetchAlerts();
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, []);

  const levelColors = {
    critical: 'bg-rose-500/20 border-rose-500/30 text-rose-400',
    error: 'bg-orange-500/20 border-orange-500/30 text-orange-400',
    warning: 'bg-amber-500/20 border-amber-500/30 text-amber-400',
    info: 'bg-blue-500/20 border-blue-500/30 text-blue-400',
  };

  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard icon={AlertTriangle} label="전체" value={alerts.statistics?.total || 0} color="cyan" />
        <StatCard icon={XCircle} label="활성" value={alerts.statistics?.active || 0} color="amber" />
        <StatCard icon={CheckCircle2} label="해결됨" value={alerts.statistics?.resolved || 0} color="emerald" />
        <StatCard icon={Zap} label="위험" value={alerts.statistics?.by_level?.critical || 0} color="rose" />
      </div>

      {/* Active Alerts */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">활성 알림</h3>
          <button onClick={fetchAlerts} className="p-2 hover:bg-slate-700 rounded-lg">
            <RefreshCw size={18} className={`text-slate-400 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {alerts.active?.length === 0 ? (
          <div className="text-center py-8 text-slate-400">
            <CheckCircle2 size={32} className="mx-auto mb-2 text-emerald-400" />
            <p>활성 알림이 없습니다</p>
          </div>
        ) : (
          <div className="space-y-3">
            {alerts.active?.map((alert, idx) => (
              <div key={idx} className={`border rounded-lg p-4 ${levelColors[alert.level]}`}>
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs uppercase font-bold">{alert.level}</span>
                      <span className="text-xs opacity-70">{alert.component}</span>
                    </div>
                    <p className="text-sm">{alert.message}</p>
                    <p className="text-xs opacity-50 mt-1">{alert.timestamp}</p>
                  </div>
                  <button
                    onClick={() => resolveAlert(alert.id)}
                    className="px-3 py-1 bg-slate-800/50 hover:bg-slate-700 rounded text-xs"
                  >
                    해결
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// Main App
function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [alertCount, setAlertCount] = useState(0);

  const fetchDashboard = useCallback(async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/dashboard`);
      setDashboard(res.data);
      setAlertCount(res.data?.summary?.active_alerts || 0);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchDashboard();
    const interval = setInterval(fetchDashboard, 30000);
    return () => clearInterval(interval);
  }, [fetchDashboard]);

  const tabs = [
    { id: 'dashboard', label: '대시보드', icon: BarChart3 },
    { id: 'process', label: '처리', icon: Play },
    { id: 'data', label: '💾 데이터', icon: Database },
    { id: 'alerts', label: '알림', icon: AlertTriangle, badge: alertCount },
    { id: 'settings', label: '설정', icon: Settings },
  ];

  return (
    <div data-testid="gvic-dashboard" className="min-h-screen bg-slate-900">
      {/* Header */}
      <header className="bg-slate-800/80 border-b border-slate-700 sticky top-0 z-50 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-cyan-400 to-blue-600 rounded-xl flex items-center justify-center">
                <Zap size={24} className="text-white" />
              </div>
              <div>
                <h1 className="text-lg font-bold text-white">GVIC Engine</h1>
                <p className="text-xs text-slate-400">통합 제어 대시보드</p>
              </div>
            </div>
            <button
              data-testid="refresh-dashboard-btn"
              onClick={fetchDashboard}
              disabled={loading}
              className="p-2 hover:bg-slate-700 rounded-lg transition-colors"
            >
              <RefreshCw size={20} className={`text-slate-400 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
          
          {/* Tabs */}
          <div className="flex -mb-px overflow-x-auto">
            {tabs.map(tab => (
              <TabButton
                key={tab.id}
                active={activeTab === tab.id}
                onClick={() => setActiveTab(tab.id)}
                icon={tab.icon}
                label={tab.label}
                badge={tab.badge}
              />
            ))}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {activeTab === 'dashboard' && <Dashboard dashboard={dashboard} onRefresh={fetchDashboard} loading={loading} />}
        {activeTab === 'process' && <ProcessTab />}
        {activeTab === 'data' && <DataTab />}
        {activeTab === 'alerts' && <AlertsTab />}
        {activeTab === 'settings' && <SettingsTab />}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 py-4 mt-8">
        <div className="max-w-7xl mx-auto px-4 text-center text-xs text-slate-500">
          GVIC Engine v1.0.0 • 6개 특허 모듈 통합 시스템
        </div>
      </footer>
    </div>
  );
}

export default App;
