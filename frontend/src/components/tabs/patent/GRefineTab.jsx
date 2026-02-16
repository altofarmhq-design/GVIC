import { Sparkles } from 'lucide-react';
import PipelineStageMonitor from '@/components/PipelineStageMonitor';

export const GRefineTab = () => (
  <PipelineStageMonitor stageId="asset_process" stageName="정제" stageCode="G" stageColor="emerald" stageIcon={Sparkles}
    prevStage="E:방어막" nextStage="B:산출" description="가치 정제 및 노이즈 제거" formula="D_idx = ∫|V_cand · Σ| dt - σ_noise" />
);
export default GRefineTab;
