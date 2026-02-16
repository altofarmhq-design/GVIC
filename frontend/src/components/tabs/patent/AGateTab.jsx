import { Eye } from 'lucide-react';
import PipelineStageMonitor from '@/components/PipelineStageMonitor';

/** A:게이트 - 데이터 인지 (특허 A: GATE) */
export const AGateTab = () => (
  <PipelineStageMonitor
    stageId="asset_process"
    stageName="게이트"
    stageCode="A"
    stageColor="cyan"
    stageIcon={Eye}
    prevStage="H:코어"
    nextStage="E:방어막"
    description="데이터 인지 및 정합성 판별"
    formula="S_idx = (V_i · Σ) / (||V_i|| × ||Σ||)"
  />
);

export default AGateTab;
