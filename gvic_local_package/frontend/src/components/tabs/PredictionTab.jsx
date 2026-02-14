import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { 
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, 
  CartesianGrid, Tooltip as RechartsTooltip, Legend, AreaChart, Area
} from 'recharts';
import { 
  TrendingUp, Brain, Play, RefreshCw, Check, 
  ArrowRight, AlertTriangle, Sparkles
} from 'lucide-react';
import { MetricCard } from "@/components/MetricCard";
import { api } from "@/lib/api";

export const PredictionTab = ({ onUpdate }) => {
  const [config, setConfig] = useState({
    window_size: 10,
    forecast_steps: 5,
    confidence_threshold: 0.7,
    auto_adjust: false
  });
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);
  const [applying, setApplying] = useState(false);

  const fetchConfig = useCallback(async () => {
    try {
      const response = await api.getPredictionConfig();
      setConfig(response.data);
    } catch (error) {
      console.error("Fetch config error:", error);
    }
  }, []);

  useEffect(() => {
    fetchConfig();
  }, [fetchConfig]);

  const handleAnalyze = async () => {
    setLoading(true);
    try {
      const response = await api.analyzePrediction();
      setPrediction(response.data);
    } catch (error) {
      console.error("Analyze error:", error);
      alert("분석 중 오류가 발생했습니다.");
    }
    setLoading(false);
  };

  const handleApply = async () => {
    setApplying(true);
    try {
      await api.applyPrediction();
      alert("예측 결과가 적용되었습니다.");
      if (onUpdate) onUpdate();
    } catch (error) {
      console.error("Apply error:", error);
      alert(error.response?.data?.detail || "적용 중 오류가 발생했습니다.");
    }
    setApplying(false);
  };

  const handleSaveConfig = async () => {
    try {
      await api.updatePredictionConfig(config);
      alert("설정이 저장되었습니다.");
    } catch (error) {
      console.error("Save config error:", error);
    }
  };

  // 예측 차트 데이터 준비
  const chartData = prediction?.ensemble_predictions ? 
    Array.from({ length: prediction.forecast_steps }, (_, i) => ({
      step: `T+${i + 1}`,
      public: (prediction.ensemble_predictions.public[i] * 100).toFixed(1),
      productive: (prediction.ensemble_predictions.productive[i] * 100).toFixed(1),
      individual: (prediction.ensemble_predictions.individual[i] * 100).toFixed(1),
      balance: (prediction.ensemble_predictions.balance[i] * 100).toFixed(1)
    })) : [];

  const confidence = prediction?.confidence || 0;
  const confidenceColor = confidence >= 0.8 ? 'emerald' : confidence >= 0.6 ? 'amber' : 'rose';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <Brain className="w-6 h-6 text-violet-400" /> 시계열 예측
          </h2>
          <p className="text-slate-400 text-sm">과거 처리 데이터 기반 미래 분배 비율 예측</p>
        </div>
        <Button 
          onClick={handleAnalyze} 
          disabled={loading}
          className="bg-violet-600 hover:bg-violet-500"
          data-testid="analyze-button"
        >
          {loading ? (
            <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
          ) : (
            <Play className="w-4 h-4 mr-2" />
          )}
          분석 실행
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Config Section */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-slate-100 text-sm">예측 설정</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-slate-300 text-sm mb-2 flex justify-between">
                <span>윈도우 크기</span>
                <span className="text-violet-400">{config.window_size}</span>
              </label>
              <Slider
                value={[config.window_size]}
                onValueChange={([v]) => setConfig({...config, window_size: v})}
                min={3}
                max={30}
                step={1}
                className="[&_[role=slider]]:bg-violet-500"
              />
            </div>
            <div>
              <label className="text-slate-300 text-sm mb-2 flex justify-between">
                <span>예측 스텝</span>
                <span className="text-violet-400">{config.forecast_steps}</span>
              </label>
              <Slider
                value={[config.forecast_steps]}
                onValueChange={([v]) => setConfig({...config, forecast_steps: v})}
                min={1}
                max={10}
                step={1}
                className="[&_[role=slider]]:bg-violet-500"
              />
            </div>
            <div>
              <label className="text-slate-300 text-sm mb-2 flex justify-between">
                <span>신뢰도 임계값</span>
                <span className="text-violet-400">{(config.confidence_threshold * 100).toFixed(0)}%</span>
              </label>
              <Slider
                value={[config.confidence_threshold * 100]}
                onValueChange={([v]) => setConfig({...config, confidence_threshold: v/100})}
                min={50}
                max={95}
                step={5}
                className="[&_[role=slider]]:bg-violet-500"
              />
            </div>
            <div className="flex items-center justify-between py-2">
              <span className="text-slate-300 text-sm">자동 적용</span>
              <Switch 
                checked={config.auto_adjust}
                onCheckedChange={(checked) => setConfig({...config, auto_adjust: checked})}
              />
            </div>
            <Button 
              onClick={handleSaveConfig} 
              variant="outline" 
              className="w-full"
              data-testid="save-prediction-config"
            >
              설정 저장
            </Button>
          </CardContent>
        </Card>

        {/* Results Section */}
        <div className="lg:col-span-2 space-y-4">
          {prediction?.success ? (
            <>
              {/* Metrics */}
              <div className="grid grid-cols-4 gap-3">
                <MetricCard 
                  icon={TrendingUp} 
                  label="데이터 포인트" 
                  value={prediction.data_points}
                  variant="cyan"
                />
                <MetricCard 
                  icon={Sparkles} 
                  label="신뢰도" 
                  value={`${(confidence * 100).toFixed(0)}%`}
                  variant={confidenceColor}
                />
                <MetricCard 
                  icon={AlertTriangle} 
                  label="최대 편차" 
                  value={`${(prediction.max_deviation * 100).toFixed(1)}%`}
                  variant={prediction.adjustment_needed ? "amber" : "teal"}
                />
                <MetricCard 
                  icon={Check} 
                  label="조정 필요" 
                  value={prediction.adjustment_needed ? "예" : "아니오"}
                  variant={prediction.adjustment_needed ? "amber" : "teal"}
                />
              </div>

              {/* Prediction Chart */}
              <Card className="bg-slate-800/50 border-slate-700">
                <CardHeader>
                  <CardTitle className="text-slate-100 text-sm">예측 분배 비율</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-48" data-testid="prediction-chart">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                        <XAxis dataKey="step" stroke="#94a3b8" fontSize={12} />
                        <YAxis stroke="#94a3b8" fontSize={10} domain={[0, 100]} />
                        <RechartsTooltip 
                          contentStyle={{ background: '#1e293b', border: '1px solid #475569', borderRadius: '8px' }}
                        />
                        <Legend />
                        <Line type="monotone" dataKey="public" stroke="#3b82f6" strokeWidth={2} name="공공 (%)" />
                        <Line type="monotone" dataKey="productive" stroke="#10b981" strokeWidth={2} name="생산 (%)" />
                        <Line type="monotone" dataKey="individual" stroke="#f59e0b" strokeWidth={2} name="개인 (%)" />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>

              {/* Comparison */}
              <Card className="bg-slate-800/50 border-slate-700">
                <CardHeader>
                  <CardTitle className="text-slate-100 text-sm">현재 vs 예측 시그마</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-3 gap-4" data-testid="sigma-comparison">
                    {['공공', '생산', '개인'].map((name, idx) => {
                      const current = prediction.current_sigma[idx] * 100;
                      const predicted = prediction.predicted_sigma[idx] * 100;
                      const diff = predicted - current;
                      const color = ['blue', 'emerald', 'amber'][idx];
                      
                      return (
                        <div key={name} className="bg-slate-900/50 rounded-lg p-3">
                          <p className={`text-${color}-400 font-medium mb-2`}>{name}</p>
                          <div className="flex items-center gap-2 text-sm">
                            <span className="text-slate-400">{current.toFixed(1)}%</span>
                            <ArrowRight className="w-4 h-4 text-violet-400" />
                            <span className="text-slate-100 font-medium">{predicted.toFixed(1)}%</span>
                          </div>
                          <p className={`text-xs mt-1 ${diff > 0 ? 'text-emerald-400' : diff < 0 ? 'text-rose-400' : 'text-slate-500'}`}>
                            {diff > 0 ? '+' : ''}{diff.toFixed(1)}%
                          </p>
                        </div>
                      );
                    })}
                  </div>

                  {prediction.adjustment_needed && (
                    <div className="mt-4 flex justify-end">
                      <Button 
                        onClick={handleApply}
                        disabled={applying}
                        className="bg-violet-600 hover:bg-violet-500"
                        data-testid="apply-prediction-button"
                      >
                        {applying ? (
                          <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                        ) : (
                          <Check className="w-4 h-4 mr-2" />
                        )}
                        예측 결과 적용
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            </>
          ) : prediction?.success === false ? (
            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="py-12 text-center">
                <AlertTriangle className="w-12 h-12 text-amber-400 mx-auto mb-4" />
                <p className="text-slate-300">{prediction.message}</p>
                <p className="text-slate-500 text-sm mt-2">현재 데이터: {prediction.data_count}건</p>
              </CardContent>
            </Card>
          ) : (
            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="py-12 text-center">
                <Brain className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                <p className="text-slate-400">
                  '분석 실행' 버튼을 클릭하여 시계열 예측을 시작하세요
                </p>
                <p className="text-slate-500 text-sm mt-2">
                  이동 평균 + 지수 평활 앙상블 예측
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};

export default PredictionTab;
