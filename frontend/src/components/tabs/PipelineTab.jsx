import React, { useState, useEffect } from 'react';
import { Button } from '../ui/button';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '../ui/card';
import { Progress } from '../ui/progress';
import { Badge } from '../ui/badge';
import { 
  Play, FileText, Download, CheckCircle, 
  TrendingUp, TrendingDown, BarChart3, 
  FileSpreadsheet, Loader2, RefreshCw
} from 'lucide-react';
import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, 
  CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import { runPipeline, getAnalysisFiles, getPipelineReports } from '../../lib/api';

const COLORS = {
  positive: '#22c55e',
  neutral: '#f59e0b', 
  negative: '#ef4444'
};

const PipelineTab = () => {
  const [files, setFiles] = useState([]);
  const [reports, setReports] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const steps = [
    { id: 1, name: '입력 어댑터', description: '데이터 로드 및 표준화' },
    { id: 2, name: '감성 분석', description: '긍정/중립/부정 분류' },
    { id: 3, name: '요인 추출', description: '긍정/부정 요인 모듈화' },
    { id: 4, name: 'GVIC 분석', description: '특허 엔진 처리' },
    { id: 5, name: 'PDF 생성', description: '리포트 출력' }
  ];

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [filesRes, reportsRes] = await Promise.all([
        getAnalysisFiles(),
        getPipelineReports()
      ]);
      setFiles(filesRes.files || []);
      setReports(reportsRes.reports || []);
    } catch (err) {
      console.error('Failed to load data:', err);
    }
  };

  const handleRunPipeline = async () => {
    setIsRunning(true);
    setError(null);
    setResult(null);
    setCurrentStep(0);

    try {
      // 단계별 진행 시뮬레이션
      for (let i = 1; i <= 5; i++) {
        setCurrentStep(i);
        await new Promise(resolve => setTimeout(resolve, 500));
      }

      const response = await runPipeline({
        file_path: selectedFile?.path || null,
        sample_size: 1000
      });

      setResult(response);
      setCurrentStep(5);
      loadData(); // 리포트 목록 갱신
    } catch (err) {
      setError(err.message || '파이프라인 실행 실패');
      console.error('Pipeline error:', err);
    } finally {
      setIsRunning(false);
    }
  };

  const sentimentData = result ? [
    { name: '긍정', value: result.sentiment_distribution?.positive?.count || 0, color: COLORS.positive },
    { name: '중립', value: result.sentiment_distribution?.neutral?.count || 0, color: COLORS.neutral },
    { name: '부정', value: result.sentiment_distribution?.negative?.count || 0, color: COLORS.negative }
  ] : [];

  const positiveFactorsData = result?.positive_factors?.map(f => ({
    name: f.category,
    count: f.count,
    ratio: (f.ratio * 100).toFixed(1)
  })) || [];

  const negativeFactorsData = result?.negative_factors?.map(f => ({
    name: f.category,
    count: f.count,
    ratio: (f.ratio * 100).toFixed(1)
  })) || [];

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">GVIC 분석 파이프라인</h2>
          <p className="text-slate-600">입력 → GVIC 엔진 분석 → PDF 리포트 출력</p>
        </div>
        <Button variant="outline" size="sm" onClick={loadData}>
          <RefreshCw className="h-4 w-4 mr-2" />
          새로고침
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 왼쪽: 입력 데이터 선택 및 실행 */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileSpreadsheet className="h-5 w-5 text-blue-600" />
              입력 데이터
            </CardTitle>
            <CardDescription>분석할 데이터 파일 선택</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* 파일 목록 */}
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {files.length > 0 ? (
                files.map((file, idx) => (
                  <div
                    key={idx}
                    onClick={() => setSelectedFile(file)}
                    className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                      selectedFile?.name === file.name 
                        ? 'border-blue-500 bg-blue-50' 
                        : 'border-slate-200 hover:border-blue-300'
                    }`}
                  >
                    <div className="font-medium text-sm truncate">{file.name}</div>
                    <div className="text-xs text-slate-500">
                      {(file.size / 1024).toFixed(1)} KB
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-slate-500 text-sm">데이터 파일이 없습니다</p>
              )}
            </div>

            {/* 실행 버튼 */}
            <Button 
              className="w-full" 
              onClick={handleRunPipeline}
              disabled={isRunning}
            >
              {isRunning ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  분석 중...
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 mr-2" />
                  파이프라인 실행
                </>
              )}
            </Button>

            {/* 진행 단계 */}
            {(isRunning || result) && (
              <div className="space-y-2 mt-4">
                <div className="flex justify-between text-sm">
                  <span>진행 상황</span>
                  <span>{currentStep}/5 단계</span>
                </div>
                <Progress value={(currentStep / 5) * 100} className="h-2" />
                
                <div className="space-y-1 mt-3">
                  {steps.map((step) => (
                    <div key={step.id} className="flex items-center gap-2 text-sm">
                      {currentStep >= step.id ? (
                        <CheckCircle className="h-4 w-4 text-green-500" />
                      ) : (
                        <div className="h-4 w-4 rounded-full border border-slate-300" />
                      )}
                      <span className={currentStep >= step.id ? 'text-slate-900' : 'text-slate-400'}>
                        {step.name}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {error && (
              <div className="p-3 bg-red-50 text-red-700 rounded-lg text-sm">
                {error}
              </div>
            )}
          </CardContent>
        </Card>

        {/* 오른쪽: 분석 결과 */}
        <div className="lg:col-span-2 space-y-6">
          {result ? (
            <>
              {/* 요약 카드 */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <Card>
                  <CardContent className="p-4">
                    <div className="text-sm text-slate-600">총 데이터</div>
                    <div className="text-2xl font-bold">{result.total_records?.toLocaleString()}</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4">
                    <div className="text-sm text-slate-600">긍정 비율</div>
                    <div className="text-2xl font-bold text-green-600">
                      {((result.sentiment_distribution?.positive?.ratio || 0) * 100).toFixed(1)}%
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4">
                    <div className="text-sm text-slate-600">공정성 지수</div>
                    <div className="text-2xl font-bold text-blue-600">
                      {(result.gvic_results?.fairness_index || 0).toFixed(3)}
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4">
                    <div className="text-sm text-slate-600">PDF 리포트</div>
                    <a 
                      href={result.pdf_url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:text-blue-800 flex items-center gap-1"
                    >
                      <Download className="h-4 w-4" />
                      다운로드
                    </a>
                  </CardContent>
                </Card>
              </div>

              {/* 감성 분포 차트 */}
              <Card>
                <CardHeader>
                  <CardTitle>감성 분포</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={sentimentData}
                          cx="50%"
                          cy="50%"
                          innerRadius={60}
                          outerRadius={100}
                          paddingAngle={2}
                          dataKey="value"
                          label={({ name, value }) => `${name}: ${value}건`}
                        >
                          {sentimentData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Pie>
                        <Tooltip />
                        <Legend />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>

              {/* 긍정/부정 요인 */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* 긍정 요인 */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-green-700">
                      <TrendingUp className="h-5 w-5" />
                      긍정 평가 요인
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {positiveFactorsData.map((factor, idx) => (
                        <div key={idx} className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                              {factor.name}
                            </Badge>
                          </div>
                          <div className="text-sm">
                            <span className="font-medium">{factor.count}건</span>
                            <span className="text-slate-500 ml-2">({factor.ratio}%)</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                {/* 부정 요인 */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-red-700">
                      <TrendingDown className="h-5 w-5" />
                      부정 평가 요인
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {negativeFactorsData.length > 0 ? negativeFactorsData.map((factor, idx) => (
                        <div key={idx} className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <Badge variant="outline" className="bg-red-50 text-red-700 border-red-200">
                              {factor.name}
                            </Badge>
                          </div>
                          <div className="text-sm">
                            <span className="font-medium">{factor.count}건</span>
                            <span className="text-slate-500 ml-2">({factor.ratio}%)</span>
                          </div>
                        </div>
                      )) : (
                        <p className="text-slate-500 text-sm">부정 요인이 없습니다</p>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* 인사이트 */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <BarChart3 className="h-5 w-5 text-purple-600" />
                    분석 인사이트
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {result.insights?.map((insight, idx) => (
                      <div key={idx} className="p-3 bg-slate-50 rounded-lg text-sm">
                        {insight}
                      </div>
                    ))}
                    {result.recommendations?.map((rec, idx) => (
                      <div key={idx} className="p-3 bg-blue-50 rounded-lg text-sm text-blue-800">
                        💡 {rec}
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </>
          ) : (
            /* 초기 상태: 기존 리포트 목록 */
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-5 w-5 text-blue-600" />
                  생성된 리포트
                </CardTitle>
                <CardDescription>이전에 생성된 PDF 리포트 목록</CardDescription>
              </CardHeader>
              <CardContent>
                {reports.length > 0 ? (
                  <div className="space-y-2">
                    {reports.map((report, idx) => (
                      <div key={idx} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                        <div>
                          <div className="font-medium text-sm">{report.name}</div>
                          <div className="text-xs text-slate-500">
                            {new Date(report.created).toLocaleString('ko-KR')} · {(report.size / 1024).toFixed(1)} KB
                          </div>
                        </div>
                        <a 
                          href={`${process.env.REACT_APP_BACKEND_URL}/api/pipeline/report/${report.name}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:text-blue-800"
                        >
                          <Download className="h-5 w-5" />
                        </a>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-slate-500">
                    <FileText className="h-12 w-12 mx-auto mb-3 opacity-50" />
                    <p>아직 생성된 리포트가 없습니다</p>
                    <p className="text-sm">파이프라인을 실행하여 첫 리포트를 생성하세요</p>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};

export default PipelineTab;
