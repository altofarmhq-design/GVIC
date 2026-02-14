import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from "@/components/ui/dialog";
import { Slider } from "@/components/ui/slider";
import { 
  Layers, Check, Plus, Trash2, RefreshCw, 
  Building2, Factory, User, Sparkles
} from 'lucide-react';
import { api } from "@/lib/api";

const MODEL_ICONS = {
  balanced: Layers,
  public_priority: Building2,
  productive_priority: Factory,
  individual_priority: User,
  growth: Sparkles,
  custom: Layers
};

const MODEL_COLORS = {
  balanced: "violet",
  public_priority: "blue",
  productive_priority: "emerald",
  individual_priority: "amber",
  growth: "rose",
  custom: "slate"
};

export const ModelsTab = ({ onModelChange }) => {
  const [models, setModels] = useState([]);
  const [currentModelId, setCurrentModelId] = useState("default");
  const [loading, setLoading] = useState(false);
  const [activating, setActivating] = useState(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  
  // New model form
  const [newModel, setNewModel] = useState({
    name: "",
    description: "",
    sigma: [0.33, 0.34, 0.33],
    omega: {
      V_pub_min: 0.2, V_pub_max: 0.5,
      V_pro_min: 0.2, V_pro_max: 0.5,
      V_ind_min: 0.1, V_ind_max: 0.5
    }
  });

  const fetchModels = useCallback(async () => {
    setLoading(true);
    try {
      const response = await api.getAllModels();
      setModels(response.data.models || []);
      setCurrentModelId(response.data.current_model_id);
    } catch (error) {
      console.error("Fetch models error:", error);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchModels();
  }, [fetchModels]);

  const handleActivateModel = async (modelId) => {
    setActivating(modelId);
    try {
      await api.activateModel(modelId);
      fetchModels();
      if (onModelChange) onModelChange();
    } catch (error) {
      console.error("Activate model error:", error);
      alert("모델 활성화 중 오류가 발생했습니다.");
    }
    setActivating(null);
  };

  const handleCreateModel = async () => {
    // Validate sigma sum
    const sigmaSum = newModel.sigma.reduce((a, b) => a + b, 0);
    if (Math.abs(sigmaSum - 1.0) > 0.01) {
      alert("시그마 합계가 1이 되어야 합니다.");
      return;
    }

    try {
      await api.createModel(newModel);
      setShowCreateDialog(false);
      setNewModel({
        name: "",
        description: "",
        sigma: [0.33, 0.34, 0.33],
        omega: {
          V_pub_min: 0.2, V_pub_max: 0.5,
          V_pro_min: 0.2, V_pro_max: 0.5,
          V_ind_min: 0.1, V_ind_max: 0.5
        }
      });
      fetchModels();
    } catch (error) {
      console.error("Create model error:", error);
      alert("모델 생성 중 오류가 발생했습니다.");
    }
  };

  const handleDeleteModel = async (modelId) => {
    if (!confirm("이 모델을 삭제하시겠습니까?")) return;
    
    try {
      await api.deleteModel(modelId);
      fetchModels();
    } catch (error) {
      console.error("Delete model error:", error);
      alert(error.response?.data?.detail || "모델 삭제 중 오류가 발생했습니다.");
    }
  };

  const sigmaSum = newModel.sigma.reduce((a, b) => a + b, 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-100">분배 모델 관리</h2>
          <p className="text-slate-400 text-sm">특허6: 4100 모델 저장부 - 다중 모델 전환</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={fetchModels} disabled={loading}>
            <RefreshCw className={`w-4 h-4 mr-1 ${loading ? 'animate-spin' : ''}`} /> 새로고침
          </Button>
          <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
            <DialogTrigger asChild>
              <Button size="sm" className="bg-violet-600 hover:bg-violet-500" data-testid="create-model-button">
                <Plus className="w-4 h-4 mr-1" /> 새 모델 생성
              </Button>
            </DialogTrigger>
            <DialogContent className="bg-slate-800 border-slate-700 max-w-lg">
              <DialogHeader>
                <DialogTitle className="text-slate-100">새 분배 모델 생성</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div>
                  <label className="text-slate-300 text-sm mb-1 block">모델 이름</label>
                  <Input
                    value={newModel.name}
                    onChange={(e) => setNewModel({...newModel, name: e.target.value})}
                    placeholder="예: 커스텀 균형 모델"
                    className="bg-slate-900 border-slate-600 text-slate-100"
                  />
                </div>
                <div>
                  <label className="text-slate-300 text-sm mb-1 block">설명</label>
                  <Input
                    value={newModel.description}
                    onChange={(e) => setNewModel({...newModel, description: e.target.value})}
                    placeholder="모델에 대한 설명"
                    className="bg-slate-900 border-slate-600 text-slate-100"
                  />
                </div>
                
                {/* Sigma Sliders */}
                <div className="space-y-3">
                  <label className="text-slate-300 text-sm">분배 비율 (Σ)</label>
                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-blue-400">공공</span>
                      <span className="text-slate-400">{(newModel.sigma[0] * 100).toFixed(0)}%</span>
                    </div>
                    <Slider
                      value={[newModel.sigma[0] * 100]}
                      onValueChange={([v]) => setNewModel({
                        ...newModel, 
                        sigma: [v/100, newModel.sigma[1], newModel.sigma[2]]
                      })}
                      max={100}
                      step={5}
                      className="[&_[role=slider]]:bg-blue-500"
                    />
                  </div>
                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-emerald-400">생산</span>
                      <span className="text-slate-400">{(newModel.sigma[1] * 100).toFixed(0)}%</span>
                    </div>
                    <Slider
                      value={[newModel.sigma[1] * 100]}
                      onValueChange={([v]) => setNewModel({
                        ...newModel, 
                        sigma: [newModel.sigma[0], v/100, newModel.sigma[2]]
                      })}
                      max={100}
                      step={5}
                      className="[&_[role=slider]]:bg-emerald-500"
                    />
                  </div>
                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-amber-400">개인</span>
                      <span className="text-slate-400">{(newModel.sigma[2] * 100).toFixed(0)}%</span>
                    </div>
                    <Slider
                      value={[newModel.sigma[2] * 100]}
                      onValueChange={([v]) => setNewModel({
                        ...newModel, 
                        sigma: [newModel.sigma[0], newModel.sigma[1], v/100]
                      })}
                      max={100}
                      step={5}
                      className="[&_[role=slider]]:bg-amber-500"
                    />
                  </div>
                  <div className={`text-center text-sm py-1 rounded ${Math.abs(sigmaSum - 1.0) <= 0.01 ? 'bg-emerald-900/30 text-emerald-400' : 'bg-amber-900/30 text-amber-400'}`}>
                    합계: {sigmaSum.toFixed(2)} {Math.abs(sigmaSum - 1.0) <= 0.01 ? '✓' : '(1.0 필요)'}
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
                  취소
                </Button>
                <Button 
                  onClick={handleCreateModel}
                  disabled={!newModel.name || Math.abs(sigmaSum - 1.0) > 0.01}
                  className="bg-violet-600 hover:bg-violet-500"
                >
                  생성
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Models Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4" data-testid="models-grid">
        {models.map((model) => {
          const Icon = MODEL_ICONS[model.type] || Layers;
          const color = MODEL_COLORS[model.type] || "slate";
          const isActive = model.is_active;
          const isActivating = activating === model.id;
          
          return (
            <Card 
              key={model.id} 
              className={`bg-slate-800/50 border-slate-700 relative overflow-hidden ${isActive ? 'ring-2 ring-violet-500' : ''}`}
            >
              {isActive && (
                <div className="absolute top-0 right-0 bg-violet-500 text-white text-xs px-2 py-1 rounded-bl">
                  활성
                </div>
              )}
              <CardHeader className="pb-2">
                <CardTitle className="text-slate-100 flex items-center gap-2 text-base">
                  <Icon className={`w-5 h-5 text-${color}-400`} />
                  {model.name}
                </CardTitle>
                <CardDescription className="text-slate-400 text-xs">
                  {model.description}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {/* Sigma Display */}
                <div className="space-y-1">
                  <div className="flex items-center gap-2 text-xs">
                    <div className="w-16 text-slate-400">공공</div>
                    <div className="flex-1 h-2 bg-slate-700 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-blue-500 rounded-full" 
                        style={{ width: `${model.sigma[0] * 100}%` }}
                      />
                    </div>
                    <div className="w-10 text-right text-blue-400">{(model.sigma[0] * 100).toFixed(0)}%</div>
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    <div className="w-16 text-slate-400">생산</div>
                    <div className="flex-1 h-2 bg-slate-700 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-emerald-500 rounded-full" 
                        style={{ width: `${model.sigma[1] * 100}%` }}
                      />
                    </div>
                    <div className="w-10 text-right text-emerald-400">{(model.sigma[1] * 100).toFixed(0)}%</div>
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    <div className="w-16 text-slate-400">개인</div>
                    <div className="flex-1 h-2 bg-slate-700 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-amber-500 rounded-full" 
                        style={{ width: `${model.sigma[2] * 100}%` }}
                      />
                    </div>
                    <div className="w-10 text-right text-amber-400">{(model.sigma[2] * 100).toFixed(0)}%</div>
                  </div>
                </div>

                {/* Type Badge */}
                <div className="flex items-center justify-between">
                  <Badge variant="outline" className="text-xs">
                    {model.type === 'custom' ? '커스텀' : '기본 제공'}
                  </Badge>
                  <span className="text-slate-500 text-xs">
                    {model.created_at?.slice(0, 10)}
                  </span>
                </div>

                {/* Actions */}
                <div className="flex gap-2 pt-2">
                  {!isActive && (
                    <Button 
                      size="sm" 
                      className="flex-1 bg-violet-600 hover:bg-violet-500"
                      onClick={() => handleActivateModel(model.id)}
                      disabled={isActivating}
                      data-testid={`activate-model-${model.id}`}
                    >
                      {isActivating ? (
                        <RefreshCw className="w-4 h-4 mr-1 animate-spin" />
                      ) : (
                        <Check className="w-4 h-4 mr-1" />
                      )}
                      활성화
                    </Button>
                  )}
                  {isActive && (
                    <Button size="sm" className="flex-1" variant="secondary" disabled>
                      <Check className="w-4 h-4 mr-1" /> 사용 중
                    </Button>
                  )}
                  {model.id.startsWith('custom_') && !isActive && (
                    <Button 
                      size="sm" 
                      variant="destructive"
                      onClick={() => handleDeleteModel(model.id)}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Current Model Info */}
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader>
          <CardTitle className="text-slate-100 text-sm">현재 활성 모델 정보</CardTitle>
        </CardHeader>
        <CardContent>
          {models.find(m => m.is_active) ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-slate-900/50 rounded-lg p-3">
                <p className="text-slate-400 text-xs mb-1">모델 이름</p>
                <p className="text-slate-100 font-medium">{models.find(m => m.is_active)?.name}</p>
              </div>
              <div className="bg-slate-900/50 rounded-lg p-3">
                <p className="text-slate-400 text-xs mb-1">타입</p>
                <p className="text-slate-100 font-medium capitalize">{models.find(m => m.is_active)?.type}</p>
              </div>
              <div className="bg-slate-900/50 rounded-lg p-3">
                <p className="text-slate-400 text-xs mb-1">시그마 (Σ)</p>
                <p className="text-slate-100 font-medium">
                  {models.find(m => m.is_active)?.sigma.map(s => (s*100).toFixed(0)+'%').join(' / ')}
                </p>
              </div>
              <div className="bg-slate-900/50 rounded-lg p-3">
                <p className="text-slate-400 text-xs mb-1">생성일</p>
                <p className="text-slate-100 font-medium">{models.find(m => m.is_active)?.created_at?.slice(0, 10)}</p>
              </div>
            </div>
          ) : (
            <p className="text-slate-500 text-center py-4">활성 모델이 없습니다</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default ModelsTab;
