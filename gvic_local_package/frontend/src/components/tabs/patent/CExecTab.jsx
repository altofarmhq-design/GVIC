import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ArrowRight, Play, Coins, Users, Building } from 'lucide-react';

/** C:집행 - 자원 배분 (특허 C: EXEC) */
export const CExecTab = () => (
  <div className="space-y-6">
    <div className="flex items-center justify-between">
      <div>
        <h2 className="text-2xl font-bold text-slate-100 flex items-center gap-3">
          <div className="w-10 h-10 bg-indigo-600 rounded-lg flex items-center justify-center">
            <Play className="w-6 h-6 text-white" />
          </div>
          C:집행
        </h2>
        <p className="text-slate-400 mt-1">자원 배분 및 가치 집행 - EXEC 모듈</p>
      </div>
      <Badge variant="outline" className="text-indigo-400 border-indigo-600">특허 C</Badge>
    </div>

    <Card className="bg-slate-900/50 border-slate-700">
      <CardContent className="py-4">
        <p className="text-slate-400 text-sm mb-2">자원 집행 수식</p>
        <div className="font-mono text-lg text-slate-200 bg-slate-800 rounded p-3">
          E_res = β · (M_conv × R_alloc)
        </div>
      </CardContent>
    </Card>

    <div className="flex items-center justify-center gap-2 text-slate-500 text-sm">
      <span className="px-3 py-1 bg-slate-700 rounded">B:산출</span>
      <ArrowRight className="w-4 h-4" />
      <span className="px-3 py-1 bg-indigo-600/30 rounded text-indigo-400">C:집행</span>
      <ArrowRight className="w-4 h-4" />
      <span className="px-3 py-1 bg-slate-700 rounded">F:실행</span>
    </div>
  </div>
);

export default CExecTab;
