import { useState, useCallback } from "react";
import axios from "axios";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Slider } from "@/components/ui/slider";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import { 
  Play, 
  RotateCcw, 
  ChevronRight, 
  ChevronDown,
  Zap,
  FileText,
  Settings2,
  BarChart3,
  Target,
  Sparkles,
  AlertCircle,
  CheckCircle2,
  Info
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export const SignalTracerTab = () => {
  // 입력 상태
  const [content, setContent] = useState("");
  const [rating, setRating] = useState(4);
  
  // 튜닝 파라미터
  const [sigma, setSigma] = useState([0.33, 0.34, 0.33]);
  const [omegaMin, setOmegaMin] = useState([0.2, 0.2, 0.1]);
  const [omegaMax, setOmegaMax] = useState([0.5, 0.5, 0.5]);
  
  // 결과 상태
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // 단계 펼침 상태
  const [expandedSteps, setExpandedSteps] = useState({
    step1: true,
    step2: true,
    step3: true,
    step4: true,
    step5: true
  });

  const toggleStep = (step) => {
    setExpandedSteps(prev => ({ ...prev, [step]: !prev[step] }));
  };

  // 분석 실행
  const handleAnalyze = useCallback(async () => {
    if (!content.trim()) {
      setError("후기 내용을 입력해주세요.");
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await api.post("/api/signal-tracer/analyze", {
        content: content,
        rating: rating,
        sigma: sigma,
        omega_min: omegaMin,
        omega_max: omegaMax
      });
      setResult(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || "분석 중 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  }, [content, rating, sigma, omegaMin, omegaMax]);

  // 초기화
  const handleReset = () => {
    setContent("");
    setRating(4);
    setSigma([0.33, 0.34, 0.33]);
    setOmegaMin([0.2, 0.2, 0.1]);
    setOmegaMax([0.5, 0.5, 0.5]);
    setResult(null);
    setError(null);
  };

  // 샘플 데이터
  const sampleReviews = [
    { content: "효과가 정말 좋아요! 포장도 꼼꼼하고 배송도 빨랐어요. 재구매 의사 있습니다.", rating: 5 },
    { content: "가격이 좀 비싼 것 같아요. 효과는 있는데 가성비는 떨어지네요.", rating: 3 },
    { content: "포장이 파손되어 왔어요. 환경을 위해 플라스틱 줄여주세요.", rating: 2 },
    { content: "매일 먹기 좋고 휴대하기 편해요. 건강해진 느낌이에요!", rating: 5 }
  ];

  const loadSample = (sample) => {
    setContent(sample.content);
    setRating(sample.rating);
    setResult(null);
  };

  // 시그마 합계 계산
  const sigmaSum = sigma.reduce((a, b) => a + b, 0);

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            <Zap className="w-6 h-6 text-violet-400" />
            시그널 추적기
          </h2>
          <p className="text-slate-400 mt-1">
            단일 후기가 GVIC 엔진에서 어떻게 처리되는지 단계별로 확인하세요
          </p>
        </div>
        <Button variant="outline" onClick={handleReset} className="gap-2">
          <RotateCcw className="w-4 h-4" />
          초기화
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 좌측: 입력 & 파라미터 */}
        <div className="lg:col-span-1 space-y-4">
          {/* 후기 입력 */}
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader className="pb-3">
              <CardTitle className="text-slate-100 text-lg flex items-center gap-2">
                <FileText className="w-5 h-5 text-blue-400" />
                후기 입력
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Textarea
                placeholder="분석할 후기 내용을 입력하세요..."
                value={content}
                onChange={(e) => setContent(e.target.value)}
                className="bg-slate-900 border-slate-600 text-slate-100 min-h-[120px]"
                data-testid="review-input"
              />
              
              <div>
                <label className="text-slate-300 text-sm mb-2 flex justify-between">
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
                  data-testid="rating-slider"
                />
              </div>

              {/* 샘플 버튼 */}
              <div>
                <p className="text-slate-400 text-xs mb-2">샘플 후기:</p>
                <div className="flex flex-wrap gap-1">
                  {sampleReviews.map((sample, idx) => (
                    <Button
                      key={idx}
                      variant="ghost"
                      size="sm"
                      onClick={() => loadSample(sample)}
                      className="text-xs h-7 px-2"
                    >
                      샘플 {idx + 1}
                    </Button>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 파라미터 튜닝 */}
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader className="pb-3">
              <CardTitle className="text-slate-100 text-lg flex items-center gap-2">
                <Settings2 className="w-5 h-5 text-emerald-400" />
                파라미터 튜닝
              </CardTitle>
              <CardDescription className="text-slate-400 text-xs">
                가중치를 조정하고 결과 변화를 확인하세요
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* 시그마 설정 */}
              <div className="space-y-3">
                <p className="text-slate-300 text-sm font-medium">Σ 시그마 (관점 비중)</p>
                
                <div>
                  <label className="text-slate-400 text-xs flex justify-between mb-1">
                    <span>🏛️ 사회·규제</span>
                    <span className="text-blue-400">{(sigma[0] * 100).toFixed(0)}%</span>
                  </label>
                  <Slider
                    value={[sigma[0] * 100]}
                    onValueChange={([v]) => setSigma([v/100, sigma[1], sigma[2]])}
                    max={100}
                    step={5}
                    className="[&_[role=slider]]:bg-blue-500"
                  />
                </div>
                
                <div>
                  <label className="text-slate-400 text-xs flex justify-between mb-1">
                    <span>🏭 기업·생산</span>
                    <span className="text-emerald-400">{(sigma[1] * 100).toFixed(0)}%</span>
                  </label>
                  <Slider
                    value={[sigma[1] * 100]}
                    onValueChange={([v]) => setSigma([sigma[0], v/100, sigma[2]])}
                    max={100}
                    step={5}
                    className="[&_[role=slider]]:bg-emerald-500"
                  />
                </div>
                
                <div>
                  <label className="text-slate-400 text-xs flex justify-between mb-1">
                    <span>👤 소비자·고객</span>
                    <span className="text-amber-400">{(sigma[2] * 100).toFixed(0)}%</span>
                  </label>
                  <Slider
                    value={[sigma[2] * 100]}
                    onValueChange={([v]) => setSigma([sigma[0], sigma[1], v/100])}
                    max={100}
                    step={5}
                    className="[&_[role=slider]]:bg-amber-500"
                  />
                </div>

                <div className={`text-center py-1 px-2 rounded text-xs ${
                  Math.abs(sigmaSum - 1.0) <= 0.01 
                    ? 'bg-emerald-900/30 text-emerald-400' 
                    : 'bg-amber-900/30 text-amber-400'
                }`}>
                  합계: {(sigmaSum * 100).toFixed(0)}% {Math.abs(sigmaSum - 1.0) <= 0.01 ? '✓' : '(100%가 되어야 함)'}
                </div>
              </div>

              <Separator className="bg-slate-700" />

              {/* 오메가 설정 (간략화) */}
              <div className="space-y-2">
                <p className="text-slate-300 text-sm font-medium">Ω 오메가 (허용 범위)</p>
                <div className="grid grid-cols-3 gap-2 text-xs">
                  <div className="text-center">
                    <p className="text-slate-400 mb-1">🏛️</p>
                    <p className="text-slate-300">{(omegaMin[0]*100).toFixed(0)}~{(omegaMax[0]*100).toFixed(0)}%</p>
                  </div>
                  <div className="text-center">
                    <p className="text-slate-400 mb-1">🏭</p>
                    <p className="text-slate-300">{(omegaMin[1]*100).toFixed(0)}~{(omegaMax[1]*100).toFixed(0)}%</p>
                  </div>
                  <div className="text-center">
                    <p className="text-slate-400 mb-1">👤</p>
                    <p className="text-slate-300">{(omegaMin[2]*100).toFixed(0)}~{(omegaMax[2]*100).toFixed(0)}%</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 분석 버튼 */}
          <Button 
            onClick={handleAnalyze} 
            disabled={loading || !content.trim()}
            className="w-full h-12 text-lg gap-2 bg-violet-600 hover:bg-violet-700"
            data-testid="analyze-button"
          >
            {loading ? (
              <>
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                분석 중...
              </>
            ) : (
              <>
                <Play className="w-5 h-5" />
                분석 시작
              </>
            )}
          </Button>

          {error && (
            <div className="bg-red-900/30 border border-red-600 rounded-lg p-3 text-red-400 text-sm">
              {error}
            </div>
          )}
        </div>

        {/* 우측: 결과 (5단계) */}
        <div className="lg:col-span-2">
          <ScrollArea className="h-[calc(100vh-200px)]">
            <div className="space-y-4 pr-4">
              {!result ? (
                <Card className="bg-slate-800/30 border-slate-700 border-dashed">
                  <CardContent className="py-16 text-center">
                    <Sparkles className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                    <p className="text-slate-500">
                      후기를 입력하고 "분석 시작" 버튼을 클릭하세요
                    </p>
                    <p className="text-slate-600 text-sm mt-2">
                      5단계 처리 과정을 실시간으로 확인할 수 있습니다
                    </p>
                  </CardContent>
                </Card>
              ) : (
                <>
                  {/* Step 1: 입력 */}
                  <StepCard
                    step={result.steps.step1_input}
                    expanded={expandedSteps.step1}
                    onToggle={() => toggleStep('step1')}
                    color="blue"
                  >
                    <div className="space-y-2">
                      <div className="bg-slate-900/50 rounded p-3">
                        <p className="text-slate-300 text-sm">{result.steps.step1_input.data.content}</p>
                      </div>
                      <div className="flex gap-4 text-xs text-slate-400">
                        <span>글자 수: {result.steps.step1_input.data.char_count}</span>
                        <span>단어 수: {result.steps.step1_input.data.word_count}</span>
                        <span>평점: {result.steps.step1_input.data.rating}점</span>
                      </div>
                    </div>
                  </StepCard>

                  {/* Step 2: 표준화 */}
                  <StepCard
                    step={result.steps.step2_standardize}
                    expanded={expandedSteps.step2}
                    onToggle={() => toggleStep('step2')}
                    color="emerald"
                  >
                    <div className="space-y-3">
                      <div className="bg-slate-900/50 rounded p-3">
                        <p className="text-slate-400 text-xs mb-1">변환 공식</p>
                        <code className="text-emerald-400 text-sm">
                          {result.steps.step2_standardize.transformation.formula}
                        </code>
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <p className="text-slate-400 text-xs">정규화 값</p>
                          <p className="text-2xl font-bold text-emerald-400">
                            {result.steps.step2_standardize.data.primary_value}
                          </p>
                        </div>
                        <div>
                          <p className="text-slate-400 text-xs">감성 힌트</p>
                          <Badge className={
                            result.steps.step2_standardize.data.sentiment_hint === 'positive' 
                              ? 'bg-green-600' 
                              : result.steps.step2_standardize.data.sentiment_hint === 'negative'
                              ? 'bg-red-600'
                              : 'bg-yellow-600'
                          }>
                            {result.steps.step2_standardize.data.sentiment_hint}
                          </Badge>
                        </div>
                      </div>
                    </div>
                  </StepCard>

                  {/* Step 3: 시그널 분석 */}
                  <StepCard
                    step={result.steps.step3_signal}
                    expanded={expandedSteps.step3}
                    onToggle={() => toggleStep('step3')}
                    color="violet"
                  >
                    <div className="space-y-3">
                      {['society', 'production', 'consumer'].map((domain) => {
                        const data = result.steps.step3_signal.keyword_analysis[domain];
                        const scoreKey = domain === 'society' ? 'V_pub' : domain === 'production' ? 'V_pro' : 'V_ind';
                        const score = result.steps.step3_signal.raw_scores[scoreKey];
                        
                        return (
                          <div key={domain} className="bg-slate-900/50 rounded p-3">
                            <div className="flex justify-between items-center mb-2">
                              <span className="text-slate-200 text-sm">{data.label}</span>
                              <span className="text-violet-400 font-bold">{score}점</span>
                            </div>
                            <Progress value={score} className="h-2 mb-2" />
                            <div className="flex flex-wrap gap-1">
                              {data.found_positive.map((kw, i) => (
                                <Badge key={i} variant="outline" className="text-xs text-green-400 border-green-600">
                                  +{kw}
                                </Badge>
                              ))}
                              {data.found_negative.map((kw, i) => (
                                <Badge key={i} variant="outline" className="text-xs text-red-400 border-red-600">
                                  -{kw}
                                </Badge>
                              ))}
                              {data.found_positive.length === 0 && data.found_negative.length === 0 && (
                                <span className="text-slate-500 text-xs">키워드 없음</span>
                              )}
                            </div>
                          </div>
                        );
                      })}
                      <p className="text-slate-500 text-xs">
                        {result.steps.step3_signal.rating_adjustment}
                      </p>
                    </div>
                  </StepCard>

                  {/* Step 4: 수렴 연산 */}
                  <StepCard
                    step={result.steps.step4_convergence}
                    expanded={expandedSteps.step4}
                    onToggle={() => toggleStep('step4')}
                    color="amber"
                  >
                    <div className="space-y-4">
                      {/* 시그마 적용 */}
                      <div className="bg-slate-900/50 rounded p-3">
                        <p className="text-slate-400 text-xs mb-2">Σ 시그마 가중치 적용</p>
                        <div className="grid grid-cols-3 gap-2 text-center text-sm">
                          {['V_pub', 'V_pro', 'V_ind'].map((key) => (
                            <div key={key}>
                              <p className="text-slate-500 text-xs">{key}</p>
                              <p className="text-slate-300">
                                × {result.steps.step4_convergence.sigma_applied.weights[key]}
                              </p>
                              <p className="text-amber-400 font-medium">
                                = {result.steps.step4_convergence.sigma_applied.weighted_scores[key]}
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* 오메가 검증 */}
                      <div className={`rounded p-3 ${
                        result.steps.step4_convergence.omega_validation.is_valid
                          ? 'bg-emerald-900/30 border border-emerald-600'
                          : 'bg-amber-900/30 border border-amber-600'
                      }`}>
                        <p className="text-slate-300 text-sm mb-2 flex items-center gap-2">
                          {result.steps.step4_convergence.omega_validation.is_valid ? (
                            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                          ) : (
                            <AlertCircle className="w-4 h-4 text-amber-400" />
                          )}
                          Ω 오메가 경계 검증
                        </p>
                        <div className="text-xs space-y-1">
                          {result.steps.step4_convergence.omega_validation.violations.map((v, i) => (
                            <p key={i} className={
                              v === "없음 - 경계 조건 충족" ? "text-emerald-400" : "text-amber-400"
                            }>{v}</p>
                          ))}
                        </div>
                      </div>

                      {/* 분배 결과 */}
                      <div className="bg-slate-900/50 rounded p-3">
                        <p className="text-slate-400 text-xs mb-2">최종 분배</p>
                        <div className="space-y-2">
                          {[
                            { key: 'V_pub', label: '🏛️ 사회·규제', color: 'bg-blue-500' },
                            { key: 'V_pro', label: '🏭 기업·생산', color: 'bg-emerald-500' },
                            { key: 'V_ind', label: '👤 소비자·고객', color: 'bg-amber-500' }
                          ].map(({ key, label, color }) => (
                            <div key={key} className="flex items-center gap-2">
                              <span className="text-slate-400 text-xs w-28">{label}</span>
                              <div className="flex-1 h-4 bg-slate-700 rounded overflow-hidden">
                                <div 
                                  className={`h-full ${color}`}
                                  style={{ width: `${result.steps.step4_convergence.distribution.after_adjustment[key]}%` }}
                                />
                              </div>
                              <span className="text-slate-300 text-sm w-14 text-right">
                                {result.steps.step4_convergence.distribution.after_adjustment[key]}%
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </StepCard>

                  {/* Step 5: 최종 출력 */}
                  <StepCard
                    step={result.steps.step5_output}
                    expanded={expandedSteps.step5}
                    onToggle={() => toggleStep('step5')}
                    color="rose"
                  >
                    <div className="space-y-4">
                      {/* 종합 점수 */}
                      <div className="text-center py-4">
                        <div className={`inline-flex items-center justify-center w-24 h-24 rounded-full ${
                          result.steps.step5_output.final_score.color === 'green'
                            ? 'bg-green-900/50 border-2 border-green-500'
                            : result.steps.step5_output.final_score.color === 'red'
                            ? 'bg-red-900/50 border-2 border-red-500'
                            : 'bg-yellow-900/50 border-2 border-yellow-500'
                        }`}>
                          <div>
                            <p className="text-3xl font-bold text-slate-100">
                              {result.steps.step5_output.final_score.value}
                            </p>
                            <p className="text-xs text-slate-400">/ 100</p>
                          </div>
                        </div>
                        <Badge className={`mt-3 ${
                          result.steps.step5_output.final_score.color === 'green'
                            ? 'bg-green-600'
                            : result.steps.step5_output.final_score.color === 'red'
                            ? 'bg-red-600'
                            : 'bg-yellow-600'
                        }`}>
                          {result.steps.step5_output.final_score.classification}
                        </Badge>
                      </div>

                      {/* 인사이트 */}
                      <div className="space-y-2">
                        {result.steps.step5_output.insights.map((insight, i) => (
                          <div key={i} className={`flex items-start gap-2 p-2 rounded ${
                            insight.type === 'positive' 
                              ? 'bg-green-900/30' 
                              : insight.type === 'negative'
                              ? 'bg-red-900/30'
                              : 'bg-slate-900/50'
                          }`}>
                            {insight.type === 'positive' && <CheckCircle2 className="w-4 h-4 text-green-400 mt-0.5" />}
                            {insight.type === 'negative' && <AlertCircle className="w-4 h-4 text-red-400 mt-0.5" />}
                            {insight.type === 'info' && <Info className="w-4 h-4 text-blue-400 mt-0.5" />}
                            <p className="text-slate-300 text-sm">{insight.text}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  </StepCard>
                </>
              )}
            </div>
          </ScrollArea>
        </div>
      </div>
    </div>
  );
};

// 단계별 카드 컴포넌트
const StepCard = ({ step, expanded, onToggle, color, children }) => {
  const colorClasses = {
    blue: 'border-l-blue-500 bg-blue-500/5',
    emerald: 'border-l-emerald-500 bg-emerald-500/5',
    violet: 'border-l-violet-500 bg-violet-500/5',
    amber: 'border-l-amber-500 bg-amber-500/5',
    rose: 'border-l-rose-500 bg-rose-500/5'
  };

  const iconColors = {
    blue: 'text-blue-400',
    emerald: 'text-emerald-400',
    violet: 'text-violet-400',
    amber: 'text-amber-400',
    rose: 'text-rose-400'
  };

  return (
    <Card className={`border-l-4 ${colorClasses[color]} border-slate-700`}>
      <CardHeader 
        className="py-3 cursor-pointer hover:bg-slate-800/30 transition-colors"
        onClick={onToggle}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center bg-slate-800 ${iconColors[color]}`}>
              {step.step}
            </div>
            <div>
              <CardTitle className="text-slate-100 text-base">{step.name}</CardTitle>
              <CardDescription className="text-slate-400 text-xs">{step.description}</CardDescription>
            </div>
          </div>
          {expanded ? (
            <ChevronDown className="w-5 h-5 text-slate-400" />
          ) : (
            <ChevronRight className="w-5 h-5 text-slate-400" />
          )}
        </div>
      </CardHeader>
      {expanded && (
        <CardContent className="pt-0 pb-4">
          {children}
        </CardContent>
      )}
    </Card>
  );
};

export default SignalTracerTab;
