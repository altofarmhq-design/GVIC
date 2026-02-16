import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import { 
  Key, 
  Plus, 
  Trash2, 
  Copy, 
  Check,
  AlertCircle,
  Clock,
  Activity,
  Shield,
  Code,
  ExternalLink,
  Eye,
  EyeOff,
  RefreshCw,
  Zap
} from 'lucide-react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL;

/**
 * API 웹훅 관리 탭
 * - API 키 생성/관리
 * - 웹훅 사용 가이드
 * - 통계 조회
 */
export const APIWebhookTab = () => {
  const [apiKeys, setApiKeys] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [newKeyName, setNewKeyName] = useState("");
  const [newKeyDescription, setNewKeyDescription] = useState("");
  const [createdKey, setCreatedKey] = useState(null);
  const [copiedKey, setCopiedKey] = useState(null);
  const [showUsageGuide, setShowUsageGuide] = useState(false);
  const [webhookHealth, setWebhookHealth] = useState(null);

  // API 키 목록 조회
  const fetchApiKeys = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_URL}/api/webhook/keys`);
      setApiKeys(response.data.keys || []);
      setError(null);
    } catch (err) {
      setError("API 키 목록을 불러올 수 없습니다");
    }
    setLoading(false);
  };

  // 웹훅 상태 확인
  const checkWebhookHealth = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/webhook/health`);
      setWebhookHealth(response.data);
    } catch (err) {
      setWebhookHealth({ status: "error" });
    }
  };

  useEffect(() => {
    fetchApiKeys();
    checkWebhookHealth();
  }, []);

  // 새 API 키 생성
  const createApiKey = async () => {
    if (!newKeyName.trim()) {
      setError("API 키 이름을 입력해주세요");
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API_URL}/api/webhook/keys`, {
        name: newKeyName,
        description: newKeyDescription,
        rate_limit: 100,
        allowed_types: ["text", "json", "event"]
      });
      
      setCreatedKey(response.data);
      setNewKeyName("");
      setNewKeyDescription("");
      fetchApiKeys();
      setError(null);
    } catch (err) {
      setError("API 키 생성에 실패했습니다");
    }
    setLoading(false);
  };

  // API 키 삭제
  const deleteApiKey = async (keyId) => {
    if (!window.confirm("이 API 키를 삭제하시겠습니까?")) return;
    
    try {
      await axios.delete(`${API_URL}/api/webhook/keys/${keyId}`);
      fetchApiKeys();
    } catch (err) {
      setError("API 키 삭제에 실패했습니다");
    }
  };

  // API 키 복사
  const copyToClipboard = (text, keyId) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(keyId);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-100 flex items-center gap-3">
            <div className="w-10 h-10 bg-purple-600 rounded-lg flex items-center justify-center">
              <Key className="w-5 h-5 text-white" />
            </div>
            API 연동
          </h2>
          <p className="text-slate-400 mt-1">외부 시스템에서 시그널을 수신하는 웹훅 API 관리</p>
        </div>
        <div className="flex items-center gap-2">
          {webhookHealth && (
            <Badge 
              variant="outline" 
              className={webhookHealth.status === "healthy" ? "text-green-400 border-green-600" : "text-red-400 border-red-600"}
            >
              <Activity className="w-3 h-3 mr-1" />
              {webhookHealth.status === "healthy" ? "서비스 정상" : "서비스 오류"}
            </Badge>
          )}
          <Button variant="outline" size="sm" onClick={fetchApiKeys}>
            <RefreshCw className="w-4 h-4 mr-1" />
            새로고침
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* 좌측: API 키 관리 */}
        <div className="space-y-4">
          {/* 새 API 키 생성 */}
          <Card className="bg-gradient-to-r from-purple-900/30 to-slate-800/50 border-purple-700">
            <CardHeader className="pb-3">
              <CardTitle className="text-slate-100 text-lg flex items-center gap-2">
                <Plus className="w-5 h-5 text-purple-400" />
                새 API 키 생성
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label className="text-slate-300 text-sm">키 이름 *</Label>
                <Input
                  placeholder="예: Production API, Test Key"
                  value={newKeyName}
                  onChange={(e) => setNewKeyName(e.target.value)}
                  className="bg-slate-900 border-slate-600 text-slate-100 mt-1"
                />
              </div>
              <div>
                <Label className="text-slate-300 text-sm">설명 (선택)</Label>
                <Input
                  placeholder="이 API 키의 용도를 설명해주세요"
                  value={newKeyDescription}
                  onChange={(e) => setNewKeyDescription(e.target.value)}
                  className="bg-slate-900 border-slate-600 text-slate-100 mt-1"
                />
              </div>
              <Button 
                onClick={createApiKey} 
                disabled={loading || !newKeyName.trim()}
                className="w-full bg-purple-600 hover:bg-purple-700"
              >
                <Key className="w-4 h-4 mr-2" />
                API 키 생성
              </Button>
            </CardContent>
          </Card>

          {/* 생성된 키 표시 (한 번만) */}
          {createdKey && (
            <Card className="bg-green-900/30 border-green-600">
              <CardContent className="py-4">
                <div className="flex items-start gap-3">
                  <Check className="w-5 h-5 text-green-400 mt-0.5" />
                  <div className="flex-1">
                    <p className="text-green-300 font-medium mb-2">API 키가 생성되었습니다!</p>
                    <p className="text-slate-400 text-xs mb-2">
                      ⚠️ 이 키는 다시 표시되지 않습니다. 안전한 곳에 저장하세요.
                    </p>
                    <div className="flex items-center gap-2">
                      <code className="bg-slate-800 px-3 py-2 rounded text-green-400 text-sm flex-1 overflow-hidden text-ellipsis">
                        {createdKey.api_key}
                      </code>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => copyToClipboard(createdKey.api_key, "new")}
                      >
                        {copiedKey === "new" ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                      </Button>
                    </div>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="mt-2 text-slate-400"
                      onClick={() => setCreatedKey(null)}
                    >
                      닫기
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* 에러 메시지 */}
          {error && (
            <div className="bg-red-900/30 border border-red-600 rounded-lg p-3 text-red-400 text-sm flex items-center gap-2">
              <AlertCircle className="w-4 h-4" />
              {error}
            </div>
          )}

          {/* API 키 목록 */}
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader className="pb-2">
              <CardTitle className="text-slate-100 text-base flex items-center justify-between">
                <span className="flex items-center gap-2">
                  <Shield className="w-4 h-4 text-blue-400" />
                  API 키 목록
                </span>
                <Badge variant="outline" className="text-slate-400">
                  {apiKeys.length}개
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[300px]">
                {apiKeys.length === 0 ? (
                  <div className="text-center py-8">
                    <Key className="w-12 h-12 text-slate-600 mx-auto mb-2" />
                    <p className="text-slate-500">생성된 API 키가 없습니다</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {apiKeys.map((key) => (
                      <div 
                        key={key.key_id} 
                        className="bg-slate-900 rounded-lg p-4 border border-slate-700"
                      >
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <span className="text-slate-100 font-medium">{key.name}</span>
                            <Badge 
                              variant="outline" 
                              className={key.is_active ? "text-green-400 border-green-600 text-xs" : "text-red-400 border-red-600 text-xs"}
                            >
                              {key.is_active ? "활성" : "비활성"}
                            </Badge>
                          </div>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="text-red-400 hover:text-red-300 hover:bg-red-900/30"
                            onClick={() => deleteApiKey(key.key_id)}
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                        
                        {key.description && (
                          <p className="text-slate-500 text-xs mb-2">{key.description}</p>
                        )}
                        
                        <div className="grid grid-cols-3 gap-2 text-xs">
                          <div>
                            <span className="text-slate-500">요청 수</span>
                            <p className="text-slate-300">{key.request_count || 0}</p>
                          </div>
                          <div>
                            <span className="text-slate-500">제한</span>
                            <p className="text-slate-300">{key.rate_limit}/시간</p>
                          </div>
                          <div>
                            <span className="text-slate-500">마지막 사용</span>
                            <p className="text-slate-300">
                              {key.last_used ? new Date(key.last_used).toLocaleDateString('ko-KR') : '-'}
                            </p>
                          </div>
                        </div>
                        
                        <div className="mt-2 flex gap-1">
                          {key.allowed_types?.map((type) => (
                            <Badge key={type} variant="secondary" className="text-xs bg-slate-800">
                              {type}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </ScrollArea>
            </CardContent>
          </Card>
        </div>

        {/* 우측: 사용 가이드 */}
        <div className="space-y-4">
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader className="pb-2">
              <CardTitle className="text-slate-100 text-base flex items-center gap-2">
                <Code className="w-4 h-4 text-green-400" />
                API 사용 가이드
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* 엔드포인트 정보 */}
              <div>
                <p className="text-slate-400 text-sm mb-2">Base URL</p>
                <code className="block bg-slate-900 px-3 py-2 rounded text-blue-400 text-sm">
                  {API_URL}/api/webhook
                </code>
              </div>

              {/* 인증 방법 */}
              <div>
                <p className="text-slate-400 text-sm mb-2">인증 헤더</p>
                <code className="block bg-slate-900 px-3 py-2 rounded text-green-400 text-sm">
                  X-API-Key: gvic_your_api_key_here
                </code>
              </div>

              {/* 단일 시그널 전송 */}
              <div>
                <p className="text-slate-300 text-sm font-medium mb-2">단일 시그널 전송</p>
                <pre className="bg-slate-900 p-3 rounded text-xs text-slate-300 overflow-x-auto">
{`curl -X POST "${API_URL}/api/webhook/signal" \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: YOUR_API_KEY" \\
  -d '{
    "type": "text",
    "content": "분석할 내용",
    "analysis_type": "general",
    "priority": "normal"
  }'`}
                </pre>
              </div>

              {/* 배치 전송 */}
              <div>
                <p className="text-slate-300 text-sm font-medium mb-2">배치 시그널 전송 (최대 100개)</p>
                <pre className="bg-slate-900 p-3 rounded text-xs text-slate-300 overflow-x-auto">
{`curl -X POST "${API_URL}/api/webhook/signal/batch" \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: YOUR_API_KEY" \\
  -d '{
    "signals": [
      {"type": "text", "content": "첫 번째 시그널"},
      {"type": "text", "content": "두 번째 시그널"}
    ]
  }'`}
                </pre>
              </div>

              {/* 이벤트 전송 */}
              <div>
                <p className="text-slate-300 text-sm font-medium mb-2">이벤트 전송</p>
                <pre className="bg-slate-900 p-3 rounded text-xs text-slate-300 overflow-x-auto">
{`curl -X POST "${API_URL}/api/webhook/event" \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: YOUR_API_KEY" \\
  -d '{
    "event_type": "user_action",
    "payload": {"action": "click", "target": "button"}
  }'`}
                </pre>
              </div>

              {/* 응답 예시 */}
              <div>
                <p className="text-slate-300 text-sm font-medium mb-2">응답 예시</p>
                <pre className="bg-slate-900 p-3 rounded text-xs text-green-400 overflow-x-auto">
{`{
  "success": true,
  "signal_id": "SIG_abc123",
  "category": "wanted",
  "status": "completed",
  "message": "시그널이 성공적으로 처리되었습니다"
}`}
                </pre>
              </div>
            </CardContent>
          </Card>

          {/* 시그널 유형 설명 */}
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader className="pb-2">
              <CardTitle className="text-slate-100 text-base flex items-center gap-2">
                <Zap className="w-4 h-4 text-amber-400" />
                파라미터 설명
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 text-sm">
                <div>
                  <p className="text-slate-300 font-medium">type</p>
                  <p className="text-slate-500">text, json, event</p>
                </div>
                <div>
                  <p className="text-slate-300 font-medium">analysis_type</p>
                  <p className="text-slate-500">general (일반), code (코드), patent_idea (특허/아이디어)</p>
                </div>
                <div>
                  <p className="text-slate-300 font-medium">priority</p>
                  <p className="text-slate-500">low, normal, high, critical</p>
                </div>
                <div>
                  <p className="text-slate-300 font-medium">metadata</p>
                  <p className="text-slate-500">추가 메타데이터 (JSON 객체)</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default APIWebhookTab;
