import React, { useState, useEffect } from 'react';
import { Button } from '../ui/button';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '../ui/card';
import { Progress } from '../ui/progress';
import { Badge } from '../ui/badge';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Textarea } from '../ui/textarea';
import { Checkbox } from '../ui/checkbox';
import { 
  Play, FileText, Download, CheckCircle, 
  TrendingUp, TrendingDown, BarChart3, 
  FileSpreadsheet, Loader2, RefreshCw, Link, Globe,
  Settings, FileDown
} from 'lucide-react';
import {
  PieChart, Pie, Cell, ResponsiveContainer
} from 'recharts';
import { runPipeline, getAnalysisFiles, getPipelineReports, analyzeUrl } from '../../lib/api';

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
  const [inputMode, setInputMode] = useState('url'); // 'url' or 'file'
  const [urlInput, setUrlInput] = useState('');
  const [maxReviews, setMaxReviews] = useState(1000);
  
  // 출력 옵션 상태
  const [outputOptions, setOutputOptions] = useState({
    reportTitle: '',
    includeInsights: true,
    includeRecommendations: true,
    includeSentiment: true,
    includeFactors: true,
    includeGvicAnalysis: true,
    customNotes: ''
  });

  const steps = [
    { id: 1, name: 'URL 크롤링', description: '데이터 수집' },
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

  const handleAnalyzeUrl = async () => {
    if (!urlInput.trim()) {
      setError('URL을 입력해주세요');
      return;
    }

    setIsRunning(true);
    setError(null);
    setResult(null);
    setCurrentStep(0);

    try {
      // 단계별 진행 시뮬레이션
      for (let i = 1; i <= 5; i++) {
        setCurrentStep(i);
        await new Promise(resolve => setTimeout(resolve, 800));
      }

      const response = await analyzeUrl({
        url: urlInput,
        max_reviews: maxReviews,
        output_options: outputOptions
      });

      setResult(response);
      setCurrentStep(5);
      loadData(); // 리포트 목록 갱신
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'URL 분석 실패');
      console.error('URL analysis error:', err);
    } finally {
      setIsRunning(false);
    }
  };

  // PDF 직접 다운로드 함수 - fetch + blob 방식
  const handleDownloadPdf = async (filename) => {
    if (!filename) return;
    
    try {
      // 같은 origin에서 파일 가져오기
      const response = await fetch(`/${filename}`);
      if (!response.ok) throw new Error('파일을 찾을 수 없습니다');
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      link.style.display = 'none';
      document.body.appendChild(link);
      link.click();
      
      // 정리
      setTimeout(() => {
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
      }, 100);
    } catch (err) {
      console.error('다운로드 오류:', err);
      alert('파일 다운로드에 실패했습니다.');
    }
  };

  const handleRunPipeline = async () => {
    setIsRunning(true);
    setError(null);
    setResult(null);
    setCurrentStep(0);

    try {
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
      loadData();
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
          <h2 className="text-2xl font-bold text-slate-100">GVIC 분석 파이프라인</h2>
          <p className="text-slate-400">URL 입력 → GVIC 엔진 분석 → PDF 리포트 출력</p>
        </div>
        <Button variant="outline" size="sm" onClick={loadData} className="border-slate-600">
          <RefreshCw className="h-4 w-4 mr-2" />
          새로고침
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 왼쪽: 입력 및 실행 */}
        <Card className="lg:col-span-1 bg-slate-800 border-slate-700">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-slate-100">
              <Globe className="h-5 w-5 text-blue-400" />
              데이터 입력
            </CardTitle>
            <CardDescription className="text-slate-400">URL을 입력하거나 파일을 선택하세요</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* 입력 모드 선택 */}
            <Tabs value={inputMode} onValueChange={setInputMode}>
              <TabsList className="grid w-full grid-cols-2 bg-slate-700">
                <TabsTrigger value="url" className="data-[state=active]:bg-slate-600">
                  <Link className="h-4 w-4 mr-2" />
                  URL 입력
                </TabsTrigger>
                <TabsTrigger value="file" className="data-[state=active]:bg-slate-600">
                  <FileSpreadsheet className="h-4 w-4 mr-2" />
                  파일 선택
                </TabsTrigger>
              </TabsList>

              <TabsContent value="url" className="space-y-4 mt-4">
                {/* URL 입력 */}
                <div className="space-y-2">
                  <Label className="text-slate-200">분석할 URL</Label>
                  <Input
                    type="url"
                    placeholder="https://www.example.com/product/..."
                    value={urlInput}
                    onChange={(e) => setUrlInput(e.target.value)}
                    className="bg-slate-700 border-slate-600 text-slate-100 placeholder:text-slate-500"
                    data-testid="url-input"
                  />
                  <p className="text-xs text-slate-500">
                    올리브영, 쿠팡, 네이버쇼핑 등 상품 페이지 URL
                  </p>
                </div>

                {/* 최대 수집 건수 */}
                <div className="space-y-2">
                  <Label className="text-slate-200">최대 수집 건수</Label>
                  <Input
                    type="number"
                    min="100"
                    max="2000"
                    value={maxReviews}
                    onChange={(e) => setMaxReviews(parseInt(e.target.value) || 1000)}
                    className="bg-slate-700 border-slate-600 text-slate-100"
                  />
                </div>

                {/* 출력 옵션 섹션 */}
                <div className="space-y-3 p-3 bg-slate-700/50 rounded-lg border border-slate-600">
                  <div className="flex items-center gap-2 text-slate-200 font-medium">
                    <Settings className="h-4 w-4 text-purple-400" />
                    리포트 출력 옵션
                  </div>
                  
                  {/* 리포트 제목 */}
                  <div className="space-y-1">
                    <Label className="text-slate-300 text-sm">리포트 제목 (선택)</Label>
                    <Input
                      type="text"
                      placeholder="예: 2024년 1분기 고객 리뷰 분석"
                      value={outputOptions.reportTitle}
                      onChange={(e) => setOutputOptions({...outputOptions, reportTitle: e.target.value})}
                      className="bg-slate-600 border-slate-500 text-slate-100 text-sm"
                      data-testid="report-title-input"
                    />
                  </div>
                  
                  {/* 포함할 섹션 선택 */}
                  <div className="space-y-2">
                    <Label className="text-slate-300 text-sm">포함할 섹션</Label>
                    <div className="grid grid-cols-2 gap-2">
                      <label className="flex items-center gap-2 text-sm text-slate-300 cursor-pointer">
                        <Checkbox
                          checked={outputOptions.includeSentiment}
                          onCheckedChange={(checked) => setOutputOptions({...outputOptions, includeSentiment: checked})}
                          className="border-slate-500"
                        />
                        감성 분석
                      </label>
                      <label className="flex items-center gap-2 text-sm text-slate-300 cursor-pointer">
                        <Checkbox
                          checked={outputOptions.includeFactors}
                          onCheckedChange={(checked) => setOutputOptions({...outputOptions, includeFactors: checked})}
                          className="border-slate-500"
                        />
                        요인 분석
                      </label>
                      <label className="flex items-center gap-2 text-sm text-slate-300 cursor-pointer">
                        <Checkbox
                          checked={outputOptions.includeGvicAnalysis}
                          onCheckedChange={(checked) => setOutputOptions({...outputOptions, includeGvicAnalysis: checked})}
                          className="border-slate-500"
                        />
                        GVIC 분석
                      </label>
                      <label className="flex items-center gap-2 text-sm text-slate-300 cursor-pointer">
                        <Checkbox
                          checked={outputOptions.includeInsights}
                          onCheckedChange={(checked) => setOutputOptions({...outputOptions, includeInsights: checked})}
                          className="border-slate-500"
                        />
                        인사이트
                      </label>
                      <label className="flex items-center gap-2 text-sm text-slate-300 cursor-pointer col-span-2">
                        <Checkbox
                          checked={outputOptions.includeRecommendations}
                          onCheckedChange={(checked) => setOutputOptions({...outputOptions, includeRecommendations: checked})}
                          className="border-slate-500"
                        />
                        권장 조치 사항
                      </label>
                    </div>
                  </div>
                  
                  {/* 추가 메모 */}
                  <div className="space-y-1">
                    <Label className="text-slate-300 text-sm">추가 메모 (선택)</Label>
                    <Textarea
                      placeholder="리포트에 포함할 추가 사항..."
                      value={outputOptions.customNotes}
                      onChange={(e) => setOutputOptions({...outputOptions, customNotes: e.target.value})}
                      className="bg-slate-600 border-slate-500 text-slate-100 text-sm min-h-[60px]"
                      data-testid="custom-notes-input"
                    />
                  </div>
                </div>

                {/* URL 분석 버튼 */}
                <Button 
                  className="w-full bg-blue-600 hover:bg-blue-700" 
                  onClick={handleAnalyzeUrl}
                  disabled={isRunning || !urlInput.trim()}
                  data-testid="analyze-url-button"
                >
                  {isRunning ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      분석 중...
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4 mr-2" />
                      URL 분석 시작
                    </>
                  )}
                </Button>
              </TabsContent>

              <TabsContent value="file" className="space-y-4 mt-4">
                {/* 파일 목록 */}
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {files.length > 0 ? (
                    files.map((file, idx) => (
                      <div
                        key={idx}
                        onClick={() => setSelectedFile(file)}
                        className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                          selectedFile?.name === file.name 
                            ? 'border-blue-500 bg-blue-500/20' 
                            : 'border-slate-600 hover:border-blue-400 bg-slate-700/50'
                        }`}
                      >
                        <div className="font-medium text-sm text-slate-200 truncate">{file.name}</div>
                        <div className="text-xs text-slate-500">
                          {(file.size / 1024).toFixed(1)} KB
                        </div>
                      </div>
                    ))
                  ) : (
                    <p className="text-slate-500 text-sm">데이터 파일이 없습니다</p>
                  )}
                </div>

                {/* 파일 분석 버튼 */}
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
                      파일 분석 시작
                    </>
                  )}
                </Button>
              </TabsContent>
            </Tabs>

            {/* 진행 단계 */}
            {(isRunning || result) && (
              <div className="space-y-2 mt-4 pt-4 border-t border-slate-700">
                <div className="flex justify-between text-sm text-slate-300">
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
                        <div className="h-4 w-4 rounded-full border border-slate-500" />
                      )}
                      <span className={currentStep >= step.id ? 'text-slate-200' : 'text-slate-500'}>
                        {step.name}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {error && (
              <div className="p-3 bg-red-500/20 text-red-400 rounded-lg text-sm border border-red-500/50">
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
                <Card className="bg-slate-800 border-slate-700">
                  <CardContent className="p-4">
                    <div className="text-sm text-slate-400">총 데이터</div>
                    <div className="text-2xl font-bold text-slate-100">{result.total_records?.toLocaleString()}</div>
                  </CardContent>
                </Card>
                <Card className="bg-slate-800 border-slate-700">
                  <CardContent className="p-4">
                    <div className="text-sm text-slate-400">긍정 비율</div>
                    <div className="text-2xl font-bold text-green-400">
                      {((result.sentiment_distribution?.positive?.ratio || 0) * 100).toFixed(1)}%
                    </div>
                  </CardContent>
                </Card>
                <Card className="bg-slate-800 border-slate-700">
                  <CardContent className="p-4">
                    <div className="text-sm text-slate-400">공정성 지수</div>
                    <div className="text-2xl font-bold text-blue-400">
                      {(result.gvic_results?.fairness_index || 0).toFixed(3)}
                    </div>
                  </CardContent>
                </Card>
                <Card className="bg-slate-800 border-slate-700">
                  <CardContent className="p-4">
                    <div className="text-sm text-slate-400">PDF 리포트</div>
                    <Button 
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDownloadPdf(result.pdf_url)}
                      className="text-blue-400 hover:text-blue-300 hover:bg-blue-500/20 p-0 h-auto flex items-center gap-1"
                      data-testid="download-pdf-button"
                    >
                      <FileDown className="h-4 w-4" />
                      다운로드
                    </Button>
                  </CardContent>
                </Card>
              </div>

              {/* 상품 정보 (URL 분석인 경우) */}
              {result.product_name && (
                <Card className="bg-slate-800 border-slate-700">
                  <CardContent className="p-4">
                    <div className="flex items-center gap-3">
                      <Globe className="h-5 w-5 text-blue-400" />
                      <div>
                        <div className="font-medium text-slate-100">{result.product_name}</div>
                        <div className="text-sm text-slate-400">
                          {result.site_type && <Badge variant="outline" className="mr-2">{result.site_type}</Badge>}
                          {result.url && <span className="truncate">{result.url.substring(0, 50)}...</span>}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* 감성 분포 차트 */}
              <Card className="bg-slate-800 border-slate-700">
                <CardHeader>
                  <CardTitle className="text-slate-100">감성 분포</CardTitle>
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
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>

              {/* 긍정/부정 요인 */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card className="bg-slate-800 border-slate-700">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-green-400">
                      <TrendingUp className="h-5 w-5" />
                      긍정 평가 요인
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {positiveFactorsData.length > 0 ? positiveFactorsData.map((factor, idx) => (
                        <div key={idx} className="flex items-center justify-between">
                          <Badge variant="outline" className="bg-green-500/20 text-green-400 border-green-500/50">
                            {factor.name}
                          </Badge>
                          <div className="text-sm text-slate-300">
                            <span className="font-medium">{factor.count}건</span>
                            <span className="text-slate-500 ml-2">({factor.ratio}%)</span>
                          </div>
                        </div>
                      )) : (
                        <p className="text-slate-500 text-sm">긍정 요인이 없습니다</p>
                      )}
                    </div>
                  </CardContent>
                </Card>

                <Card className="bg-slate-800 border-slate-700">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-red-400">
                      <TrendingDown className="h-5 w-5" />
                      부정 평가 요인
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {negativeFactorsData.length > 0 ? negativeFactorsData.map((factor, idx) => (
                        <div key={idx} className="flex items-center justify-between">
                          <Badge variant="outline" className="bg-red-500/20 text-red-400 border-red-500/50">
                            {factor.name}
                          </Badge>
                          <div className="text-sm text-slate-300">
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
              <Card className="bg-slate-800 border-slate-700">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-slate-100">
                    <BarChart3 className="h-5 w-5 text-purple-400" />
                    분석 인사이트
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {result.insights?.map((insight, idx) => (
                      <div key={idx} className="p-3 bg-slate-700/50 rounded-lg text-sm text-slate-200">
                        {insight}
                      </div>
                    ))}
                    {result.recommendations?.map((rec, idx) => (
                      <div key={idx} className="p-3 bg-blue-500/20 rounded-lg text-sm text-blue-300 border border-blue-500/30">
                        💡 {rec}
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </>
          ) : (
            /* 초기 상태: 기존 리포트 목록 */
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-slate-100">
                  <FileText className="h-5 w-5 text-blue-400" />
                  생성된 리포트
                </CardTitle>
                <CardDescription className="text-slate-400">이전에 생성된 PDF 리포트 목록</CardDescription>
              </CardHeader>
              <CardContent>
                {reports.length > 0 ? (
                  <div className="space-y-2">
                    {reports.map((report, idx) => (
                      <div key={idx} className="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg">
                        <div>
                          <div className="font-medium text-sm text-slate-200">{report.name}</div>
                          <div className="text-xs text-slate-500">
                            {new Date(report.created).toLocaleString('ko-KR')} · {(report.size / 1024).toFixed(1)} KB
                          </div>
                        </div>
                        <Button 
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDownloadPdf(report.name)}
                          className="text-blue-400 hover:text-blue-300 hover:bg-blue-500/20"
                          data-testid={`download-report-${idx}`}
                          title="PDF 다운로드"
                        >
                          <FileDown className="h-5 w-5" />
                        </Button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-slate-500">
                    <FileText className="h-12 w-12 mx-auto mb-3 opacity-50" />
                    <p>아직 생성된 리포트가 없습니다</p>
                    <p className="text-sm">URL을 입력하여 첫 분석을 시작하세요</p>
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
