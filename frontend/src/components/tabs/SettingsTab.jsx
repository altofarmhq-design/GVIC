import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Slider } from "@/components/ui/slider";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Zap, RefreshCw, History, Settings2, ArrowRight } from 'lucide-react';
import { api } from "@/lib/api";

export const SettingsTab = ({ sigma, omega, modules, onUpdate }) => {
  const [sigmaValues, setSigmaValues] = useState(sigma || [0.33, 0.34, 0.33]);
  const [omegaValues, setOmegaValues] = useState(omega || {
    V_pub_min: 0.2, V_pub_max: 0.5,
    V_pro_min: 0.2, V_pro_max: 0.5,
    V_ind_min: 0.1, V_ind_max: 0.5,
    sum_constraint: 1.0
  });
  const [saving, setSaving] = useState(false);
  
  // Dynamic Adjustment State
  const [adjustConfig, setAdjustConfig] = useState({
    enabled: false,
    threshold: 0.05,
    adjustment_rate: 0.01,
    max_adjustments: 10,
    interval_seconds: 60
  });
  const [adjustHistory, setAdjustHistory] = useState([]);
  const [adjusting, setAdjusting] = useState(false);
  const [lastResult, setLastResult] = useState(null);

  useEffect(() => {
    if (sigma) setSigmaValues(sigma);
    if (omega) setOmegaValues(omega);
  }, [sigma, omega]);

  // Fetch adjustment config and history
  const fetchAdjustmentData = useCallback(async () => {
    try {
      const [configRes, historyRes] = await Promise.all([
        api.getAdjustmentConfig(),
        api.getAdjustmentHistory(10)
      ]);
      setAdjustConfig(configRes.data);
      setAdjustHistory(historyRes.data.history || []);
    } catch (error) {
      console.error("Fetch adjustment data error:", error);
    }
  }, []);

  useEffect(() => {
    fetchAdjustmentData();
  }, [fetchAdjustmentData]);

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

  const handleSaveAdjustConfig = async () => {
    setSaving(true);
    try {
      await api.updateAdjustmentConfig(adjustConfig);
      fetchAdjustmentData();
    } catch (error) {
      console.error("Save adjust config error:", error);
    }
    setSaving(false);
  };

  const handleExecuteAdjustment = async () => {
    setAdjusting(true);
    try {
      const response = await api.executeAdjustment();
      setLastResult(response.data);
      fetchAdjustmentData();
      onUpdate();
    } catch (error) {
      console.error("Execute adjustment error:", error);
    }
    setAdjusting(false);
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Sigma Settings */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-slate-100 flex items-center gap-2">
              <span className="text-xl">Σ</span> 시그마 설정
            </CardTitle>
            <CardDescription className="text-slate-400">특허6: 가중 분배 모델 - 목표 비율</CardDescription>
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
              Σ 저장
            </Button>
          </CardContent>
        </Card>

        {/* Omega Settings */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-slate-100 flex items-center gap-2">
              <span className="text-xl">Ω</span> 오메가 설정
            </CardTitle>
            <CardDescription className="text-slate-400">특허1: 경계 조건 기반 수렴 제어</CardDescription>
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
                <label className="text-slate-300 text-sm mb-1 block">V_pro 최소</label>
                <Input
                  type="number"
                  min={0}
                  max={1}
                  step={0.05}
                  value={omegaValues.V_pro_min}
                  onChange={(e) => setOmegaValues({...omegaValues, V_pro_min: parseFloat(e.target.value)})}
                  className="bg-slate-900 border-slate-600 text-slate-100"
                />
              </div>
              <div>
                <label className="text-slate-300 text-sm mb-1 block">V_pro 최대</label>
                <Input
                  type="number"
                  min={0}
                  max={1}
                  step={0.05}
                  value={omegaValues.V_pro_max}
                  onChange={(e) => setOmegaValues({...omegaValues, V_pro_max: parseFloat(e.target.value)})}
                  className="bg-slate-900 border-slate-600 text-slate-100"
                />
              </div>
              <div>
                <label className="text-slate-300 text-sm mb-1 block">V_ind 최소</label>
                <Input
                  type="number"
                  min={0}
                  max={1}
                  step={0.05}
                  value={omegaValues.V_ind_min}
                  onChange={(e) => setOmegaValues({...omegaValues, V_ind_min: parseFloat(e.target.value)})}
                  className="bg-slate-900 border-slate-600 text-slate-100"
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
              Ω 저장
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Dynamic Adjustment Settings */}
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader>
          <CardTitle className="text-slate-100 flex items-center gap-2">
            <Zap className="w-5 h-5" /> 동적 조정 (DynamicAdjuster)
          </CardTitle>
          <CardDescription className="text-slate-400">
            특허6: 임계값 기반 자동/수동 분배 비율 조정
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Config Section */}
            <div className="space-y-4">
              <h4 className="text-slate-200 font-medium flex items-center gap-2">
                <Settings2 className="w-4 h-4" /> 조정 설정
              </h4>
              
              <div className="flex items-center justify-between py-2">
                <span className="text-slate-300">자동 조정 활성화</span>
                <Switch 
                  checked={adjustConfig.enabled}
                  onCheckedChange={(checked) => setAdjustConfig({...adjustConfig, enabled: checked})}
                  data-testid="auto-adjust-toggle"
                />
              </div>

              <div>
                <label className="text-slate-300 text-sm mb-2 flex justify-between">
                  <span>편차 임계값</span>
                  <span className="text-violet-400">{(adjustConfig.threshold * 100).toFixed(0)}%</span>
                </label>
                <Slider
                  value={[adjustConfig.threshold * 100]}
                  onValueChange={([v]) => setAdjustConfig({...adjustConfig, threshold: v/100})}
                  max={20}
                  min={1}
                  step={1}
                  className="[&_[role=slider]]:bg-violet-500"
                  data-testid="threshold-slider"
                />
              </div>

              <div>
                <label className="text-slate-300 text-sm mb-2 flex justify-between">
                  <span>조정률</span>
                  <span className="text-violet-400">{(adjustConfig.adjustment_rate * 100).toFixed(1)}%</span>
                </label>
                <Slider
                  value={[adjustConfig.adjustment_rate * 100]}
                  onValueChange={([v]) => setAdjustConfig({...adjustConfig, adjustment_rate: v/100})}
                  max={10}
                  min={0.5}
                  step={0.5}
                  className="[&_[role=slider]]:bg-violet-500"
                />
              </div>

              <div className="flex gap-2">
                <Button 
                  onClick={handleSaveAdjustConfig} 
                  disabled={saving}
                  className="flex-1"
                  data-testid="save-adjust-config-button"
                >
                  설정 저장
                </Button>
                <Button 
                  onClick={handleExecuteAdjustment} 
                  disabled={adjusting}
                  variant="secondary"
                  className="flex-1"
                  data-testid="execute-adjustment-button"
                >
                  {adjusting ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <Zap className="w-4 h-4 mr-2" />}
                  수동 조정 실행
                </Button>
              </div>

              {/* Last Result */}
              {lastResult && (
                <div className={`mt-4 p-3 rounded-lg ${lastResult.adjusted ? 'bg-violet-900/30 border border-violet-600' : 'bg-slate-900/50 border border-slate-600'}`}>
                  <p className={`font-medium mb-2 ${lastResult.adjusted ? 'text-violet-300' : 'text-slate-400'}`}>
                    {lastResult.adjusted ? '✓ 조정 완료' : '조정 불필요'}
                  </p>
                  {lastResult.adjusted && lastResult.adjustments?.map((adj, idx) => (
                    <div key={idx} className="text-sm text-slate-300 flex items-center gap-2">
                      <span className="capitalize">{adj.category}</span>
                      <span className="text-slate-500">{(adj.from * 100).toFixed(1)}%</span>
                      <ArrowRight className="w-3 h-3 text-violet-400" />
                      <span className="text-violet-400">{(adj.to * 100).toFixed(1)}%</span>
                    </div>
                  ))}
                  <p className="text-slate-500 text-xs mt-2">
                    최대 편차: {(lastResult.max_deviation * 100).toFixed(2)}%
                  </p>
                </div>
              )}
            </div>

            {/* History Section */}
            <div className="space-y-4">
              <h4 className="text-slate-200 font-medium flex items-center gap-2">
                <History className="w-4 h-4" /> 조정 이력
              </h4>
              <ScrollArea className="h-64" data-testid="adjustment-history">
                {adjustHistory.length > 0 ? (
                  <div className="space-y-2">
                    {adjustHistory.map((record, idx) => (
                      <div key={idx} className="bg-slate-900/50 rounded-lg p-3">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-slate-400 text-xs">
                            {record.timestamp?.slice(0, 19).replace('T', ' ')}
                          </span>
                          <Badge variant="outline" className="text-xs">
                            {record.adjustments?.length || 0}건 조정
                          </Badge>
                        </div>
                        <div className="text-xs text-slate-300">
                          {record.adjustments?.map((adj, i) => (
                            <span key={i} className="mr-2">
                              {adj.category}: {adj.direction === 'increase' ? '↑' : '↓'}
                            </span>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-slate-500 text-center py-8">조정 이력이 없습니다</p>
                )}
              </ScrollArea>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Module Status */}
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader>
          <CardTitle className="text-slate-100 text-sm">모듈 상태</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3" data-testid="module-status">
            {(modules || []).map((mod, idx) => (
              <div key={idx} className="bg-slate-900/50 rounded-lg p-3 text-center">
                <p className="text-slate-100 text-sm font-medium">{mod.name}</p>
                <Badge variant={mod.status === 'active' ? 'default' : 'secondary'} className="mt-2">
                  {mod.status === 'active' ? '활성' : '비활성'}
                </Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default SettingsTab;
