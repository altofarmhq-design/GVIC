import React, { useState, useEffect, useMemo } from 'react';
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
  Settings, FileDown, Search, ChevronLeft, ChevronRight
} from 'lucide-react';
import {
  PieChart, Pie, Cell, ResponsiveContainer
} from 'recharts';
import { runPipeline, getAnalysisFiles, getPipelineReports, analyzeUrl } from '../../lib/api';
import { api } from '../../lib/api';

const COLORS = {
  positive: '#22c55e',
  neutral: '#f59e0b', 
  negative: '#ef4444'
};

const ITEMS_PER_PAGE = 10;

const PipelineTab = () => {
  const [files, setFiles] = useState([]);
  const [reports, setReports] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [inputMode, setInputMode] = useState('url'); // 'url' or 'file'
  const [urlInput, setUrlInput] = useState('');
  const [maxReviews, setMaxReviews] = useState(1000);
  
  // 검색 및 페이지네이션 상태
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedReportSession, setSelectedReportSession] = useState(null);
  
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
      const [filesRes, reportsRes, sessionsRes] = await Promise.all([
        getAnalysisFiles(),
        getPipelineReports(),
        api.getAnalysisSessions(100).then(res => res.data)
      ]);
      setFiles(filesRes.files || []);
      setReports(reportsRes.reports || []);
      setSessions(sessionsRes.sessions || []);
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

      // 사용자 타임존 오프셋 (분 단위)
      const timezoneOffset = new Date().getTimezoneOffset();

      const response = await analyzeUrl({
        url: urlInput,
        max_reviews: maxReviews,
        output_options: outputOptions,
        timezone_offset: timezoneOffset
      });

      setResult(response);
      setCurrentStep(5);
      loadData(); // 리포트 목록 갱신
    } catch (err) {
      // detail이 객체인 경우 문자열로 변환
      let errorMsg = 'URL 분석 실패';
      if (err.response?.data?.detail) {
        const detail = err.response.data.detail;
        if (typeof detail === 'string') {
          errorMsg = detail;
        } else if (Array.isArray(detail)) {
          errorMsg = detail.map(d => d.msg || JSON.stringify(d)).join(', ');
        } else {
          errorMsg = JSON.stringify(detail);
        }
      } else if (err.message) {
        errorMsg = err.message;
      }
      setError(errorMsg);
      console.error('URL analysis error:', err);
    } finally {
      setIsRunning(false);
    }
  };

  // PDF 다운로드 함수 - fetch + blob 방식으로 강제 다운로드
  const handleDownloadPdf = async (filename) => {
    try {
      const url = `${process.env.REACT_APP_BACKEND_URL}/api/pipeline/download/${filename}`;
      console.log('Downloading PDF from:', url);
      
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Accept': 'application/pdf',
        },
      });
      
      if (!response.ok) {
        throw new Error(`다운로드 실패: ${response.status}`);
      }
      
      const blob = await response.blob();
      console.log('Blob received:', blob.size, 'bytes, type:', blob.type);
      
      // Blob URL 생성
      const blobUrl = window.URL.createObjectURL(blob);
      
      // 다운로드 링크 생성 및 클릭
      const link = document.createElement('a');
      link.style.display = 'none';
      link.href = blobUrl;
      link.download = filename;
      link.setAttribute('download', filename);
      
      // body에 추가
      document.body.appendChild(link);
      
      // 클릭 이벤트 발생
      link.click();
      
      // 정리 (약간의 딜레이 후)
      setTimeout(() => {
        document.body.removeChild(link);
        window.URL.revokeObjectURL(blobUrl);
      }, 100);
      
      console.log('Download triggered for:', filename);
    } catch (error) {
      console.error('PDF 다운로드 오류:', error);
      // Fallback: 새 탭에서 열기
      const fallbackUrl = `${process.env.REACT_APP_BACKEND_URL}/api/pipeline/download/${filename}`;
      window.open(fallbackUrl, '_blank');
    }
  };

  // URL 방식 (fallback)
  const getDownloadUrl = (filename) => {
    return `${process.env.REACT_APP_BACKEND_URL}/api/pipeline/download/${filename}`;
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
      let errorMsg = '파이프라인 실행 실패';
      if (err.response?.data?.detail) {
        const detail = err.response.data.detail;
        if (typeof detail === 'string') {
          errorMsg = detail;
        } else if (Array.isArray(detail)) {
          errorMsg = detail.map(d => d.msg || JSON.stringify(d)).join(', ');
        } else {
          errorMsg = JSON.stringify(detail);
        }
      } else if (err.message) {
        errorMsg = err.message;
      }
      setError(errorMsg);
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

  // 검색 필터링된 리포트 목록
  const filteredReports = useMemo(() => {
    if (!searchQuery.trim()) return reports;
    return reports.filter(report => 
      report.name.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [reports, searchQuery]);

  // 페이지네이션 계산
  const totalPages = Math.ceil(filteredReports.length / ITEMS_PER_PAGE);
  const paginatedReports = useMemo(() => {
    const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
    return filteredReports.slice(startIndex, startIndex + ITEMS_PER_PAGE);
  }, [filteredReports, currentPage]);

  // 검색어 변경 시 페이지 초기화
  useEffect(() => {
    setCurrentPage(1);
  }, [searchQuery]);

  // 리포트 클릭 시 해당 분석 결과 불러오기
  const handleReportClick = async (report) => {
    try {
      // 파일명에서 타임스탬프 추출 (예: GVIC_Report_20260214_004500.pdf)
      const match = report.name.match(/(\d{8}_\d{6})/);
      if (match) {
        const fileTimestamp = match[1]; // "20260214_004500"
        
        // 세션 목록에서 pdf_path가 일치하는 세션 찾기
        let matchingSession = sessions.find(s => {
          if (s.pdf_path) {
            return s.pdf_path.includes(fileTimestamp);
          }
          return false;
        });
        
        // pdf_path로 못 찾으면 시간으로 매칭
        if (!matchingSession) {
          matchingSession = sessions.find(s => {
            const sessionDate = new Date(s.created_at);
            const sessionTimestamp = sessionDate.toISOString()
              .replace(/[-:T]/g, '')
              .slice(0, 14); // "20260214004500" 형식
            const fileTs = fileTimestamp.replace('_', ''); // "20260214004500"
            return sessionTimestamp === fileTs;
          });
        }
        
        if (matchingSession) {
          // 세션 상세 정보 불러오기
          const sessionDetail = await api.getSessionDetail(matchingSession.session_id).then(res => res.data);
          
          // 분석 결과 형식으로 변환 (sentiment_distribution 구조 맞추기)
          setResult({
            total_records: sessionDetail.total_records || 0,
            sentiment_distribution: {
              positive: {
                count: sessionDetail.sentiment_positive || 0,
                ratio: sessionDetail.sentiment_positive_ratio || 0
              },
              neutral: {
                count: sessionDetail.sentiment_neutral || 0,
                ratio: sessionDetail.sentiment_neutral_ratio || 0
              },
              negative: {
                count: sessionDetail.sentiment_negative || 0,
                ratio: sessionDetail.sentiment_negative_ratio || 0
              }
            },
            positive_factors: sessionDetail.positive_factors || [],
            negative_factors: sessionDetail.negative_factors || [],
            gvic_results: {
              fairness_index: sessionDetail.fairness_index || 0,
              convergence: {
                status: sessionDetail.convergence_status,
                balance_index: sessionDetail.convergence_balance_index
              },
              signal: {
                conformance_rate: sessionDetail.signal_conformance_rate
              },
              distribution: {
                public: sessionDetail.distribution_public,
                productive: sessionDetail.distribution_productive,
                individual: sessionDetail.distribution_individual
              }
            },
            insights: sessionDetail.insights || [],
            recommendations: sessionDetail.recommendations || [],
            product_name: sessionDetail.product_name,
            site_type: sessionDetail.source_type,
            url: sessionDetail.source_url,
            pdf_filename: report.name
          });
          return;
        }
      }
      // 매칭되는 세션이 없으면 PDF만 다운로드
      handleDownloadPdf(report.name);
    } catch (err) {
      console.error('Failed to load session detail:', err);
      handleDownloadPdf(report.name);
    }
  };

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

                {/* 최대 수집 건수 - 슬라이더 + 직접 입력 */}
                <div className="space-y-2">
                  <Label className="text-slate-200">최대 수집 건수</Label>
                  <div className="flex items-center gap-3">
                    <input
                      type="range"
                      min="100"
                      max="2000"
                      step="100"
                      value={Math.min(maxReviews, 2000)}
                      onChange={(e) => setMaxReviews(parseInt(e.target.value))}
                      className="flex-1 h-2 bg-slate-600 rounded-lg appearance-none cursor-pointer accent-cyan-500"
                    />
                    <Input
                      type="number"
                      min="100"
                      step="100"
                      value={maxReviews}
                      onChange={(e) => {
                        const val = parseInt(e.target.value) || 100;
                        setMaxReviews(Math.max(100, val));
                      }}
                      className="w-24 bg-slate-700 border-slate-600 text-slate-100 text-center"
                    />
                    <span className="text-slate-400 text-sm">건</span>
                  </div>
                  <p className="text-slate-500 text-xs">권장: 2000건 이하 (더 많은 건수는 직접 입력)</p>
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
                      onClick={() => handleDownloadPdf(result.pdf_filename || 'GVIC_Report_Latest.pdf')}
                      className="text-blue-400 hover:text-blue-300 hover:bg-blue-500/20 p-0 h-auto flex items-center gap-1 mt-1"
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
            /* 초기 상태: 안내 메시지 */
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-slate-100">
                  <BarChart3 className="h-5 w-5 text-purple-400" />
                  분석 결과
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center py-12 text-slate-500">
                  <Globe className="h-16 w-16 mx-auto mb-4 opacity-50" />
                  <p className="text-lg font-medium text-slate-300">URL을 입력하고 분석을 시작하세요</p>
                  <p className="text-sm mt-2">GVIC 엔진이 자동으로 데이터를 수집하고 분석합니다</p>
                </div>
              </CardContent>
            </Card>
          )}
          
          {/* 생성된 리포트 목록 - 검색 및 페이지네이션 */}
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2 text-slate-100">
                    <FileText className="h-5 w-5 text-blue-400" />
                    생성된 리포트
                  </CardTitle>
                  <CardDescription className="text-slate-400">
                    총 {reports.length}개 · 클릭하면 분석 결과 확인
                  </CardDescription>
                </div>
              </div>
              {/* 검색창 */}
              <div className="relative mt-3">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
                <Input
                  type="text"
                  placeholder="파일명으로 검색..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 bg-slate-700 border-slate-600 text-slate-100 placeholder:text-slate-500"
                  data-testid="report-search-input"
                />
              </div>
            </CardHeader>
            <CardContent>
              {filteredReports.length > 0 ? (
                <div className="space-y-4">
                  {/* 리포트 목록 */}
                  <div className="space-y-2">
                    {paginatedReports.map((report, idx) => {
                      const createdDate = new Date(report.created);
                      const localTimeStr = createdDate.toLocaleString('ko-KR', {
                        year: 'numeric',
                        month: '2-digit',
                        day: '2-digit',
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit',
                        hour12: false
                      });
                      
                      return (
                        <div 
                          key={report.name || idx} 
                          className="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg hover:bg-slate-700 cursor-pointer transition-colors"
                          onClick={() => handleReportClick(report)}
                          data-testid={`report-item-${idx}`}
                        >
                          <div className="flex-1">
                            <div className="font-medium text-sm text-slate-200">{report.name}</div>
                            <div className="text-xs text-slate-500">
                              {localTimeStr} · {(report.size / 1024).toFixed(1)} KB
                            </div>
                          </div>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDownloadPdf(report.name);
                            }}
                            className="text-blue-400 hover:text-blue-300 hover:bg-blue-500/20 p-2"
                            data-testid={`download-report-list-${idx}`}
                            title="PDF 다운로드"
                          >
                            <FileDown className="h-5 w-5" />
                          </Button>
                        </div>
                      );
                    })}
                  </div>
                  
                  {/* 페이지네이션 */}
                  {totalPages > 1 && (
                    <div className="flex items-center justify-center gap-2 pt-4 border-t border-slate-700">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                        disabled={currentPage === 1}
                        className="border-slate-600 text-slate-300 disabled:opacity-50"
                      >
                        <ChevronLeft className="h-4 w-4" />
                      </Button>
                      
                      <div className="flex items-center gap-1">
                        {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                          let pageNum;
                          if (totalPages <= 5) {
                            pageNum = i + 1;
                          } else if (currentPage <= 3) {
                            pageNum = i + 1;
                          } else if (currentPage >= totalPages - 2) {
                            pageNum = totalPages - 4 + i;
                          } else {
                            pageNum = currentPage - 2 + i;
                          }
                          
                          return (
                            <Button
                              key={pageNum}
                              variant={currentPage === pageNum ? "default" : "outline"}
                              size="sm"
                              onClick={() => setCurrentPage(pageNum)}
                              className={`w-8 h-8 p-0 ${
                                currentPage === pageNum 
                                  ? 'bg-blue-600 text-white' 
                                  : 'border-slate-600 text-slate-300'
                              }`}
                            >
                              {pageNum}
                            </Button>
                          );
                        })}
                      </div>
                      
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                        disabled={currentPage === totalPages}
                        className="border-slate-600 text-slate-300 disabled:opacity-50"
                      >
                        <ChevronRight className="h-4 w-4" />
                      </Button>
                      
                      <span className="text-sm text-slate-500 ml-2">
                        {currentPage} / {totalPages} 페이지
                      </span>
                    </div>
                  )}
                </div>
              ) : searchQuery ? (
                <div className="text-center py-8 text-slate-500">
                  <Search className="h-12 w-12 mx-auto mb-3 opacity-50" />
                  <p>"{searchQuery}" 검색 결과가 없습니다</p>
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
        </div>
      </div>
    </div>
  );
};

export default PipelineTab;
