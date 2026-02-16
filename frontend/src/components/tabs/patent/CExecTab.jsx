import { Play } from 'lucide-react';
import PipelineStageMonitor from '@/components/PipelineStageMonitor';

export const CExecTab = () => (
  <PipelineStageMonitor stageId="module" stageName="집행" stageCode="C" stageColor="indigo" stageIcon={Play}
    prevStage="B:산출" nextStage="F:실행" description="자원 배분 및 가치 집행" formula="E_res = β · (M_conv × R_alloc)" />
);
export default CExecTab;
