import { Database } from 'lucide-react';
import PipelineStageMonitor from '@/components/PipelineStageMonitor';

export const DLedgerTab = () => (
  <PipelineStageMonitor stageId="d_ledger" stageName="원장" stageCode="D" stageColor="teal" stageIcon={Database}
    prevStage="F:실행" nextStage="I:무결성" description="궤적 저장 및 이력 보존" formula="H(T) = Σ[S(t) · G + L(V_proof(t))]" />
);
export default DLedgerTab;
