import { Cpu } from 'lucide-react';
import PipelineStageMonitor from '@/components/PipelineStageMonitor';

/**
 * H:코어 - 분석 및 라우팅 (특허 H: CORE)
 */
export const HCoreTab = () => {
  return (
    <PipelineStageMonitor
      stageId="h_core"
      stageName="코어"
      stageCode="H"
      stageColor="purple"
      stageIcon={Cpu}
      prevStage="LL:의도"
      nextStage="A:게이트"
      description="코어 처리 - 분석 및 라우팅 (결이론 5:3:2)"
      formula="Σ = [0.5, 0.3, 0.2]ᵀ (공공:생산:개인)"
    />
  );
};

export default HCoreTab;
