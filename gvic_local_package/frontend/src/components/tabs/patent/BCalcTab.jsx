import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ArrowRight, Calculator, PieChart, DollarSign, TrendingUp } from 'lucide-react';

/**
 * B:산출 - 가치 산출 (특허 B: CALC)
 */
export const BCalcTab = () => (
  <div className="space-y-6">
    <div className="flex items-center justify-between">
      <div>
        <h2 className="text-2xl font-bold text-slate-100 flex items-center gap-3">
          <div className="w-10 h-10 bg-orange-600 rounded-lg flex items-center justify-center">
            <Calculator className="w-6 h-6 text-white" />
          </div>
          B:산출
        </h2>
        <p className="text-slate-400 mt-1">가치 산출 및 5:3:2 배분 - CALC 모듈</p>
      </div>
      <Badge variant="outline" className="text-orange-400 border-orange-600">특허 B</Badge>
    </div>

    <div className="grid grid-cols-3 gap-4">
      <Card className="bg-blue-900/30 border-blue-600">
        <CardContent className="py-6 text-center">
          <p className="text-slate-400 text-sm mb-1">공공 배분</p>
          <p className="text-4xl font-bold text-blue-400">50%</p>
          <p className="text-slate-500 text-xs mt-1">V_pub</p>
        </CardContent>
      </Card>
      <Card className="bg-emerald-900/30 border-emerald-600">
        <CardContent className="py-6 text-center">
          <p className="text-slate-400 text-sm mb-1">생산 배분</p>
          <p className="text-4xl font-bold text-emerald-400">30%</p>
          <p className="text-slate-500 text-xs mt-1">V_pro</p>
        </CardContent>
      </Card>
      <Card className="bg-amber-900/30 border-amber-600">
        <CardContent className="py-6 text-center">
          <p className="text-slate-400 text-sm mb-1">개인 배분</p>
          <p className="text-4xl font-bold text-amber-400">20%</p>
          <p className="text-slate-500 text-xs mt-1">V_ind</p>
        </CardContent>
      </Card>
    </div>

    <Card className="bg-slate-900/50 border-slate-700">
      <CardContent className="py-4">
        <p className="text-slate-400 text-sm mb-2">유량 제어 수식 (dQ/dt)</p>
        <div className="font-mono text-lg text-slate-200 bg-slate-800 rounded p-3">
          dQ/dt = α(R_alloc - R_current) - β∇S
        </div>
      </CardContent>
    </Card>

    <div className="flex items-center justify-center gap-2 text-slate-500 text-sm">
      <span className="px-3 py-1 bg-slate-700 rounded">G:정제</span>
      <ArrowRight className="w-4 h-4" />
      <span className="px-3 py-1 bg-orange-600/30 rounded text-orange-400">B:산출</span>
      <ArrowRight className="w-4 h-4" />
      <span className="px-3 py-1 bg-slate-700 rounded">C:집행</span>
    </div>
  </div>
);

export default BCalcTab;
