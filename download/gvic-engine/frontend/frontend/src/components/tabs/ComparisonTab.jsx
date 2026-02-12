import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { 
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, 
  CartesianGrid, Tooltip as RechartsTooltip, Legend, BarChart, Bar, Cell
} from 'recharts';
import { 
  GitCompare, Play, RefreshCw, TrendingUp, TrendingDown, 
  Minus, AlertTriangle, BarChart3
} from 'lucide-react';
import { MetricCard } from "@/components/MetricCard";
import { api } from "@/lib/api";

const TREND_ICONS = {
  increasing: TrendingUp,
  decreasing: TrendingDown,
  stable: Minus
};

const TREND_COLORS = {
  increasing: "text-emerald-400",
  decreasing: "text-rose-400",
  stable: "text-slate-400"
};

export const ComparisonTab = () => {
  const [limit, setLimit] = useState(10);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

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

  // 차트 데이터 준비
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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <GitCompare className="w-6 h-6 text-cyan-400" /> 처리 결과 비교 분석
          </h2>
          <p className="text-slate-400 text-sm">과거 처리 결과의 통계 및 트렌드 분석</p>
        </div>
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
            {loading ? (
              <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <Play className="w-4 h-4 mr-2" />
            )}
            분석 실행
          </Button>
        </div>
      </div>

      {result?.success && (
        <>
          {/* Summary Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <MetricCard 
              icon={BarChart3} 
              label="분석 레코드" 
              value={result.records_count}
              variant="cyan"
            />
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

          {/* Statistics Cards */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Asset Value Stats */}
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="text-slate-100 text-sm">자산 가치 통계</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3" data-testid="asset-stats">
                  <div className="flex justify-between">
                    <span className="text-slate-400">최소</span>
                    <span className="text-slate-100 font-medium">{stats?.asset_value?.min?.toFixed(3) || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">최대</span>
                    <span className="text-slate-100 font-medium">{stats?.asset_value?.max?.toFixed(3) || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">평균</span>
                    <span className="text-cyan-400 font-bold">{stats?.asset_value?.avg?.toFixed(3) || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">표준편차</span>
                    <span className="text-slate-100 font-medium">{stats?.asset_value?.std?.toFixed(4) || 0}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Balance Score Stats */}
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="text-slate-100 text-sm">균형 점수 통계</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3" data-testid="balance-stats">
                  <div className="flex justify-between">
                    <span className="text-slate-400">최소</span>
                    <span className="text-slate-100 font-medium">{((stats?.balance_score?.min || 0) * 100).toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">최대</span>
                    <span className="text-slate-100 font-medium">{((stats?.balance_score?.max || 0) * 100).toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">평균</span>
                    <span className="text-emerald-400 font-bold">{((stats?.balance_score?.avg || 0) * 100).toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">표준편차</span>
                    <span className="text-slate-100 font-medium">{((stats?.balance_score?.std || 0) * 100).toFixed(2)}%</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Distribution Stats */}
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="text-slate-100 text-sm">분배 비율 통계 (평균)</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3" data-testid="distribution-stats">
                  <div className="flex justify-between items-center">
                    <span className="text-blue-400">공공</span>
                    <div className="flex items-center gap-2">
                      <div className="w-24 h-2 bg-slate-700 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-blue-500 rounded-full"
                          style={{ width: `${(stats?.distribution?.public?.avg || 0) * 100}%` }}
                        />
                      </div>
                      <span className="text-slate-100 w-14 text-right">{((stats?.distribution?.public?.avg || 0) * 100).toFixed(1)}%</span>
                    </div>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-emerald-400">생산</span>
                    <div className="flex items-center gap-2">
                      <div className="w-24 h-2 bg-slate-700 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-emerald-500 rounded-full"
                          style={{ width: `${(stats?.distribution?.productive?.avg || 0) * 100}%` }}
                        />
                      </div>
                      <span className="text-slate-100 w-14 text-right">{((stats?.distribution?.productive?.avg || 0) * 100).toFixed(1)}%</span>
                    </div>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-amber-400">개인</span>
                    <div className="flex items-center gap-2">
                      <div className="w-24 h-2 bg-slate-700 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-amber-500 rounded-full"
                          style={{ width: `${(stats?.distribution?.individual?.avg || 0) * 100}%` }}
                        />
                      </div>
                      <span className="text-slate-100 w-14 text-right">{((stats?.distribution?.individual?.avg || 0) * 100).toFixed(1)}%</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Trend Chart */}
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="text-slate-100 text-sm">자산 가치 & 균형 점수 추이</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64" data-testid="trend-chart">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                      <XAxis dataKey="name" stroke="#94a3b8" fontSize={10} />
                      <YAxis yAxisId="left" stroke="#94a3b8" fontSize={10} />
                      <YAxis yAxisId="right" orientation="right" stroke="#94a3b8" fontSize={10} domain={[0, 100]} />
                      <RechartsTooltip 
                        contentStyle={{ background: '#1e293b', border: '1px solid #475569', borderRadius: '8px' }}
                      />
                      <Legend />
                      <Line yAxisId="left" type="monotone" dataKey="asset" stroke="#22d3ee" strokeWidth={2} name="자산 가치" />
                      <Line yAxisId="right" type="monotone" dataKey="balance" stroke="#10b981" strokeWidth={2} name="균형 (%)" />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            {/* Distribution Chart */}
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="text-slate-100 text-sm">분배 비율 비교 (최근 5건)</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64" data-testid="distribution-chart">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={distributionData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                      <XAxis dataKey="name" stroke="#94a3b8" fontSize={10} />
                      <YAxis stroke="#94a3b8" fontSize={10} domain={[0, 100]} />
                      <RechartsTooltip 
                        contentStyle={{ background: '#1e293b', border: '1px solid #475569', borderRadius: '8px' }}
                        formatter={(value) => [`${value.toFixed(1)}%`]}
                      />
                      <Legend />
                      <Bar dataKey="public" fill="#3b82f6" name="공공 (%)" stackId="a" />
                      <Bar dataKey="productive" fill="#10b981" name="생산 (%)" stackId="a" />
                      <Bar dataKey="individual" fill="#f59e0b" name="개인 (%)" stackId="a" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Outliers */}
          {result.outliers && result.outliers.length > 0 && (
            <Card className="bg-slate-800/50 border-slate-700 border-amber-500/50">
              <CardHeader>
                <CardTitle className="text-slate-100 text-sm flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-amber-400" /> 이상치 감지
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3" data-testid="outliers-list">
                  {result.outliers.map((outlier, idx) => (
                    <div key={idx} className="bg-amber-900/20 border border-amber-600/50 rounded-lg p-3">
                      <div className="flex items-center justify-between mb-1">
                        <Badge variant="outline" className="text-amber-400">레코드 #{outlier.index + 1}</Badge>
                        <span className="text-amber-300 text-sm">{outlier.type}</span>
                      </div>
                      <p className="text-slate-300">값: {outlier.value.toFixed(3)}</p>
                      <p className="text-amber-400 text-xs">편차: {outlier.deviation.toFixed(2)}σ</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

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
                      <th className="text-right p-2">품질 점수</th>
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
                        <td className="p-2 text-right text-violet-400">{(item.quality_score * 100).toFixed(0)}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </ScrollArea>
            </CardContent>
          </Card>
        </>
      )}

      {result?.success === false && (
        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="py-12 text-center">
            <AlertTriangle className="w-12 h-12 text-amber-400 mx-auto mb-4" />
            <p className="text-slate-300">{result.message}</p>
            <p className="text-slate-500 text-sm mt-2">현재 레코드: {result.records_count}건</p>
          </CardContent>
        </Card>
      )}

      {!result && (
        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="py-12 text-center">
            <GitCompare className="w-12 h-12 text-slate-600 mx-auto mb-4" />
            <p className="text-slate-400">
              '분석 실행' 버튼을 클릭하여 처리 결과 비교 분석을 시작하세요
            </p>
            <p className="text-slate-500 text-sm mt-2">
              통계, 트렌드, 이상치 분석 제공
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default ComparisonTab;
