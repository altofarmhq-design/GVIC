import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ArrowRight, Cpu, Activity, Zap } from 'lucide-react';

/** F:실행 - 물리 계층 실행 (특허 F: FIELD) */
export const FFieldTab = () => (
  <div className="space-y-6">
    <div className="flex items-center justify-between">
      <div>
        <h2 className="text-2xl font-bold text-slate-100 flex items-center gap-3">
          <div className="w-10 h-10 bg-pink-600 rounded-lg flex items-center justify-center">
            <Activity className="w-6 h-6 text-white" />
          </div>
          F:실행
        </h2>
        <p className="text-slate-400 mt-1">물리 계층 실행 - FIELD 모듈</p>
      </div>
      <Badge variant="outline" className="text-pink-400 border-pink-600">특허 F</Badge>
    </div>

    <Card className="bg-slate-900/50 border-slate-700">
      <CardContent className="py-4">
        <p className="text-slate-400 text-sm mb-2">물리 실행 수식</p>
        <div className="font-mono text-lg text-slate-200 bg-slate-800 rounded p-3">
          E_i(t) = ∫(R_alloc · F_i - κ × dS_i/dt) dt
        </div>
      </CardContent>
    </Card>

    <div className="flex items-center justify-center gap-2 text-slate-500 text-sm">
      <span className="px-3 py-1 bg-slate-700 rounded">C:집행</span>
      <ArrowRight className="w-4 h-4" />
      <span className="px-3 py-1 bg-pink-600/30 rounded text-pink-400">F:실행</span>
      <ArrowRight className="w-4 h-4" />
      <span className="px-3 py-1 bg-slate-700 rounded">D:원장</span>
    </div>
  </div>
);

export default FFieldTab;
