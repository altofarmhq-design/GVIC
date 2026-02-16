import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { 
  RefreshCw, 
  ArrowRight, 
  CheckCircle2,
  Clock,
  AlertCircle,
  Eye
} from 'lucide-react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL;

/**
 * 파이프라인 단계 모니터링 공통 컴포넌트
 */
export const PipelineStageMonitor = ({ 
  stageId, 
  stageName, 
  stageCode,
  stageColor = "blue",
  stageIcon: StageIcon,
  prevStage,
  nextStage,
  description,
  formula
}) => {
  const [signals, setSignals] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedSignal, setSelectedSignal] = useState(null);

  // 데이터 로드
  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const [signalsRes, statsRes] = await Promise.all([
        axios.get(`${API_URL}/api/pipeline/signals?stage=${stageId}&limit=50`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        axios.get(`${API_URL}/api/pipeline/stats`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
      ]);
      setSignals(Array.isArray(signalsRes.data) ? signalsRes.data : []);
      setStats(statsRes.data);
    } catch (error) {
      console.error("Failed to load pipeline data:", error);
    }
    setLoading(false);
  }, [stageId]);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, [loadData]);

  // 시그널 상세 조회
  const loadSignalDetail = async (signalId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/api/pipeline/signal/${signalId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setSelectedSignal(response.data);
    } catch (error) {
      console.error("Failed to load signal detail:", error);
    }
  };

  const stageCount = stats?.stage_counts?.[stageId] || 0;
  const completedCount = signals.filter(s => s.stages?.[stageId]?.status === 'completed').length;

  const getCategoryBadge = (category) => {
    switch(category) {
      case 'wanted': return <Badge className="bg-blue-600">원하는 것</Badge>;
      case 'unwanted': return <Badge className="bg-amber-600">자산화 대상</Badge>;
      case 'null': return <Badge className="bg-slate-600">Null</Badge>;
      default: return <Badge className="bg-slate-600">분류 중</Badge>;
    }
  };

  const getStatusBadge = (status) => {
    switch(status) {
      case 'completed': return <Badge className="bg-green-600"><CheckCircle2 className="w-3 h-3 mr-1" />완료</Badge>;
      case 'processing': return <Badge className="bg-blue-600"><Clock className="w-3 h-3 mr-1" />처리중</Badge>;
      case 'failed': return <Badge className="bg-red-600"><AlertCircle className="w-3 h-3 mr-1" />실패</Badge>;
      case 'skipped': return <Badge className="bg-slate-500">건너뜀</Badge>;
      default: return <Badge className="bg-slate-600">대기</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-100 flex items-center gap-3">
            <div className={`w-10 h-10 bg-${stageColor}-600 rounded-lg flex items-center justify-center`}>
              {StageIcon ? <StageIcon className="w-6 h-6 text-white" /> : <span className="text-white font-bold">{stageCode}</span>}
            </div>
            {stageCode}:{stageName}
          </h2>
          <p className="text-slate-400 mt-1">{description}</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={loadData} disabled={loading}>
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </Button>
          <Badge variant="outline" className={`text-${stageColor}-400 border-${stageColor}-600`}>
            특허 {stageCode}
          </Badge>
        </div>
      </div>

      {/* 통계 카드 */}
      <div className="grid grid-cols-4 gap-4">
        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="py-4 text-center">
            <p className="text-3xl font-bold text-white">{stats?.total_signals || 0}</p>
            <p className="text-slate-400 text-sm">총 시그널</p>
          </CardContent>
        </Card>
        <Card className={`bg-${stageColor}-900/30 border-${stageColor}-600`}>
          <CardContent className="py-4 text-center">
            <p className={`text-3xl font-bold text-${stageColor}-400`}>{stageCount}</p>
            <p className="text-slate-400 text-sm">현재 처리 중</p>
          </CardContent>
        </Card>
        <Card className="bg-green-900/30 border-green-600">
          <CardContent className="py-4 text-center">
            <p className="text-3xl font-bold text-green-400">{completedCount}</p>
            <p className="text-slate-400 text-sm">완료</p>
          </CardContent>
        </Card>
        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="py-4 text-center">
            <p className="text-3xl font-bold text-amber-400">{stats?.total_assets || 0}</p>
            <p className="text-slate-400 text-sm">자산화됨</p>
          </CardContent>
        </Card>
      </div>

      {/* 수식 (있는 경우) */}
      {formula && (
        <Card className="bg-slate-900/50 border-slate-700">
          <CardContent className="py-4">
            <p className="text-slate-400 text-sm mb-2">{stageName} 처리 수식</p>
            <div className="font-mono text-lg text-slate-200 bg-slate-800 rounded p-3">
              {formula}
            </div>
          </CardContent>
        </Card>
      )}

      {/* 시그널 목록 & 상세 */}
      <div className="grid grid-cols-2 gap-6">
        {/* 시그널 목록 */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader className="pb-2">
            <CardTitle className="text-slate-100 text-base">시그널 목록</CardTitle>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[300px]">
              {signals.length === 0 ? (
                <div className="text-center py-8 text-slate-500">
                  이 단계에 시그널이 없습니다
                </div>
              ) : (
                <div className="space-y-2">
                  {signals.map((sig) => (
                    <div 
                      key={sig.signal_id}
                      onClick={() => loadSignalDetail(sig.signal_id)}
                      className={`p-3 rounded-lg cursor-pointer transition-colors ${
                        selectedSignal?.signal_id === sig.signal_id 
                          ? `bg-${stageColor}-900/30 border border-${stageColor}-600`
                          : 'bg-slate-900/50 hover:bg-slate-800'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-slate-300 font-mono text-xs">
                          {sig.signal_id?.slice(0, 20)}...
                        </span>
                        {getStatusBadge(sig.status)}
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-slate-500 text-xs">{sig.type}</span>
                        {getCategoryBadge(sig.category)}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </ScrollArea>
          </CardContent>
        </Card>

        {/* 시그널 상세 */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader className="pb-2">
            <CardTitle className="text-slate-100 text-base flex items-center gap-2">
              <Eye className="w-4 h-4" /> 시그널 상세
            </CardTitle>
          </CardHeader>
          <CardContent>
            {!selectedSignal ? (
              <div className="text-center py-8 text-slate-500">
                좌측에서 시그널을 선택하세요
              </div>
            ) : (
              <ScrollArea className="h-[300px]">
                <div className="space-y-4">
                  <div>
                    <p className="text-slate-500 text-xs">시그널 ID</p>
                    <p className="text-slate-200 font-mono text-sm">{selectedSignal.signal_id}</p>
                  </div>
                  <div>
                    <p className="text-slate-500 text-xs">유형</p>
                    <p className="text-slate-200">{selectedSignal.type}</p>
                  </div>
                  <div>
                    <p className="text-slate-500 text-xs">분류</p>
                    {getCategoryBadge(selectedSignal.category)}
                  </div>
                  <div>
                    <p className="text-slate-500 text-xs">현재 단계</p>
                    <Badge variant="outline">{selectedSignal.current_stage}</Badge>
                  </div>
                  <div>
                    <p className="text-slate-500 text-xs">내용</p>
                    <p className="text-slate-300 text-sm bg-slate-900 rounded p-2 max-h-[100px] overflow-y-auto">
                      {selectedSignal.content?.slice(0, 500)}
                      {selectedSignal.content?.length > 500 && '...'}
                    </p>
                  </div>
                  <div>
                    <p className="text-slate-500 text-xs">단계별 상태</p>
                    <div className="space-y-1 mt-1">
                      {Object.entries(selectedSignal.stages || {}).map(([stage, data]) => (
                        <div key={stage} className="flex items-center justify-between text-xs">
                          <span className="text-slate-400">{stage}</span>
                          {getStatusBadge(data.status)}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </ScrollArea>
            )}
          </CardContent>
        </Card>
      </div>

      {/* 플로우 안내 */}
      <div className="flex items-center justify-center gap-2 text-slate-500 text-sm">
        {prevStage && (
          <>
            <span className="px-3 py-1 bg-slate-700 rounded">{prevStage}</span>
            <ArrowRight className="w-4 h-4" />
          </>
        )}
        <span className={`px-3 py-1 bg-${stageColor}-600/30 rounded text-${stageColor}-400`}>
          {stageCode}:{stageName}
        </span>
        {nextStage && (
          <>
            <ArrowRight className="w-4 h-4" />
            <span className="px-3 py-1 bg-slate-700 rounded">{nextStage}</span>
          </>
        )}
      </div>
    </div>
  );
};

export default PipelineStageMonitor;
