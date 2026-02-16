import { Brain } from 'lucide-react';
import PipelineStageMonitor from '@/components/PipelineStageMonitor';

/**
 * LL:의도 - 시그널 평가단 (특허 LL: INTELLIGENCE)
 * 시그널을 3가지로 분류: wanted / unwanted / null
 */
export const LLIntentTab = () => {
  return (
    <PipelineStageMonitor
      stageId="ll_evaluate"
      stageName="의도"
      stageCode="LL"
      stageColor="violet"
      stageIcon={Brain}
      prevStage="J:입력"
      nextStage="H:코어"
      description="시그널 평가단 - 원하는것 / 원치않는것 / Null 분류"
      formula="Category = f(Signal, UserPreference)"
    />
  );
};

export default LLIntentTab;
