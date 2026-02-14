import { useState, useCallback, useEffect } from "react";
import axios from "axios";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { 
  Play, 
  RotateCcw, 
  Zap,
  FileText,
  ArrowRight,
  ArrowDown,
  Database,
  TrendingUp,
  BarChart3,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Layers,
  Target,
  Sparkles,
  Save,
  Search,
  User,
  Hash,
  Box,
  GitBranch,
  Eye,
  MessageSquare,
  Tag,
  Lightbulb
} from 'lucide-react';
import { Input } from "@/components/ui/input";

const API_URL = process.env.REACT_APP_BACKEND_URL;

export const GVICShowcaseTab = () => {
  // 입력 상태
  const [content, setContent] = useState("");
  
  // 분석 결과
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // 자산 상태
  const [assets, setAssets] = useState([]);
  const [assetStats, setAssetStats] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  
  // 탭
  const [activeView, setActiveView] = useState("flow");

  // 자산 목록 로드
  const loadAssets = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/api/gvic-assets`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setAssets(response.data.assets || []);
      setAssetStats(response.data.stats || null);
    } catch (err) {
      console.error("Failed to load assets:", err);
    }
  }, []);

  useEffect(() => {
    loadAssets();
  }, [loadAssets]);

  // AI 분석 실행
  const handleAnalyze = useCallback(async () => {
    if (!content.trim()) {
      setError("텍스트를 입력해주세요.");
      return;
    }
    
    setLoading(true);
    setError(null);
    setResult(null);
    
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API_URL}/api/signal-tracer/ai-analyze`, {
        content: content
      }, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setResult(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || "분석 중 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  }, [content]);

  // 자산으로 저장
  const handleSaveAsset = useCallback(async () => {
    if (!result) return;
    
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API_URL}/api/gvic-assets`, {
        content,
        rating: 5,
        analysis_result: result
      }, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      loadAssets();
      alert("자산으로 저장되었습니다!");
    } catch (err) {
      console.error("Failed to save asset:", err);
      alert("저장 실패");
    }
  }, [content, result, loadAssets]);

  // 샘플 데이터
  const samples = [
    { label: "상품 후기", content: "효과가 정말 좋아요! 포장도 꼼꼼하고 배송도 빨랐어요. 재구매 의사 있습니다." },
    { label: "요구사항", content: "실제 시그널이 어떻게 gvic에서 가공되고 결과를 얻게 되는 구나를 알 수 있어야 겠지. 모니터 화면에 꽉차게 시각적 구현하는 것도 좋겠다." },
    { label: "체념적 만족", content: "두 번째 구매할 때 2kg를 주문했는데 키로 수도 맛도 믿음이 안 갔는데. 사장님께서 직접 전화 주시고 친절하게 대응하시기에 미안함도 있고. 맛은 맛있어요. 그냥 그것에 만족할게요." },
  ];

  // 초기화
  const handleReset = () => {
    setContent("");
    setResult(null);
    setError(null);
  };

  return (
    <div className="h-[calc(100vh-140px)] flex flex-col">
      {/* 헤더 */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            <Sparkles className="w-6 h-6 text-amber-400" />
            GVIC 쇼케이스
          </h2>
          <p className="text-slate-400 text-sm">AI 기반 시그널 감지 및 모듈화 시스템</p>
        </div>
        
        <div className="flex gap-2">
          <Button
            variant={activeView === "flow" ? "default" : "outline"}
            onClick={() => setActiveView("flow")}
            className="gap-2"
          >
            <Zap className="w-4 h-4" /> 시그널 분석
          </Button>
          <Button
            variant={activeView === "assets" ? "default" : "outline"}
            onClick={() => setActiveView("assets")}
            className="gap-2"
          >
            <Database className="w-4 h-4" /> 자산 저장소
          </Button>
        </div>
      </div>

      {/* 메인 컨텐츠 */}
      {activeView === "flow" && (
        <div className="flex-1 grid grid-cols-5 gap-4">
          {/* 좌측: 입력 */}
          <div className="col-span-2 flex flex-col gap-4">
            <Card className="bg-slate-800/50 border-slate-700 flex-1">
              <CardHeader className="pb-3">
                <CardTitle className="text-slate-100 text-lg flex items-center gap-2">
                  <FileText className="w-5 h-5 text-blue-400" />
                  시그널 입력
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <Textarea
                  placeholder="분석할 텍스트를 입력하세요... (어떤 형태든 가능)"
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  className="bg-slate-900 border-slate-600 text-slate-100 min-h-[180px] text-base"
                />
                
                {/* 샘플 */}
                <div>
                  <p className="text-slate-400 text-xs mb-2">샘플 텍스트:</p>
                  <div className="flex flex-wrap gap-1">
                    {samples.map((s, i) => (
                      <Button
                        key={i}
                        variant="outline"
                        size="sm"
                        onClick={() => setContent(s.content)}
                        className="text-xs h-7"
                      >
                        {s.label}
                      </Button>
                    ))}
                  </div>
                </div>

                <div className="flex gap-2">
                  <Button 
                    onClick={handleAnalyze}
                    disabled={loading || !content.trim()}
                    className="flex-1 gap-2 bg-violet-600 hover:bg-violet-700 h-12 text-base"
                  >
                    {loading ? (
                      <>
                        <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        AI 분석 중...
                      </>
                    ) : (
                      <>
                        <Zap className="w-5 h-5" />
                        AI 분석 시작
                      </>
                    )}
                  </Button>
                  <Button variant="outline" onClick={handleReset} className="h-12">
                    <RotateCcw className="w-5 h-5" />
                  </Button>
                </div>

                {error && (
                  <div className="bg-red-900/30 border border-red-600 rounded-lg p-3 text-red-400 text-sm">
                    {error}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* 우측: 결과 */}
          <div className="col-span-3 flex flex-col gap-4">
            {!result ? (
              <Card className="bg-slate-800/30 border-slate-700 border-dashed flex-1 flex items-center justify-center">
                <div className="text-center py-12">
                  <Sparkles className="w-16 h-16 text-slate-600 mx-auto mb-4" />
                  <p className="text-slate-500 text-lg">텍스트를 입력하고 "AI 분석 시작" 버튼을 클릭하세요</p>
                  <p className="text-slate-600 text-sm mt-2">
                    GVIC가 시그널 유형을 자동 감지하고 특징을 추출합니다
                  </p>
                </div>
              </Card>
            ) : (
              <ScrollArea className="flex-1">
                <div className="space-y-4 pr-4">
                  {/* ID 체계 */}
                  <Card className="bg-slate-900/50 border-slate-700">
                    <CardContent className="py-4">
                      <div className="flex items-center justify-between mb-3">
                        <h3 className="text-slate-300 font-medium flex items-center gap-2">
                          <GitBranch className="w-4 h-4 text-violet-400" />
                          ID 추적 체계
                        </h3>
                        <Button size="sm" onClick={handleSaveAsset} className="gap-1 bg-amber-600 hover:bg-amber-700">
                          <Save className="w-4 h-4" /> 자산 저장
                        </Button>
                      </div>
                      <div className="grid grid-cols-4 gap-3 text-xs">
                        <div className="bg-slate-800 rounded p-2">
                          <p className="text-slate-500 flex items-center gap-1"><User className="w-3 h-3" /> 요구자</p>
                          <p className="text-slate-300 font-mono truncate">{result.requester_id}</p>
                        </div>
                        <div className="bg-slate-800 rounded p-2">
                          <p className="text-slate-500 flex items-center gap-1"><FileText className="w-3 h-3" /> 입력</p>
                          <p className="text-blue-400 font-mono truncate">{result.input_id}</p>
                        </div>
                        <div className="bg-slate-800 rounded p-2">
                          <p className="text-slate-500 flex items-center gap-1"><Box className="w-3 h-3" /> 모듈</p>
                          <p className="text-emerald-400 font-mono truncate">{result.module_id}</p>
                        </div>
                        <div className="bg-slate-800 rounded p-2">
                          <p className="text-slate-500 flex items-center gap-1"><Hash className="w-3 h-3" /> 시그널</p>
                          <p className="text-amber-400 font-mono">{result.signal_count}개</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  {/* 시그널 유형 감지 */}
                  <Card className="bg-gradient-to-r from-violet-900/30 to-blue-900/30 border-violet-600">
                    <CardContent className="py-4">
                      <div className="flex items-start gap-4">
                        <div className="w-16 h-16 bg-violet-600 rounded-xl flex items-center justify-center">
                          <Eye className="w-8 h-8 text-white" />
                        </div>
                        <div className="flex-1">
                          <p className="text-slate-400 text-xs">1단계: 시그널 유형 감지</p>
                          <h3 className="text-2xl font-bold text-white mt-1">
                            {result.signal_type_label}
                          </h3>
                          <div className="flex items-center gap-2 mt-2">
                            <Badge className={`${
                              result.signal_type_confidence >= 0.8 ? 'bg-green-600' :
                              result.signal_type_confidence >= 0.5 ? 'bg-yellow-600' : 'bg-red-600'
                            }`}>
                              신뢰도 {(result.signal_type_confidence * 100).toFixed(0)}%
                            </Badge>
                            <span className="text-slate-400 text-sm">{result.signal_type}</span>
                          </div>
                          <p className="text-slate-300 text-sm mt-2">{result.signal_type_reason}</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  {/* 발견된 시그널들 */}
                  <Card className="bg-slate-800/50 border-slate-700">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-slate-100 text-base flex items-center gap-2">
                        <Zap className="w-5 h-5 text-amber-400" />
                        2단계: 발견된 시그널 ({result.signal_count}개)
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        {result.discovered_signals.map((sig, idx) => (
                          <div key={sig.signal_id} className="bg-slate-900/50 rounded-lg p-3 border-l-4 border-amber-500">
                            <div className="flex items-start justify-between mb-2">
                              <div className="flex items-center gap-2">
                                <span className="text-amber-400 font-mono text-xs">{sig.signal_id}</span>
                                <Badge variant="outline" className={`text-xs ${
                                  sig.sentiment === 'positive' ? 'text-green-400 border-green-600' :
                                  sig.sentiment === 'negative' ? 'text-red-400 border-red-600' :
                                  sig.sentiment === 'mixed' ? 'text-purple-400 border-purple-600' :
                                  'text-slate-400 border-slate-600'
                                }`}>
                                  {sig.sentiment}
                                </Badge>
                                <Badge className="bg-slate-700 text-xs">{sig.type}</Badge>
                              </div>
                              <span className="text-slate-500 text-xs">
                                강도: {(sig.intensity * 100).toFixed(0)}%
                              </span>
                            </div>
                            <p className="text-slate-200 text-sm mb-2">"{sig.text}"</p>
                            <p className="text-slate-400 text-xs mb-1">
                              <span className="text-slate-500">맥락:</span> {sig.context}
                            </p>
                            {sig.hidden_meaning && (
                              <p className="text-violet-400 text-xs flex items-start gap-1">
                                <Lightbulb className="w-3 h-3 mt-0.5 flex-shrink-0" />
                                <span className="text-slate-500">숨겨진 의미:</span> {sig.hidden_meaning}
                              </p>
                            )}
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>

                  {/* 분석 요약 */}
                  <Card className="bg-slate-800/50 border-slate-700">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-slate-100 text-base flex items-center gap-2">
                        <MessageSquare className="w-5 h-5 text-blue-400" />
                        3단계: 모듈화 결과
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {/* 요약 */}
                      <div className="bg-slate-900/50 rounded-lg p-3">
                        <p className="text-slate-400 text-xs mb-1">요약</p>
                        <p className="text-slate-200">{result.summary}</p>
                      </div>

                      {/* 주요 테마 */}
                      <div>
                        <p className="text-slate-400 text-xs mb-2">주요 테마</p>
                        <div className="flex flex-wrap gap-2">
                          {result.key_themes.map((theme, idx) => (
                            <Badge key={idx} variant="outline" className="text-slate-300 border-slate-600">
                              <Tag className="w-3 h-3 mr-1" />
                              {theme}
                            </Badge>
                          ))}
                        </div>
                      </div>

                      {/* 전체 감성 */}
                      <div className="flex items-center gap-4">
                        <div>
                          <p className="text-slate-400 text-xs mb-1">전체 감성</p>
                          <Badge className={`${
                            result.overall_sentiment === 'positive' ? 'bg-green-600' :
                            result.overall_sentiment === 'negative' ? 'bg-red-600' :
                            result.overall_sentiment === 'mixed' ? 'bg-purple-600' :
                            'bg-slate-600'
                          }`}>
                            {result.overall_sentiment}
                          </Badge>
                        </div>
                        <Separator orientation="vertical" className="h-8 bg-slate-700" />
                        <div>
                          <p className="text-slate-400 text-xs mb-1">3관점 분석 적용</p>
                          <div className="flex gap-2">
                            <Badge variant="outline" className={result.applicable_perspectives?.society ? 'text-blue-400 border-blue-600' : 'text-slate-600 border-slate-700'}>
                              🏛️ 사회
                            </Badge>
                            <Badge variant="outline" className={result.applicable_perspectives?.production ? 'text-emerald-400 border-emerald-600' : 'text-slate-600 border-slate-700'}>
                              🏭 생산
                            </Badge>
                            <Badge variant="outline" className={result.applicable_perspectives?.consumer ? 'text-amber-400 border-amber-600' : 'text-slate-600 border-slate-700'}>
                              👤 소비자
                            </Badge>
                          </div>
                        </div>
                      </div>

                      {/* 3관점 적용 이유 */}
                      {result.perspective_relevance && (
                        <div className="bg-slate-900/50 rounded-lg p-3">
                          <p className="text-slate-400 text-xs mb-1">3관점 분석 적합성</p>
                          <p className="text-slate-300 text-sm">{result.perspective_relevance}</p>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </div>
              </ScrollArea>
            )}
          </div>
        </div>
      )}

      {activeView === "assets" && (
        <AssetStorageView
          assets={assets}
          stats={assetStats}
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
          onRefresh={loadAssets}
        />
      )}
    </div>
  );
};

// ==================== 자산화창고 뷰 ====================
const AssetStorageView = ({ assets, stats, searchQuery, setSearchQuery, onRefresh }) => {
  const [selectedAsset, setSelectedAsset] = useState(null);
  const [warehouseData, setWarehouseData] = useState(null);
  const [searchResults, setSearchResults] = useState(null);
  const [searching, setSearching] = useState(false);
  
  // 자산화창고 데이터 로드
  const loadWarehouse = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/api/gvic-warehouse`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setWarehouseData(response.data);
    } catch (err) {
      console.error("Failed to load warehouse:", err);
    }
  }, []);

  useEffect(() => {
    loadWarehouse();
  }, [loadWarehouse]);

  // 자연어 검색
  const handleNLSearch = useCallback(async () => {
    if (!searchQuery.trim()) {
      setSearchResults(null);
      return;
    }
    
    setSearching(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API_URL}/api/gvic-warehouse/search`, {
        query: searchQuery
      }, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setSearchResults(response.data);
    } catch (err) {
      console.error("Search failed:", err);
    }
    setSearching(false);
  }, [searchQuery]);

  // 엔터키로 검색
  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleNLSearch();
    }
  };

  return (
    <div className="flex-1 flex flex-col gap-4">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <Database className="w-6 h-6 text-amber-400" />
            자산화창고
          </h2>
          <p className="text-slate-400 text-sm">유사 모듈 탑 10 - 궁금증을 자아내는 쇼케이스</p>
        </div>
        <Button variant="outline" onClick={() => { loadWarehouse(); onRefresh(); }} size="sm">
          <RotateCcw className="w-4 h-4" />
        </Button>
      </div>

      {/* 통계 요약 */}
      {warehouseData && (
        <div className="grid grid-cols-5 gap-4">
          <Card className="bg-slate-800/50 border-slate-700">
            <CardContent className="py-3 text-center">
              <p className="text-2xl font-bold text-white">{warehouseData.total_showcase || 0}</p>
              <p className="text-slate-400 text-xs">공개 모듈</p>
            </CardContent>
          </Card>
          <Card className="bg-slate-800/50 border-slate-700">
            <CardContent className="py-3 text-center">
              <p className="text-2xl font-bold text-green-400">{warehouseData.sentiment_stats?.positive || 0}</p>
              <p className="text-slate-400 text-xs">긍정</p>
            </CardContent>
          </Card>
          <Card className="bg-slate-800/50 border-slate-700">
            <CardContent className="py-3 text-center">
              <p className="text-2xl font-bold text-purple-400">{warehouseData.sentiment_stats?.mixed || 0}</p>
              <p className="text-slate-400 text-xs">혼합</p>
            </CardContent>
          </Card>
          <Card className="bg-slate-800/50 border-slate-700">
            <CardContent className="py-3 text-center">
              <p className="text-2xl font-bold text-yellow-400">{warehouseData.sentiment_stats?.neutral || 0}</p>
              <p className="text-slate-400 text-xs">중립</p>
            </CardContent>
          </Card>
          <Card className="bg-slate-800/50 border-slate-700">
            <CardContent className="py-3 text-center">
              <p className="text-2xl font-bold text-red-400">{warehouseData.sentiment_stats?.negative || 0}</p>
              <p className="text-slate-400 text-xs">부정</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* 자연어 검색 */}
      <Card className="bg-slate-800/50 border-slate-700">
        <CardContent className="py-4">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <Input
                placeholder="자연어로 검색하세요... (예: 배송이 빠른 긍정적인 후기)"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={handleKeyPress}
                className="pl-10 bg-slate-900 border-slate-600 text-slate-100"
              />
            </div>
            <Button 
              onClick={handleNLSearch} 
              disabled={searching}
              className="bg-amber-600 hover:bg-amber-700"
            >
              {searching ? (
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <Search className="w-4 h-4" />
              )}
            </Button>
          </div>
          
          {/* 검색 분석 결과 */}
          {searchResults?.analysis && (
            <div className="mt-3 p-2 bg-slate-900/50 rounded-lg text-xs">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-slate-500">검색 의도:</span>
                <span className="text-slate-300">{searchResults.analysis.intent}</span>
                <span className="text-slate-600">|</span>
                <span className="text-slate-500">키워드:</span>
                {searchResults.analysis.keywords.map((kw, i) => (
                  <Badge key={i} variant="outline" className="text-xs text-amber-400 border-amber-600">
                    {kw}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* 검색 결과 또는 탑 10 */}
      {searchResults ? (
        // 검색 결과
        <Card className="flex-1 bg-slate-800/50 border-slate-700">
          <CardHeader className="pb-2">
            <CardTitle className="text-slate-100 text-base flex items-center justify-between">
              <span className="flex items-center gap-2">
                <Search className="w-5 h-5 text-amber-400" />
                검색 결과 ({searchResults.count}건)
              </span>
              <Button variant="ghost" size="sm" onClick={() => { setSearchResults(null); setSearchQuery(''); }}>
                <RotateCcw className="w-4 h-4 mr-1" /> 초기화
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[350px]">
              {searchResults.results.length === 0 ? (
                <div className="text-center py-8 text-slate-500">
                  <Search className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>검색 결과가 없습니다</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {searchResults.results.map((asset, idx) => (
                    <AssetCard key={asset.asset_id || idx} asset={asset} />
                  ))}
                </div>
              )}
            </ScrollArea>
          </CardContent>
        </Card>
      ) : (
        // 탑 10 유사 모듈
        <Card className="flex-1 bg-slate-800/50 border-slate-700">
          <CardHeader className="pb-2">
            <CardTitle className="text-slate-100 text-base flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-amber-400" />
              유사 모듈 탑 10
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[350px]">
              {!warehouseData?.top_modules?.length ? (
                <div className="text-center py-8 text-slate-500">
                  <Database className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>아직 자산화된 모듈이 없습니다</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {warehouseData.top_modules.map((module, idx) => (
                    <div key={idx} className="bg-slate-900/50 rounded-lg p-4 border border-slate-700">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 bg-amber-600 rounded-full flex items-center justify-center text-white font-bold text-sm">
                            {idx + 1}
                          </div>
                          <div>
                            <h4 className="text-slate-100 font-medium">{module.signal_type || '알 수 없음'}</h4>
                            <p className="text-slate-500 text-xs">{module.count}개 모듈</p>
                          </div>
                        </div>
                        <Badge className="bg-amber-600 text-white">{module.count}</Badge>
                      </div>
                      
                      {/* 샘플 모듈들 */}
                      {module.samples?.length > 0 && (
                        <div className="space-y-2">
                          {module.samples.map((sample, sidx) => (
                            <div key={sidx} className="bg-slate-800 rounded p-2 text-sm">
                              <p className="text-slate-300 line-clamp-2">{sample.summary || '요약 없음'}</p>
                              <div className="flex items-center gap-2 mt-1">
                                <Badge variant="outline" className={`text-xs ${
                                  sample.overall_sentiment === 'positive' ? 'text-green-400 border-green-600' :
                                  sample.overall_sentiment === 'negative' ? 'text-red-400 border-red-600' :
                                  sample.overall_sentiment === 'mixed' ? 'text-purple-400 border-purple-600' :
                                  'text-slate-400 border-slate-600'
                                }`}>
                                  {sample.classification || sample.overall_sentiment}
                                </Badge>
                                {sample.key_themes?.slice(0, 2).map((theme, tidx) => (
                                  <Badge key={tidx} variant="outline" className="text-xs text-slate-400 border-slate-600">
                                    {theme}
                                  </Badge>
                                ))}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </ScrollArea>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default GVICShowcaseTab;
