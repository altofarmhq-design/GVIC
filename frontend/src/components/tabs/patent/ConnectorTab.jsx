import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { 
  Plug, 
  Play, 
  CheckCircle,
  XCircle,
  Clock,
  Zap,
  RefreshCw,
  Settings,
  FileText,
  Send,
  BarChart3,
  ArrowRight,
  Workflow,
  Calendar,
  Globe,
  Code
} from 'lucide-react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL;

/**
 * 외부 연동 커넥터 탭
 * - Zapier, n8n, Make 등 연동 준비
 * - 시뮬레이션 테스트
 * - 워크플로우 테스트
 */
export const ConnectorTab = () => {
  const [integrations, setIntegrations] = useState([]);
  const [selectedIntegration, setSelectedIntegration] = useState(null);
  const [eventLog, setEventLog] = useState([]);
  const [loading, setLoading] = useState(false);
  const [simulateContent, setSimulateContent] = useState("");
  const [simulateResult, setSimulateResult] = useState(null);
  const [useCases, setUseCases] = useState([]);
  const [activeTab, setActiveTab] = useState("integrations"); // integrations, simulate, workflows

  // 연동 목록 조회
  const fetchIntegrations = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/connector/integrations`);
      setIntegrations(response.data.integrations || []);
    } catch (err) {
      console.error("Failed to fetch integrations:", err);
    }
  };

  // 이벤트 로그 조회
  const fetchEventLog = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/connector/events/log?limit=20`);
      setEventLog(response.data.events || []);
    } catch (err) {
      console.error("Failed to fetch event log:", err);
    }
  };

  // 활용 사례 조회
  const fetchUseCases = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/connector/guide/use-cases`);
      setUseCases(response.data.use_cases || []);
    } catch (err) {
      console.error("Failed to fetch use cases:", err);
    }
  };

  useEffect(() => {
    fetchIntegrations();
    fetchEventLog();
    fetchUseCases();
  }, []);

  // 연동 상세 정보 조회
  const selectIntegration = async (integrationId) => {
    try {
      const response = await axios.get(`${API_URL}/api/connector/integrations/${integrationId}`);
      setSelectedIntegration(response.data);
    } catch (err) {
      console.error("Failed to fetch integration detail:", err);
    }
  };

  // 시그널 시뮬레이션
  const runSimulation = async () => {
    if (!simulateContent.trim()) return;
    
    setLoading(true);
    try {
      const response = await axios.post(`${API_URL}/api/connector/simulate/signal`, {
        source: "manual_test",
        signal_type: "text",
        content: simulateContent
      });
      setSimulateResult(response.data);
      fetchEventLog();
    } catch (err) {
      setSimulateResult({ success: false, error: err.message });
    }
    setLoading(false);
  };

  // 배치 시뮬레이션
  const runBatchSimulation = async (count = 5) => {
    setLoading(true);
    try {
      const response = await axios.post(`${API_URL}/api/connector/simulate/batch?count=${count}`);
      setSimulateResult(response.data);
      fetchEventLog();
    } catch (err) {
      setSimulateResult({ success: false, error: err.message });
    }
    setLoading(false);
  };

  // 워크플로우 시뮬레이션
  const runWorkflowSimulation = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${API_URL}/api/connector/simulate/workflow`);
      setSimulateResult(response.data);
      fetchEventLog();
    } catch (err) {
      setSimulateResult({ success: false, error: err.message });
    }
    setLoading(false);
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case "connected":
        return <Badge className="bg-green-600">연결됨</Badge>;
      case "ready":
        return <Badge className="bg-blue-600">준비됨</Badge>;
      case "error":
        return <Badge className="bg-red-600">오류</Badge>;
      default:
        return <Badge className="bg-slate-600">{status}</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-100 flex items-center gap-3">
            <div className="w-10 h-10 bg-indigo-600 rounded-lg flex items-center justify-center">
              <Plug className="w-5 h-5 text-white" />
            </div>
            외부 연동 커넥터
          </h2>
          <p className="text-slate-400 mt-1">Zapier, n8n, Make 등 자동화 도구 연동 준비 및 테스트</p>
        </div>
        <Button variant="outline" size="sm" onClick={() => { fetchIntegrations(); fetchEventLog(); }}>
          <RefreshCw className="w-4 h-4 mr-1" />
          새로고침
        </Button>
      </div>

      {/* 탭 선택 */}
      <div className="flex gap-2 bg-slate-800/50 p-1 rounded-lg w-fit">
        {[
          { id: "integrations", label: "연동 플랫폼", icon: Globe },
          { id: "simulate", label: "시뮬레이션", icon: Play },
          { id: "workflows", label: "활용 사례", icon: Workflow }
        ].map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-md transition-all ${
                activeTab === tab.id
                  ? 'bg-indigo-600 text-white'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* 연동 플랫폼 탭 */}
      {activeTab === "integrations" && (
        <div className="grid grid-cols-2 gap-6">
          {/* 좌측: 플랫폼 목록 */}
          <div className="space-y-4">
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader className="pb-2">
                <CardTitle className="text-slate-100 text-base">지원 플랫폼</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {integrations.map((integration) => (
                    <div
                      key={integration.id}
                      onClick={() => selectIntegration(integration.id)}
                      className={`p-4 rounded-lg cursor-pointer transition-all border ${
                        selectedIntegration?.id === integration.id
                          ? 'bg-indigo-900/30 border-indigo-600'
                          : 'bg-slate-900 border-slate-700 hover:border-slate-600'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-3">
                          <span className="text-2xl">{integration.icon}</span>
                          <div>
                            <p className="text-slate-100 font-medium">{integration.name}</p>
                            <p className="text-slate-500 text-xs">{integration.description}</p>
                          </div>
                        </div>
                        {getStatusBadge(integration.status)}
                      </div>
                      <div className="flex gap-4 text-xs text-slate-500 mt-2">
                        <span>트리거: {integration.triggers_count}개</span>
                        <span>액션: {integration.actions_count}개</span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* 우측: 상세 정보 */}
          <div className="space-y-4">
            {selectedIntegration ? (
              <>
                <Card className="bg-slate-800/50 border-slate-700">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-slate-100 text-base flex items-center gap-2">
                      <span className="text-2xl">{selectedIntegration.icon}</span>
                      {selectedIntegration.name} 연동 가이드
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ScrollArea className="h-[400px]">
                      <pre className="text-slate-300 text-sm whitespace-pre-wrap font-mono bg-slate-900 p-4 rounded-lg">
                        {selectedIntegration.setup_guide}
                      </pre>
                    </ScrollArea>
                  </CardContent>
                </Card>

                {/* 트리거 & 액션 */}
                <div className="grid grid-cols-2 gap-4">
                  <Card className="bg-slate-800/50 border-slate-700">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-slate-100 text-sm flex items-center gap-2">
                        <Zap className="w-4 h-4 text-amber-400" />
                        트리거
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        {selectedIntegration.triggers?.map((trigger) => (
                          <div key={trigger.id} className="bg-slate-900 rounded p-2">
                            <p className="text-slate-200 text-sm">{trigger.name}</p>
                            <p className="text-slate-500 text-xs">{trigger.description}</p>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="bg-slate-800/50 border-slate-700">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-slate-100 text-sm flex items-center gap-2">
                        <Play className="w-4 h-4 text-green-400" />
                        액션
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        {selectedIntegration.actions?.map((action) => (
                          <div key={action.id} className="bg-slate-900 rounded p-2">
                            <p className="text-slate-200 text-sm">{action.name}</p>
                            <p className="text-slate-500 text-xs">{action.description}</p>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </>
            ) : (
              <Card className="bg-slate-800/30 border-slate-700 border-dashed h-full flex items-center justify-center min-h-[400px]">
                <div className="text-center py-8">
                  <Settings className="w-16 h-16 text-slate-600 mx-auto mb-4" />
                  <p className="text-slate-500 text-lg">연동 플랫폼을 선택하세요</p>
                  <p className="text-slate-600 text-sm mt-2">설정 가이드를 확인할 수 있습니다</p>
                </div>
              </Card>
            )}
          </div>
        </div>
      )}

      {/* 시뮬레이션 탭 */}
      {activeTab === "simulate" && (
        <div className="grid grid-cols-2 gap-6">
          {/* 좌측: 시뮬레이션 실행 */}
          <div className="space-y-4">
            {/* 단일 시그널 시뮬레이션 */}
            <Card className="bg-gradient-to-r from-indigo-900/30 to-slate-800/50 border-indigo-700">
              <CardHeader className="pb-2">
                <CardTitle className="text-slate-100 text-base flex items-center gap-2">
                  <Send className="w-5 h-5 text-indigo-400" />
                  시그널 시뮬레이션
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <Textarea
                  placeholder="시뮬레이션할 시그널 내용을 입력하세요..."
                  value={simulateContent}
                  onChange={(e) => setSimulateContent(e.target.value)}
                  className="bg-slate-900 border-slate-600 text-slate-100 min-h-[100px]"
                />
                <Button 
                  onClick={runSimulation}
                  disabled={loading || !simulateContent.trim()}
                  className="w-full bg-indigo-600 hover:bg-indigo-700"
                >
                  {loading ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <Play className="w-4 h-4 mr-2" />}
                  시뮬레이션 실행
                </Button>
              </CardContent>
            </Card>

            {/* 배치 시뮬레이션 */}
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader className="pb-2">
                <CardTitle className="text-slate-100 text-base flex items-center gap-2">
                  <BarChart3 className="w-5 h-5 text-green-400" />
                  배치 시뮬레이션
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-slate-400 text-sm mb-3">
                  여러 시그널을 동시에 처리하는 테스트입니다.
                </p>
                <div className="flex gap-2">
                  <Button 
                    variant="outline" 
                    onClick={() => runBatchSimulation(3)}
                    disabled={loading}
                  >
                    3개 테스트
                  </Button>
                  <Button 
                    variant="outline" 
                    onClick={() => runBatchSimulation(5)}
                    disabled={loading}
                  >
                    5개 테스트
                  </Button>
                  <Button 
                    variant="outline" 
                    onClick={() => runBatchSimulation(10)}
                    disabled={loading}
                  >
                    10개 테스트
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* 워크플로우 시뮬레이션 */}
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader className="pb-2">
                <CardTitle className="text-slate-100 text-base flex items-center gap-2">
                  <Workflow className="w-5 h-5 text-purple-400" />
                  전체 워크플로우 테스트
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-slate-400 text-sm mb-3">
                  시그널 수신 → AI 분석 → 분류 → 완료까지 전 과정을 테스트합니다.
                </p>
                <Button 
                  onClick={runWorkflowSimulation}
                  disabled={loading}
                  className="w-full bg-purple-600 hover:bg-purple-700"
                >
                  {loading ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <Workflow className="w-4 h-4 mr-2" />}
                  워크플로우 실행
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* 우측: 결과 및 로그 */}
          <div className="space-y-4">
            {/* 시뮬레이션 결과 */}
            {simulateResult && (
              <Card className={`border ${simulateResult.success ? 'bg-green-900/20 border-green-600' : 'bg-red-900/20 border-red-600'}`}>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base flex items-center gap-2">
                    {simulateResult.success ? (
                      <CheckCircle className="w-5 h-5 text-green-400" />
                    ) : (
                      <XCircle className="w-5 h-5 text-red-400" />
                    )}
                    <span className={simulateResult.success ? 'text-green-300' : 'text-red-300'}>
                      시뮬레이션 결과
                    </span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <pre className="text-slate-300 text-xs bg-slate-900 p-3 rounded overflow-auto max-h-[200px]">
                    {JSON.stringify(simulateResult, null, 2)}
                  </pre>
                </CardContent>
              </Card>
            )}

            {/* 이벤트 로그 */}
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader className="pb-2">
                <CardTitle className="text-slate-100 text-base flex items-center justify-between">
                  <span className="flex items-center gap-2">
                    <Clock className="w-4 h-4 text-slate-400" />
                    이벤트 로그
                  </span>
                  <Badge variant="outline" className="text-slate-400">
                    {eventLog.length}건
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[300px]">
                  {eventLog.length === 0 ? (
                    <div className="text-center py-8">
                      <FileText className="w-12 h-12 text-slate-600 mx-auto mb-2" />
                      <p className="text-slate-500">이벤트 로그가 없습니다</p>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {eventLog.map((event, idx) => (
                        <div key={idx} className="bg-slate-900 rounded p-3 text-sm">
                          <div className="flex items-center justify-between mb-1">
                            <Badge variant="outline" className="text-xs">
                              {event.type}
                            </Badge>
                            <span className="text-slate-500 text-xs">
                              {new Date(event.timestamp).toLocaleTimeString('ko-KR')}
                            </span>
                          </div>
                          {event.signal_id && (
                            <p className="text-slate-400 text-xs">Signal: {event.signal_id}</p>
                          )}
                          {event.source && (
                            <p className="text-slate-400 text-xs">Source: {event.source}</p>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </ScrollArea>
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* 활용 사례 탭 */}
      {activeTab === "workflows" && (
        <div className="grid grid-cols-2 gap-6">
          {useCases.map((useCase) => (
            <Card key={useCase.id} className="bg-slate-800/50 border-slate-700 hover:border-indigo-600 transition-all">
              <CardHeader className="pb-2">
                <CardTitle className="text-slate-100 text-base">{useCase.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-slate-400 text-sm mb-4">{useCase.description}</p>
                
                <div className="flex items-center gap-2 mb-3">
                  <Badge className="bg-blue-600/30 text-blue-300">{useCase.trigger}</Badge>
                  <ArrowRight className="w-4 h-4 text-slate-500" />
                  <Badge className="bg-green-600/30 text-green-300">{useCase.action}</Badge>
                </div>
                
                <div className="flex gap-2">
                  {useCase.platforms.map((platform) => (
                    <Badge key={platform} variant="outline" className="text-slate-400 text-xs">
                      {platform}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default ConnectorTab;
