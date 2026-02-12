import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { 
  ResponsiveContainer, ScatterChart, Scatter, XAxis, YAxis, 
  CartesianGrid, Tooltip as RechartsTooltip, ZAxis, Cell
} from 'recharts';
import { 
  Target, Play, RefreshCw, Check, Trophy, 
  TrendingUp, Shield, Sparkles
} from 'lucide-react';
import { MetricCard } from "@/components/MetricCard";
import { api } from "@/lib/api";

const OBJECTIVE_ICONS = {
  balance: Target,
  public_value: Shield,
  efficiency: TrendingUp,
  risk: Sparkles
};

export const ParetoTab = ({ onUpdate }) => {
  const [config, setConfig] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [applying, setApplying] = useState(null);

  const fetchConfig = useCallback(async () => {
    try {
      const response = await api.getParetoConfig();
      setConfig(response.data);
    } catch (error) {
      console.error("Fetch config error:", error);
    }
  }, []);

  useEffect(() => {
    fetchConfig();
  }, [fetchConfig]);

  const handleOptimize = async () => {
    setLoading(true);
    try {
      const response = await api.runParetoOptimization();
      setResult(response.data);
    } catch (error) {
      console.error("Optimize error:", error);
      alert("최적화 중 오류가 발생했습니다.");
    }
    setLoading(false);
  };

  const handleApply = async (index) => {
    setApplying(index);
    try {
      await api.applyParetoSolution(index);
      alert("솔루션이 적용되었습니다.");
      if (onUpdate) onUpdate();
    } catch (error) {
      console.error("Apply error:", error);
      alert("적용 중 오류가 발생했습니다.");
    }
    setApplying(null);
  };

  // 산점도 데이터 준비
  const scatterData = result?.pareto_front?.map((sol, idx) => ({
    x: sol.scores.balance * 100,
    y: sol.scores.efficiency * 100,
    z: sol.weighted_score * 100,
    label: sol.label,
    index: idx,
    isBest: idx === 0
  })) || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <Target className="w-6 h-6 text-rose-400" /> 파레토 최적화
          </h2>
          <p className="text-slate-400 text-sm">다목적 최적화를 통한 최적 분배 비율 탐색</p>
        </div>
        <Button 
          onClick={handleOptimize} 
          disabled={loading}
          className="bg-rose-600 hover:bg-rose-500"
          data-testid="pareto-optimize-button"
        >
          {loading ? (
            <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
          ) : (
            <Play className="w-4 h-4 mr-2" />
          )}
          최적화 실행
        </Button>
      </div>

      {/* Objectives */}
      {config && (
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-slate-100 text-sm">최적화 목표</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4" data-testid="objectives-list">
              {config.objectives.map((obj, idx) => {
                const Icon = OBJECTIVE_ICONS[obj.name] || Target;
                return (
                  <div key={idx} className="bg-slate-900/50 rounded-lg p-3">
                    <div className="flex items-center gap-2 mb-2">
                      <Icon className="w-4 h-4 text-rose-400" />
                      <span className="text-slate-100 text-sm font-medium">{obj.description}</span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <Badge variant={obj.target === 'maximize' ? 'default' : 'secondary'}>
                        {obj.target === 'maximize' ? '최대화' : '최소화'}
                      </Badge>
                      <span className="text-slate-400">가중치: {obj.weight}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Results */}
      {result?.success && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Best Solution */}
          <Card className="bg-slate-800/50 border-slate-700 border-2 border-rose-500/50">
            <CardHeader>
              <CardTitle className="text-slate-100 flex items-center gap-2">
                <Trophy className="w-5 h-5 text-amber-400" /> 최적 솔루션
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {result.best_solution && (
                <>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-300">가중 점수</span>
                    <span className="text-2xl font-bold text-rose-400">
                      {(result.best_solution.weighted_score * 100).toFixed(1)}%
                    </span>
                  </div>
                  
                  <div className="space-y-2">
                    <p className="text-slate-400 text-sm">추천 시그마</p>
                    {['공공', '생산', '개인'].map((name, idx) => {
                      const value = result.best_solution.sigma[idx] * 100;
                      const colors = ['blue', 'emerald', 'amber'];
                      return (
                        <div key={name} className="flex items-center gap-2">
                          <span className={`text-${colors[idx]}-400 w-12`}>{name}</span>
                          <div className="flex-1 h-3 bg-slate-700 rounded-full overflow-hidden">
                            <div 
                              className={`h-full bg-${colors[idx]}-500 rounded-full`}
                              style={{ width: `${value}%` }}
                            />
                          </div>
                          <span className="text-slate-300 w-14 text-right">{value.toFixed(1)}%</span>
                        </div>
                      );
                    })}
                  </div>

                  <div className="grid grid-cols-2 gap-2 mt-4">
                    {Object.entries(result.best_solution.scores).map(([key, value]) => (
                      <div key={key} className="bg-slate-900/50 rounded p-2 text-center">
                        <p className="text-slate-500 text-xs capitalize">{key}</p>
                        <p className="text-slate-100 font-medium">
                          {(value * 100).toFixed(1)}%
                        </p>
                      </div>
                    ))}
                  </div>

                  <Button 
                    onClick={() => handleApply(0)}
                    disabled={applying === 0}
                    className="w-full bg-rose-600 hover:bg-rose-500 mt-4"
                    data-testid="apply-best-solution"
                  >
                    {applying === 0 ? (
                      <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                    ) : (
                      <Check className="w-4 h-4 mr-2" />
                    )}
                    최적 솔루션 적용
                  </Button>
                </>
              )}
            </CardContent>
          </Card>

          {/* Pareto Front Chart */}
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader>
              <CardTitle className="text-slate-100 text-sm">파레토 프론트</CardTitle>
              <CardDescription className="text-slate-400">
                균형 vs 효율성 (점 크기 = 가중 점수)
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-64" data-testid="pareto-chart">
                <ResponsiveContainer width="100%" height="100%">
                  <ScatterChart>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis 
                      type="number" 
                      dataKey="x" 
                      name="균형" 
                      stroke="#94a3b8" 
                      fontSize={10}
                      domain={[0, 100]}
                      label={{ value: '균형 (%)', position: 'bottom', fill: '#94a3b8', fontSize: 10 }}
                    />
                    <YAxis 
                      type="number" 
                      dataKey="y" 
                      name="효율성" 
                      stroke="#94a3b8" 
                      fontSize={10}
                      domain={[0, 100]}
                      label={{ value: '효율성 (%)', angle: -90, position: 'left', fill: '#94a3b8', fontSize: 10 }}
                    />
                    <ZAxis type="number" dataKey="z" range={[50, 400]} />
                    <RechartsTooltip 
                      contentStyle={{ background: '#1e293b', border: '1px solid #475569', borderRadius: '8px' }}
                      formatter={(value, name) => [`${value.toFixed(1)}%`, name]}
                    />
                    <Scatter name="솔루션" data={scatterData}>
                      {scatterData.map((entry, index) => (
                        <Cell 
                          key={`cell-${index}`} 
                          fill={entry.isBest ? '#f43f5e' : '#8b5cf6'} 
                        />
                      ))}
                    </Scatter>
                  </ScatterChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* All Pareto Solutions */}
      {result?.pareto_front && result.pareto_front.length > 0 && (
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-slate-100 text-sm">
              파레토 프론트 솔루션 ({result.pareto_front.length}개)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-64" data-testid="pareto-solutions">
              <div className="space-y-2">
                {result.pareto_front.map((sol, idx) => (
                  <div 
                    key={idx} 
                    className={`bg-slate-900/50 rounded-lg p-3 flex items-center justify-between ${idx === 0 ? 'ring-1 ring-rose-500' : ''}`}
                  >
                    <div className="flex items-center gap-4">
                      <div className="text-center w-8">
                        {idx === 0 ? (
                          <Trophy className="w-5 h-5 text-amber-400" />
                        ) : (
                          <span className="text-slate-500">#{idx + 1}</span>
                        )}
                      </div>
                      <div>
                        <p className="text-slate-100 font-medium">{sol.label}</p>
                        <p className="text-slate-500 text-xs">
                          σ: {sol.sigma.map(s => (s*100).toFixed(0)+'%').join(' / ')}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <p className="text-rose-400 font-bold">{(sol.weighted_score * 100).toFixed(1)}%</p>
                        <p className="text-slate-500 text-xs">가중 점수</p>
                      </div>
                      {idx > 0 && (
                        <Button 
                          size="sm" 
                          variant="outline"
                          onClick={() => handleApply(idx)}
                          disabled={applying === idx}
                        >
                          {applying === idx ? (
                            <RefreshCw className="w-4 h-4 animate-spin" />
                          ) : (
                            <Check className="w-4 h-4" />
                          )}
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      )}

      {/* Empty State */}
      {!result && (
        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="py-12 text-center">
            <Target className="w-12 h-12 text-slate-600 mx-auto mb-4" />
            <p className="text-slate-400">
              '최적화 실행' 버튼을 클릭하여 파레토 최적화를 시작하세요
            </p>
            <p className="text-slate-500 text-sm mt-2">
              다목적 최적화를 통해 최적의 분배 비율을 찾습니다
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default ParetoTab;
