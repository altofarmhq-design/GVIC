import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { 
  ResponsiveContainer, 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, 
  Tooltip as RechartsTooltip, Cell, AreaChart, Area, LineChart, Line
} from 'recharts';
import { Play, RefreshCw, AlertCircle, Layers, History, CheckCircle, XCircle } from 'lucide-react';
import { api } from "@/lib/api";

export const ProcessingTab = ({ onProcess }) => {
  const [inputValue, setInputValue] = useState(5.0);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [sessionHistory, setSessionHistory] = useState([]);
  const [dbHistory, setDbHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);

  // MongoDB에서 이력 불러오기
  const fetchHistory = async () => {
    try {
      const response = await api.getProcessHistory(50);
      setDbHistory(response.data.history || []);
    } catch (error) {
      console.error("Fetch history error:", error);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleProcess = async () => {
    setLoading(true);
    try {
      const response = await api.process(inputValue);
      setResult(response.data);
      setSessionHistory(prev => [...prev.slice(-9), {
        time: new Date().toLocaleTimeString(),
        input: inputValue,
        value: response.data?.data?.asset?.value || 0,
        balance: response.data?.data?.balance_score || 0
      }]);
      // 처리 후 이력 새로고침
      fetchHistory();
      if (onProcess) onProcess();
    } catch (error) {
      console.error("Process error:", error);
    }
    setLoading(false);
  };

  const distData = result?.data?.distribution ? [
    { name: '공공', value: result.data.distribution.public, fill: '#3b82f6' },
    { name: '생산', value: result.data.distribution.productive, fill: '#10b981' },
    { name: '개인', value: result.data.distribution.individual, fill: '#f59e0b' }
  ] : [];

  const convergenceData = result?.data?.convergence ? [
    { name: '입력', pub: result.data.convergence.input_ratio[0]*100, pro: result.data.convergence.input_ratio[1]*100, ind: result.data.convergence.input_ratio[2]*100 },
    { name: '출력', pub: result.data.convergence.output_ratio[0]*100, pro: result.data.convergence.output_ratio[1]*100, ind: result.data.convergence.output_ratio[2]*100 }
  ] : [];

  // 차트용 이력 데이터 변환
  const chartHistory = dbHistory.slice(0, 20).reverse().map((item, idx) => ({
    idx: idx + 1,
    value: item.data?.asset?.value || 0,
    balance: (item.data?.balance_score || 0) * 100,
    input: item.input_value
  }));

  return (
    <div className="space-y-6">
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader>
          <CardTitle className="text-slate-100 flex items-center gap-2">
            <Play className="w-5 h-5" /> GVIC 엔진 처리
          </CardTitle>
          <CardDescription className="text-slate-400">
            7개 특허 모듈 통합 파이프라인
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Input Section */}
            <div className="space-y-6">
              <div>
                <label className="text-slate-300 text-sm mb-2 block">처리할 값</label>
                <Input
                  type="number"
                  min={0}
                  max={100}
                  step={0.5}
                  value={inputValue}
                  onChange={(e) => setInputValue(parseFloat(e.target.value) || 0)}
                  className="bg-slate-900 border-slate-600 text-slate-100 text-lg"
                  data-testid="process-input"
                />
              </div>
              <Button 
                onClick={handleProcess} 
                disabled={loading}
                className="w-full bg-emerald-600 hover:bg-emerald-500 h-12"
                data-testid="process-button"
              >
                {loading ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <Play className="w-4 h-4 mr-2" />}
                처리 실행
              </Button>

              {/* Processing Pipeline Info */}
              <div className="bg-slate-900/50 rounded-lg p-3 text-xs text-slate-400 space-y-1">
                <p>1. 입력 인터페이스 (특허6-J)</p>
                <p>2. 비적합 감지 (특허5 - 3000)</p>
                <p>3. 신호 전처리 (특허2)</p>
                <p>4. 신호 자산화 (특허3)</p>
                <p>5. 가중 분배 (특허6 - 4000)</p>
                <p>6. 수렴 제어 (특허1)</p>
              </div>
            </div>

            {/* Result Section */}
            <div className="lg:col-span-2 space-y-4">
              {result?.success ? (
                <>
                  {/* Key Metrics */}
                  <div className="grid grid-cols-4 gap-3" data-testid="process-result">
                    <div className="bg-slate-900/50 rounded-lg p-3 text-center">
                      <p className="text-slate-400 text-xs">자산 가치</p>
                      <p className="text-slate-100 text-xl font-bold">
                        {result.data?.asset?.value?.toFixed(3) || 0}
                      </p>
                    </div>
                    <div className="bg-slate-900/50 rounded-lg p-3 text-center">
                      <p className="text-slate-400 text-xs">품질 점수</p>
                      <p className="text-blue-400 text-xl font-bold">
                        {((result.data?.asset?.quality_score || 0) * 100).toFixed(0)}%
                      </p>
                    </div>
                    <div className="bg-slate-900/50 rounded-lg p-3 text-center">
                      <p className="text-slate-400 text-xs">균형 점수</p>
                      <p className="text-emerald-400 text-xl font-bold">
                        {((result.data?.balance_score || 0) * 100).toFixed(1)}%
                      </p>
                    </div>
                    <div className="bg-slate-900/50 rounded-lg p-3 text-center">
                      <p className="text-slate-400 text-xs">수렴 상태</p>
                      <p className={`text-xl font-bold ${result.data?.convergence?.is_valid ? 'text-emerald-400' : 'text-amber-400'}`}>
                        {result.data?.convergence?.is_valid ? "✓ 유효" : "⚠ 조정"}
                      </p>
                    </div>
                  </div>

                  {/* Nonconformance Alert */}
                  {result.data?.nonconformance?.detected && (
                    <div className="bg-amber-900/30 border border-amber-600/50 rounded-lg p-3 flex items-center gap-3">
                      <AlertCircle className="w-5 h-5 text-amber-400" />
                      <div>
                        <p className="text-amber-300 font-medium">비적합 데이터 감지 (특허5)</p>
                        <p className="text-amber-400/70 text-sm">
                          조정값: {result.data.nonconformance.adjustment.toFixed(3)} → 2차 자산화 처리됨
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Distribution Chart */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-slate-900/30 rounded-lg p-3">
                      <p className="text-slate-400 text-xs mb-2">분배 결과</p>
                      <div className="h-40">
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={distData}>
                            <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} />
                            <YAxis stroke="#94a3b8" fontSize={10} />
                            <RechartsTooltip 
                              contentStyle={{ background: '#1e293b', border: '1px solid #475569', borderRadius: '8px' }}
                            />
                            <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                              {distData.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={entry.fill} />
                              ))}
                            </Bar>
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </div>

                    <div className="bg-slate-900/30 rounded-lg p-3">
                      <p className="text-slate-400 text-xs mb-2">수렴 변환</p>
                      <div className="h-40">
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={convergenceData} layout="vertical">
                            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                            <XAxis type="number" stroke="#94a3b8" fontSize={10} />
                            <YAxis dataKey="name" type="category" stroke="#94a3b8" fontSize={12} />
                            <RechartsTooltip 
                              contentStyle={{ background: '#1e293b', border: '1px solid #475569', borderRadius: '8px' }}
                            />
                            <Bar dataKey="pub" fill="#3b82f6" name="공공" stackId="a" />
                            <Bar dataKey="pro" fill="#10b981" name="생산" stackId="a" />
                            <Bar dataKey="ind" fill="#f59e0b" name="개인" stackId="a" />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                  </div>

                  {/* Preprocessing Info */}
                  <div className="bg-slate-900/30 rounded-lg p-3">
                    <p className="text-slate-400 text-xs mb-2">전처리 결과 (특허2)</p>
                    <div className="flex gap-4 text-sm">
                      <span className="text-slate-300">
                        생성 모듈: <span className="text-blue-400">{result.data?.preprocessing?.modules_generated || 0}</span>
                      </span>
                      <span className="text-slate-300">
                        정합: <span className="text-emerald-400">{result.data?.preprocessing?.conforming || 0}</span>
                      </span>
                    </div>
                  </div>
                </>
              ) : (
                <div className="flex items-center justify-center h-64 text-slate-500">
                  <div className="text-center">
                    <Layers className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <p>왼쪽에서 값을 입력하고 '처리 실행'을 클릭하세요</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* History Section */}
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-slate-100 flex items-center gap-2">
              <History className="w-5 h-5" /> 처리 이력 (MongoDB)
            </CardTitle>
            <CardDescription className="text-slate-400">
              총 {dbHistory.length}건의 처리 기록
            </CardDescription>
          </div>
          <div className="flex gap-2">
            <Button 
              variant="outline" 
              size="sm" 
              onClick={fetchHistory}
              data-testid="refresh-history-button"
            >
              <RefreshCw className="w-4 h-4 mr-1" /> 새로고침
            </Button>
            <Button 
              variant={showHistory ? "default" : "outline"}
              size="sm" 
              onClick={() => setShowHistory(!showHistory)}
              data-testid="toggle-history-button"
            >
              {showHistory ? "차트 보기" : "목록 보기"}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {showHistory ? (
            // 이력 목록 테이블
            <ScrollArea className="h-64" data-testid="history-list">
              <div className="space-y-2">
                {dbHistory.map((item, idx) => (
                  <div key={item.id || idx} className="bg-slate-900/50 rounded-lg p-3 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      {item.success ? (
                        <CheckCircle className="w-5 h-5 text-emerald-400" />
                      ) : (
                        <XCircle className="w-5 h-5 text-red-400" />
                      )}
                      <div>
                        <p className="text-slate-100 font-medium">입력값: {item.input_value}</p>
                        <p className="text-slate-500 text-xs">{item.timestamp?.slice(0, 19).replace('T', ' ')}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      {item.success && item.data && (
                        <>
                          <p className="text-violet-400 font-medium">
                            자산: {item.data?.asset?.value?.toFixed(3) || '-'}
                          </p>
                          <p className="text-emerald-400 text-sm">
                            균형: {((item.data?.balance_score || 0) * 100).toFixed(1)}%
                          </p>
                        </>
                      )}
                      {!item.success && (
                        <Badge variant="destructive">실패</Badge>
                      )}
                    </div>
                  </div>
                ))}
                {dbHistory.length === 0 && (
                  <p className="text-slate-500 text-center py-8">처리 이력이 없습니다</p>
                )}
              </div>
            </ScrollArea>
          ) : (
            // 이력 차트
            <div className="h-64">
              {chartHistory.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartHistory}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis dataKey="idx" stroke="#94a3b8" fontSize={10} label={{ value: '처리 순서', position: 'bottom', fill: '#94a3b8', fontSize: 10 }} />
                    <YAxis stroke="#94a3b8" fontSize={10} />
                    <RechartsTooltip 
                      contentStyle={{ background: '#1e293b', border: '1px solid #475569', borderRadius: '8px' }}
                      formatter={(value, name) => [typeof value === 'number' ? value.toFixed(3) : value, name]}
                    />
                    <Line type="monotone" dataKey="value" stroke="#8b5cf6" strokeWidth={2} dot={{ fill: '#8b5cf6' }} name="자산 가치" />
                    <Line type="monotone" dataKey="balance" stroke="#10b981" strokeWidth={2} dot={{ fill: '#10b981' }} name="균형 점수 (%)" />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex items-center justify-center h-full text-slate-500">
                  <p>처리 이력이 없습니다. 값을 처리하면 이력이 표시됩니다.</p>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default ProcessingTab;
