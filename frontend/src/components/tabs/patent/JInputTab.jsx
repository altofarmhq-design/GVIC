import { useState, useCallback, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
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
  Clock
} from 'lucide-react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL;

/**
 * J:입력 - 외부 시그널 유입 (특허 J: PLATFORM)
 * 다양한 형태의 외부 시그널을 시스템으로 유입시키는 입구
 */
export const JInputTab = ({ onSignalSubmit }) => {
  const [inputType, setInputType] = useState("text");
  const [textContent, setTextContent] = useState("");
  const [urlInput, setUrlInput] = useState("");
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [submitting, setSubmitting] = useState(false);
  const [lastSubmission, setLastSubmission] = useState(null);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  // 파일 선택 처리
  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    setSelectedFiles(prev => [...prev, ...files]);
    setError(null);
  };

  // 파일 제거
  const removeFile = (index) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  // 파일 아이콘 결정
  const getFileIcon = (file) => {
    const ext = file.name.split('.').pop().toLowerCase();
    if (['xlsx', 'xls', 'csv'].includes(ext)) return FileSpreadsheet;
    if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp'].includes(ext)) return Image;
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
    
    try {
      const token = localStorage.getItem('token');
      
      // 토큰 검증
      if (!token) {
        setError('로그인이 필요합니다. 페이지를 새로고침 후 다시 로그인해주세요.');
        setSubmitting(false);
        return;
      }
      
      const response = await axios.post(`${API_URL}/api/signal/ingest`, {
        type: 'text',
        content: textContent
      }, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      setLastSubmission({
        type: 'text',
        status: 'success',
        message: response.data.message || '시그널 전송 완료',
        timestamp: new Date().toISOString()
      });
      
      if (onSignalSubmit) onSignalSubmit(response.data);
      setTextContent("");
    } catch (err) {
      setError(err.response?.data?.detail || '전송 실패');
      setLastSubmission({
        type: 'text',
        status: 'error',
        message: err.response?.data?.detail || '전송 실패',
        timestamp: new Date().toISOString()
      });
    }
    setSubmitting(false);
  };

  // URL 제출
  const handleUrlSubmit = async () => {
    if (!urlInput.trim()) return;
    
    setSubmitting(true);
    setError(null);
    
    try {
      const token = localStorage.getItem('token');
      
      if (!token) {
        setError('로그인이 필요합니다. 페이지를 새로고침 후 다시 로그인해주세요.');
        setSubmitting(false);
        return;
      }
      
      const response = await axios.post(`${API_URL}/api/signal/ingest/url`, {
        url: urlInput
      }, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      setLastSubmission({
        type: 'url',
        status: 'success',
        message: response.data.message || 'URL 처리 완료',
        extracted_text: response.data.extracted_text,
        timestamp: new Date().toISOString()
      });
      
      if (onSignalSubmit) onSignalSubmit(response.data);
      setUrlInput("");
    } catch (err) {
      setError(err.response?.data?.detail || 'URL 처리 실패');
      setLastSubmission({
        type: 'url',
        status: 'error',
        message: err.response?.data?.detail || 'URL 처리 실패',
        timestamp: new Date().toISOString()
      });
    }
    setSubmitting(false);
  };

  // 파일 제출
  const handleFileSubmit = async () => {
    if (selectedFiles.length === 0) return;
    
    setSubmitting(true);
    setError(null);
    
    try {
      const token = localStorage.getItem('token');
      const formData = new FormData();
      selectedFiles.forEach(file => {
        formData.append('files', file);
      });
      
      const response = await axios.post(`${API_URL}/api/signal/ingest/files`, formData, {
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        }
      });
      
      setLastSubmission({
        type: 'file',
        status: 'success',
        message: response.data.message || `${selectedFiles.length}개 파일 처리 완료`,
        results: response.data.results,
        timestamp: new Date().toISOString()
      });
      
      if (onSignalSubmit) onSignalSubmit(response.data);
      setSelectedFiles([]);
    } catch (err) {
      setError(err.response?.data?.detail || '파일 처리 실패');
      setLastSubmission({
        type: 'file',
        status: 'error',
        message: err.response?.data?.detail || '파일 처리 실패',
        timestamp: new Date().toISOString()
      });
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

  const inputTypes = [
    { id: "text", label: "텍스트", icon: FileText, desc: "직접 입력", enabled: true },
    { id: "file", label: "파일", icon: Upload, desc: "다양한 형식", enabled: true },
    { id: "url", label: "URL", icon: Globe, desc: "웹페이지", enabled: true },
    { id: "api", label: "API", icon: Link2, desc: "준비 중", enabled: false }
  ];

  const supportedFormats = [
    { ext: "Excel", formats: ".xlsx, .xls" },
    { ext: "CSV", formats: ".csv" },
    { ext: "PDF", formats: ".pdf" },
    { ext: "텍스트", formats: ".txt" },
    { ext: "이미지", formats: ".jpg, .png, .gif, .webp" }
  ];

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

      {/* 입력 유형 선택 */}
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader className="pb-3">
          <CardTitle className="text-slate-100 text-lg">시그널 입력 방식</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-4 gap-3">
            {inputTypes.map((type) => (
              <button
                key={type.id}
                onClick={() => type.enabled && setInputType(type.id)}
                disabled={!type.enabled}
                className={`p-4 rounded-lg border-2 transition-all relative ${
                  !type.enabled 
                    ? 'border-slate-700 bg-slate-800/30 cursor-not-allowed opacity-50'
                    : inputType === type.id
                      ? 'border-blue-500 bg-blue-500/20'
                      : 'border-slate-600 bg-slate-800/50 hover:border-slate-500'
                }`}
              >
                {!type.enabled && (
                  <div className="absolute top-1 right-1">
                    <Badge className="bg-slate-600 text-[10px] px-1 py-0">
                      <Clock className="w-2 h-2 mr-0.5" />준비중
                    </Badge>
                  </div>
                )}
                <type.icon className={`w-8 h-8 mx-auto mb-2 ${
                  !type.enabled ? 'text-slate-600' :
                  inputType === type.id ? 'text-blue-400' : 'text-slate-400'
                }`} />
                <p className={`font-medium ${
                  !type.enabled ? 'text-slate-600' :
                  inputType === type.id ? 'text-blue-300' : 'text-slate-300'
                }`}>{type.label}</p>
                <p className="text-xs text-slate-500 mt-1">{type.desc}</p>
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* 입력 영역 */}
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader className="pb-3">
          <CardTitle className="text-slate-100 text-lg flex items-center gap-2">
            {inputTypes.find(t => t.id === inputType)?.icon && (
              <>
                {(() => {
                  const Icon = inputTypes.find(t => t.id === inputType).icon;
                  return <Icon className="w-5 h-5 text-blue-400" />;
                })()}
              </>
            )}
            시그널 입력
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* 텍스트 입력 */}
          {inputType === "text" && (
            <Textarea
              placeholder="시그널을 입력하세요"
              value={textContent}
              onChange={(e) => setTextContent(e.target.value)}
              className="bg-slate-900 border-slate-600 text-slate-100 min-h-[200px]"
            />
          )}

          {/* URL 입력 */}
          {inputType === "url" && (
            <div className="space-y-3">
              <Input
                placeholder="URL 입력"
                value={urlInput}
                onChange={(e) => setUrlInput(e.target.value)}
                className="bg-slate-900 border-slate-600 text-slate-100"
              />
            </div>
          )}

          {/* 파일 업로드 */}
          {inputType === "file" && (
            <div className="space-y-4">
              <div 
                className="border-2 border-dashed border-slate-600 rounded-lg p-6 text-center cursor-pointer hover:border-blue-500 transition-colors"
                onClick={() => fileInputRef.current?.click()}
                onDragOver={(e) => e.preventDefault()}
                onDrop={(e) => {
                  e.preventDefault();
                  const files = Array.from(e.dataTransfer.files);
                  setSelectedFiles(prev => [...prev, ...files]);
                }}
              >
                <Upload className="w-10 h-10 text-slate-500 mx-auto mb-3" />
                <p className="text-slate-400 mb-2">파일을 드래그하거나 클릭하여 업로드</p>
                <div className="flex flex-wrap justify-center gap-2 mt-3">
                  {supportedFormats.map((f, i) => (
                    <Badge key={i} variant="outline" className="text-slate-400 border-slate-600 text-xs">
                      {f.ext}
                    </Badge>
                  ))}
                </div>
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  accept=".xlsx,.xls,.csv,.pdf,.txt,.jpg,.jpeg,.png,.gif,.webp,.bmp"
                  onChange={handleFileSelect}
                  className="hidden"
                />
              </div>

              {/* 선택된 파일 목록 */}
              {selectedFiles.length > 0 && (
                <div className="space-y-2">
                  <p className="text-slate-400 text-sm">{selectedFiles.length}개 파일 선택됨</p>
                  <div className="max-h-[200px] overflow-y-auto space-y-2">
                    {selectedFiles.map((file, index) => {
                      const FileIcon = getFileIcon(file);
                      return (
                        <div 
                          key={index}
                          className="flex items-center justify-between bg-slate-900 rounded-lg p-3"
                        >
                          <div className="flex items-center gap-3">
                            <FileIcon className="w-5 h-5 text-blue-400" />
                            <div>
                              <p className="text-slate-200 text-sm truncate max-w-[300px]">{file.name}</p>
                              <p className="text-slate-500 text-xs">{formatFileSize(file.size)}</p>
                            </div>
                          </div>
                          <button 
                            onClick={() => removeFile(index)}
                            className="text-slate-500 hover:text-red-400 transition-colors"
                          >
                            <X className="w-4 h-4" />
                          </button>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* 에러 메시지 */}
          {error && (
            <div className="bg-red-900/30 border border-red-600 rounded-lg p-3 text-red-400 text-sm flex items-center gap-2">
              <AlertCircle className="w-4 h-4" />
              {error}
            </div>
          )}

          {/* 제출 버튼 */}
          <div className="flex items-center gap-3">
            <Button 
              onClick={handleSubmit}
              disabled={
                submitting || 
                (inputType === "text" && !textContent.trim()) || 
                (inputType === "url" && !urlInput.trim()) ||
                (inputType === "file" && selectedFiles.length === 0)
              }
              className="flex-1 h-12 bg-blue-600 hover:bg-blue-700"
            >
              {submitting ? (
                <>
                  <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                  처리 중...
                </>
              ) : (
                <>
                  <ArrowRight className="w-5 h-5 mr-2" />
                  LL:의도 모듈로 전송
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* 마지막 전송 결과 */}
      {lastSubmission && (
        <Card className={`border ${
          lastSubmission.status === "success" 
            ? 'bg-green-900/20 border-green-600' 
            : 'bg-red-900/20 border-red-600'
        }`}>
          <CardContent className="py-4">
            <div className="flex items-center gap-3">
              {lastSubmission.status === "success" ? (
                <CheckCircle2 className="w-6 h-6 text-green-400" />
              ) : (
                <AlertCircle className="w-6 h-6 text-red-400" />
              )}
              <div className="flex-1">
                <p className={`font-medium ${
                  lastSubmission.status === "success" ? 'text-green-300' : 'text-red-300'
                }`}>
                  {lastSubmission.message}
                </p>
                <p className="text-slate-400 text-sm">
                  {new Date(lastSubmission.timestamp).toLocaleString('ko-KR')}
                </p>
              </div>
            </div>
            {lastSubmission.extracted_text && (
              <div className="mt-3 p-3 bg-slate-800 rounded-lg">
                <p className="text-slate-400 text-xs mb-1">추출된 텍스트:</p>
                <p className="text-slate-200 text-sm line-clamp-3">{lastSubmission.extracted_text}</p>
              </div>
            )}
          </CardContent>
        </Card>
      )}

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
