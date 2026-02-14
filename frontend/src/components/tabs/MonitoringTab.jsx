import { useState, useEffect, useCallback, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { 
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, 
  CartesianGrid, Tooltip as RechartsTooltip, AreaChart, Area, PieChart, Pie, Cell
} from 'recharts';
import { Activity, Radio, AlertTriangle, CheckCircle, RefreshCw, Zap, Database, Clock, TrendingUp } from 'lucide-react';
import { MetricCard } from "@/components/MetricCard";
import { api } from "@/lib/api";
import axios from "axios";

const API_URL = process.env.REACT_APP_BACKEND_URL;

export const MonitoringTab = () => {
  const [signalStats, setSignalStats] = useState(null);
  const [isLive, setIsLive] = useState(true);
  const [loading, setLoading] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/api/monitor/signals`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setSignalStats(response.data);
    } catch (error) {
      console.error("Monitoring fetch error:", error);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // 실시간 폴링 (3초)
  useEffect(() => {
    if (!isLive) return;
    const interval = setInterval(fetchData, 3000);
    return () => clearInterval(interval);
  }, [isLive, fetchData]);

  // 실제 데이터
  const totalAnalyzed = signalStats?.total_analyzed || 0;
  const totalAssets = signalStats?.total_assets || 0;
  const successRate = (signalStats?.success_rate || 0) * 100;
  const lastHourCount = signalStats?.last_hour_count || 0;
  const status = signalStats?.status || "idle";
  const chartData = signalStats?.chart_data || [];
  const recentSignals = signalStats?.recent_signals || [];
  const recentAssets = signalStats?.recent_assets || [];
  const bySignalType = signalStats?.by_signal_type || {};
  const bySentiment = signalStats?.by_sentiment || {};

  // 감성 차트 데이터
  const sentimentChartData = [
    { name: '긍정', value: bySentiment.positive || 0, color: '#10b981' },
    { name: '혼합', value: bySentiment.mixed || 0, color: '#8b5cf6' },
    { name: '중립', value: bySentiment.neutral || 0, color: '#3b82f6' },
    { name: '부정', value: bySentiment.negative || 0, color: '#ef4444' }
  ].filter(d => d.value > 0);

  // 상태 표시
  const statusConfig = {
    active: { label: '활발', color: 'bg-emerald-500', icon: CheckCircle },
    normal: { label: '정상', color: 'bg-blue-500', icon: Activity },
    low: { label: '저조', color: 'bg-yellow-500', icon: AlertTriangle },
    idle: { label: '대기', color: 'bg-slate-500', icon: Radio }
  };
  const currentStatus = statusConfig[status] || statusConfig.idle;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className={`w-3 h-3 rounded-full ${isLive ? 'bg-emerald-400 animate-pulse' : 'bg-slate-500'}`} />
          <span className="text-slate-300">
            {isLive ? '실시간 모니터링 중' : '모니터링 일시정지'}
          </span>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Switch 
              checked={isLive} 
              onCheckedChange={setIsLive}
              data-testid="live-toggle"
            />
            <span className="text-slate-400 text-sm">{isLive ? '실시간' : '정지'}</span>
          </div>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={fetchData}
            disabled={loading}
            data-testid="refresh-monitoring-button"
          >
            <RefreshCw className={`w-4 h-4 mr-1 ${loading ? 'animate-spin' : ''}`} /> 새로고침
          </Button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <MetricCard 
          icon={Activity} 
          label="총 소비량" 
          value={current.consumption?.total?.toFixed(1) || 0}
          variant="cyan"
        />
        <MetricCard 
          icon={Radio} 
          label="효율성" 
          value={`${efficiency.toFixed(1)}%`}
          variant={efficiency >= 90 ? "teal" : efficiency >= 70 ? "amber" : "rose"}
        />
        <MetricCard 
          icon={status === "optimal" ? CheckCircle : AlertTriangle} 
          label="상태" 
          value={status === "optimal" ? "최적" : status === "adjusting" ? "조정중" : "경고"}
          variant={status === "optimal" ? "teal" : status === "adjusting" ? "amber" : "rose"}
        />
        <MetricCard 
          icon={AlertTriangle} 
          label="위반 사항" 
          value={distribution?.violations?.length || 0}
          variant={distribution?.is_valid ? "teal" : "rose"}
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Consumption Chart */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-slate-100 flex items-center gap-2">
              <Activity className="w-5 h-5" /> 실시간 소비량
            </CardTitle>
            <CardDescription className="text-slate-400">
              특허6: ConsumptionMonitor 데이터
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-64" data-testid="consumption-chart">
              {history.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%" key={`chart-${history.length}`}>
                  <AreaChart data={history}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis dataKey="time" stroke="#94a3b8" fontSize={10} />
                    <YAxis stroke="#94a3b8" fontSize={10} />
                    <RechartsTooltip 
                      contentStyle={{ background: '#1e293b', border: '1px solid #475569', borderRadius: '8px' }}
                    />
                    <Area type="monotone" dataKey="public" stackId="1" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.6} name="공공" />
                    <Area type="monotone" dataKey="productive" stackId="1" stroke="#10b981" fill="#10b981" fillOpacity={0.6} name="생산" />
                    <Area type="monotone" dataKey="individual" stackId="1" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.6} name="개인" />
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-slate-500">
                  데이터 로딩 중...
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Distribution Comparison */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-slate-100 flex items-center gap-2">
              <Radio className="w-5 h-5" /> 분배 비율 비교
            </CardTitle>
            <CardDescription className="text-slate-400">
              목표 (Σ) vs 실제 분배
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-6" data-testid="distribution-comparison">
              {/* Public */}
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-slate-300">공공 (V_pub)</span>
                  <span className="text-slate-400">
                    목표: {((distribution?.target?.[0] || 0) * 100).toFixed(1)}% / 
                    실제: {((distribution?.actual?.[0] || 0) * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="h-4 bg-slate-700 rounded-full overflow-hidden relative">
                  <div 
                    className="h-full bg-blue-500 rounded-full absolute"
                    style={{ width: `${(distribution?.target?.[0] || 0) * 100}%`, opacity: 0.5 }}
                  />
                  <div 
                    className="h-full bg-blue-400 rounded-full absolute"
                    style={{ width: `${(distribution?.actual?.[0] || 0) * 100}%` }}
                  />
                </div>
              </div>

              {/* Productive */}
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-slate-300">생산 (V_pro)</span>
                  <span className="text-slate-400">
                    목표: {((distribution?.target?.[1] || 0) * 100).toFixed(1)}% / 
                    실제: {((distribution?.actual?.[1] || 0) * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="h-4 bg-slate-700 rounded-full overflow-hidden relative">
                  <div 
                    className="h-full bg-emerald-500 rounded-full absolute"
                    style={{ width: `${(distribution?.target?.[1] || 0) * 100}%`, opacity: 0.5 }}
                  />
                  <div 
                    className="h-full bg-emerald-400 rounded-full absolute"
                    style={{ width: `${(distribution?.actual?.[1] || 0) * 100}%` }}
                  />
                </div>
              </div>

              {/* Individual */}
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-slate-300">개인 (V_ind)</span>
                  <span className="text-slate-400">
                    목표: {((distribution?.target?.[2] || 0) * 100).toFixed(1)}% / 
                    실제: {((distribution?.actual?.[2] || 0) * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="h-4 bg-slate-700 rounded-full overflow-hidden relative">
                  <div 
                    className="h-full bg-amber-500 rounded-full absolute"
                    style={{ width: `${(distribution?.target?.[2] || 0) * 100}%`, opacity: 0.5 }}
                  />
                  <div 
                    className="h-full bg-amber-400 rounded-full absolute"
                    style={{ width: `${(distribution?.actual?.[2] || 0) * 100}%` }}
                  />
                </div>
              </div>

              {/* Status */}
              <div className={`p-3 rounded-lg flex items-center gap-3 ${distribution?.is_valid ? 'bg-emerald-900/30 border border-emerald-600' : 'bg-amber-900/30 border border-amber-600'}`}>
                {distribution?.is_valid ? (
                  <>
                    <CheckCircle className="w-5 h-5 text-emerald-400" />
                    <span className="text-emerald-300">모든 경계 조건 충족</span>
                  </>
                ) : (
                  <>
                    <AlertTriangle className="w-5 h-5 text-amber-400" />
                    <span className="text-amber-300">
                      {distribution?.violations?.length || 0}건의 경계 조건 위반
                    </span>
                  </>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Deviation Chart */}
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader>
          <CardTitle className="text-slate-100 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5" /> 편차 분석
          </CardTitle>
          <CardDescription className="text-slate-400">
            목표 대비 실제 분배의 편차 (낮을수록 좋음)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4" data-testid="deviation-analysis">
            {['공공', '생산', '개인'].map((name, idx) => {
              const deviation = (current.deviation?.[idx] || 0) * 100;
              const color = deviation < 3 ? 'emerald' : deviation < 6 ? 'amber' : 'rose';
              return (
                <div key={name} className="bg-slate-900/50 rounded-lg p-4 text-center">
                  <p className="text-slate-400 text-sm mb-2">{name} 편차</p>
                  <p className={`text-2xl font-bold text-${color}-400`}>
                    {deviation.toFixed(2)}%
                  </p>
                  <Badge variant={deviation < 3 ? 'default' : deviation < 6 ? 'secondary' : 'destructive'} className="mt-2">
                    {deviation < 3 ? '최적' : deviation < 6 ? '양호' : '조정필요'}
                  </Badge>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default MonitoringTab;
