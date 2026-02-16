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
  
  // 5:3:2 비율 설정
  const [showRatioSettings, setShowRatioSettings] = useState(false);
  const [ratioWanted, setRatioWanted] = useState(5);      // 원하는 것 (직접 분석)
  const [ratioUnwanted, setRatioUnwanted] = useState(3);  // 자산화 대상
  const [ratioNull, setRatioNull] = useState(2);          // Null

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
        analysis_type: analysisType,
        // 5:3:2 비율 설정
        classification_ratio: {
          wanted: ratioWanted,
          unwanted: ratioUnwanted,
          null: ratioNull
        }
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
          {/* 통합 질문 입력 카드 */}
          <Card className="bg-gradient-to-r from-slate-800/80 to-blue-900/30 border-blue-700">
            <CardHeader className="pb-3">
              <CardTitle className="text-slate-100 text-lg flex items-center gap-2">
                <Target className="w-5 h-5 text-blue-400" />
                질문 입력
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* 입력 방식 슬라이드 탭 */}
              <div className="flex items-center gap-1 bg-slate-900/50 rounded-lg p-1">
                {inputTypes.map((type) => {
                  const Icon = type.icon;
                  const isDisabled = !type.enabled;
                  return (
                    <button
                      key={type.id}
                      onClick={() => type.enabled && setInputType(type.id)}
                      disabled={isDisabled}
                      className={`flex-1 flex items-center justify-center gap-2 py-2 px-3 rounded-md transition-all ${
                        isDisabled
                          ? 'text-slate-600 cursor-not-allowed'
                          : inputType === type.id
                            ? 'bg-blue-600 text-white'
                            : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                      }`}
                    >
                      <Icon className="w-4 h-4" />
                      <span className="text-sm">{type.label}</span>
                      {isDisabled && (
                        <span className="text-xs text-amber-500 ml-1">(준비중)</span>
                      )}
                    </button>
                  );
                })}
              </div>

              {/* 텍스트 입력 */}
              {inputType === "text" && (
                <div>
                  <Textarea
                    placeholder="질문이나 분석할 내용을 자유롭게 입력하세요.&#10;&#10;예시:&#10;• 이 코드의 버그를 찾아주세요&#10;• 새로운 아이디어의 시장성을 분석해주세요&#10;• 이 문서의 핵심 내용을 요약해주세요"
                    value={textContent}
                    onChange={(e) => setTextContent(e.target.value)}
                    className="bg-slate-900 border-slate-600 text-slate-100 min-h-[180px] text-base"
                  />
                </div>
              )}

              {/* URL 입력 */}
              {inputType === "url" && (
                <div className="space-y-3">
                  <Input
                    placeholder="분석할 웹페이지 URL을 입력하세요 (http:// 또는 https://)"
                    value={urlInput}
                    onChange={(e) => setUrlInput(e.target.value)}
                    className="bg-slate-900 border-slate-600 text-slate-100 text-base py-6"
                  />
                  <Textarea
                    placeholder="이 URL에서 무엇을 알고 싶으신가요?&#10;&#10;예시:&#10;• 구매후기를 크롤링해서 분석해줘&#10;• 이 제품의 가격과 특징을 요약해줘&#10;• 고객 리뷰에서 장단점을 추출해줘&#10;• 경쟁사 제품과 비교 분석해줘"
                    value={purpose}
                    onChange={(e) => setPurpose(e.target.value)}
                    className="bg-slate-900 border-slate-600 text-slate-100 min-h-[100px] text-sm"
                  />
                  <p className="text-xs text-slate-500">
                    💡 "리뷰", "후기", "크롤링" 키워드 입력 시 자동으로 구매후기를 수집합니다
                  </p>
                </div>
              )}

              {/* 파일 업로드 */}
              {inputType === "file" && (
                <div className="space-y-3">
                  <div 
                    className="border-2 border-dashed border-slate-600 rounded-lg p-6 text-center cursor-pointer hover:border-blue-500 transition-colors"
                    onClick={() => fileInputRef.current?.click()}
                  >
                    <Upload className="w-10 h-10 text-slate-500 mx-auto mb-2" />
                    <p className="text-slate-300 text-sm">클릭하여 파일 선택</p>
                    <p className="text-slate-500 text-xs mt-2">
                      문서, 코드, 스프레드시트, 이미지 지원
                    </p>
                    <input
                      ref={fileInputRef}
                      type="file"
                      multiple
                      accept=".pdf,.hwp,.hwpx,.docx,.txt,.xlsx,.xls,.csv,.jpg,.jpeg,.png,.gif,.webp,.bmp,.py,.js,.ts,.jsx,.tsx,.java,.c,.cpp,.cs,.go,.rs,.rb,.php,.swift,.kt,.html,.css,.scss,.sql,.json,.xml,.yaml,.yml,.sh,.bat,.md"
                      onChange={handleFileSelect}
                      className="hidden"
                    />
                  </div>
                  
                  {/* 선택된 파일 목록 */}
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

              <p className="text-xs text-slate-500">
                💡 AI가 질문의 목적과 기대결과를 자동으로 분석합니다
              </p>
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

          {/* 5:3:2 시그널 분류 비율 설정 */}
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-slate-100 text-base flex items-center gap-2">
                  <Target className="w-4 h-4 text-purple-400" />
                  시그널 분류 비율 (5:3:2)
                </CardTitle>
                <button
                  onClick={() => setShowRatioSettings(!showRatioSettings)}
                  className="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1"
                >
                  {showRatioSettings ? '접기' : '조절하기'}
                  <ArrowRight className={`w-3 h-3 transition-transform ${showRatioSettings ? 'rotate-90' : ''}`} />
                </button>
              </div>
            </CardHeader>
            <CardContent>
              {/* 기본 설명 */}
              <div className="bg-slate-900/50 rounded-lg p-3 mb-3">
                <p className="text-slate-300 text-sm mb-2">
                  입력된 시그널은 AI가 자동으로 분류합니다:
                </p>
                <div className="grid grid-cols-3 gap-2 text-xs">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-blue-500"></div>
                    <span className="text-slate-400">원하는 것 <span className="text-blue-400 font-bold">{ratioWanted}</span></span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-amber-500"></div>
                    <span className="text-slate-400">자산화 대상 <span className="text-amber-400 font-bold">{ratioUnwanted}</span></span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-slate-500"></div>
                    <span className="text-slate-400">Null <span className="text-slate-300 font-bold">{ratioNull}</span></span>
                  </div>
                </div>
                <p className="text-slate-500 text-xs mt-2">
                  {ratioWanted === 5 && ratioUnwanted === 3 && ratioNull === 2 
                    ? '※ 기본 비율 5:3:2가 적용됩니다. 조절하지 않으면 이 비율을 유지합니다.'
                    : `※ 사용자 설정 비율 ${ratioWanted}:${ratioUnwanted}:${ratioNull}이 적용됩니다.`
                  }
                </p>
              </div>

              {/* 비율 조절 (토글) */}
              {showRatioSettings && (
                <div className="space-y-3 border-t border-slate-700 pt-3">
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <label className="text-xs text-blue-400 mb-1 block">원하는 것 (직접 분석)</label>
                      <input
                        type="range"
                        min="0"
                        max="10"
                        value={ratioWanted}
                        onChange={(e) => setRatioWanted(parseInt(e.target.value))}
                        className="w-full accent-blue-500"
                      />
                      <p className="text-center text-blue-300 font-bold">{ratioWanted}</p>
                    </div>
                    <div>
                      <label className="text-xs text-amber-400 mb-1 block">자산화 대상</label>
                      <input
                        type="range"
                        min="0"
                        max="10"
                        value={ratioUnwanted}
                        onChange={(e) => setRatioUnwanted(parseInt(e.target.value))}
                        className="w-full accent-amber-500"
                      />
                      <p className="text-center text-amber-300 font-bold">{ratioUnwanted}</p>
                    </div>
                    <div>
                      <label className="text-xs text-slate-400 mb-1 block">Null (무시)</label>
                      <input
                        type="range"
                        min="0"
                        max="10"
                        value={ratioNull}
                        onChange={(e) => setRatioNull(parseInt(e.target.value))}
                        className="w-full accent-slate-500"
                      />
                      <p className="text-center text-slate-300 font-bold">{ratioNull}</p>
                    </div>
                  </div>
                  <div className="flex justify-between items-center">
                    <p className="text-xs text-slate-500">
                      현재 비율: <span className="text-slate-300 font-mono">{ratioWanted}:{ratioUnwanted}:{ratioNull}</span>
                    </p>
                    <button
                      onClick={() => { setRatioWanted(5); setRatioUnwanted(3); setRatioNull(2); }}
                      className="text-xs text-purple-400 hover:text-purple-300"
                    >
                      기본값(5:3:2) 복원
                    </button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* 에러 메시지 및 제출 버튼 */}
          <Card className="bg-slate-800/50 border-slate-700">
            <CardContent className="pt-4 space-y-3">
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
                  질문을 입력하고<br/>분석 시작 버튼을 클릭하세요
                </p>
              </div>
            </Card>
          ) : (
            <ScrollArea className="h-[600px]">
              <div className="space-y-4 pr-4">
                {/* 처리 결과 요약 */}
                <Card className="bg-green-900/20 border-green-600">
                  <CardContent className="py-4">
                    <div className="flex items-center gap-3 mb-3">
                      <CheckCircle2 className="w-6 h-6 text-green-400" />
                      <div>
                        <p className="text-green-300 font-medium">분석 완료</p>
                        <p className="text-slate-400 text-sm">시그널 ID: {result.signal_id}</p>
                      </div>
                    </div>
                    <div className="grid grid-cols-3 gap-2 text-sm">
                      <div className="bg-slate-800 rounded p-2">
                        <p className="text-slate-500 text-xs">분석 유형</p>
                        <Badge className="bg-blue-600 mt-1">
                          {result.ai_analysis?.analysis_type === 'code' ? '💻 코드 분석' :
                           result.ai_analysis?.analysis_type === 'patent_idea' ? '💡 특허/아이디어' : '📝 일반 분석'}
                        </Badge>
                      </div>
                      <div className="bg-slate-800 rounded p-2">
                        <p className="text-slate-500 text-xs">분류</p>
                        <Badge className={
                          result.category === 'wanted' ? 'bg-emerald-600 mt-1' :
                          result.category === 'unwanted' ? 'bg-amber-600 mt-1' : 'bg-slate-600 mt-1'
                        }>
                          {result.category === 'wanted' ? '원하는 것' :
                           result.category === 'unwanted' ? '자산화 대상' : 'Null'}
                        </Badge>
                      </div>
                      <div className="bg-slate-800 rounded p-2">
                        <p className="text-slate-500 text-xs">신뢰도</p>
                        <p className="text-slate-200 mt-1">{((result.ai_analysis?.confidence || 0) * 100).toFixed(0)}%</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* AI 분석 요약 */}
                {result.ai_analysis?.analysis_summary && (
                  <Card className="bg-blue-900/20 border-blue-600">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-blue-300 text-base flex items-center gap-2">
                        <Sparkles className="w-5 h-5" />
                        AI 분석 요약
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-slate-200 text-sm leading-relaxed">
                        {result.ai_analysis.analysis_summary}
                      </p>
                    </CardContent>
                  </Card>
                )}

                {/* 일반 분석 결과 */}
                {result.ai_analysis?.analysis_type === 'general' && result.ai_analysis?.purpose_analysis && (
                  <>
                    <Card className="bg-slate-800/50 border-slate-700">
                      <CardHeader className="pb-2">
                        <CardTitle className="text-slate-100 text-base flex items-center gap-2">
                          <Target className="w-5 h-5 text-blue-400" />
                          목적 분석
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-3">
                        <div>
                          <p className="text-slate-500 text-xs mb-1">해석</p>
                          <p className="text-slate-300 text-sm">{result.ai_analysis.purpose_analysis.interpretation}</p>
                        </div>
                        <div>
                          <p className="text-slate-500 text-xs mb-1">분석 결과</p>
                          <p className="text-slate-300 text-sm">{result.ai_analysis.purpose_analysis.findings}</p>
                        </div>
                      </CardContent>
                    </Card>

                    {result.ai_analysis?.expected_result && (
                      <Card className="bg-emerald-900/20 border-emerald-600">
                        <CardHeader className="pb-2">
                          <CardTitle className="text-emerald-300 text-base flex items-center gap-2">
                            <Lightbulb className="w-5 h-5" />
                            기대 결과 답변
                          </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-3">
                          <p className="text-slate-200 text-sm leading-relaxed">
                            {result.ai_analysis.expected_result.answer}
                          </p>
                          {result.ai_analysis.expected_result.evidence?.length > 0 && (
                            <div>
                              <p className="text-slate-500 text-xs mb-2">근거</p>
                              <ul className="space-y-1">
                                {result.ai_analysis.expected_result.evidence.map((ev, idx) => (
                                  <li key={idx} className="text-slate-400 text-sm flex items-start gap-2">
                                    <span className="text-emerald-400">•</span> {ev}
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </CardContent>
                      </Card>
                    )}
                  </>
                )}

                {/* 코드 분석 결과 */}
                {result.ai_analysis?.analysis_type === 'code' && (
                  <>
                    {/* 문법 오류 */}
                    {result.ai_analysis?.syntax_errors?.length > 0 && (
                      <Card className="bg-red-900/20 border-red-600">
                        <CardHeader className="pb-2">
                          <CardTitle className="text-red-300 text-base flex items-center gap-2">
                            <AlertCircle className="w-5 h-5" />
                            문법/컴파일 오류 ({result.ai_analysis.syntax_errors.length}건)
                          </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-2">
                          {result.ai_analysis.syntax_errors.map((err, idx) => (
                            <div key={idx} className="bg-slate-800 rounded p-3">
                              <div className="flex items-center gap-2 mb-2">
                                <Badge variant="outline" className="text-red-400 border-red-600 text-xs">
                                  Line {err.line}
                                </Badge>
                                <span className="text-red-300 text-sm font-medium">{err.error}</span>
                              </div>
                              <p className="text-slate-400 text-sm">💡 {err.suggestion}</p>
                            </div>
                          ))}
                        </CardContent>
                      </Card>
                    )}

                    {/* 버그 가능성 */}
                    {result.ai_analysis?.potential_bugs?.length > 0 && (
                      <Card className="bg-amber-900/20 border-amber-600">
                        <CardHeader className="pb-2">
                          <CardTitle className="text-amber-300 text-base flex items-center gap-2">
                            <AlertCircle className="w-5 h-5" />
                            버그 가능성 ({result.ai_analysis.potential_bugs.length}건)
                          </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-2">
                          {result.ai_analysis.potential_bugs.map((bug, idx) => (
                            <div key={idx} className="bg-slate-800 rounded p-3">
                              <div className="flex items-center justify-between mb-2">
                                <span className="text-amber-300 text-sm">{bug.location}</span>
                                <Badge className={
                                  bug.severity === 'high' ? 'bg-red-600' :
                                  bug.severity === 'medium' ? 'bg-amber-600' : 'bg-slate-600'
                                }>{bug.severity}</Badge>
                              </div>
                              <p className="text-slate-300 text-sm mb-1">{bug.issue}</p>
                              <p className="text-slate-400 text-sm">🔧 {bug.fix}</p>
                            </div>
                          ))}
                        </CardContent>
                      </Card>
                    )}

                    {/* 코드 품질 */}
                    {result.ai_analysis?.code_quality && (
                      <Card className="bg-slate-800/50 border-slate-700">
                        <CardHeader className="pb-2">
                          <CardTitle className="text-slate-100 text-base">코드 품질 평가</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="grid grid-cols-4 gap-2 mb-3">
                            {[
                              { label: '가독성', value: result.ai_analysis.code_quality.readability_score },
                              { label: '유지보수성', value: result.ai_analysis.code_quality.maintainability_score },
                              { label: '효율성', value: result.ai_analysis.code_quality.efficiency_score },
                              { label: '종합', value: result.ai_analysis.code_quality.overall_score }
                            ].map((item, idx) => (
                              <div key={idx} className="text-center">
                                <p className="text-slate-500 text-xs mb-1">{item.label}</p>
                                <div className={`text-lg font-bold ${
                                  item.value >= 0.8 ? 'text-green-400' :
                                  item.value >= 0.6 ? 'text-amber-400' : 'text-red-400'
                                }`}>
                                  {(item.value * 100).toFixed(0)}%
                                </div>
                              </div>
                            ))}
                          </div>
                          <p className="text-slate-400 text-sm">{result.ai_analysis.code_quality.comments}</p>
                        </CardContent>
                      </Card>
                    )}

                    {/* 개선 제안 */}
                    {result.ai_analysis?.improvements?.length > 0 && (
                      <Card className="bg-blue-900/20 border-blue-600">
                        <CardHeader className="pb-2">
                          <CardTitle className="text-blue-300 text-base flex items-center gap-2">
                            <Lightbulb className="w-5 h-5" />
                            개선 제안
                          </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-2">
                          {result.ai_analysis.improvements.map((imp, idx) => (
                            <div key={idx} className="bg-slate-800 rounded p-3">
                              <div className="flex items-center justify-between mb-2">
                                <Badge variant="outline" className="text-blue-400 border-blue-600 text-xs">
                                  {imp.category}
                                </Badge>
                                <Badge className={
                                  imp.priority === 'high' ? 'bg-red-600' :
                                  imp.priority === 'medium' ? 'bg-amber-600' : 'bg-slate-600'
                                }>{imp.priority}</Badge>
                              </div>
                              <p className="text-slate-300 text-sm">{imp.suggestion}</p>
                              {imp.example && (
                                <pre className="mt-2 p-2 bg-slate-900 rounded text-xs text-green-400 overflow-x-auto">
                                  {imp.example}
                                </pre>
                              )}
                            </div>
                          ))}
                        </CardContent>
                      </Card>
                    )}
                  </>
                )}

                {/* 특허/아이디어 분석 결과 */}
                {result.ai_analysis?.analysis_type === 'patent_idea' && (
                  <>
                    {/* 핵심 개념 */}
                    {result.ai_analysis?.core_concept && (
                      <Card className="bg-slate-800/50 border-slate-700">
                        <CardHeader className="pb-2">
                          <CardTitle className="text-slate-100 text-base flex items-center gap-2">
                            <Target className="w-5 h-5 text-blue-400" />
                            핵심 개념
                          </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-3">
                          <div className="bg-blue-900/30 rounded p-3">
                            <p className="text-blue-300 font-medium">{result.ai_analysis.core_concept.main_idea}</p>
                          </div>
                          <div className="grid grid-cols-2 gap-3">
                            <div>
                              <p className="text-slate-500 text-xs mb-2">핵심 요소</p>
                              <div className="flex flex-wrap gap-1">
                                {result.ai_analysis.core_concept.key_elements?.map((elem, idx) => (
                                  <Badge key={idx} variant="outline" className="text-slate-300 border-slate-600 text-xs">
                                    {elem}
                                  </Badge>
                                ))}
                              </div>
                            </div>
                            <div>
                              <p className="text-slate-500 text-xs mb-2">기술 분야</p>
                              <p className="text-slate-300 text-sm">{result.ai_analysis.core_concept.technical_domain}</p>
                            </div>
                          </div>
                          <div>
                            <p className="text-slate-500 text-xs mb-1">해결하는 문제</p>
                            <p className="text-slate-300 text-sm">{result.ai_analysis.core_concept.problem_solved}</p>
                          </div>
                        </CardContent>
                      </Card>
                    )}

                    {/* 평가 점수 */}
                    <Card className="bg-gradient-to-r from-emerald-900/20 to-blue-900/20 border-emerald-600">
                      <CardHeader className="pb-2">
                        <CardTitle className="text-emerald-300 text-base">종합 평가</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="grid grid-cols-4 gap-3">
                          {[
                            { label: '신규성', value: result.ai_analysis?.novelty_assessment?.novelty_score, color: 'blue' },
                            { label: '실현가능성', value: result.ai_analysis?.feasibility?.technical_feasibility_score, color: 'green' },
                            { label: '시장성', value: result.ai_analysis?.market_potential?.market_score, color: 'amber' },
                            { label: '혁신성', value: result.ai_analysis?.overall_evaluation?.innovation_score, color: 'purple' }
                          ].map((item, idx) => (
                            <div key={idx} className="text-center bg-slate-800/50 rounded-lg p-3">
                              <p className="text-slate-500 text-xs mb-2">{item.label}</p>
                              <div className={`text-2xl font-bold ${
                                (item.value || 0) >= 0.8 ? 'text-green-400' :
                                (item.value || 0) >= 0.6 ? 'text-amber-400' : 'text-red-400'
                              }`}>
                                {item.value ? (item.value * 100).toFixed(0) : '-'}%
                              </div>
                            </div>
                          ))}
                        </div>
                        {result.ai_analysis?.feasibility?.timeline_estimate && (
                          <div className="mt-3 flex items-center justify-center gap-2 text-slate-400 text-sm">
                            <Clock className="w-4 h-4" />
                            예상 개발 기간: <span className="text-slate-200">{result.ai_analysis.feasibility.timeline_estimate}</span>
                          </div>
                        )}
                      </CardContent>
                    </Card>

                    {/* 시장 잠재력 */}
                    {result.ai_analysis?.market_potential && (
                      <Card className="bg-amber-900/20 border-amber-600">
                        <CardHeader className="pb-2">
                          <CardTitle className="text-amber-300 text-base flex items-center gap-2">
                            <Package className="w-5 h-5" />
                            시장 잠재력
                          </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-3">
                          <div className="grid grid-cols-2 gap-3">
                            <div>
                              <p className="text-slate-500 text-xs mb-2">타겟 시장</p>
                              <ul className="space-y-1">
                                {result.ai_analysis.market_potential.target_markets?.map((market, idx) => (
                                  <li key={idx} className="text-slate-300 text-sm flex items-start gap-2">
                                    <span className="text-amber-400">•</span> {market}
                                  </li>
                                ))}
                              </ul>
                            </div>
                            <div>
                              <p className="text-slate-500 text-xs mb-2">응용 분야</p>
                              <ul className="space-y-1">
                                {result.ai_analysis.market_potential.application_areas?.map((area, idx) => (
                                  <li key={idx} className="text-slate-300 text-sm flex items-start gap-2">
                                    <span className="text-amber-400">•</span> {area}
                                  </li>
                                ))}
                              </ul>
                            </div>
                          </div>
                          <div>
                            <p className="text-slate-500 text-xs mb-1">수익화 가능성</p>
                            <p className="text-slate-300 text-sm">{result.ai_analysis.market_potential.monetization_potential}</p>
                          </div>
                        </CardContent>
                      </Card>
                    )}

                    {/* 종합 추천 */}
                    {result.ai_analysis?.overall_evaluation?.recommendation && (
                      <Card className="bg-purple-900/20 border-purple-600">
                        <CardHeader className="pb-2">
                          <CardTitle className="text-purple-300 text-base flex items-center gap-2">
                            <Lightbulb className="w-5 h-5" />
                            종합 추천
                          </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-3">
                          <p className="text-slate-200 text-sm">{result.ai_analysis.overall_evaluation.recommendation}</p>
                          {result.ai_analysis.overall_evaluation.next_steps?.length > 0 && (
                            <div>
                              <p className="text-slate-500 text-xs mb-2">다음 단계</p>
                              <ul className="space-y-1">
                                {result.ai_analysis.overall_evaluation.next_steps.map((step, idx) => (
                                  <li key={idx} className="text-slate-300 text-sm flex items-start gap-2">
                                    <span className="text-purple-400">{idx + 1}.</span> {step}
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </CardContent>
                      </Card>
                    )}
                  </>
                )}

                {/* 핵심 포인트 */}
                {result.ai_analysis?.key_points?.length > 0 && (
                  <Card className="bg-slate-800/50 border-slate-700">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-slate-100 text-base">핵심 포인트</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <ul className="space-y-2">
                        {result.ai_analysis.key_points.map((point, idx) => (
                          <li key={idx} className="flex items-start gap-2 text-slate-300 text-sm">
                            <CheckCircle2 className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
                            {point}
                          </li>
                        ))}
                      </ul>
                    </CardContent>
                  </Card>
                )}

                {/* 관련 자산 추천 */}
                <Card className="bg-slate-800/30 border-slate-700">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-slate-300 text-base flex items-center gap-2">
                      <Package className="w-5 h-5 text-slate-500" />
                      관련 모듈화 자산
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
                      <p className="text-slate-500 text-sm">
                        관련된 모듈화 자산이 없습니다.
                      </p>
                    )}
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
