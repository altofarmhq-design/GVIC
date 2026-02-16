import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ArrowRight, Database, History, FileText } from 'lucide-react';

/** D:원장 - 궤적 저장 (특허 D: LEDGER) */
export const DLedgerTab = () => (
  <div className="space-y-6">
    <div className="flex items-center justify-between">
      <div>
        <h2 className="text-2xl font-bold text-slate-100 flex items-center gap-3">
          <div className="w-10 h-10 bg-teal-600 rounded-lg flex items-center justify-center">
            <Database className="w-6 h-6 text-white" />
          </div>
          D:원장
        </h2>
        <p className="text-slate-400 mt-1">궤적 저장 및 이력 보존 - LEDGER 모듈</p>
      </div>
      <Badge variant="outline" className="text-teal-400 border-teal-600">특허 D</Badge>
    </div>

    <Card className="bg-slate-900/50 border-slate-700">
      <CardContent className="py-4">
        <p className="text-slate-400 text-sm mb-2">궤적 저장 수식</p>
        <div className="font-mono text-lg text-slate-200 bg-slate-800 rounded p-3">
          H(T) = Σ[S(t) · G + L(V_proof(t))]
        </div>
      </CardContent>
    </Card>

    <div className="flex items-center justify-center gap-2 text-slate-500 text-sm">
      <span className="px-3 py-1 bg-slate-700 rounded">F:실행</span>
      <ArrowRight className="w-4 h-4" />
      <span className="px-3 py-1 bg-teal-600/30 rounded text-teal-400">D:원장</span>
      <ArrowRight className="w-4 h-4" />
      <span className="px-3 py-1 bg-slate-700 rounded">I:무결성</span>
    </div>
  </div>
);

export default DLedgerTab;
