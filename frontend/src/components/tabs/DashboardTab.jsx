import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { 
  PieChart, Pie, Cell, ResponsiveContainer, 
  RadialBarChart, RadialBar, Tooltip as RechartsTooltip,
  AreaChart, Area, XAxis, YAxis, CartesianGrid
} from 'recharts';
import { 
  Activity, CheckCircle, AlertTriangle, Zap, 
  Shield, BarChart3, TrendingUp, PieChart as PieChartIcon,
  FileDown, RefreshCw, Database, Clock
} from 'lucide-react';
import { MetricCard } from "@/components/MetricCard";
import { api } from "@/lib/api";
import axios from "axios";

const API_URL = process.env.REACT_APP_BACKEND_URL;

export const DashboardTab = ({ dashboard, systemStatus }) => {
  const [generating, setGenerating] = useState(false);
  const [realStats, setRealStats] = useState(null);
  const [loading, setLoading] = useState(false);

  // 실제 통계 로드
  const loadRealStats = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/api/dashboard/realstats`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setRealStats(response.data);
    } catch (error) {
      console.error("Failed to load real stats:", error);
    }
  }, []);

  useEffect(() => {
    loadRealStats();
    // 10초마다 업데이트
    const interval = setInterval(loadRealStats, 10000);
    return () => clearInterval(interval);
  }, [loadRealStats]);

  // 실제 데이터 또는 기본값
  const totalAnalyzed = realStats?.realtime?.total_analyzed || 0;
  const totalAssets = realStats?.assets?.total || 0;
  const successRate = realStats?.realtime?.success_rate || 0;
  const lastHourCount = realStats?.realtime?.last_hour_count || 0;
  const status = realStats?.realtime?.status || "idle";

  // 감성 분포 (실제 데이터)
  const sentimentData = realStats?.by_sentiment || {};
  const pieData = [
    { name: '긍정', value: sentimentData.positive || 0, color: '#10b981' },
    { name: '혼합', value: sentimentData.mixed || 0, color: '#8b5cf6' },
    { name: '중립', value: sentimentData.neutral || 0, color: '#3b82f6' },
    { name: '부정', value: sentimentData.negative || 0, color: '#ef4444' }
  ].filter(d => d.value > 0);

  // 차트 데이터
  const chartData = realStats?.chart_data || [];

  const balanceScore = dashboard?.balance_score || 0.85;
  const gaugeData = [{ name: '균형', value: balanceScore * 100, fill: '#10b981' }];

  // 상태 색상
  const statusColors = {
    active: 'bg-emerald-500',
    normal: 'bg-blue-500',
    low: 'bg-yellow-500',
    idle: 'bg-slate-500'
  };

  const statusLabels = {
    active: '활발',
    normal: '정상',
    low: '저조',
    idle: '대기'
  };

  // PDF 리포트 다운로드
  const handleDownloadReport = async () => {
    setGenerating(true);
    try {
      const response = await api.generateReport({ include_history: true, limit: 20 });
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `gvic_report_${new Date().toISOString().slice(0,10)}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Report generation error:", error);
      alert("리포트 생성 중 오류가 발생했습니다.");
    }
    setGenerating(false);
  };

  return (
    <div className="space-y-6">
      {/* Header with Report Button */}
      <div className="flex justify-end">
        <Button 
          onClick={handleDownloadReport} 
          disabled={generating}
          className="bg-violet-600 hover:bg-violet-500"
          data-testid="download-report-button"
        >
          {generating ? (
            <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
          ) : (
            <FileDown className="w-4 h-4 mr-2" />
          )}
          PDF 리포트 다운로드
        </Button>
      </div>

      {/* Metrics Row - 실제 데이터 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4" data-testid="metrics-row">
        <MetricCard 
          icon={Activity} 
          label="총 분석 건수" 
          value={totalAnalyzed}
          variant="cyan"
        />
        <MetricCard 
          icon={Database} 
          label="자산화 건수" 
          value={totalAssets}
          variant="purple"
        />
        <MetricCard 
          icon={CheckCircle} 
          label="성공률" 
          value={`${(successRate * 100).toFixed(1)}%`}
          variant="teal"
        />
        <MetricCard 
          icon={Clock} 
          label="최근 1시간" 
          value={lastHourCount}
          subValue="처리량"
          variant="amber"
        />
        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Zap className="w-5 h-5 text-slate-400" />
                <span className="text-slate-400 text-sm">상태</span>
              </div>
              <Badge className={`${statusColors[status]} text-white`}>
                {statusLabels[status]}
              </Badge>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 감성 분포 Chart - 실제 데이터 */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-slate-100 flex items-center gap-2">
              <PieChartIcon className="w-5 h-5" /> 감성 분포
            </CardTitle>
            <CardDescription className="text-slate-400">
              실제 분석된 시그널의 감성 분포
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-64" data-testid="distribution-chart">
              {pieData.length > 0 ? (
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
              ) : (
                <div className="h-full flex items-center justify-center text-slate-500">
                  <div className="text-center">
                    <Database className="w-12 h-12 mx-auto mb-2 opacity-50" />
                    <p>분석 데이터가 없습니다</p>
                    <p className="text-sm">시그널분석 탭에서 분석을 시작하세요</p>
                  </div>
                </div>
              )}
            </div>
            <div className="flex justify-center gap-6 mt-4">
              {pieData.map((item, idx) => (
                <div key={idx} className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full" style={{ background: item.color }} />
                  <span className="text-slate-300 text-sm">{item.name}: {item.value}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* 실시간 처리 현황 차트 */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-slate-100 flex items-center gap-2">
              <TrendingUp className="w-5 h-5" /> 실시간 처리 현황
            </CardTitle>
            <CardDescription className="text-slate-400">
              최근 분석된 시그널 수 추이
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-64" data-testid="realtime-chart">
              {chartData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis dataKey="time" stroke="#94a3b8" tick={{ fontSize: 10 }} />
                    <YAxis stroke="#94a3b8" tick={{ fontSize: 10 }} />
                    <RechartsTooltip
                      contentStyle={{ background: '#1e293b', border: '1px solid #475569', borderRadius: '8px' }}
                    />
                    <Area 
                      type="monotone" 
                      dataKey="signals" 
                      stroke="#8b5cf6" 
                      fill="#8b5cf6" 
                      fillOpacity={0.3}
                      name="시그널 수"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-slate-500">
                  <div className="text-center">
                    <Activity className="w-12 h-12 mx-auto mb-2 opacity-50" />
                    <p>처리 기록이 없습니다</p>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 시그널 유형별 통계 */}
      {realStats?.by_signal_type && Object.keys(realStats.by_signal_type).length > 0 && (
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-slate-100 flex items-center gap-2">
              <BarChart3 className="w-5 h-5" /> 시그널 유형별 통계
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
              {Object.entries(realStats.by_signal_type).map(([type, count]) => (
                <div key={type} className="bg-slate-900/50 rounded-lg p-3 text-center">
                  <p className="text-2xl font-bold text-violet-400">{count}</p>
                  <p className="text-slate-400 text-xs">{type}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* 최근 처리 이력 */}
      {realStats?.recent_signals?.length > 0 && (
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-slate-100 flex items-center gap-2">
              <Clock className="w-5 h-5" /> 최근 처리 이력
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {realStats.recent_signals.slice(0, 5).map((signal, idx) => (
                <div key={idx} className="flex items-center justify-between bg-slate-900/50 rounded p-2">
                  <div className="flex items-center gap-3">
                    <span className="text-slate-500 text-xs">{signal.time_display}</span>
                    <Badge variant="outline" className="text-xs">{signal.signal_type_label}</Badge>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-slate-400 text-xs">{signal.signal_count}개 시그널</span>
                    <Badge className={`text-xs ${
                      signal.overall_sentiment === 'positive' ? 'bg-green-600' :
                      signal.overall_sentiment === 'negative' ? 'bg-red-600' :
                      signal.overall_sentiment === 'mixed' ? 'bg-purple-600' :
                      'bg-slate-600'
                    }`}>
                      {signal.overall_sentiment}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
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

      {/* Module Stats Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Convergence Stats */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader className="pb-3">
            <CardTitle className="text-slate-100 text-sm flex items-center gap-2">
              <Shield className="w-4 h-4 text-emerald-400" /> 수렴 제어 (특허1)
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-slate-400">총 처리</span>
              <span className="text-slate-200">{moduleStats?.convergence?.total_operations || 0}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-slate-400">유효 비율</span>
              <span className="text-emerald-400">{((moduleStats?.convergence?.valid_rate || 0) * 100).toFixed(1)}%</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-slate-400">위반 횟수</span>
              <span className="text-amber-400">{moduleStats?.convergence?.violation_count || 0}</span>
            </div>
          </CardContent>
        </Card>

        {/* Distributor Stats */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader className="pb-3">
            <CardTitle className="text-slate-100 text-sm flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-blue-400" /> 가중 분배 (특허6)
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-slate-400">분배 횟수</span>
              <span className="text-slate-200">{moduleStats?.distributor?.count || 0}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-slate-400">총 분배량</span>
              <span className="text-blue-400">{(moduleStats?.distributor?.total_distributed || 0).toFixed(2)}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-slate-400">현재 비율</span>
              <span className="text-slate-300 text-xs">
                {moduleStats?.distributor?.current_ratio?.map(r => (r*100).toFixed(0)+'%').join(' / ') || '-'}
              </span>
            </div>
          </CardContent>
        </Card>

        {/* Assetizer Stats */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader className="pb-3">
            <CardTitle className="text-slate-100 text-sm flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-violet-400" /> 자산화 (특허3)
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-slate-400">자산 생성</span>
              <span className="text-slate-200">{moduleStats?.assetizer?.count || 0}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-slate-400">총 가치</span>
              <span className="text-violet-400">{(moduleStats?.assetizer?.total_value || 0).toFixed(2)}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-slate-400">평균 가치</span>
              <span className="text-slate-300">{(moduleStats?.assetizer?.average || 0).toFixed(3)}</span>
            </div>
          </CardContent>
        </Card>

        {/* 통합 분석 통계 */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader className="pb-3">
            <CardTitle className="text-slate-100 text-sm flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-green-400" /> 통합 분석 통계
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-slate-400">분석 세션</span>
              <span className="text-slate-200">{dashboard?.metrics?.total_sessions || 0}회</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-slate-400">평균 긍정률</span>
              <span className="text-green-400">{((dashboard?.metrics?.avg_positive_ratio || 0) * 100).toFixed(1)}%</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-slate-400">평균 공정성</span>
              <span className="text-blue-400">{(dashboard?.metrics?.avg_fairness_index || 0).toFixed(3)}</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 최근 분석 세션 */}
      {dashboard?.recent_sessions?.length > 0 && (
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-slate-100 flex items-center gap-2">
              <Activity className="w-5 h-5 text-cyan-400" /> 최근 분석 세션
            </CardTitle>
            <CardDescription className="text-slate-400">
              URL/파일 분석을 통해 처리된 최근 데이터
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {dashboard.recent_sessions.slice(0, 5).map((session, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 bg-slate-700/30 rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className={`w-2 h-2 rounded-full ${session.status === 'completed' ? 'bg-green-500' : 'bg-yellow-500'}`} />
                    <div>
                      <div className="text-sm text-slate-200 truncate max-w-xs">
                        {session.product_name || session.source_url?.substring(0, 40) || '분석'}
                      </div>
                      <div className="text-xs text-slate-500">
                        {session.completed_at ? new Date(session.completed_at).toLocaleString('ko-KR') : '-'}
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm text-slate-300">{session.total_records?.toLocaleString() || 0}건</div>
                    <div className="text-xs text-green-400">
                      긍정 {((session.sentiment_positive_ratio || 0) * 100).toFixed(0)}%
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default DashboardTab;
