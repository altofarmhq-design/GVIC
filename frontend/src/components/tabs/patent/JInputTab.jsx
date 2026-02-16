import { useState, useCallback, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import { 
  Upload, 
  FileText, 
  Globe, 
  Link2, 
  ArrowRight,
  CheckCircle2,
  AlertCircle,
  Loader2,
  X,
  File,
  Image,
  FileSpreadsheet,
  Clock,
  HelpCircle,
  Target,
  Lightbulb,
  Package,
  Code,
  FileCode,
  Sparkles
} from 'lucide-react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL;

/**
 * J:입력 - 외부 시그널 유입 (특허 J: PLATFORM)
 */
export const JInputTab = ({ onSignalSubmit }) => {
  const [inputType, setInputType] = useState("text");
  const [analysisType, setAnalysisType] = useState("general");  // 분석 유형
  
  // 새로운 입력 필드들
  const [purpose, setPurpose] = useState("");        // 왜 질문하는지
  const [expectedResult, setExpectedResult] = useState("");  // 기대하는 결과
  const [textContent, setTextContent] = useState("");
  
  const [urlInput, setUrlInput] = useState("");
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  // 분석 유형 정의
  const analysisTypes = [
    { id: "general", label: "일반 분석", icon: FileText, desc: "텍스트/문서 분석", color: "blue" },
    { id: "code", label: "코드 분석", icon: Code, desc: "오류 검출/품질 평가", color: "green" },
    { id: "patent_idea", label: "특허/아이디어", icon: Lightbulb, desc: "신규성/실현가능성", color: "amber" }
  ];

  // 코드 파일 확장자
  const CODE_EXTENSIONS = ['py', 'js', 'ts', 'jsx', 'tsx', 'java', 'c', 'cpp', 'cs', 'go', 'rs', 'rb', 'php', 'swift', 'kt', 'html', 'css', 'scss', 'sql', 'json', 'xml', 'yaml', 'yml', 'sh', 'bat', 'md'];

  // 파일이 코드인지 확인
  const isCodeFile = (filename) => {
    const ext = filename.split('.').pop().toLowerCase();
    return CODE_EXTENSIONS.includes(ext);
  };

  // 파일 선택 처리
  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    const validFiles = [];
    const invalidFiles = [];
    let hasCodeFile = false;
    
    files.forEach(file => {
      if (isFileSupported(file.name)) {
        validFiles.push(file);
        if (isCodeFile(file.name)) {
          hasCodeFile = true;
        }
      } else {
        const ext = file.name.split('.').pop().toLowerCase();
        invalidFiles.push({ name: file.name, ext });
      }
    });
    
    if (invalidFiles.length > 0) {
      const invalidExts = [...new Set(invalidFiles.map(f => `.${f.ext}`))].join(', ');
      setError(`지원하지 않는 파일 형식입니다: ${invalidExts}\n\n✅ 지원 형식: 문서(.pdf, .hwp, .docx, .txt), 코드(.py, .js, .java 등), 스프레드시트, 이미지`);
    } else {
      setError(null);
    }
    
    if (validFiles.length > 0) {
      setSelectedFiles(prev => [...prev, ...validFiles]);
      // 코드 파일이면 자동으로 코드 분석 모드로 전환
      if (hasCodeFile && analysisType === "general") {
        setAnalysisType("code");
      }
    }
  };

  // 파일 제거
  const removeFile = (index) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
    setError(null);
  };

  // 파일 아이콘 결정
  const getFileIcon = (file) => {
    const ext = file.name.split('.').pop().toLowerCase();
    if (['xlsx', 'xls', 'csv'].includes(ext)) return FileSpreadsheet;
    if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp'].includes(ext)) return Image;
    if (['hwp', 'hwpx'].includes(ext)) return FileText;
    if (ext === 'docx') return FileText;
    if (CODE_EXTENSIONS.includes(ext)) return FileCode;
    return File;
  };

  // 파일 크기 포맷
  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  // 텍스트 제출
  const handleTextSubmit = async () => {
    if (!textContent.trim()) return;
    
    setSubmitting(true);
    setError(null);
    setResult(null);
    
    try {
      const token = localStorage.getItem('token');
      
      if (!token) {
        setError('로그인이 필요합니다. 페이지를 새로고침 후 다시 로그인해주세요.');
        setSubmitting(false);
        return;
      }
      
      const response = await axios.post(`${API_URL}/api/signal/ingest`, {
        type: 'text',
        content: textContent,
        purpose: purpose,
        expected_result: expectedResult,
        analysis_type: analysisType
      }, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      setResult(response.data);
      if (onSignalSubmit) onSignalSubmit(response.data);
      
    } catch (err) {
      setError(err.response?.data?.detail || '전송 실패');
    }
    setSubmitting(false);
  };

  // URL 제출
  const handleUrlSubmit = async () => {
    if (!urlInput.trim()) return;
    
    setSubmitting(true);
    setError(null);
    setResult(null);
    
    try {
      const token = localStorage.getItem('token');
      
      if (!token) {
        setError('로그인이 필요합니다. 페이지를 새로고침 후 다시 로그인해주세요.');
        setSubmitting(false);
        return;
      }
      
      const response = await axios.post(`${API_URL}/api/signal/ingest/url`, {
        url: urlInput,
        purpose: purpose,
        expected_result: expectedResult
      }, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      setResult(response.data);
      if (onSignalSubmit) onSignalSubmit(response.data);
      
    } catch (err) {
      setError(err.response?.data?.detail || 'URL 처리 실패');
    }
    setSubmitting(false);
  };

  // 파일 제출
  const handleFileSubmit = async () => {
    if (selectedFiles.length === 0) return;
    
    setSubmitting(true);
    setError(null);
    setResult(null);
    
    try {
      const token = localStorage.getItem('token');
      
      if (!token) {
        setError('로그인이 필요합니다.');
        setSubmitting(false);
        return;
      }
      
      const formData = new FormData();
      selectedFiles.forEach(file => {
        formData.append('files', file);
      });
      formData.append('purpose', purpose);
      formData.append('expected_result', expectedResult);
      
      const response = await axios.post(`${API_URL}/api/signal/ingest/files`, formData, {
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        }
      });
      
      setResult(response.data);
      if (onSignalSubmit) onSignalSubmit(response.data);
      setSelectedFiles([]);
      
    } catch (err) {
      setError(err.response?.data?.detail || '파일 처리 실패');
    }
    setSubmitting(false);
  };

  // 제출 핸들러
  const handleSubmit = () => {
    switch (inputType) {
      case 'text': handleTextSubmit(); break;
      case 'url': handleUrlSubmit(); break;
      case 'file': handleFileSubmit(); break;
      default: break;
    }
  };

  // 초기화
  const handleReset = () => {
    setPurpose("");
    setExpectedResult("");
    setTextContent("");
    setUrlInput("");
    setSelectedFiles([]);
    setResult(null);
    setError(null);
  };

  const inputTypes = [
    { id: "text", label: "텍스트", icon: FileText, desc: "직접 입력", enabled: true },
    { id: "file", label: "파일", icon: Upload, desc: "다양한 형식", enabled: true },
    { id: "url", label: "URL", icon: Globe, desc: "웹페이지", enabled: true },
    { id: "api", label: "API", icon: Link2, desc: "준비 중", enabled: false }
  ];

  const supportedFormats = [
    { ext: "문서", formats: ".pdf, .hwp, .hwpx, .docx, .txt" },
    { ext: "스프레드시트", formats: ".xlsx, .xls, .csv" },
    { ext: "이미지", formats: ".jpg, .png, .gif, .webp" },
    { ext: "코드", formats: ".py, .js, .ts, .java, .c, .cpp, .go, .html, .css, .sql 등" }
  ];

  // 지원하는 파일 확장자 목록
  const SUPPORTED_EXTENSIONS = [
    // 문서
    'pdf', 'hwp', 'hwpx', 'docx', 'txt',
    // 스프레드시트
    'xlsx', 'xls', 'csv',
    // 이미지
    'jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp',
    // 코드
    ...CODE_EXTENSIONS
  ];

  // 파일 확장자 검증
  const isFileSupported = (filename) => {
    const ext = filename.split('.').pop().toLowerCase();
    return SUPPORTED_EXTENSIONS.includes(ext);
  };

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-100 flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold">J</span>
            </div>
            J:입력
          </h2>
          <p className="text-slate-400 mt-1">외부 시그널 유입 - PLATFORM 모듈</p>
        </div>
        <Badge variant="outline" className="text-blue-400 border-blue-600">
          특허 J
        </Badge>
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* 좌측: 입력 영역 */}
        <div className="space-y-4">
          {/* 질문 목적 & 기대 결과 */}
          <Card className="bg-gradient-to-r from-slate-800/80 to-blue-900/30 border-blue-700">
            <CardHeader className="pb-3">
              <CardTitle className="text-slate-100 text-lg flex items-center gap-2">
                <Target className="w-5 h-5 text-blue-400" />
                질문 정의
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label className="text-slate-300 flex items-center gap-2 mb-2">
                  <HelpCircle className="w-4 h-4 text-amber-400" />
                  왜 질문하는지 (목적)
                </Label>
                <Textarea
                  placeholder="이 시그널을 분석하는 목적을 입력하세요"
                  value={purpose}
                  onChange={(e) => setPurpose(e.target.value)}
                  className="bg-slate-900 border-slate-600 text-slate-100 min-h-[80px]"
                />
              </div>
              <div>
                <Label className="text-slate-300 flex items-center gap-2 mb-2">
                  <Lightbulb className="w-4 h-4 text-emerald-400" />
                  기대하는 결과
                </Label>
                <Textarea
                  placeholder="어떤 결과를 얻고 싶은지 입력하세요"
                  value={expectedResult}
                  onChange={(e) => setExpectedResult(e.target.value)}
                  className="bg-slate-900 border-slate-600 text-slate-100 min-h-[80px]"
                />
              </div>
            </CardContent>
          </Card>

          {/* 입력 유형 선택 */}
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader className="pb-2">
              <CardTitle className="text-slate-100 text-base">시그널 입력 방식</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-4 gap-2">
                {inputTypes.map((type) => (
                  <button
                    key={type.id}
                    onClick={() => type.enabled && setInputType(type.id)}
                    disabled={!type.enabled}
                    className={`p-3 rounded-lg border-2 transition-all relative ${
                      !type.enabled 
                        ? 'border-slate-700 bg-slate-800/30 cursor-not-allowed opacity-50'
                        : inputType === type.id
                          ? 'border-blue-500 bg-blue-500/20'
                          : 'border-slate-600 bg-slate-800/50 hover:border-slate-500'
                    }`}
                  >
                    {!type.enabled && (
                      <Badge className="absolute -top-1 -right-1 bg-slate-600 text-[8px] px-1 py-0">
                        준비중
                      </Badge>
                    )}
                    <type.icon className={`w-6 h-6 mx-auto mb-1 ${
                      !type.enabled ? 'text-slate-600' :
                      inputType === type.id ? 'text-blue-400' : 'text-slate-400'
                    }`} />
                    <p className={`text-xs font-medium ${
                      !type.enabled ? 'text-slate-600' :
                      inputType === type.id ? 'text-blue-300' : 'text-slate-300'
                    }`}>{type.label}</p>
                  </button>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* 분석 유형 선택 */}
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader className="pb-2">
              <CardTitle className="text-slate-100 text-base flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-amber-400" />
                AI 분석 유형
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-3">
                {analysisTypes.map((type) => {
                  const Icon = type.icon;
                  const isSelected = analysisType === type.id;
                  const colorClass = {
                    blue: isSelected ? 'border-blue-500 bg-blue-500/20' : 'hover:border-blue-500/50',
                    green: isSelected ? 'border-green-500 bg-green-500/20' : 'hover:border-green-500/50',
                    amber: isSelected ? 'border-amber-500 bg-amber-500/20' : 'hover:border-amber-500/50'
                  }[type.color];
                  const iconColor = {
                    blue: isSelected ? 'text-blue-400' : 'text-slate-400',
                    green: isSelected ? 'text-green-400' : 'text-slate-400',
                    amber: isSelected ? 'text-amber-400' : 'text-slate-400'
                  }[type.color];
                  
                  return (
                    <button
                      key={type.id}
                      onClick={() => setAnalysisType(type.id)}
                      className={`p-4 rounded-lg border-2 transition-all ${
                        isSelected 
                          ? colorClass
                          : `border-slate-600 bg-slate-800/50 ${colorClass}`
                      }`}
                    >
                      <Icon className={`w-6 h-6 mx-auto mb-2 ${iconColor}`} />
                      <p className={`text-sm font-medium ${isSelected ? 'text-slate-100' : 'text-slate-300'}`}>
                        {type.label}
                      </p>
                      <p className="text-xs text-slate-500 mt-1">{type.desc}</p>
                    </button>
                  );
                })}
              </div>
              <p className="text-xs text-slate-500 mt-3 text-center">
                * 코드 파일 업로드 시 자동으로 "코드 분석" 모드로 전환됩니다
              </p>
            </CardContent>
          </Card>

          {/* 시그널 입력 */}
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader className="pb-2">
              <CardTitle className="text-slate-100 text-base">시그널 내용</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {inputType === "text" && (
                <Textarea
                  placeholder="분석할 시그널을 입력하세요"
                  value={textContent}
                  onChange={(e) => setTextContent(e.target.value)}
                  className="bg-slate-900 border-slate-600 text-slate-100 min-h-[120px]"
                />
              )}

              {inputType === "url" && (
                <Input
                  placeholder="URL 입력 (http:// 또는 https://)"
                  value={urlInput}
                  onChange={(e) => setUrlInput(e.target.value)}
                  className="bg-slate-900 border-slate-600 text-slate-100"
                />
              )}

              {inputType === "file" && (
                <div className="space-y-3">
                  <div 
                    className="border-2 border-dashed border-slate-600 rounded-lg p-4 text-center cursor-pointer hover:border-blue-500 transition-colors"
                    onClick={() => fileInputRef.current?.click()}
                  >
                    <Upload className="w-8 h-8 text-slate-500 mx-auto mb-2" />
                    <p className="text-slate-400 text-sm">클릭하여 파일 선택</p>
                    <p className="text-slate-500 text-xs mt-2">
                      지원 형식: PDF, HWP, HWPX, DOCX, TXT, Excel, CSV, 이미지
                    </p>
                    <input
                      ref={fileInputRef}
                      type="file"
                      multiple
                      accept=".pdf,.hwp,.hwpx,.docx,.txt,.xlsx,.xls,.csv,.jpg,.jpeg,.png,.gif,.webp,.bmp"
                      onChange={handleFileSelect}
                      className="hidden"
                    />
                  </div>
                  
                  {/* 지원 형식 상세 안내 */}
                  <div className="bg-slate-900/50 rounded-lg p-3 text-xs">
                    <p className="text-slate-400 mb-2 font-medium">📁 지원하는 파일 형식:</p>
                    <div className="grid grid-cols-3 gap-2 text-slate-500">
                      <div>
                        <span className="text-blue-400">문서:</span>
                        <p>.pdf .hwp .hwpx .docx .txt</p>
                      </div>
                      <div>
                        <span className="text-green-400">스프레드시트:</span>
                        <p>.xlsx .xls .csv</p>
                      </div>
                      <div>
                        <span className="text-amber-400">이미지:</span>
                        <p>.jpg .png .gif .webp</p>
                      </div>
                    </div>
                  </div>
                  
                  {selectedFiles.length > 0 && (
                    <div className="space-y-1">
                      {selectedFiles.map((file, index) => {
                        const FileIcon = getFileIcon(file);
                        return (
                          <div key={index} className="flex items-center justify-between bg-slate-900 rounded p-2">
                            <div className="flex items-center gap-2">
                              <FileIcon className="w-4 h-4 text-blue-400" />
                              <span className="text-slate-200 text-sm truncate max-w-[200px]">{file.name}</span>
                              <span className="text-slate-500 text-xs">({formatFileSize(file.size)})</span>
                            </div>
                            <button onClick={() => removeFile(index)} className="text-slate-500 hover:text-red-400">
                              <X className="w-4 h-4" />
                            </button>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              )}

              {error && (
                <div className="bg-red-900/30 border border-red-600 rounded-lg p-2 text-red-400 text-sm flex items-center gap-2">
                  <AlertCircle className="w-4 h-4" />
                  {error}
                </div>
              )}

              <div className="flex gap-2">
                <Button 
                  onClick={handleSubmit}
                  disabled={
                    submitting || 
                    (inputType === "text" && !textContent.trim()) || 
                    (inputType === "url" && !urlInput.trim()) ||
                    (inputType === "file" && selectedFiles.length === 0)
                  }
                  className="flex-1 bg-blue-600 hover:bg-blue-700"
                >
                  {submitting ? (
                    <><Loader2 className="w-4 h-4 mr-2 animate-spin" />처리 중...</>
                  ) : (
                    <><ArrowRight className="w-4 h-4 mr-2" />분석 시작</>
                  )}
                </Button>
                <Button variant="outline" onClick={handleReset}>
                  초기화
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* 우측: 결과 영역 */}
        <div className="space-y-4">
          {!result ? (
            <Card className="bg-slate-800/30 border-slate-700 border-dashed h-full flex items-center justify-center min-h-[400px]">
              <div className="text-center py-8">
                <Target className="w-16 h-16 text-slate-600 mx-auto mb-4" />
                <p className="text-slate-500 text-lg">분석 결과 대기 중</p>
                <p className="text-slate-600 text-sm mt-2">
                  질문 목적과 기대 결과를 입력하고<br/>시그널을 전송하세요
                </p>
              </div>
            </Card>
          ) : (
            <ScrollArea className="h-[550px]">
              <div className="space-y-4 pr-4">
                {/* 처리 결과 */}
                <Card className="bg-green-900/20 border-green-600">
                  <CardContent className="py-4">
                    <div className="flex items-center gap-3 mb-3">
                      <CheckCircle2 className="w-6 h-6 text-green-400" />
                      <div>
                        <p className="text-green-300 font-medium">파이프라인 처리 완료</p>
                        <p className="text-slate-400 text-sm">시그널 ID: {result.signal_id}</p>
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div className="bg-slate-800 rounded p-2">
                        <p className="text-slate-500">분류</p>
                        <Badge className={
                          result.category === 'wanted' ? 'bg-blue-600' :
                          result.category === 'unwanted' ? 'bg-amber-600' : 'bg-slate-600'
                        }>
                          {result.category === 'wanted' ? '원하는 것' :
                           result.category === 'unwanted' ? '자산화 대상' : 'Null'}
                        </Badge>
                      </div>
                      <div className="bg-slate-800 rounded p-2">
                        <p className="text-slate-500">처리 단계</p>
                        <p className="text-slate-200">{Object.keys(result.stages_completed || {}).length}개 완료</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* 요청 결과 */}
                <Card className="bg-blue-900/20 border-blue-600">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-blue-300 text-base flex items-center gap-2">
                      <Lightbulb className="w-5 h-5" />
                      요청하신 결과
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-slate-300 text-sm">
                      {result.analysis_result || "시그널이 성공적으로 처리되었습니다. 상세 분석 결과는 각 단계별 탭에서 확인할 수 있습니다."}
                    </p>
                  </CardContent>
                </Card>

                {/* 관련 자산 추천 */}
                <Card className="bg-amber-900/20 border-amber-600">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-amber-300 text-base flex items-center gap-2">
                      <Package className="w-5 h-5" />
                      관련 모듈화 자산 추천
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {result.related_assets && result.related_assets.length > 0 ? (
                      <div className="space-y-2">
                        {result.related_assets.map((asset, idx) => (
                          <div key={idx} className="bg-slate-800 rounded p-3">
                            <div className="flex items-center justify-between mb-1">
                              <Badge variant="outline" className="text-amber-400 border-amber-600">
                                {asset.asset_id}
                              </Badge>
                              <span className="text-slate-400 text-xs">관련도: {(asset.relevance * 100).toFixed(0)}%</span>
                            </div>
                            <p className="text-slate-300 text-sm">{asset.summary}</p>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-slate-400 text-sm">
                        아직 관련된 모듈화 자산이 없습니다. 시스템이 더 많은 시그널을 학습하면 관련 자산을 추천해 드립니다.
                      </p>
                    )}
                  </CardContent>
                </Card>

                {/* 단계별 처리 상태 */}
                <Card className="bg-slate-800/50 border-slate-700">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-slate-100 text-base">처리 단계</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-1">
                      {Object.entries(result.stages_completed || {}).map(([stage, status]) => (
                        <div key={stage} className="flex items-center justify-between text-sm">
                          <span className="text-slate-400">{stage}</span>
                          <Badge className={status === 'completed' ? 'bg-green-600' : 'bg-slate-600'}>
                            {status}
                          </Badge>
                        </div>
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
        <span className="px-3 py-1 bg-blue-600/30 rounded text-blue-400">J:입력</span>
        <ArrowRight className="w-4 h-4" />
        <span className="px-3 py-1 bg-slate-700 rounded">LL:의도</span>
        <ArrowRight className="w-4 h-4" />
        <span className="px-3 py-1 bg-slate-700 rounded">H:코어</span>
        <ArrowRight className="w-4 h-4" />
        <span className="px-3 py-1 bg-slate-700 rounded">...</span>
      </div>
    </div>
  );
};

export default JInputTab;
