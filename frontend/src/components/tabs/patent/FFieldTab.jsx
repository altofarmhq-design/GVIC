import { Activity } from 'lucide-react';
import PipelineStageMonitor from '@/components/PipelineStageMonitor';

export const FFieldTab = () => (
  <PipelineStageMonitor stageId="module" stageName="실행" stageCode="F" stageColor="pink" stageIcon={Activity}
    prevStage="C:집행" nextStage="D:원장" description="물리 계층 실행" formula="E_i(t) = ∫(R_alloc · F_i - κ × dS_i/dt) dt" />
);
export default FFieldTab;
