import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { 
  PieChart, Pie, Cell, ResponsiveContainer, 
  RadialBarChart, RadialBar, Tooltip as RechartsTooltip
} from 'recharts';
import { 
  Activity, CheckCircle, AlertTriangle, Zap, 
  Shield, BarChart3, TrendingUp, PieChart as PieChartIcon,
  FileDown, RefreshCw
} from 'lucide-react';
import { MetricCard } from "@/components/MetricCard";
import { api } from "@/lib/api";

export const DashboardTab = ({ dashboard, systemStatus }) => {
  const [generating, setGenerating] = useState(false);

  const pieData = dashboard?.charts?.distribution?.data || [
    { name: '공공', value: 33, color: '#3b82f6' },
    { name: '생산', value: 34, color: '#10b981' },
    { name: '개인', value: 33, color: '#f59e0b' }
  ];

  const balanceScore = dashboard?.balance_score || 0.85;
  const gaugeData = [{ name: '균형', value: balanceScore * 100, fill: '#10b981' }];
  const sigma = dashboard?.sigma || [0.33, 0.34, 0.33];

  // 모듈 상태
  const moduleStats = systemStatus?.modules || {};

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
          label="비적합 감지" 
          value={moduleStats?.nonconform?.nonconform_count || 0}
          subValue={`비율: ${((moduleStats?.nonconform?.nonconform_rate || 0) * 100).toFixed(1)}%`}
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
              <PieChartIcon className="w-5 h-5" /> 분배 비율 (Σ)
            </CardTitle>
            <CardDescription className="text-slate-400">
              특허 6: 가중 분배 모델 기반
            </CardDescription>
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
              <CheckCircle className="w-5 h-5" /> 균형 상태 (Ω)
            </CardTitle>
            <CardDescription className="text-slate-400">
              특허 1: 경계 조건 기반 수렴 제어
            </CardDescription>
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
      </div>
    </div>
  );
};

export default DashboardTab;
