import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { 
  PieChart, Pie, Cell, ResponsiveContainer, 
  RadialBarChart, RadialBar, Tooltip as RechartsTooltip,
  AreaChart, Area, XAxis, YAxis, CartesianGrid
} from 'recharts';
import { 
  Activity, CheckCircle, AlertTriangle, Zap, 
  Shield, BarChart3, TrendingUp, PieChart as PieChartIcon,
  FileDown, RefreshCw, Database, Clock, ArrowRight,
  Upload, Brain, Cpu, Package, Coins
} from 'lucide-react';
import { MetricCard } from "@/components/MetricCard";
import { api } from "@/lib/api";
import axios from "axios";

const API_URL = process.env.REACT_APP_BACKEND_URL;

export const DashboardTab = ({ dashboard, systemStatus }) => {
  const [generating, setGenerating] = useState(false);
  const [realStats, setRealStats] = useState(null);
  const [pipelineStats, setPipelineStats] = useState(null);
  const [loading, setLoading] = useState(false);

  // 실제 통계 로드
  const loadRealStats = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      const [statsRes, pipelineRes] = await Promise.all([
        axios.get(`${API_URL}/api/dashboard/realstats`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        axios.get(`${API_URL}/api/pipeline/stats`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
      ]);
      setRealStats(statsRes.data);
      setPipelineStats(pipelineRes.data);
    } catch (error) {
      console.error("Failed to load stats:", error);
    }
  }, []);

  useEffect(() => {
    loadRealStats();
    const interval = setInterval(loadRealStats, 5000);
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

      {/* 파이프라인 모니터링 */}
      {pipelineStats && (
        <Card className="bg-gradient-to-r from-slate-800/80 to-slate-900/80 border-slate-700">
          <CardHeader className="pb-2">
            <CardTitle className="text-slate-100 flex items-center gap-2">
              <Activity className="w-5 h-5 text-blue-400" />
              파이프라인 모니터링
            </CardTitle>
          </CardHeader>
          <CardContent>
            {/* 파이프라인 플로우 */}
            <div className="flex items-center justify-between mb-4 py-3 px-4 bg-slate-900/50 rounded-lg overflow-x-auto">
              <div className="flex items-center gap-2 text-xs">
                <div className="flex flex-col items-center">
                  <div className="w-10 h-10 rounded-lg bg-blue-600 flex items-center justify-center">
                    <Upload className="w-5 h-5 text-white" />
                  </div>
                  <span className="text-slate-400 mt-1">입력</span>
                  <span className="text-blue-400 font-bold">{pipelineStats.stage_counts?.j_input || 0}</span>
                </div>
                <ArrowRight className="w-4 h-4 text-slate-600" />
                <div className="flex flex-col items-center">
                  <div className="w-10 h-10 rounded-lg bg-violet-600 flex items-center justify-center">
                    <Brain className="w-5 h-5 text-white" />
                  </div>
                  <span className="text-slate-400 mt-1">평가</span>
                  <span className="text-violet-400 font-bold">{pipelineStats.stage_counts?.ll_evaluate || 0}</span>
                </div>
                <ArrowRight className="w-4 h-4 text-slate-600" />
                <div className="flex flex-col items-center">
                  <div className="w-10 h-10 rounded-lg bg-purple-600 flex items-center justify-center">
                    <Cpu className="w-5 h-5 text-white" />
                  </div>
                  <span className="text-slate-400 mt-1">코어</span>
                  <span className="text-purple-400 font-bold">{pipelineStats.stage_counts?.h_core || 0}</span>
                </div>
                <ArrowRight className="w-4 h-4 text-slate-600" />
                <div className="flex flex-col items-center">
                  <div className="w-10 h-10 rounded-lg bg-emerald-600 flex items-center justify-center">
                    <Package className="w-5 h-5 text-white" />
                  </div>
                  <span className="text-slate-400 mt-1">자산화</span>
                  <span className="text-emerald-400 font-bold">{pipelineStats.stage_counts?.asset_process || 0}</span>
                </div>
                <ArrowRight className="w-4 h-4 text-slate-600" />
                <div className="flex flex-col items-center">
                  <div className="w-10 h-10 rounded-lg bg-amber-600 flex items-center justify-center">
                    <Coins className="w-5 h-5 text-white" />
                  </div>
                  <span className="text-slate-400 mt-1">모듈화</span>
                  <span className="text-amber-400 font-bold">{pipelineStats.stage_counts?.module || 0}</span>
                </div>
                <ArrowRight className="w-4 h-4 text-slate-600" />
                <div className="flex flex-col items-center">
                  <div className="w-10 h-10 rounded-lg bg-green-600 flex items-center justify-center">
                    <CheckCircle className="w-5 h-5 text-white" />
                  </div>
                  <span className="text-slate-400 mt-1">완료</span>
                  <span className="text-green-400 font-bold">{pipelineStats.stage_counts?.completed || 0}</span>
                </div>
              </div>
            </div>
            
            {/* 통계 카드 */}
            <div className="grid grid-cols-4 gap-3">
              <div className="bg-slate-800 rounded-lg p-3 text-center">
                <p className="text-2xl font-bold text-white">{pipelineStats.total_signals || 0}</p>
                <p className="text-slate-400 text-xs">총 시그널</p>
              </div>
              <div className="bg-blue-900/30 rounded-lg p-3 text-center border border-blue-700">
                <p className="text-2xl font-bold text-blue-400">{pipelineStats.category_counts?.wanted || 0}</p>
                <p className="text-slate-400 text-xs">원하는 것</p>
              </div>
              <div className="bg-amber-900/30 rounded-lg p-3 text-center border border-amber-700">
                <p className="text-2xl font-bold text-amber-400">{pipelineStats.category_counts?.unwanted || 0}</p>
                <p className="text-slate-400 text-xs">자산화 대상</p>
              </div>
              <div className="bg-slate-700/50 rounded-lg p-3 text-center">
                <p className="text-2xl font-bold text-slate-400">{pipelineStats.category_counts?.null || 0}</p>
                <p className="text-slate-400 text-xs">Null</p>
              </div>
            </div>

            {/* 최근 시그널 */}
            {pipelineStats.recent_signals?.length > 0 && (
              <div className="mt-4">
                <p className="text-slate-400 text-xs mb-2">최근 처리 이력</p>
                <ScrollArea className="h-[140px]">
                  <div className="space-y-2">
                    {pipelineStats.recent_signals.slice(0, 5).map((sig) => (
                      <div key={sig.signal_id} className="flex items-center justify-between bg-slate-900/50 rounded p-2 text-xs">
                        <div className="flex items-center gap-2">
                          <Badge variant="outline" className={`
                            ${sig.category === 'wanted' ? 'text-blue-400 border-blue-600' : 
                              sig.category === 'unwanted' ? 'text-amber-400 border-amber-600' : 
                              'text-slate-400 border-slate-600'}
                          `}>
                            {sig.category === 'wanted' ? '분석' : sig.category === 'unwanted' ? '자산화' : 'null'}
                          </Badge>
                          <span className="text-slate-300 font-mono">{sig.signal_id?.slice(4, 16)}...</span>
                          {sig.metadata?.analysis_type && (
                            <Badge className={`text-[10px] px-1.5 ${
                              sig.metadata.analysis_type === 'code' ? 'bg-green-700' :
                              sig.metadata.analysis_type === 'patent_idea' ? 'bg-amber-700' : 'bg-blue-700'
                            }`}>
                              {sig.metadata.analysis_type === 'code' ? '코드' :
                               sig.metadata.analysis_type === 'patent_idea' ? '아이디어' : '일반'}
                            </Badge>
                          )}
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge className={`
                            ${sig.status === 'completed' ? 'bg-green-600' : 
                              sig.status === 'processing' ? 'bg-blue-600' : 
                              sig.status === 'failed' ? 'bg-red-600' : 'bg-slate-600'}
                          `}>
                            {sig.status === 'completed' ? '완료' : sig.status}
                          </Badge>
                          <span className="text-slate-500">{sig.type === 'text' ? '텍스트' : sig.type === 'file' ? '파일' : sig.type}</span>
                          {sig.created_at && (
                            <span className="text-slate-600 text-[10px]">
                              {new Date(sig.created_at).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })}
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </div>
            )}
          </CardContent>
        </Card>
      )}

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
          value={`${successRate.toFixed(1)}%`}
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
    </div>
  );
};

