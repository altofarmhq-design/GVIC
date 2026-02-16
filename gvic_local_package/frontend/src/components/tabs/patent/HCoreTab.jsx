import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Slider } from "@/components/ui/slider";
import { 
  Cpu, 
  Target,
  BarChart3,
  ArrowRight,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  Settings2
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

/**
 * H:코어 - 전역 수렴 제어 (특허 H: CORE)
 * 결이론 5:3:2 비율 적용, 시스템 전체 수렴 제어
 */
export const HCoreTab = ({ onUpdate }) => {
  const [sigma, setSigma] = useState([0.5, 0.3, 0.2]);
  const [omega, setOmega] = useState(null);
  const [balanceScore, setBalanceScore] = useState(0);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // 데이터 로드
  const loadData = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      const [sigmaRes, omegaRes] = await Promise.all([
        axios.get(`${API_URL}/api/config/sigma`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        axios.get(`${API_URL}/api/config/omega`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
      ]);
      setSigma(sigmaRes.data.sigma || [0.5, 0.3, 0.2]);
      setOmega(omegaRes.data.omega);
      
      // 균형 점수 계산
      const target = [0.5, 0.3, 0.2];
      const deviation = sigmaRes.data.sigma.reduce((sum, val, i) => 
        sum + Math.abs(val - target[i]), 0) / 3;
      setBalanceScore(1 - deviation);
    } catch (err) {
      console.error("Failed to load config:", err);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // 시그마 업데이트
  const handleSigmaChange = (index, value) => {
    const newSigma = [...sigma];
    newSigma[index] = value;
    
    // 나머지 값 자동 조정 (합계 = 1)
    const others = [0, 1, 2].filter(i => i !== index);
    const remaining = 1 - value;
    const currentSum = others.reduce((sum, i) => sum + newSigma[i], 0);
    
    if (currentSum > 0) {
      others.forEach(i => {
        newSigma[i] = (newSigma[i] / currentSum) * remaining;
      });
    } else {
      others.forEach((i, idx) => {
        newSigma[i] = remaining / others.length;
      });
    }
    
    setSigma(newSigma);
  };

  // 저장
  const handleSave = async () => {
    setSaving(true);
    try {
      const token = localStorage.getItem('token');
      await axios.put(`${API_URL}/api/config/sigma`, {
        sigma: sigma
      }, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (onUpdate) onUpdate();
      alert("시그마 설정이 저장되었습니다.");
    } catch (err) {
      console.error("Failed to save sigma:", err);
      alert("저장 실패: " + (err.response?.data?.detail || err.message));
    }
    setSaving(false);
  };

  // 기본값으로 복원
  const handleReset = () => {
    setSigma([0.5, 0.3, 0.2]);
  };

  const categories = [
    { name: "공공 (V_pub)", color: "blue", icon: "🏛️", desc: "사회적 가치" },
    { name: "생산 (V_pro)", color: "emerald", icon: "🏭", desc: "생산적 가치" },
    { name: "개인 (V_ind)", color: "amber", icon: "👤", desc: "개인적 가치" }
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin text-violet-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-100 flex items-center gap-3">
            <div className="w-10 h-10 bg-purple-600 rounded-lg flex items-center justify-center">
              <Cpu className="w-6 h-6 text-white" />
            </div>
            H:코어
          </h2>
          <p className="text-slate-400 mt-1">전역 수렴 제어 - CORE 모듈 (결이론 5:3:2)</p>
        </div>
        <Badge variant="outline" className="text-purple-400 border-purple-600">
          특허 H
        </Badge>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* 좌측: 시그마 설정 */}
        <div className="col-span-2 space-y-4">
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader className="pb-3">
              <CardTitle className="text-slate-100 text-lg flex items-center gap-2">
                <Target className="w-5 h-5 text-purple-400" />
                Σ (시그마) - 전역 분배 비율
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {categories.map((cat, idx) => (
                <div key={idx} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-xl">{cat.icon}</span>
                      <span className="text-slate-200 font-medium">{cat.name}</span>
                      <span className="text-slate-500 text-sm">- {cat.desc}</span>
                    </div>
                    <Badge className={`bg-${cat.color}-600`}>
                      {(sigma[idx] * 100).toFixed(1)}%
                    </Badge>
                  </div>
                  <Slider
                    value={[sigma[idx]]}
                    onValueChange={(val) => handleSigmaChange(idx, val[0])}
                    min={0.05}
                    max={0.8}
                    step={0.01}
                    className="py-2"
                  />
                </div>
              ))}

              <div className="flex items-center justify-between pt-4 border-t border-slate-700">
                <div className="flex items-center gap-2">
                  <span className="text-slate-400">합계:</span>
                  <Badge variant={Math.abs(sigma.reduce((a, b) => a + b, 0) - 1) < 0.01 ? "default" : "destructive"}>
                    {(sigma.reduce((a, b) => a + b, 0) * 100).toFixed(1)}%
                  </Badge>
                </div>
                <div className="flex gap-2">
                  <Button variant="outline" onClick={handleReset} size="sm">
                    <RefreshCw className="w-4 h-4 mr-1" /> 기본값
                  </Button>
                  <Button onClick={handleSave} disabled={saving} className="bg-purple-600 hover:bg-purple-700">
                    {saving ? "저장 중..." : "저장"}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 수학적 표현 */}
          <Card className="bg-slate-900/50 border-slate-700">
            <CardContent className="py-4">
              <p className="text-slate-400 text-sm mb-2">수학적 표현</p>
              <div className="font-mono text-lg text-slate-200 bg-slate-800 rounded p-3">
                Σ = [{sigma.map(s => s.toFixed(2)).join(', ')}]<sup>T</sup>
              </div>
              <p className="text-slate-500 text-xs mt-2">
                * 결이론에 따른 이상적 비율: [0.50, 0.30, 0.20]
              </p>
            </CardContent>
          </Card>
        </div>

        {/* 우측: 상태 */}
        <div className="space-y-4">
          {/* 균형 점수 */}
          <Card className="bg-gradient-to-br from-purple-900/30 to-slate-800/50 border-purple-600">
            <CardContent className="py-6 text-center">
              <p className="text-slate-400 text-sm mb-2">시스템 균형 점수</p>
              <div className="text-5xl font-bold text-white mb-2">
                {(balanceScore * 100).toFixed(0)}%
              </div>
              <div className="flex items-center justify-center gap-2">
                {balanceScore >= 0.9 ? (
                  <>
                    <CheckCircle2 className="w-5 h-5 text-green-400" />
                    <span className="text-green-400">최적 상태</span>
                  </>
                ) : balanceScore >= 0.7 ? (
                  <>
                    <Settings2 className="w-5 h-5 text-yellow-400" />
                    <span className="text-yellow-400">조정 필요</span>
                  </>
                ) : (
                  <>
                    <AlertTriangle className="w-5 h-5 text-red-400" />
                    <span className="text-red-400">불균형</span>
                  </>
                )}
              </div>
            </CardContent>
          </Card>

          {/* 분배 시각화 */}
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader className="pb-2">
              <CardTitle className="text-slate-100 text-base flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-purple-400" />
                분배 시각화
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {categories.map((cat, idx) => (
                  <div key={idx}>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-400">{cat.icon} {cat.name.split(' ')[0]}</span>
                      <span className="text-slate-300">{(sigma[idx] * 100).toFixed(1)}%</span>
                    </div>
                    <div className="h-3 bg-slate-700 rounded-full overflow-hidden">
                      <div 
                        className={`h-full bg-${cat.color}-500 transition-all duration-300`}
                        style={{ width: `${sigma[idx] * 100}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Ω 조건 */}
          {omega && (
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader className="pb-2">
                <CardTitle className="text-slate-100 text-base">Ω 경계 조건</CardTitle>
              </CardHeader>
              <CardContent className="text-sm">
                <div className="space-y-2 text-slate-400">
                  <p>V_pub: {omega.V_pub_min} ~ {omega.V_pub_max}</p>
                  <p>V_pro: {omega.V_pro_min} ~ {omega.V_pro_max}</p>
                  <p>V_ind: {omega.V_ind_min} ~ {omega.V_ind_max}</p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* 플로우 안내 */}
      <div className="flex items-center justify-center gap-2 text-slate-500 text-sm">
        <span className="px-3 py-1 bg-slate-700 rounded">LL:의도</span>
        <ArrowRight className="w-4 h-4" />
        <span className="px-3 py-1 bg-purple-600/30 rounded text-purple-400">H:코어</span>
        <ArrowRight className="w-4 h-4" />
        <span className="px-3 py-1 bg-slate-700 rounded">A:게이트</span>
        <ArrowRight className="w-4 h-4" />
        <span className="px-3 py-1 bg-slate-700 rounded">E:방어막</span>
      </div>
    </div>
  );
};

export default HCoreTab;
