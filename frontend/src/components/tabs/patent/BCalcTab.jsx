import { Calculator } from 'lucide-react';
import PipelineStageMonitor from '@/components/PipelineStageMonitor';

export const BCalcTab = () => (
  <PipelineStageMonitor stageId="module" stageName="산출" stageCode="B" stageColor="orange" stageIcon={Calculator}
    prevStage="G:정제" nextStage="C:집행" description="가치 산출 및 5:3:2 배분" formula="dQ/dt = α(R_alloc - R_current) - β∇S" />
);
export default BCalcTab;
