import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { 
  Shield, 
  ArrowRight,
  RefreshCw,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Eye,
  Filter,
  Trash2
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

/**
 * A:게이트 - 데이터 인지 (특허 A: GATE)
 * 데이터 정합성 판별, 입력 검증
 */
export const AGateTab = () => {
  const [validationHistory, setValidationHistory] = useState([]);
  const [stats, setStats] = useState({ total: 0, passed: 0, rejected: 0 });
  const [loading, setLoading] = useState(false);

  // 시뮬레이션 데이터 로드
  useEffect(() => {
    // 샘플 검증 이력
    setValidationHistory([
      { id: 'VAL_001', timestamp: new Date().toISOString(), type: '상품 후기', status: 'passed', score: 0.95, reason: '정합성 충족' },
      { id: 'VAL_002', timestamp: new Date().toISOString(), type: '요구사항', status: 'passed', score: 0.88, reason: '정합성 충족' },
      { id: 'VAL_003', timestamp: new Date().toISOString(), type: '스팸', status: 'rejected', score: 0.23, reason: '정합성 미달 (스팸 패턴)' },
    ]);
    setStats({ total: 3, passed: 2, rejected: 1 });
  }, []);

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-100 flex items-center gap-3">
            <div className="w-10 h-10 bg-cyan-600 rounded-lg flex items-center justify-center">
              <Eye className="w-6 h-6 text-white" />
            </div>
            A:게이트
          </h2>
          <p className="text-slate-400 mt-1">데이터 인지 및 정합성 판별 - GATE 모듈</p>
        </div>
        <Badge variant="outline" className="text-cyan-400 border-cyan-600">
          특허 A
        </Badge>
      </div>

      <div className="grid grid-cols-4 gap-4">
        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="py-4 text-center">
            <Filter className="w-8 h-8 text-cyan-400 mx-auto mb-2" />
            <p className="text-3xl font-bold text-white">{stats.total}</p>
            <p className="text-slate-400 text-sm">총 검증</p>
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
            <XCircle className="w-8 h-8 text-red-400 mx-auto mb-2" />
            <p className="text-3xl font-bold text-red-400">{stats.rejected}</p>
            <p className="text-slate-400 text-sm">거부</p>
          </CardContent>
        </Card>
        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="py-4 text-center">
            <Shield className="w-8 h-8 text-blue-400 mx-auto mb-2" />
            <p className="text-3xl font-bold text-blue-400">
              {stats.total > 0 ? ((stats.passed / stats.total) * 100).toFixed(0) : 0}%
            </p>
            <p className="text-slate-400 text-sm">통과율</p>
          </CardContent>
        </Card>
      </div>

      {/* 정합성 수식 */}
      <Card className="bg-slate-900/50 border-slate-700">
        <CardContent className="py-4">
          <p className="text-slate-400 text-sm mb-2">정합성 지수 수식 (S_idx)</p>
          <div className="font-mono text-lg text-slate-200 bg-slate-800 rounded p-3">
            S_idx = (V_i · Σ) / (||V_i|| × ||Σ||)
          </div>
          <p className="text-slate-500 text-xs mt-2">
            * 입력 벡터와 전역 수렴 지표의 코사인 유사도로 정합성 측정
          </p>
        </CardContent>
      </Card>

      {/* 검증 이력 */}
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader className="pb-3">
          <CardTitle className="text-slate-100 text-lg flex items-center gap-2">
            <Filter className="w-5 h-5 text-cyan-400" />
            검증 이력
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[250px]">
            <div className="space-y-3">
              {validationHistory.map((item) => (
                <div 
                  key={item.id} 
                  className={`p-3 rounded-lg border ${
                    item.status === 'passed' 
                      ? 'bg-green-900/20 border-green-700' 
                      : 'bg-red-900/20 border-red-700'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      {item.status === 'passed' ? (
                        <CheckCircle2 className="w-5 h-5 text-green-400" />
                      ) : (
                        <XCircle className="w-5 h-5 text-red-400" />
                      )}
                      <span className="text-slate-200 font-medium">{item.id}</span>
                      <Badge variant="outline" className="text-slate-400 border-slate-600">
                        {item.type}
                      </Badge>
                    </div>
                    <Badge className={item.status === 'passed' ? 'bg-green-600' : 'bg-red-600'}>
                      점수: {(item.score * 100).toFixed(0)}%
                    </Badge>
                  </div>
                  <p className="text-slate-400 text-sm">{item.reason}</p>
                </div>
              ))}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>

      {/* 플로우 안내 */}
      <div className="flex items-center justify-center gap-2 text-slate-500 text-sm">
        <span className="px-3 py-1 bg-slate-700 rounded">H:코어</span>
        <ArrowRight className="w-4 h-4" />
        <span className="px-3 py-1 bg-cyan-600/30 rounded text-cyan-400">A:게이트</span>
        <ArrowRight className="w-4 h-4" />
        <span className="px-3 py-1 bg-slate-700 rounded">E:방어막</span>
        <ArrowRight className="w-4 h-4" />
        <span className="px-3 py-1 bg-slate-700 rounded">G:정제</span>
      </div>
    </div>
  );
};

export default AGateTab;
