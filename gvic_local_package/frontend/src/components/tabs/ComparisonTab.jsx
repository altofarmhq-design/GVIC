import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, 
  CartesianGrid, Tooltip as RechartsTooltip, Legend, BarChart, Bar, Cell, PieChart, Pie
} from 'recharts';
import { 
  GitCompare, Play, RefreshCw, TrendingUp, TrendingDown, 
  Minus, AlertTriangle, BarChart3, Globe, Database, FileText
} from 'lucide-react';
import { MetricCard } from "@/components/MetricCard";
import { api } from "@/lib/api";

const TREND_ICONS = {
  increasing: TrendingUp,
  decreasing: TrendingDown,
  stable: Minus
};

const SENTIMENT_COLORS = {
  positive: "#22c55e",
  neutral: "#94a3b8",
  negative: "#ef4444"
};

export const ComparisonTab = () => {
  const [limit, setLimit] = useState(10);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState("processing");
  
  // DataHub 연동: URL 분석 세션 비교 데이터
  const [hubComparison, setHubComparison] = useState(null);
  const [hubLoading, setHubLoading] = useState(false);

  // DataHub 비교 데이터 불러오기
  const fetchHubComparison = useCallback(async () => {
    setHubLoading(true);
    try {
      const response = await api.getHubComparison();
      setHubComparison(response.data);
    } catch (error) {
      console.error("Hub comparison fetch error:", error);
    }
    setHubLoading(false);
  }, []);

  useEffect(() => {
    fetchHubComparison();
  }, [fetchHubComparison]);

  const handleAnalyze = async () => {
    setLoading(true);
    try {
      const response = await api.analyzeComparison({ limit });
      setResult(response.data);
    } catch (error) {
      console.error("Analyze error:", error);
      alert("분석 중 오류가 발생했습니다.");
    }
    setLoading(false);
  };

  // 처리 이력 차트 데이터 준비
  const chartData = result?.comparison_data?.map((item, idx) => ({
    name: `#${idx + 1}`,
    asset: item.asset_value,
    balance: item.balance_score * 100,
    quality: item.quality_score * 100,
    input: item.input_value
  })).reverse() || [];

  const distributionData = result?.comparison_data?.slice(0, 5).map((item, idx) => {
    const dist = item.distribution;
    const total = (dist?.public || 0) + (dist?.productive || 0) + (dist?.individual || 0);
    return {
      name: `#${idx + 1}`,
      public: total > 0 ? (dist?.public / total * 100) : 0,
      productive: total > 0 ? (dist?.productive / total * 100) : 0,
      individual: total > 0 ? (dist?.individual / total * 100) : 0
    };
  }).reverse() || [];

  const stats = result?.statistics;

  // DataHub 세션 차트 데이터 준비
  const hubChartData = hubComparison?.comparisons?.map((item, idx) => ({
    name: item.product_name?.substring(0, 12) || `세션${idx + 1}`,
    positive: (item.metrics?.positive_ratio || 0) * 100,
    fairness: (item.metrics?.fairness_index || 0) * 100,
    balance: (item.metrics?.balance_index || 0) * 100,
    records: item.metrics?.total_records || 0
  })) || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <GitCompare className="w-6 h-6 text-cyan-400" /> 비교 분석
          </h2>
          <p className="text-slate-400 text-sm">처리 결과 및 URL 분석 세션 비교</p>
        </div>
        <Button 
          variant="outline" 
          size="sm" 
          onClick={fetchHubComparison}
          disabled={hubLoading}
          className="border-slate-600"
        >
          <RefreshCw className={`w-4 h-4 mr-1 ${hubLoading ? 'animate-spin' : ''}`} /> 새로고침
        </Button>
      </div>

      {/* 탭 선택 */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="bg-slate-800 border border-slate-700">
          <TabsTrigger value="processing" className="data-[state=active]:bg-slate-700">
            <Database className="w-4 h-4 mr-2" /> 처리 이력 비교
          </TabsTrigger>
          <TabsTrigger value="sessions" className="data-[state=active]:bg-slate-700">
            <Globe className="w-4 h-4 mr-2" /> URL 분석 세션 비교
          </TabsTrigger>
        </TabsList>

        {/* 처리 이력 비교 탭 */}
        <TabsContent value="processing" className="space-y-6 mt-4">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="text-slate-400 text-sm">분석 개수:</span>
              <Slider
                value={[limit]}
                onValueChange={([v]) => setLimit(v)}
                min={5}
                max={50}
                step={5}
                className="w-32 [&_[role=slider]]:bg-cyan-500"
              />
              <span className="text-cyan-400 w-8">{limit}</span>
            </div>
            <Button 
              onClick={handleAnalyze} 
              disabled={loading}
              className="bg-cyan-600 hover:bg-cyan-500"
              data-testid="comparison-analyze-button"
            >
              {loading ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <Play className="w-4 h-4 mr-2" />}
              분석 실행
            </Button>
          </div>

          {result?.success && (
            <>
              {/* Summary Stats */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <MetricCard icon={BarChart3} label="분석 레코드" value={result.records_count} variant="cyan" />
                <MetricCard 
                  icon={TREND_ICONS[result.trend?.asset_value] || Minus} 
                  label="자산 가치 트렌드" 
                  value={result.trend?.asset_value === 'increasing' ? '상승' : result.trend?.asset_value === 'decreasing' ? '하락' : '안정'}
                  variant={result.trend?.asset_value === 'increasing' ? 'teal' : result.trend?.asset_value === 'decreasing' ? 'rose' : 'purple'}
                />
                <MetricCard 
                  icon={TREND_ICONS[result.trend?.balance_score] || Minus} 
                  label="균형 점수 트렌드" 
                  value={result.trend?.balance_score === 'increasing' ? '상승' : result.trend?.balance_score === 'decreasing' ? '하락' : '안정'}
                  variant={result.trend?.balance_score === 'increasing' ? 'teal' : result.trend?.balance_score === 'decreasing' ? 'rose' : 'purple'}
                />
                <MetricCard 
                  icon={AlertTriangle} 
                  label="이상치" 
                  value={result.outliers?.length || 0}
                  variant={result.outliers?.length > 0 ? 'amber' : 'teal'}
                />
              </div>

              {/* Trend Chart */}
              <Card className="bg-slate-800/50 border-slate-700">
                <CardHeader>
                  <CardTitle className="text-slate-100 text-sm">자산 가치 & 균형 점수 추이</CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={250}>
                    <LineChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                      <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} />
                      <YAxis yAxisId="left" stroke="#94a3b8" fontSize={12} />
                      <YAxis yAxisId="right" orientation="right" stroke="#94a3b8" fontSize={12} domain={[0, 100]} />
                      <RechartsTooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }} />
                      <Legend />
                      <Line yAxisId="left" type="monotone" dataKey="asset" name="자산 가치" stroke="#06b6d4" strokeWidth={2} dot={{ fill: '#06b6d4' }} />
                      <Line yAxisId="right" type="monotone" dataKey="balance" name="균형 점수 (%)" stroke="#10b981" strokeWidth={2} dot={{ fill: '#10b981' }} />
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              {/* Distribution Chart */}
              <Card className="bg-slate-800/50 border-slate-700">
                <CardHeader>
                  <CardTitle className="text-slate-100 text-sm">최근 5건 분배 비교</CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={distributionData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                      <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} />
                      <YAxis stroke="#94a3b8" fontSize={12} domain={[0, 100]} />
                      <RechartsTooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }} />
                      <Legend />
                      <Bar dataKey="public" name="공공" stackId="a" fill="#3b82f6" />
                      <Bar dataKey="productive" name="생산" stackId="a" fill="#10b981" />
                      <Bar dataKey="individual" name="개인" stackId="a" fill="#f59e0b" />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              {/* Data Table */}
              <Card className="bg-slate-800/50 border-slate-700">
                <CardHeader>
                  <CardTitle className="text-slate-100 text-sm">상세 데이터</CardTitle>
                </CardHeader>
                <CardContent>
                  <ScrollArea className="h-64" data-testid="data-table">
                    <table className="w-full text-sm">
                      <thead className="text-slate-400 border-b border-slate-700">
                        <tr>
                          <th className="text-left p-2">#</th>
                          <th className="text-left p-2">시간</th>
                          <th className="text-right p-2">입력값</th>
                          <th className="text-right p-2">자산 가치</th>
                          <th className="text-right p-2">균형 점수</th>
                        </tr>
                      </thead>
                      <tbody>
                        {result.comparison_data?.map((item, idx) => (
                          <tr key={idx} className="border-b border-slate-800 hover:bg-slate-800/50">
                            <td className="p-2 text-slate-500">{idx + 1}</td>
                            <td className="p-2 text-slate-300">{item.timestamp?.slice(0, 16).replace('T', ' ')}</td>
                            <td className="p-2 text-right text-slate-300">{item.input_value}</td>
                            <td className="p-2 text-right text-cyan-400 font-medium">{item.asset_value?.toFixed(3)}</td>
                            <td className="p-2 text-right text-emerald-400">{(item.balance_score * 100).toFixed(1)}%</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </ScrollArea>
                </CardContent>
              </Card>
            </>
          )}

          {!result && (
            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="py-12 text-center">
                <GitCompare className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                <p className="text-slate-400">'분석 실행' 버튼을 클릭하여 처리 결과 비교 분석을 시작하세요</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* URL 분석 세션 비교 탭 (DataHub 연동) */}
        <TabsContent value="sessions" className="space-y-6 mt-4">
          {hubComparison?.comparisons?.length > 0 ? (
            <>
              {/* 요약 통계 */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <MetricCard 
                  icon={FileText} 
                  label="총 분석 세션" 
                  value={hubComparison.total_sessions || 0} 
                  variant="cyan" 
                />
                <MetricCard 
                  icon={TrendingUp} 
                  label="평균 긍정률" 
                  value={`${((hubComparison.average_metrics?.positive_ratio || 0) * 100).toFixed(1)}%`}
                  variant="teal" 
                />
                <MetricCard 
                  icon={BarChart3} 
                  label="평균 공정성" 
                  value={`${((hubComparison.average_metrics?.fairness_index || 0) * 100).toFixed(1)}%`}
                  variant="purple" 
                />
                <MetricCard 
                  icon={Database} 
                  label="총 분석 건수" 
                  value={hubComparison.comparisons?.reduce((acc, s) => acc + (s.metrics?.total_records || 0), 0) || 0}
                  variant="amber" 
                />
              </div>

              {/* 세션별 비교 차트 */}
              <Card className="bg-slate-800/50 border-slate-700">
                <CardHeader>
                  <CardTitle className="text-slate-100 text-sm">세션별 지표 비교</CardTitle>
                  <CardDescription>긍정률, 공정성, 균형 지수 비교</CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={hubChartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                      <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} angle={-20} textAnchor="end" height={60} />
                      <YAxis stroke="#94a3b8" fontSize={12} domain={[0, 100]} />
                      <RechartsTooltip 
                        contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }} 
                        formatter={(value) => `${value.toFixed(1)}%`}
                      />
                      <Legend />
                      <Bar dataKey="positive" name="긍정률" fill="#22c55e" />
                      <Bar dataKey="fairness" name="공정성" fill="#8b5cf6" />
                      <Bar dataKey="balance" name="균형 지수" fill="#06b6d4" />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              {/* 세션 목록 */}
              <Card className="bg-slate-800/50 border-slate-700">
                <CardHeader>
                  <CardTitle className="text-slate-100 text-sm">분석 세션 목록</CardTitle>
                </CardHeader>
                <CardContent>
                  <ScrollArea className="h-80">
                    <div className="space-y-3">
                      {hubComparison.comparisons?.map((session, idx) => (
                        <div key={idx} className="p-4 bg-slate-900/50 rounded-lg border border-slate-700">
                          <div className="flex items-start justify-between mb-3">
                            <div>
                              <h4 className="text-slate-100 font-medium">{session.product_name || '분석 세션'}</h4>
                              <p className="text-slate-500 text-xs mt-1">
                                {session.analyzed_at ? new Date(session.analyzed_at).toLocaleString('ko-KR') : '-'}
                              </p>
                            </div>
                            <Badge variant="outline" className="text-cyan-400 border-cyan-400/50">
                              {session.metrics?.total_records || 0}건
                            </Badge>
                          </div>
                          <div className="grid grid-cols-3 gap-4 text-sm">
                            <div>
                              <span className="text-slate-500">긍정률</span>
                              <p className="text-emerald-400 font-medium">{((session.metrics?.positive_ratio || 0) * 100).toFixed(1)}%</p>
                            </div>
                            <div>
                              <span className="text-slate-500">공정성</span>
                              <p className="text-violet-400 font-medium">{((session.metrics?.fairness_index || 0) * 100).toFixed(1)}%</p>
                            </div>
                            <div>
                              <span className="text-slate-500">균형 지수</span>
                              <p className="text-cyan-400 font-medium">{((session.metrics?.balance_index || 0) * 100).toFixed(1)}%</p>
                            </div>
                          </div>
                          {session.source_url && (
                            <p className="text-slate-600 text-xs mt-2 truncate">{session.source_url}</p>
                          )}
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                </CardContent>
              </Card>
            </>
          ) : (
            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="py-12 text-center">
                <Globe className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                <p className="text-slate-400">아직 URL 분석 세션이 없습니다</p>
                <p className="text-slate-500 text-sm mt-2">
                  '분석' 탭에서 URL 분석을 실행하면 여기서 비교할 수 있습니다
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default ComparisonTab;
