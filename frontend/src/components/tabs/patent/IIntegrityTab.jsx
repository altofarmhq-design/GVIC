import { Lock } from 'lucide-react';
import PipelineStageMonitor from '@/components/PipelineStageMonitor';

export const IIntegrityTab = () => (
  <PipelineStageMonitor stageId="completed" stageName="무결성" stageCode="I" stageColor="slate" stageIcon={Lock}
    prevStage="D:원장" nextStage={null} description="무결성 증명 및 해시 체인" formula="V_proof(t) = Hash(Σ(t) ⊕ E(t) + V_proof(t-1))" />
);
export default IIntegrityTab;
