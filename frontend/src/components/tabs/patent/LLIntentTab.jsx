import { useState, useCallback, useEffect } from "react";
import axios from "axios";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { 
  Brain, 
  Zap,
  Eye,
  Lightbulb,
  ArrowRight,
  Play,
  RotateCcw,
  Hash,
  Tag,
  MessageSquare,
  GitBranch,
  User,
  FileText,
  Box,
  Save
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

/**
 * LL:의도 - 기여도 정량화 (특허 LL: INTELLIGENCE)
 * 비정형 입력에서 의도를 추출하고 정량화
 */
export const LLIntentTab = () => {
  const [content, setContent] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

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
      alert("자산으로 저장되었습니다!");
    } catch (err) {
      console.error("Failed to save asset:", err);
      alert("저장 실패");
    }
  }, [content, result]);

  const handleReset = () => {
    setContent("");
    setResult(null);
    setError(null);
  };

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-100 flex items-center gap-3">
            <div className="w-10 h-10 bg-violet-600 rounded-lg flex items-center justify-center">
              <Brain className="w-6 h-6 text-white" />
            </div>
            LL:의도
          </h2>
          <p className="text-slate-400 mt-1">기여도 정량화 - INTELLIGENCE 모듈</p>
        </div>
        <Badge variant="outline" className="text-violet-400 border-violet-600">
          특허 LL
        </Badge>
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* 좌측: 입력 */}
        <div className="space-y-4">
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader className="pb-3">
              <CardTitle className="text-slate-100 text-lg flex items-center gap-2">
                <FileText className="w-5 h-5 text-blue-400" />
                시그널 입력
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Textarea
                placeholder="분석할 텍스트를 입력하세요..."
                value={content}
                onChange={(e) => setContent(e.target.value)}
                className="bg-slate-900 border-slate-600 text-slate-100 min-h-[200px]"
              />
              
              <div>
                <p className="text-slate-400 text-xs mb-2">샘플:</p>
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
                  className="flex-1 gap-2 bg-violet-600 hover:bg-violet-700 h-12"
                >
                  {loading ? (
                    <>
                      <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      의도 추출 중...
                    </>
                  ) : (
                    <>
                      <Brain className="w-5 h-5" />
                      의도 추출
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
        <div className="space-y-4">
          {!result ? (
            <Card className="bg-slate-800/30 border-slate-700 border-dashed h-full flex items-center justify-center">
              <div className="text-center py-12">
                <Brain className="w-16 h-16 text-slate-600 mx-auto mb-4" />
                <p className="text-slate-500 text-lg">의도 추출 대기 중</p>
                <p className="text-slate-600 text-sm mt-2">
                  텍스트를 입력하고 "의도 추출" 버튼을 클릭하세요
                </p>
              </div>
            </Card>
          ) : (
            <ScrollArea className="h-[500px]">
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
                    <div className="grid grid-cols-2 gap-3 text-xs">
                      <div className="bg-slate-800 rounded p-2">
                        <p className="text-slate-500 flex items-center gap-1"><FileText className="w-3 h-3" /> 입력 ID</p>
                        <p className="text-blue-400 font-mono truncate">{result.input_id}</p>
                      </div>
                      <div className="bg-slate-800 rounded p-2">
                        <p className="text-slate-500 flex items-center gap-1"><Box className="w-3 h-3" /> 모듈 ID</p>
                        <p className="text-emerald-400 font-mono truncate">{result.module_id}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* 시그널 유형 */}
                <Card className="bg-gradient-to-r from-violet-900/30 to-purple-900/30 border-violet-600">
                  <CardContent className="py-4">
                    <div className="flex items-start gap-4">
                      <div className="w-14 h-14 bg-violet-600 rounded-xl flex items-center justify-center">
                        <Eye className="w-7 h-7 text-white" />
                      </div>
                      <div className="flex-1">
                        <p className="text-slate-400 text-xs">감지된 시그널 유형</p>
                        <h3 className="text-xl font-bold text-white mt-1">
                          {result.signal_type_label}
                        </h3>
                        <div className="flex items-center gap-2 mt-2">
                          <Badge className={`${
                            result.signal_type_confidence >= 0.8 ? 'bg-green-600' :
                            result.signal_type_confidence >= 0.5 ? 'bg-yellow-600' : 'bg-red-600'
                          }`}>
                            신뢰도 {(result.signal_type_confidence * 100).toFixed(0)}%
                          </Badge>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* 발견된 시그널 */}
                <Card className="bg-slate-800/50 border-slate-700">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-slate-100 text-base flex items-center gap-2">
                      <Zap className="w-5 h-5 text-amber-400" />
                      추출된 의도 ({result.signal_count}개)
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {result.discovered_signals?.map((sig, idx) => (
                        <div key={sig.signal_id} className="bg-slate-900/50 rounded-lg p-3 border-l-4 border-violet-500">
                          <div className="flex items-start justify-between mb-2">
                            <div className="flex items-center gap-2">
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
                          {sig.hidden_meaning && (
                            <p className="text-violet-400 text-xs flex items-start gap-1">
                              <Lightbulb className="w-3 h-3 mt-0.5 flex-shrink-0" />
                              숨겨진 의미: {sig.hidden_meaning}
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                {/* 요약 */}
                <Card className="bg-slate-800/50 border-slate-700">
                  <CardContent className="py-4">
                    <p className="text-slate-400 text-xs mb-2">의도 요약</p>
                    <p className="text-slate-200">{result.summary}</p>
                    <div className="flex flex-wrap gap-2 mt-3">
                      {result.key_themes?.map((theme, idx) => (
                        <Badge key={idx} variant="outline" className="text-slate-300 border-slate-600">
                          <Tag className="w-3 h-3 mr-1" />
                          {theme}
                        </Badge>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>
            </ScrollArea>
          )}
        </div>
      </div>

      {/* 플로우 안내 */}
      <div className="flex items-center justify-center gap-2 text-slate-500 text-sm">
        <span className="px-3 py-1 bg-slate-700 rounded">J:입력</span>
        <ArrowRight className="w-4 h-4" />
        <span className="px-3 py-1 bg-violet-600/30 rounded text-violet-400">LL:의도</span>
        <ArrowRight className="w-4 h-4" />
        <span className="px-3 py-1 bg-slate-700 rounded">H:코어</span>
        <ArrowRight className="w-4 h-4" />
        <span className="px-3 py-1 bg-slate-700 rounded">A:게이트</span>
      </div>
    </div>
  );
};

export default LLIntentTab;
