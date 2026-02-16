/**
 * API Guide Tab - API 키 및 연동 가이드
 * API 키 발급, 문서화, 코드 샘플 제공
 */
import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from '@/components/ui/dialog';
import { 
  Key, Copy, Check, RefreshCw, Trash2, Plus, Code, 
  BookOpen, Terminal, Webhook, Shield, Clock, Eye, EyeOff
} from 'lucide-react';
import { api } from '@/lib/api';
import { toast } from 'sonner';

export default function ApiGuideTab() {
  const [apiKeys, setApiKeys] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showKey, setShowKey] = useState({});
  const [copied, setCopied] = useState(null);
  const [newKeyDialogOpen, setNewKeyDialogOpen] = useState(false);
  const [keyForm, setKeyForm] = useState({
    name: '',
    permissions: ['read', 'analyze'],
    rate_limit: 1000
  });
  const [newKeyValue, setNewKeyValue] = useState(null);
  
  // 웹훅 설정 상태
  const [webhookUrl, setWebhookUrl] = useState('');
  const [subscribedEvents, setSubscribedEvents] = useState({
    analysis_complete: true,
    complaint_alert: true,
    insight_summary: true
  });

  const toggleEvent = (event) => {
    setSubscribedEvents(prev => ({
      ...prev,
      [event]: !prev[event]
    }));
  };

  const fetchApiKeys = async () => {
    setLoading(true);
    try {
      const res = await api.getApiKeys();
      setApiKeys(res.data?.api_keys || []);
    } catch (error) {
      console.error('API Keys fetch error:', error);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchApiKeys();
  }, []);

  const handleCreateKey = async () => {
    try {
      const res = await api.createApiKey(keyForm);
      setNewKeyValue(res.data?.api_key);
      toast.success('API 키가 생성되었습니다');
      fetchApiKeys();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'API 키 생성에 실패했습니다');
    }
  };

  const handleRevokeKey = async (keyId) => {
    if (!window.confirm('이 API 키를 폐기하시겠습니까? 이 작업은 되돌릴 수 없습니다.')) return;
    try {
      await api.revokeApiKey(keyId);
      toast.success('API 키가 폐기되었습니다');
      fetchApiKeys();
    } catch (error) {
      toast.error('API 키 폐기에 실패했습니다');
    }
  };

  const copyToClipboard = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopied(id);
    setTimeout(() => setCopied(null), 2000);
    toast.success('클립보드에 복사되었습니다');
  };

  const BASE_URL = process.env.REACT_APP_BACKEND_URL || 'https://api.gvic.com';

  // 코드 샘플
  const codeSamples = {
    curl: `# 제품 분석 요청
curl -X POST "${BASE_URL}/api/insights/analyze/{product_id}" \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "reviews": [
      {"content": "배송이 빠르고 품질이 좋아요", "rating": 5},
      {"content": "가격 대비 괜찮은 제품입니다", "rating": 4}
    ],
    "analysis_depth": "standard"
  }'`,
    python: `import requests

API_KEY = "YOUR_API_KEY"
BASE_URL = "${BASE_URL}"

def analyze_product(product_id, reviews):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "reviews": reviews,
        "analysis_depth": "standard"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/insights/analyze/{product_id}",
        headers=headers,
        json=payload
    )
    
    return response.json()

# 사용 예시
reviews = [
    {"content": "배송이 빠르고 품질이 좋아요", "rating": 5},
    {"content": "가격 대비 괜찮은 제품입니다", "rating": 4}
]

result = analyze_product("product_123", reviews)
print(result)`,
    javascript: `const API_KEY = 'YOUR_API_KEY';
const BASE_URL = '${BASE_URL}';

async function analyzeProduct(productId, reviews) {
  const response = await fetch(
    \`\${BASE_URL}/api/insights/analyze/\${productId}\`,
    {
      method: 'POST',
      headers: {
        'Authorization': \`Bearer \${API_KEY}\`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        reviews,
        analysis_depth: 'standard'
      })
    }
  );
  
  return response.json();
}

// 사용 예시
const reviews = [
  { content: '배송이 빠르고 품질이 좋아요', rating: 5 },
  { content: '가격 대비 괜찮은 제품입니다', rating: 4 }
];

analyzeProduct('product_123', reviews)
  .then(result => console.log(result));`
  };

  return (
    <div className="space-y-6" data-testid="api-guide-tab">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">API 연동 가이드</h2>
          <p className="text-slate-400">API 키를 발급받고 연동하세요</p>
        </div>
        <Button onClick={fetchApiKeys} variant="outline" size="sm">
          <RefreshCw className="w-4 h-4 mr-2" /> 새로고침
        </Button>
      </div>

      <Tabs defaultValue="keys" className="space-y-4">
        <TabsList className="bg-slate-800">
          <TabsTrigger value="keys" className="data-[state=active]:bg-violet-600">
            <Key className="w-4 h-4 mr-2" /> API 키 관리
          </TabsTrigger>
          <TabsTrigger value="docs" className="data-[state=active]:bg-violet-600">
            <BookOpen className="w-4 h-4 mr-2" /> API 문서
          </TabsTrigger>
          <TabsTrigger value="samples" className="data-[state=active]:bg-violet-600">
            <Code className="w-4 h-4 mr-2" /> 코드 샘플
          </TabsTrigger>
          <TabsTrigger value="webhook" className="data-[state=active]:bg-violet-600">
            <Webhook className="w-4 h-4 mr-2" /> 웹훅 설정
          </TabsTrigger>
        </TabsList>

        {/* API 키 관리 */}
        <TabsContent value="keys" className="space-y-4">
          <div className="flex justify-end">
            <Dialog open={newKeyDialogOpen} onOpenChange={(open) => {
              setNewKeyDialogOpen(open);
              if (!open) setNewKeyValue(null);
            }}>
              <DialogTrigger asChild>
                <Button className="bg-violet-600 hover:bg-violet-700">
                  <Plus className="w-4 h-4 mr-2" /> 새 API 키 생성
                </Button>
              </DialogTrigger>
              <DialogContent className="bg-slate-900 border-slate-700">
                <DialogHeader>
                  <DialogTitle className="text-white">새 API 키 생성</DialogTitle>
                  <DialogDescription>
                    API 키 이름과 권한을 설정하세요
                  </DialogDescription>
                </DialogHeader>
                
                {newKeyValue ? (
                  <div className="py-4 space-y-4">
                    <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-lg">
                      <p className="text-emerald-400 text-sm mb-2 flex items-center gap-2">
                        <Shield className="w-4 h-4" />
                        API 키가 생성되었습니다. 이 키는 다시 표시되지 않으니 안전하게 보관하세요.
                      </p>
                      <div className="flex items-center gap-2 mt-3">
                        <Input 
                          value={newKeyValue} 
                          readOnly 
                          className="bg-slate-800 font-mono text-sm"
                        />
                        <Button size="sm" onClick={() => copyToClipboard(newKeyValue, 'new')}>
                          {copied === 'new' ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                        </Button>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="py-4 space-y-4">
                    <div className="space-y-2">
                      <Label>키 이름</Label>
                      <Input 
                        value={keyForm.name}
                        onChange={(e) => setKeyForm({ ...keyForm, name: e.target.value })}
                        placeholder="예: Production API Key"
                        className="bg-slate-800 border-slate-700"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>일일 요청 제한</Label>
                      <Input 
                        type="number"
                        value={keyForm.rate_limit}
                        onChange={(e) => setKeyForm({ ...keyForm, rate_limit: parseInt(e.target.value) })}
                        className="bg-slate-800 border-slate-700"
                      />
                    </div>
                  </div>
                )}

                <DialogFooter>
                  {newKeyValue ? (
                    <Button onClick={() => { setNewKeyDialogOpen(false); setNewKeyValue(null); }}>
                      완료
                    </Button>
                  ) : (
                    <>
                      <Button variant="outline" onClick={() => setNewKeyDialogOpen(false)}>취소</Button>
                      <Button onClick={handleCreateKey} className="bg-violet-600 hover:bg-violet-700">생성</Button>
                    </>
                  )}
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>

          {loading ? (
            <div className="flex items-center justify-center h-32">
              <RefreshCw className="w-6 h-6 animate-spin text-violet-500" />
            </div>
          ) : apiKeys.length === 0 ? (
            <Card className="bg-slate-800/50 border-slate-700 border-dashed">
              <CardContent className="p-12 text-center">
                <Key className="w-12 h-12 text-slate-500 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-white mb-2">API 키가 없습니다</h3>
                <p className="text-slate-400 mb-4">첫 번째 API 키를 생성하세요</p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-3">
              {apiKeys.map((key) => (
                <Card key={key.key_id} className="bg-slate-800/50 border-slate-700">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 bg-violet-500/20 rounded-lg flex items-center justify-center">
                          <Key className="w-5 h-5 text-violet-400" />
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <h4 className="text-white font-medium">{key.name}</h4>
                            {key.is_active ? (
                              <Badge className="bg-emerald-500/20 text-emerald-400">활성</Badge>
                            ) : (
                              <Badge className="bg-slate-600">비활성</Badge>
                            )}
                          </div>
                          <div className="flex items-center gap-2 mt-1">
                            <code className="text-slate-400 text-sm font-mono">
                              {showKey[key.key_id] ? key.key_preview : `${key.key_preview?.slice(0, 12)}...`}
                            </code>
                            <Button 
                              variant="ghost" 
                              size="sm" 
                              onClick={() => setShowKey({ ...showKey, [key.key_id]: !showKey[key.key_id] })}
                            >
                              {showKey[key.key_id] ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
                            </Button>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="text-right text-sm">
                          <p className="text-slate-400">
                            <Clock className="w-3 h-3 inline mr-1" />
                            {new Date(key.created_at).toLocaleDateString('ko-KR')} 생성
                          </p>
                          <p className="text-slate-500">
                            요청 {key.request_count || 0} / {key.rate_limit}/일
                          </p>
                        </div>
                        <Button 
                          variant="ghost" 
                          size="sm"
                          onClick={() => handleRevokeKey(key.key_id)}
                          className="text-red-400 hover:text-red-300"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* API 문서 */}
        <TabsContent value="docs" className="space-y-4">
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white">API 엔드포인트</CardTitle>
              <CardDescription>GVIC 셀러 인텔리전스 허브 API</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <EndpointDoc 
                method="POST"
                path="/api/insights/analyze/{product_id}"
                description="제품 리뷰를 분석하여 4대 인사이트를 추출합니다"
                params={[
                  { name: 'product_id', type: 'string', description: '분석할 제품 ID' },
                  { name: 'reviews', type: 'array', description: '리뷰 목록 [{content, rating}]' },
                  { name: 'analysis_depth', type: 'string', description: 'quick | standard | deep' }
                ]}
              />
              <EndpointDoc 
                method="GET"
                path="/api/insights/product/{product_id}"
                description="제품의 최근 분석 결과를 조회합니다"
                params={[
                  { name: 'product_id', type: 'string', description: '제품 ID' }
                ]}
              />
              <EndpointDoc 
                method="GET"
                path="/api/assets/checklist/{hs_code}"
                description="품목군별 개선점 체크리스트를 조회합니다"
                params={[
                  { name: 'hs_code', type: 'string', description: 'HS Code (예: 8518)' }
                ]}
              />
              <EndpointDoc 
                method="POST"
                path="/api/shop/shops"
                description="새 쇼핑몰을 등록합니다"
                params={[
                  { name: 'name', type: 'string', description: '쇼핑몰 이름' },
                  { name: 'platform', type: 'string', description: 'naver | coupang | 11st | gmarket | self' },
                  { name: 'url', type: 'string', description: '쇼핑몰 URL' }
                ]}
              />
            </CardContent>
          </Card>
        </TabsContent>

        {/* 코드 샘플 */}
        <TabsContent value="samples" className="space-y-4">
          <Tabs defaultValue="curl">
            <TabsList className="bg-slate-800">
              <TabsTrigger value="curl">
                <Terminal className="w-4 h-4 mr-2" /> cURL
              </TabsTrigger>
              <TabsTrigger value="python">
                🐍 Python
              </TabsTrigger>
              <TabsTrigger value="javascript">
                📜 JavaScript
              </TabsTrigger>
            </TabsList>
            
            {Object.entries(codeSamples).map(([lang, code]) => (
              <TabsContent key={lang} value={lang}>
                <Card className="bg-slate-900 border-slate-700">
                  <CardContent className="p-0">
                    <div className="flex justify-between items-center px-4 py-2 border-b border-slate-700">
                      <span className="text-slate-400 text-sm">{lang}.{lang === 'curl' ? 'sh' : lang === 'python' ? 'py' : 'js'}</span>
                      <Button 
                        variant="ghost" 
                        size="sm"
                        onClick={() => copyToClipboard(code, lang)}
                      >
                        {copied === lang ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                      </Button>
                    </div>
                    <pre className="p-4 overflow-x-auto text-sm text-slate-300 font-mono">
                      {code}
                    </pre>
                  </CardContent>
                </Card>
              </TabsContent>
            ))}
          </Tabs>
        </TabsContent>

        {/* 웹훅 설정 */}
        <TabsContent value="webhook" className="space-y-4">
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Webhook className="w-5 h-5 text-violet-400" />
                웹훅 설정
              </CardTitle>
              <CardDescription>
                분석 완료 시 자동으로 알림을 받으세요
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>웹훅 URL</Label>
                <Input 
                  placeholder="https://your-server.com/webhook/gvic"
                  className="bg-slate-900 border-slate-700"
                />
              </div>
              <div className="space-y-2">
                <Label>이벤트 구독</Label>
                <div className="flex flex-wrap gap-2">
                  {['analysis_complete', 'complaint_alert', 'insight_summary'].map(event => (
                    <Badge key={event} className="bg-violet-500/20 text-violet-400 cursor-pointer">
                      <Check className="w-3 h-3 mr-1" /> {event}
                    </Badge>
                  ))}
                </div>
              </div>
              <div className="p-4 bg-slate-900 rounded-lg">
                <p className="text-slate-400 text-sm mb-2">웹훅 페이로드 예시</p>
                <pre className="text-sm text-slate-300 font-mono overflow-x-auto">
{`{
  "event": "analysis_complete",
  "product_id": "prod_123",
  "timestamp": "2024-01-15T10:30:00Z",
  "insights": {
    "strengths": 5,
    "suggestions": 3,
    "complaints": 2,
    "new_needs": 1
  }
}`}
                </pre>
              </div>
              <Button className="bg-violet-600 hover:bg-violet-700">
                웹훅 저장
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

// API 문서 컴포넌트
function EndpointDoc({ method, path, description, params }) {
  const methodColors = {
    GET: 'bg-emerald-500',
    POST: 'bg-blue-500',
    PUT: 'bg-orange-500',
    DELETE: 'bg-red-500'
  };

  return (
    <div className="p-4 bg-slate-900 rounded-lg">
      <div className="flex items-center gap-3 mb-2">
        <Badge className={methodColors[method]}>{method}</Badge>
        <code className="text-violet-400 font-mono">{path}</code>
      </div>
      <p className="text-slate-300 text-sm mb-3">{description}</p>
      <div className="space-y-2">
        {params.map(param => (
          <div key={param.name} className="flex items-start gap-2 text-sm">
            <code className="text-emerald-400 font-mono">{param.name}</code>
            <span className="text-slate-500">({param.type})</span>
            <span className="text-slate-400">- {param.description}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
