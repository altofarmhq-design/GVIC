import { useState, useCallback } from "react";
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
  Loader2
} from 'lucide-react';

/**
 * J:입력 - 외부 시그널 유입 (특허 J: PLATFORM)
 * 다양한 형태의 외부 시그널을 시스템으로 유입시키는 입구
 */
export const JInputTab = ({ onSignalSubmit }) => {
  const [inputType, setInputType] = useState("text");
  const [textContent, setTextContent] = useState("");
  const [urlInput, setUrlInput] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [lastSubmission, setLastSubmission] = useState(null);

  const handleSubmit = useCallback(async () => {
    if (inputType === "text" && !textContent.trim()) return;
    if (inputType === "url" && !urlInput.trim()) return;

    setSubmitting(true);
    
    // 시뮬레이션 - 실제로는 onSignalSubmit 콜백 호출
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    setLastSubmission({
      type: inputType,
      content: inputType === "text" ? textContent : urlInput,
      timestamp: new Date().toISOString(),
      status: "success"
    });
    
    if (onSignalSubmit) {
      onSignalSubmit({
        type: inputType,
        content: inputType === "text" ? textContent : urlInput
      });
    }
    
    setSubmitting(false);
  }, [inputType, textContent, urlInput, onSignalSubmit]);

  const inputTypes = [
    { id: "text", label: "텍스트", icon: FileText, desc: "직접 입력" },
    { id: "url", label: "URL", icon: Globe, desc: "웹페이지" },
    { id: "file", label: "파일", icon: Upload, desc: "Excel/CSV" },
    { id: "api", label: "API", icon: Link2, desc: "외부 연동" }
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
                onClick={() => setInputType(type.id)}
                className={`p-4 rounded-lg border-2 transition-all ${
                  inputType === type.id
                    ? 'border-blue-500 bg-blue-500/20'
                    : 'border-slate-600 bg-slate-800/50 hover:border-slate-500'
                }`}
              >
                <type.icon className={`w-8 h-8 mx-auto mb-2 ${
                  inputType === type.id ? 'text-blue-400' : 'text-slate-400'
                }`} />
                <p className={`font-medium ${
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
            {inputTypes.find(t => t.id === inputType)?.icon && 
              <span>{inputTypes.find(t => t.id === inputType).label}</span>
            }
            시그널 입력
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {inputType === "text" && (
            <Textarea
              placeholder="시그널을 입력하세요"
              value={textContent}
              onChange={(e) => setTextContent(e.target.value)}
              className="bg-slate-900 border-slate-600 text-slate-100 min-h-[200px]"
            />
          )}

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

          {inputType === "file" && (
            <div className="border-2 border-dashed border-slate-600 rounded-lg p-8 text-center">
              <Upload className="w-12 h-12 text-slate-500 mx-auto mb-4" />
              <p className="text-slate-400 mb-2">파일을 드래그하거나 클릭하여 업로드</p>
              <Button variant="outline" className="mt-4">
                파일 선택
              </Button>
            </div>
          )}

          {inputType === "api" && (
            <div className="space-y-3">
              <Input
                placeholder="API 엔드포인트 URL"
                className="bg-slate-900 border-slate-600 text-slate-100"
              />
              <div className="grid grid-cols-2 gap-3">
                <Input
                  placeholder="API Key (선택)"
                  className="bg-slate-900 border-slate-600 text-slate-100"
                />
                <Input
                  placeholder="Header Token (선택)"
                  className="bg-slate-900 border-slate-600 text-slate-100"
                />
              </div>
              <p className="text-slate-500 text-sm">
                외부 API에서 데이터를 가져와 시그널로 변환합니다.
              </p>
            </div>
          )}

          <div className="flex items-center gap-3">
            <Button 
              onClick={handleSubmit}
              disabled={submitting || (inputType === "text" && !textContent.trim()) || (inputType === "url" && !urlInput.trim())}
              className="flex-1 h-12 bg-blue-600 hover:bg-blue-700"
            >
              {submitting ? (
                <>
                  <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                  시그널 전송 중...
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
              <div>
                <p className={`font-medium ${
                  lastSubmission.status === "success" ? 'text-green-300' : 'text-red-300'
                }`}>
                  {lastSubmission.status === "success" ? '시그널 전송 완료' : '전송 실패'}
                </p>
                <p className="text-slate-400 text-sm">
                  {new Date(lastSubmission.timestamp).toLocaleString('ko-KR')}
                </p>
              </div>
            </div>
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
