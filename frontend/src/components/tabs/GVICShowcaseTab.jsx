import { useState, useCallback, useEffect, useRef } from "react";
import axios from "axios";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Slider } from "@/components/ui/slider";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  Play, 
  RotateCcw, 
  Zap,
  FileText,
  ArrowRight,
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
  Eye,
  Search,
  Filter
} from 'lucide-react';
import { Input } from "@/components/ui/input";

const API_URL = process.env.REACT_APP_BACKEND_URL;

export const GVICShowcaseTab = () => {
  // 입력 상태
  const [content, setContent] = useState("");
  const [rating, setRating] = useState(4);
  
  // 파라미터
  const [sigma, setSigma] = useState([0.33, 0.34, 0.33]);
  
  // 분석 결과
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [animationStep, setAnimationStep] = useState(0);
  const [isAnimating, setIsAnimating] = useState(false);
  
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

  // 분석 및 애니메이션 실행
  const handleAnalyze = useCallback(async () => {
    if (!content.trim()) return;
    
    setLoading(true);
    setIsAnimating(true);
    setAnimationStep(0);
    setResult(null);
    
    // 애니메이션 시퀀스
    const steps = [1, 2, 3, 4, 5];
    for (let i = 0; i < steps.length; i++) {
      await new Promise(resolve => setTimeout(resolve, 600));
      setAnimationStep(steps[i]);
    }
    
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API_URL}/api/signal-tracer/analyze`, {
        content,
        rating,
        sigma
      }, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setResult(response.data);
    } catch (err) {
      console.error("Analysis failed:", err);
    } finally {
      setLoading(false);
      setIsAnimating(false);
    }
  }, [content, rating, sigma]);

  // 자산으로 저장
  const handleSaveAsset = useCallback(async () => {
    if (!result) return;
    
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API_URL}/api/gvic-assets`, {
        content,
        rating,
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
  }, [content, rating, result, loadAssets]);

  // 샘플 데이터
  const samples = [
    { content: "효과가 정말 좋아요! 포장도 꼼꼼하고 배송도 빨랐어요.", rating: 5 },
    { content: "가격이 좀 비싸요. 효과는 있는데 환경에 안 좋은 플라스틱이 아쉬워요.", rating: 3 },
    { content: "배송이 지연되었고 포장이 파손되어 왔어요. 실망입니다.", rating: 1 },
  ];

  return (
    <div className="h-[calc(100vh-140px)] flex flex-col">
      {/* 헤더 */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            <Sparkles className="w-6 h-6 text-amber-400" />
            GVIC 쇼케이스
          </h2>
          <p className="text-slate-400 text-sm">시그널이 GVIC에서 어떻게 가공되어 자산이 되는지 확인하세요</p>
        </div>
        
        <div className="flex gap-2">
          <Button
            variant={activeView === "flow" ? "default" : "outline"}
            onClick={() => setActiveView("flow")}
            className="gap-2"
          >
            <Zap className="w-4 h-4" /> 시그널 흐름
          </Button>
          <Button
            variant={activeView === "assets" ? "default" : "outline"}
            onClick={() => setActiveView("assets")}
            className="gap-2"
          >
            <Database className="w-4 h-4" /> 자산 저장소
          </Button>
          <Button
            variant={activeView === "usage" ? "default" : "outline"}
            onClick={() => setActiveView("usage")}
            className="gap-2"
          >
            <TrendingUp className="w-4 h-4" /> 활용 현황
          </Button>
        </div>
      </div>

      {/* 메인 컨텐츠 */}
      {activeView === "flow" && (
        <SignalFlowView
          content={content}
          setContent={setContent}
          rating={rating}
          setRating={setRating}
          sigma={sigma}
          setSigma={setSigma}
          samples={samples}
          result={result}
          loading={loading}
          animationStep={animationStep}
          isAnimating={isAnimating}
          onAnalyze={handleAnalyze}
          onSaveAsset={handleSaveAsset}
          onReset={() => { setContent(""); setResult(null); setAnimationStep(0); }}
        />
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

      {activeView === "usage" && (
        <AssetUsageView stats={assetStats} assets={assets} />
      )}
    </div>
  );
};

// ==================== 시그널 흐름 뷰 ====================
const SignalFlowView = ({
  content, setContent, rating, setRating, sigma, setSigma,
  samples, result, loading, animationStep, isAnimating,
  onAnalyze, onSaveAsset, onReset
}) => {
  const steps = [
    { id: 1, name: "입력", icon: FileText, color: "blue" },
    { id: 2, name: "표준화", icon: Layers, color: "emerald" },
    { id: 3, name: "시그널분석", icon: Zap, color: "violet" },
    { id: 4, name: "수렴", icon: Target, color: "amber" },
    { id: 5, name: "출력", icon: BarChart3, color: "rose" },
  ];

  return (
    <div className="flex-1 flex flex-col gap-4">
      {/* 파이프라인 시각화 */}
      <Card className="bg-slate-900/50 border-slate-700">
        <CardContent className="py-6">
          <div className="flex items-center justify-between px-8">
            {steps.map((step, idx) => (
              <div key={step.id} className="flex items-center">
                <div className={`
                  flex flex-col items-center transition-all duration-500
                  ${animationStep >= step.id ? 'scale-110' : 'scale-100 opacity-50'}
                `}>
                  <div className={`
                    w-16 h-16 rounded-full flex items-center justify-center
                    transition-all duration-500
                    ${animationStep >= step.id 
                      ? `bg-${step.color}-500 shadow-lg shadow-${step.color}-500/50` 
                      : 'bg-slate-700'}
                  `}
                  style={{
                    backgroundColor: animationStep >= step.id 
                      ? step.color === 'blue' ? '#3b82f6'
                      : step.color === 'emerald' ? '#10b981'
                      : step.color === 'violet' ? '#8b5cf6'
                      : step.color === 'amber' ? '#f59e0b'
                      : '#f43f5e'
                      : '#334155',
                    boxShadow: animationStep >= step.id 
                      ? `0 0 20px ${
                        step.color === 'blue' ? '#3b82f680'
                        : step.color === 'emerald' ? '#10b98180'
                        : step.color === 'violet' ? '#8b5cf680'
                        : step.color === 'amber' ? '#f59e0b80'
                        : '#f43f5e80'
                      }`
                      : 'none'
                  }}
                  >
                    <step.icon className={`w-8 h-8 ${animationStep >= step.id ? 'text-white' : 'text-slate-500'}`} />
                  </div>
                  <span className={`mt-2 text-sm font-medium ${animationStep >= step.id ? 'text-slate-200' : 'text-slate-500'}`}>
                    {step.name}
                  </span>
                </div>
                
                {idx < steps.length - 1 && (
                  <div className="mx-4 flex items-center">
                    <div className={`
                      w-20 h-1 rounded transition-all duration-500
                      ${animationStep > step.id ? 'bg-gradient-to-r from-slate-400 to-slate-400' : 'bg-slate-700'}
                    `}
                    style={{
                      background: animationStep > step.id 
                        ? 'linear-gradient(90deg, #94a3b8, #94a3b8)'
                        : '#334155'
                    }}
                    />
                    <ArrowRight className={`w-5 h-5 mx-1 ${animationStep > step.id ? 'text-slate-400' : 'text-slate-700'}`} />
                  </div>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* 입력 및 결과 */}
      <div className="flex-1 grid grid-cols-2 gap-4">
        {/* 좌측: 입력 */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader className="pb-3">
            <CardTitle className="text-slate-100 text-lg flex items-center gap-2">
              <FileText className="w-5 h-5 text-blue-400" />
              입력 데이터
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Textarea
              placeholder="분석할 후기를 입력하세요..."
              value={content}
              onChange={(e) => setContent(e.target.value)}
              className="bg-slate-900 border-slate-600 text-slate-100 min-h-[100px]"
            />
            
            <div>
              <label className="text-slate-300 text-sm flex justify-between mb-2">
                <span>평점</span>
                <span className="text-yellow-400">{"⭐".repeat(rating)}</span>
              </label>
              <Slider
                value={[rating]}
                onValueChange={([v]) => setRating(v)}
                min={1}
                max={5}
                step={1}
                className="[&_[role=slider]]:bg-yellow-500"
              />
            </div>

            {/* 시그마 설정 */}
            <div className="space-y-2">
              <p className="text-slate-300 text-sm font-medium">관점 비중 (Σ)</p>
              <div className="grid grid-cols-3 gap-2 text-xs text-center">
                <div>
                  <span className="text-blue-400">🏛️ {(sigma[0]*100).toFixed(0)}%</span>
                </div>
                <div>
                  <span className="text-emerald-400">🏭 {(sigma[1]*100).toFixed(0)}%</span>
                </div>
                <div>
                  <span className="text-amber-400">👤 {(sigma[2]*100).toFixed(0)}%</span>
                </div>
              </div>
            </div>

            {/* 샘플 */}
            <div className="flex flex-wrap gap-1">
              {samples.map((s, i) => (
                <Button
                  key={i}
                  variant="ghost"
                  size="sm"
                  onClick={() => { setContent(s.content); setRating(s.rating); }}
                  className="text-xs h-7"
                >
                  샘플 {i+1}
                </Button>
              ))}
            </div>

            <div className="flex gap-2">
              <Button 
                onClick={onAnalyze}
                disabled={loading || !content.trim()}
                className="flex-1 gap-2 bg-violet-600 hover:bg-violet-700"
              >
                {loading ? (
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <Play className="w-4 h-4" />
                )}
                {loading ? "분석 중..." : "분석 시작"}
              </Button>
              <Button variant="outline" onClick={onReset} className="gap-2">
                <RotateCcw className="w-4 h-4" />
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* 우측: 결과 */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader className="pb-3 flex flex-row items-center justify-between">
            <CardTitle className="text-slate-100 text-lg flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-rose-400" />
              분석 결과
            </CardTitle>
            {result && (
              <Button size="sm" onClick={onSaveAsset} className="gap-1 bg-amber-600 hover:bg-amber-700">
                <Save className="w-4 h-4" /> 자산 저장
              </Button>
            )}
          </CardHeader>
          <CardContent>
            {!result ? (
              <div className="h-[300px] flex items-center justify-center text-slate-500">
                {isAnimating ? (
                  <div className="text-center">
                    <div className="w-12 h-12 border-4 border-violet-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
                    <p>시그널 처리 중...</p>
                  </div>
                ) : (
                  <p>후기를 입력하고 분석을 시작하세요</p>
                )}
              </div>
            ) : (
              <ScrollArea className="h-[300px]">
                <div className="space-y-4 pr-4">
                  {/* 최종 점수 */}
                  <div className="text-center py-4 bg-slate-900/50 rounded-lg">
                    <div className={`
                      inline-flex items-center justify-center w-20 h-20 rounded-full
                      ${result.steps.step5_output.final_score.color === 'green' ? 'bg-green-900/50 border-2 border-green-500' :
                        result.steps.step5_output.final_score.color === 'red' ? 'bg-red-900/50 border-2 border-red-500' :
                        'bg-yellow-900/50 border-2 border-yellow-500'}
                    `}>
                      <div>
                        <p className="text-3xl font-bold text-white">{result.steps.step5_output.final_score.value}</p>
                        <p className="text-xs text-slate-400">/100</p>
                      </div>
                    </div>
                    <Badge className={`mt-2 ${
                      result.steps.step5_output.final_score.color === 'green' ? 'bg-green-600' :
                      result.steps.step5_output.final_score.color === 'red' ? 'bg-red-600' : 'bg-yellow-600'
                    }`}>
                      {result.steps.step5_output.final_score.classification}
                    </Badge>
                  </div>

                  {/* 시그널 분포 */}
                  <div className="space-y-2">
                    <p className="text-slate-300 text-sm font-medium">시그널 분포</p>
                    {[
                      { key: 'V_pub', label: '🏛️ 사회·규제', color: 'bg-blue-500' },
                      { key: 'V_pro', label: '🏭 기업·생산', color: 'bg-emerald-500' },
                      { key: 'V_ind', label: '👤 소비자·고객', color: 'bg-amber-500' }
                    ].map(({ key, label, color }) => (
                      <div key={key} className="flex items-center gap-2">
                        <span className="text-slate-400 text-xs w-24">{label}</span>
                        <div className="flex-1 h-5 bg-slate-700 rounded overflow-hidden">
                          <div className={`h-full ${color} transition-all duration-1000`}
                            style={{ width: `${result.steps.step4_convergence.distribution.after_adjustment[key]}%` }}
                          />
                        </div>
                        <span className="text-slate-300 text-sm w-12 text-right">
                          {result.steps.step4_convergence.distribution.after_adjustment[key]}%
                        </span>
                      </div>
                    ))}
                  </div>

                  {/* 감지된 키워드 */}
                  <div>
                    <p className="text-slate-300 text-sm font-medium mb-2">감지된 키워드</p>
                    <div className="flex flex-wrap gap-1">
                      {Object.entries(result.steps.step3_signal.keyword_analysis).map(([domain, data]) => (
                        <>
                          {data.found_positive.map((kw, i) => (
                            <Badge key={`${domain}-pos-${i}`} className="text-xs bg-green-600">+{kw}</Badge>
                          ))}
                          {data.found_negative.map((kw, i) => (
                            <Badge key={`${domain}-neg-${i}`} className="text-xs bg-red-600">-{kw}</Badge>
                          ))}
                        </>
                      ))}
                    </div>
                  </div>

                  {/* 인사이트 */}
                  <div>
                    <p className="text-slate-300 text-sm font-medium mb-2">인사이트</p>
                    {result.steps.step5_output.insights.map((insight, i) => (
                      <div key={i} className={`text-sm p-2 rounded mb-1 ${
                        insight.type === 'positive' ? 'bg-green-900/30 text-green-400' :
                        insight.type === 'negative' ? 'bg-red-900/30 text-red-400' :
                        'bg-slate-900/50 text-slate-300'
                      }`}>
                        {insight.text}
                      </div>
                    ))}
                  </div>
                </div>
              </ScrollArea>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

// ==================== 자산 저장소 뷰 ====================
const AssetStorageView = ({ assets, stats, searchQuery, setSearchQuery, onRefresh }) => {
  const filteredAssets = assets.filter(a => 
    a.content?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="flex-1 flex flex-col gap-4">
      {/* 통계 */}
      <div className="grid grid-cols-4 gap-4">
        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="py-4 text-center">
            <Database className="w-8 h-8 text-violet-400 mx-auto mb-2" />
            <p className="text-2xl font-bold text-white">{stats?.total || 0}</p>
            <p className="text-slate-400 text-sm">총 자산</p>
          </CardContent>
        </Card>
        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="py-4 text-center">
            <CheckCircle2 className="w-8 h-8 text-green-400 mx-auto mb-2" />
            <p className="text-2xl font-bold text-green-400">{stats?.positive || 0}</p>
            <p className="text-slate-400 text-sm">긍정</p>
          </CardContent>
        </Card>
        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="py-4 text-center">
            <Clock className="w-8 h-8 text-yellow-400 mx-auto mb-2" />
            <p className="text-2xl font-bold text-yellow-400">{stats?.neutral || 0}</p>
            <p className="text-slate-400 text-sm">중립</p>
          </CardContent>
        </Card>
        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="py-4 text-center">
            <AlertTriangle className="w-8 h-8 text-red-400 mx-auto mb-2" />
            <p className="text-2xl font-bold text-red-400">{stats?.negative || 0}</p>
            <p className="text-slate-400 text-sm">부정</p>
          </CardContent>
        </Card>
      </div>

      {/* 검색 및 목록 */}
      <Card className="flex-1 bg-slate-800/50 border-slate-700">
        <CardHeader className="pb-3 flex flex-row items-center justify-between">
          <CardTitle className="text-slate-100 text-lg flex items-center gap-2">
            <Database className="w-5 h-5 text-violet-400" />
            자산 목록
          </CardTitle>
          <div className="flex gap-2">
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <Input
                placeholder="검색..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9 w-64 bg-slate-900 border-slate-600"
              />
            </div>
            <Button variant="outline" onClick={onRefresh} size="sm">
              <RotateCcw className="w-4 h-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[400px]">
            {filteredAssets.length === 0 ? (
              <div className="text-center py-12 text-slate-500">
                <Database className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>저장된 자산이 없습니다</p>
                <p className="text-sm">시그널 흐름 탭에서 분석 후 자산으로 저장하세요</p>
              </div>
            ) : (
              <div className="space-y-2">
                {filteredAssets.map((asset, idx) => (
                  <div key={asset.asset_id || idx} className="bg-slate-900/50 rounded-lg p-3 flex items-center gap-4">
                    <div className={`
                      w-10 h-10 rounded-full flex items-center justify-center
                      ${asset.classification === '긍정' ? 'bg-green-900/50 text-green-400' :
                        asset.classification === '부정' ? 'bg-red-900/50 text-red-400' :
                        'bg-yellow-900/50 text-yellow-400'}
                    `}>
                      {asset.score || '-'}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-slate-200 text-sm truncate">{asset.content}</p>
                      <p className="text-slate-500 text-xs">{asset.created_at}</p>
                    </div>
                    <Badge className={
                      asset.classification === '긍정' ? 'bg-green-600' :
                      asset.classification === '부정' ? 'bg-red-600' : 'bg-yellow-600'
                    }>
                      {asset.classification || '미분류'}
                    </Badge>
                    <div className="text-xs text-slate-400">
                      <p>🏛️ {asset.v_pub?.toFixed(1) || '-'}%</p>
                      <p>🏭 {asset.v_pro?.toFixed(1) || '-'}%</p>
                      <p>👤 {asset.v_ind?.toFixed(1) || '-'}%</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
};

// ==================== 자산 활용 현황 뷰 ====================
const AssetUsageView = ({ stats, assets }) => {
  const usageData = [
    { 
      icon: TrendingUp, 
      title: "예측 모델 학습", 
      description: "자산 데이터를 기반으로 미래 트렌드 예측 모델 개선",
      count: stats?.used_for_prediction || Math.floor((stats?.total || 0) * 0.7),
      color: "violet"
    },
    { 
      icon: BarChart3, 
      title: "트렌드 분석", 
      description: "시간별/카테고리별 감성 변화 추적",
      count: stats?.used_for_trend || Math.floor((stats?.total || 0) * 0.9),
      color: "blue"
    },
    { 
      icon: Target, 
      title: "비교 리포트", 
      description: "경쟁 제품/기간 간 비교 분석에 활용",
      count: stats?.used_for_comparison || Math.floor((stats?.total || 0) * 0.3),
      color: "emerald"
    },
    { 
      icon: AlertTriangle, 
      title: "이상 탐지 기준", 
      description: "정상 범위 벗어난 이상 신호 감지 기준 설정",
      count: stats?.used_for_anomaly || Math.floor((stats?.total || 0) * 0.15),
      color: "amber"
    },
  ];

  return (
    <div className="flex-1 flex flex-col gap-4">
      {/* 활용 현황 카드 */}
      <div className="grid grid-cols-2 gap-4">
        {usageData.map((usage, idx) => (
          <Card key={idx} className="bg-slate-800/50 border-slate-700">
            <CardContent className="py-6">
              <div className="flex items-start gap-4">
                <div className={`
                  w-14 h-14 rounded-lg flex items-center justify-center
                  ${usage.color === 'violet' ? 'bg-violet-900/50' :
                    usage.color === 'blue' ? 'bg-blue-900/50' :
                    usage.color === 'emerald' ? 'bg-emerald-900/50' : 'bg-amber-900/50'}
                `}>
                  <usage.icon className={`w-7 h-7 ${
                    usage.color === 'violet' ? 'text-violet-400' :
                    usage.color === 'blue' ? 'text-blue-400' :
                    usage.color === 'emerald' ? 'text-emerald-400' : 'text-amber-400'
                  }`} />
                </div>
                <div className="flex-1">
                  <h3 className="text-slate-100 font-medium">{usage.title}</h3>
                  <p className="text-slate-400 text-sm mt-1">{usage.description}</p>
                  <div className="mt-3 flex items-baseline gap-2">
                    <span className={`text-2xl font-bold ${
                      usage.color === 'violet' ? 'text-violet-400' :
                      usage.color === 'blue' ? 'text-blue-400' :
                      usage.color === 'emerald' ? 'text-emerald-400' : 'text-amber-400'
                    }`}>{usage.count.toLocaleString()}</span>
                    <span className="text-slate-500 text-sm">건 활용</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* GVIC 가치 흐름 */}
      <Card className="flex-1 bg-slate-800/50 border-slate-700">
        <CardHeader>
          <CardTitle className="text-slate-100 text-lg flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-amber-400" />
            GVIC 가치 창출 흐름
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-around py-8">
            {[
              { label: "원시 데이터", value: "후기/리뷰", icon: FileText },
              { label: "시그널 추출", value: "3관점 분석", icon: Zap },
              { label: "자산화", value: `${stats?.total || 0}건`, icon: Database },
              { label: "가치 창출", value: "인사이트", icon: TrendingUp },
            ].map((step, idx) => (
              <div key={idx} className="flex items-center">
                <div className="text-center">
                  <div className="w-16 h-16 bg-gradient-to-br from-violet-600 to-amber-600 rounded-full flex items-center justify-center mx-auto mb-2">
                    <step.icon className="w-8 h-8 text-white" />
                  </div>
                  <p className="text-slate-300 font-medium">{step.label}</p>
                  <p className="text-slate-500 text-sm">{step.value}</p>
                </div>
                {idx < 3 && (
                  <ArrowRight className="w-8 h-8 text-slate-600 mx-4" />
                )}
              </div>
            ))}
          </div>

          <div className="mt-6 p-4 bg-slate-900/50 rounded-lg">
            <p className="text-slate-300 text-sm text-center">
              💡 GVIC는 원시 데이터를 <span className="text-violet-400 font-medium">3가지 관점(사회·생산·소비자)</span>으로 분석하여
              <span className="text-amber-400 font-medium"> 구조화된 자산</span>으로 변환합니다.
              이 자산은 예측, 트렌드 분석, 비교 리포트, 이상 탐지 등 다양한 비즈니스 인사이트 창출에 활용됩니다.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default GVICShowcaseTab;
