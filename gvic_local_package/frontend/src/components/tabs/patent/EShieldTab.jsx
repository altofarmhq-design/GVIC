import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { 
  ShieldAlert, 
  ArrowRight,
  AlertTriangle,
  Ban,
  CheckCircle2,
  Biohazard,
  Lock
} from 'lucide-react';

/**
 * E:방어막 - 독소 검역 (특허 E: SHIELD)
 * 유해 데이터 검역 및 격리
 */
export const EShieldTab = () => {
  const [quarantineList, setQuarantineList] = useState([]);
  const [stats, setStats] = useState({ scanned: 0, quarantined: 0, passed: 0 });

  useEffect(() => {
    // 샘플 데이터
    setQuarantineList([
      { id: 'QRN_001', type: 'spam', risk: 'high', status: 'quarantined', reason: '광고성 스팸 패턴 감지' },
      { id: 'QRN_002', type: 'malicious', risk: 'critical', status: 'blocked', reason: '악성 링크 포함' },
      { id: 'QRN_003', type: 'noise', risk: 'low', status: 'flagged', reason: '의미 없는 반복 문자' },
    ]);
    setStats({ scanned: 150, quarantined: 3, passed: 147 });
  }, []);

  const getRiskColor = (risk) => {
    switch(risk) {
      case 'critical': return 'text-red-500 bg-red-500/20';
      case 'high': return 'text-orange-500 bg-orange-500/20';
      case 'medium': return 'text-yellow-500 bg-yellow-500/20';
      default: return 'text-green-500 bg-green-500/20';
    }
  };

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-100 flex items-center gap-3">
            <div className="w-10 h-10 bg-red-600 rounded-lg flex items-center justify-center">
              <ShieldAlert className="w-6 h-6 text-white" />
            </div>
            E:방어막
          </h2>
          <p className="text-slate-400 mt-1">독소 검역 및 격리 - SHIELD 모듈</p>
        </div>
        <Badge variant="outline" className="text-red-400 border-red-600">
          특허 E
        </Badge>
      </div>

      {/* 통계 */}
      <div className="grid grid-cols-4 gap-4">
        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="py-4 text-center">
            <Biohazard className="w-8 h-8 text-slate-400 mx-auto mb-2" />
            <p className="text-3xl font-bold text-white">{stats.scanned}</p>
            <p className="text-slate-400 text-sm">스캔됨</p>
          </CardContent>
        </Card>
        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="py-4 text-center">
            <Lock className="w-8 h-8 text-red-400 mx-auto mb-2" />
            <p className="text-3xl font-bold text-red-400">{stats.quarantined}</p>
            <p className="text-slate-400 text-sm">격리됨</p>
          </CardContent>
        </Card>
        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="py-4 text-center">
            <CheckCircle2 className="w-8 h-8 text-green-400 mx-auto mb-2" />
            <p className="text-3xl font-bold text-green-400">{stats.passed}</p>
            <p className="text-slate-400 text-sm">통과</p>
          </CardContent>
        </Card>
        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="py-4 text-center">
            <ShieldAlert className="w-8 h-8 text-emerald-400 mx-auto mb-2" />
            <p className="text-3xl font-bold text-emerald-400">
              {stats.scanned > 0 ? ((stats.passed / stats.scanned) * 100).toFixed(1) : 100}%
            </p>
            <p className="text-slate-400 text-sm">안전율</p>
          </CardContent>
        </Card>
      </div>

      {/* 독소 판별 수식 */}
      <Card className="bg-slate-900/50 border-slate-700">
        <CardContent className="py-4">
          <p className="text-slate-400 text-sm mb-2">독소 판별 수식 (ΔS)</p>
          <div className="font-mono text-lg text-slate-200 bg-slate-800 rounded p-3">
            ΔS = -Σ P(x_i|Σ) log P(x_i|Σ)
          </div>
          <p className="text-slate-500 text-xs mt-2">
            * 독소 조건: ΔS {">"} θ 또는 Z_score ∉ 허용 범위
          </p>
        </CardContent>
      </Card>

      {/* 격리 목록 */}
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader className="pb-3">
          <CardTitle className="text-slate-100 text-lg flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-red-400" />
            격리 목록
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[250px]">
            <div className="space-y-3">
              {quarantineList.map((item) => (
                <div 
                  key={item.id} 
                  className="p-3 rounded-lg bg-slate-900/50 border border-red-900/50"
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Ban className="w-5 h-5 text-red-400" />
                      <span className="text-slate-200 font-medium">{item.id}</span>
                      <Badge variant="outline" className={getRiskColor(item.risk)}>
                        {item.risk.toUpperCase()}
                      </Badge>
                    </div>
                    <Badge className="bg-red-600">
                      {item.status}
                    </Badge>
                  </div>
                  <p className="text-slate-400 text-sm">{item.reason}</p>
                </div>
              ))}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>

      {/* 플로우 */}
      <div className="flex items-center justify-center gap-2 text-slate-500 text-sm">
        <span className="px-3 py-1 bg-slate-700 rounded">A:게이트</span>
        <ArrowRight className="w-4 h-4" />
        <span className="px-3 py-1 bg-red-600/30 rounded text-red-400">E:방어막</span>
        <ArrowRight className="w-4 h-4" />
        <span className="px-3 py-1 bg-slate-700 rounded">G:정제</span>
        <ArrowRight className="w-4 h-4" />
        <span className="px-3 py-1 bg-slate-700 rounded">B:산출</span>
      </div>
    </div>
  );
};

export default EShieldTab;
