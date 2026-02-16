import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { 
  Sparkles, 
  ArrowRight,
  Filter,
  Gem,
  TrendingUp,
  Trash2
} from 'lucide-react';

/**
 * G:정제 - 가치 정제 (특허 G: REFINE)
 * 노이즈 제거 및 가치 정제
 */
export const GRefineTab = () => {
  const [refineStats, setRefineStats] = useState({
    input: 100,
    noise_removed: 15,
    refined: 85,
    quality_score: 0.92
  });

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-100 flex items-center gap-3">
            <div className="w-10 h-10 bg-emerald-600 rounded-lg flex items-center justify-center">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            G:정제
          </h2>
          <p className="text-slate-400 mt-1">가치 정제 및 노이즈 제거 - REFINE 모듈</p>
        </div>
        <Badge variant="outline" className="text-emerald-400 border-emerald-600">
          특허 G
        </Badge>
      </div>

      {/* 통계 */}
      <div className="grid grid-cols-4 gap-4">
        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="py-4 text-center">
            <Filter className="w-8 h-8 text-blue-400 mx-auto mb-2" />
            <p className="text-3xl font-bold text-white">{refineStats.input}</p>
            <p className="text-slate-400 text-sm">입력 데이터</p>
          </CardContent>
        </Card>
        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="py-4 text-center">
            <Trash2 className="w-8 h-8 text-red-400 mx-auto mb-2" />
            <p className="text-3xl font-bold text-red-400">{refineStats.noise_removed}</p>
            <p className="text-slate-400 text-sm">노이즈 제거</p>
          </CardContent>
        </Card>
        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="py-4 text-center">
            <Gem className="w-8 h-8 text-emerald-400 mx-auto mb-2" />
            <p className="text-3xl font-bold text-emerald-400">{refineStats.refined}</p>
            <p className="text-slate-400 text-sm">정제 완료</p>
          </CardContent>
        </Card>
        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="py-4 text-center">
            <TrendingUp className="w-8 h-8 text-amber-400 mx-auto mb-2" />
            <p className="text-3xl font-bold text-amber-400">
              {(refineStats.quality_score * 100).toFixed(0)}%
            </p>
            <p className="text-slate-400 text-sm">품질 점수</p>
          </CardContent>
        </Card>
      </div>

      {/* 정제 프로세스 시각화 */}
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader className="pb-3">
          <CardTitle className="text-slate-100 text-lg">정제 프로세스</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <div className="flex justify-between mb-2">
                <span className="text-slate-400">원본 데이터</span>
                <span className="text-slate-300">100%</span>
              </div>
              <Progress value={100} className="h-3" />
            </div>
            <ArrowRight className="w-6 h-6 text-slate-500" />
            <div className="flex-1">
              <div className="flex justify-between mb-2">
                <span className="text-slate-400">노이즈 제거 후</span>
                <span className="text-emerald-400">{refineStats.refined}%</span>
              </div>
              <Progress value={refineStats.refined} className="h-3 bg-slate-700" />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4 pt-4 border-t border-slate-700">
            <div className="text-center p-3 bg-slate-900/50 rounded-lg">
              <p className="text-slate-500 text-xs mb-1">중복 제거</p>
              <p className="text-lg font-bold text-slate-300">5건</p>
            </div>
            <div className="text-center p-3 bg-slate-900/50 rounded-lg">
              <p className="text-slate-500 text-xs mb-1">이상치 제거</p>
              <p className="text-lg font-bold text-slate-300">7건</p>
            </div>
            <div className="text-center p-3 bg-slate-900/50 rounded-lg">
              <p className="text-slate-500 text-xs mb-1">무의미 데이터</p>
              <p className="text-lg font-bold text-slate-300">3건</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 가치 판별 지수 수식 */}
      <Card className="bg-slate-900/50 border-slate-700">
        <CardContent className="py-4">
          <p className="text-slate-400 text-sm mb-2">가치 판별 지수 (D_idx)</p>
          <div className="font-mono text-lg text-slate-200 bg-slate-800 rounded p-3">
            D_idx = ∫|V_cand · Σ| dt - σ_noise
          </div>
          <p className="text-slate-500 text-xs mt-2">
            * 후보 가치 벡터와 전역 지표의 적분에서 노이즈 표준편차 차감
          </p>
        </CardContent>
      </Card>

      {/* 플로우 */}
      <div className="flex items-center justify-center gap-2 text-slate-500 text-sm">
        <span className="px-3 py-1 bg-slate-700 rounded">E:방어막</span>
        <ArrowRight className="w-4 h-4" />
        <span className="px-3 py-1 bg-emerald-600/30 rounded text-emerald-400">G:정제</span>
        <ArrowRight className="w-4 h-4" />
        <span className="px-3 py-1 bg-slate-700 rounded">B:산출</span>
        <ArrowRight className="w-4 h-4" />
        <span className="px-3 py-1 bg-slate-700 rounded">C:집행</span>
      </div>
    </div>
  );
};

export default GRefineTab;
