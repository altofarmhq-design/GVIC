import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Slider } from "@/components/ui/slider";
import { Badge } from "@/components/ui/badge";
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

  useEffect(() => {
    if (sigma) setSigmaValues(sigma);
    if (omega) setOmegaValues(omega);
  }, [sigma, omega]);

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

  return (
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

          <div className="mt-6">
            <h4 className="text-slate-200 font-medium mb-3">모듈 상태</h4>
            <div className="space-y-2" data-testid="module-status">
              {(modules || []).map((mod, idx) => (
                <div key={idx} className="flex items-center justify-between py-2 border-b border-slate-700">
                  <span className="text-slate-100">{mod.name}</span>
                  <Badge variant={mod.status === 'active' ? 'default' : 'secondary'}>
                    {mod.status === 'active' ? '활성' : '비활성'}
                  </Badge>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default SettingsTab;
