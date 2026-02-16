import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ArrowRight, Shield, Lock, CheckCircle2 } from 'lucide-react';

/** I:무결성 - 무결성 증명 (특허 I: INTEGRITY) */
export const IIntegrityTab = () => (
  <div className="space-y-6">
    <div className="flex items-center justify-between">
      <div>
        <h2 className="text-2xl font-bold text-slate-100 flex items-center gap-3">
          <div className="w-10 h-10 bg-slate-600 rounded-lg flex items-center justify-center">
            <Lock className="w-6 h-6 text-white" />
          </div>
          I:무결성
        </h2>
        <p className="text-slate-400 mt-1">무결성 증명 및 해시 체인 - INTEGRITY 모듈</p>
      </div>
      <Badge variant="outline" className="text-slate-400 border-slate-500">특허 I</Badge>
    </div>

    <Card className="bg-slate-900/50 border-slate-700">
      <CardContent className="py-4">
        <p className="text-slate-400 text-sm mb-2">무결성 증명 수식</p>
        <div className="font-mono text-lg text-slate-200 bg-slate-800 rounded p-3">
          V_proof(t) = Hash(Σ(t) ⊕ E(t) + V_proof(t-1))
        </div>
      </CardContent>
    </Card>

    <div className="flex items-center justify-center gap-2 text-slate-500 text-sm">
      <span className="px-3 py-1 bg-slate-700 rounded">D:원장</span>
      <ArrowRight className="w-4 h-4" />
      <span className="px-3 py-1 bg-slate-500/30 rounded text-slate-300">I:무결성</span>
      <ArrowRight className="w-4 h-4" />
      <span className="px-3 py-1 bg-green-700 rounded text-green-300">완료</span>
    </div>
  </div>
);

export default IIntegrityTab;
