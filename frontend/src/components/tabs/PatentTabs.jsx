/**
 * GVIC 특허 기반 탭 컴포넌트
 * 각 특허별 기능을 담당하는 탭 컴포넌트들
 */

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { 
  Upload, Brain, Target, Shield, Filter, Calculator, 
  Package, Database, Lock, Factory, Download, Settings,
  Activity, TrendingUp, Users, FileText, AlertCircle,
  CheckCircle, Clock, Zap, BarChart3
} from 'lucide-react';

/**
 * J:입력 - PLATFORM
 * 외부 시그널 수신, 정규화
 */
export const JInputTab = () => {
  const [inputText, setInputText] = useState("");
  const [inputCount, setInputCount] = useState(0);

  const handleSubmit = () => {
    if (inputText.trim()) {
      setInputCount(prev => prev + 1);
      setInputText("");
      // TODO: API 호출
    }
  };

  return (
    <div className="space-y-6">
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-500/20 rounded-lg">
              <Upload className="w-6 h-6 text-blue-400" />
            </div>
            <div>
              <CardTitle className="text-slate-100">J:입력 - PLATFORM</CardTitle>
              <CardDescription className="text-slate-400">
                외부 시그널 수신 및 정규화
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="bg-slate-900/50 rounded-lg p-4 text-center">
              <p className="text-3xl font-bold text-blue-400">{inputCount}</p>
              <p className="text-slate-400 text-sm">오늘 입력</p>
            </div>
            <div className="bg-slate-900/50 rounded-lg p-4 text-center">
              <p className="text-3xl font-bold text-green-400">🔓</p>
              <p className="text-slate-400 text-sm">완전 개방</p>
            </div>
            <div className="bg-slate-900/50 rounded-lg p-4 text-center">
              <Badge className="bg-emerald-600">활성</Badge>
              <p className="text-slate-400 text-sm mt-2">상태</p>
            </div>
          </div>

          <div className="space-y-4">
            <Textarea
              placeholder="시그널을 입력하세요... (텍스트, 데이터, 어떤 형태든 가능)"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              className="bg-slate-900 border-slate-600 text-slate-100 min-h-32"
            />
            <div className="flex gap-4">
              <Button onClick={handleSubmit} className="bg-blue-600 hover:bg-blue-500">
                <Upload className="w-4 h-4 mr-2" /> 시그널 입력
              </Button>
              <Button variant="outline" className="border-slate-600">
                <FileText className="w-4 h-4 mr-2" /> 파일 업로드
              </Button>
            </div>
          </div>

          <div className="mt-6 p-4 bg-slate-900/30 rounded-lg">
            <p className="text-slate-400 text-sm">
              💡 <strong className="text-slate-300">완전 개방 원칙</strong>: 
              어떤 형태의 시그널이든 수용합니다. 텍스트, 숫자, 파일 등 제한 없음.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

/**
 * LL:의도 - INTELLIGENCE
 * 비정형 의도 정량화
 */
export const LLIntentTab = () => {
  return (
    <div className="space-y-6">
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-500/20 rounded-lg">
              <Brain className="w-6 h-6 text-purple-400" />
            </div>
            <div>
              <CardTitle className="text-slate-100">LL:의도 - INTELLIGENCE</CardTitle>
              <CardDescription className="text-slate-400">
                비정형 의도 정량화 및 기여도 계산
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4 mb-6">
            <div className="bg-slate-900/50 rounded-lg p-4">
              <p className="text-slate-400 text-sm mb-2">핵심 수식</p>
              <code className="text-purple-400 text-sm">C_i = H(D_un) × cos(θ_ref)</code>
            </div>
            <div className="bg-slate-900/50 rounded-lg p-4">
              <p className="text-slate-400 text-sm mb-2">기능</p>
              <ul className="text-slate-300 text-sm space-y-1">
                <li>• 섀넌 엔트로피 계산</li>
                <li>• 코사인 유사도 측정</li>
                <li>• 기여도 정량화</li>
              </ul>
            </div>
          </div>

          <div className="bg-slate-900/30 rounded-lg p-4">
            <p className="text-slate-400 text-sm">
              📌 <strong className="text-slate-300">의도 = 자산</strong>: 
              질문하고 분석하는 의도 자체가 자산입니다. 분석 결과가 아닌 의도를 축적합니다.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

/**
 * H:코어 - CORE
 * 전역 수렴 제어, 배분 비율 설정
 */
export const HCoreTab = () => {
  const [alpha, setAlpha] = useState(0.5);
  const [beta, setBeta] = useState(0.3);
  const [gamma, setGamma] = useState(0.2);
  const [labels, setLabels] = useState(["공공", "생산", "개인"]);

  return (
    <div className="space-y-6">
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="p-2 bg-amber-500/20 rounded-lg">
              <Target className="w-6 h-6 text-amber-400" />
            </div>
            <div>
              <CardTitle className="text-slate-100">H:코어 - CORE</CardTitle>
              <CardDescription className="text-slate-400">
                전역 수렴 제어 및 배분 비율 설정
              </CardDescription>
            </div>
            <Badge className="ml-auto bg-red-600">🔒 불변 로직</Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {/* 배분 비율 설정 */}
            <div className="bg-slate-900/50 rounded-lg p-4">
              <h3 className="text-slate-200 font-medium mb-4">배분 비율 (Σ) - 🔧 설정 가능</h3>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="text-slate-400 text-sm">α (영역1): {labels[0]}</label>
                  <Input 
                    type="number" 
                    step="0.1" 
                    min="0" 
                    max="1"
                    value={alpha}
                    onChange={(e) => setAlpha(parseFloat(e.target.value))}
                    className="bg-slate-800 border-slate-600 text-slate-100 mt-1"
                  />
                  <p className="text-amber-400 text-lg font-bold mt-2">{(alpha * 100).toFixed(0)}%</p>
                </div>
                <div>
                  <label className="text-slate-400 text-sm">β (영역2): {labels[1]}</label>
                  <Input 
                    type="number" 
                    step="0.1" 
                    min="0" 
                    max="1"
                    value={beta}
                    onChange={(e) => setBeta(parseFloat(e.target.value))}
                    className="bg-slate-800 border-slate-600 text-slate-100 mt-1"
                  />
                  <p className="text-green-400 text-lg font-bold mt-2">{(beta * 100).toFixed(0)}%</p>
                </div>
                <div>
                  <label className="text-slate-400 text-sm">γ (영역3): {labels[2]}</label>
                  <Input 
                    type="number" 
                    step="0.1" 
                    min="0" 
                    max="1"
                    value={gamma}
                    onChange={(e) => setGamma(parseFloat(e.target.value))}
                    className="bg-slate-800 border-slate-600 text-slate-100 mt-1"
                  />
                  <p className="text-blue-400 text-lg font-bold mt-2">{(gamma * 100).toFixed(0)}%</p>
                </div>
              </div>
              <p className="text-slate-500 text-sm mt-4">
                합계: {((alpha + beta + gamma) * 100).toFixed(0)}% 
                {Math.abs(alpha + beta + gamma - 1) < 0.01 ? 
                  <span className="text-green-400 ml-2">✓ 정상</span> : 
                  <span className="text-red-400 ml-2">⚠ 합계는 100%여야 합니다</span>
                }
              </p>
            </div>

            {/* 영역 명칭 설정 */}
            <div className="bg-slate-900/50 rounded-lg p-4">
              <h3 className="text-slate-200 font-medium mb-4">영역 명칭 - 🔧 설정 가능</h3>
              <div className="grid grid-cols-3 gap-4">
                <Input 
                  value={labels[0]}
                  onChange={(e) => setLabels([e.target.value, labels[1], labels[2]])}
                  className="bg-slate-800 border-slate-600 text-slate-100"
                  placeholder="영역1 명칭"
                />
                <Input 
                  value={labels[1]}
                  onChange={(e) => setLabels([labels[0], e.target.value, labels[2]])}
                  className="bg-slate-800 border-slate-600 text-slate-100"
                  placeholder="영역2 명칭"
                />
                <Input 
                  value={labels[2]}
                  onChange={(e) => setLabels([labels[0], labels[1], e.target.value])}
                  className="bg-slate-800 border-slate-600 text-slate-100"
                  placeholder="영역3 명칭"
                />
              </div>
            </div>

            {/* 생존 임계 조건 */}
            <div className="bg-slate-900/50 rounded-lg p-4">
              <h3 className="text-slate-200 font-medium mb-4">생존 임계 조건 (Ω) - 🔒 고정</h3>
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div className="bg-red-500/10 border border-red-500/30 rounded p-3">
                  <p className="text-red-400">0.2 ≤ α ≤ 0.8</p>
                  <p className="text-slate-500 text-xs mt-1">영역1 범위 제한</p>
                </div>
                <div className="bg-red-500/10 border border-red-500/30 rounded p-3">
                  <p className="text-red-400">γ ≤ 0.5</p>
                  <p className="text-slate-500 text-xs mt-1">영역3 상한</p>
                </div>
                <div className="bg-red-500/10 border border-red-500/30 rounded p-3">
                  <p className="text-red-400">α + β + γ = 1.0</p>
                  <p className="text-slate-500 text-xs mt-1">합계 보존</p>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

/**
 * A:인지 - GATE
 * 시그널 인지, 분류
 */
export const AGateTab = () => {
  return (
    <div className="space-y-6">
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="p-2 bg-cyan-500/20 rounded-lg">
              <Activity className="w-6 h-6 text-cyan-400" />
            </div>
            <div>
              <CardTitle className="text-slate-100">A:인지 - GATE</CardTitle>
              <CardDescription className="text-slate-400">
                데이터 인지 및 정합성 판별
              </CardDescription>
            </div>
            <Badge className="ml-auto bg-red-600">🔒 불변</Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4 mb-6">
            <div className="bg-slate-900/50 rounded-lg p-4">
              <p className="text-slate-400 text-sm mb-2">정합성 지수 수식</p>
              <code className="text-cyan-400 text-sm">S_idx = (V_i · Σ) / (||V_i|| × ||Σ||)</code>
            </div>
            <div className="bg-slate-900/50 rounded-lg p-4">
              <p className="text-slate-400 text-sm mb-2">분류 결과</p>
              <div className="flex gap-2">
                <Badge className="bg-green-600">정합</Badge>
                <Badge className="bg-yellow-600">비정합</Badge>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4 text-center">
              <CheckCircle className="w-8 h-8 text-green-400 mx-auto mb-2" />
              <p className="text-green-400 font-bold">1) 원하는 것</p>
              <p className="text-slate-400 text-sm">→ G:정제로</p>
            </div>
            <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4 text-center">
              <AlertCircle className="w-8 h-8 text-yellow-400 mx-auto mb-2" />
              <p className="text-yellow-400 font-bold">2) 원치 않는 것</p>
              <p className="text-slate-400 text-sm">→ E:검역으로</p>
            </div>
            <div className="bg-slate-500/10 border border-slate-500/30 rounded-lg p-4 text-center">
              <Clock className="w-8 h-8 text-slate-400 mx-auto mb-2" />
              <p className="text-slate-400 font-bold">3) Null</p>
              <p className="text-slate-400 text-sm">→ E:검역으로</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

/**
 * E:검역 - SHIELD
 * 독소 데이터 검역
 */
export const EShieldTab = () => {
  return (
    <div className="space-y-6">
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="p-2 bg-red-500/20 rounded-lg">
              <Shield className="w-6 h-6 text-red-400" />
            </div>
            <div>
              <CardTitle className="text-slate-100">E:검역 - SHIELD</CardTitle>
              <CardDescription className="text-slate-400">
                독소 데이터 다차원 수리적 검역
              </CardDescription>
            </div>
            <Badge className="ml-auto bg-red-600">🔒 불변</Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="bg-slate-900/50 rounded-lg p-4 mb-6">
            <p className="text-slate-400 text-sm mb-2">독소 판별 수식</p>
            <code className="text-red-400 text-sm">ΔS = -Σ P(x_i|Σ) log P(x_i|Σ)</code>
            <p className="text-slate-500 text-xs mt-2">독소 조건: ΔS {">"} θ 또는 Z_score ∉ 허용범위</p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4">
              <CheckCircle className="w-6 h-6 text-green-400 mb-2" />
              <p className="text-green-400 font-medium">통과</p>
              <p className="text-slate-400 text-sm">→ G:정제로 이동</p>
            </div>
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
              <Shield className="w-6 h-6 text-red-400 mb-2" />
              <p className="text-red-400 font-medium">격리/폐기</p>
              <p className="text-slate-400 text-sm">→ 독소 데이터 처리</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

/**
 * G:정제 - REFINE
 * 가치 정제
 */
export const GRefineTab = () => {
  return (
    <div className="space-y-6">
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="p-2 bg-emerald-500/20 rounded-lg">
              <Filter className="w-6 h-6 text-emerald-400" />
            </div>
            <div>
              <CardTitle className="text-slate-100">G:정제 - REFINE</CardTitle>
              <CardDescription className="text-slate-400">
                다단계 가치 정제 및 노이즈 제거
              </CardDescription>
            </div>
            <Badge className="ml-auto bg-red-600">🔒 불변</Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="bg-slate-900/50 rounded-lg p-4 mb-6">
            <p className="text-slate-400 text-sm mb-2">가치 판별 지수</p>
            <code className="text-emerald-400 text-sm">D_idx = ∫|V_cand · Σ| dt - σ_noise</code>
          </div>

          <div className="bg-slate-900/30 rounded-lg p-4">
            <p className="text-slate-400 text-sm">
              🔬 <strong className="text-slate-300">정제 과정</strong>: 
              검역 통과 데이터의 잔류 노이즈를 제거하고, 수렴 지표와의 상관 성분만 추출합니다.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

/**
 * B:산출 - CALC
 * 가치 산출
 */
export const BCalcTab = () => {
  return (
    <div className="space-y-6">
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="p-2 bg-violet-500/20 rounded-lg">
              <Calculator className="w-6 h-6 text-violet-400" />
            </div>
            <div>
              <CardTitle className="text-slate-100">B:산출 - CALC</CardTitle>
              <CardDescription className="text-slate-400">
                가치 산출 및 배분 계산
              </CardDescription>
            </div>
            <Badge className="ml-auto bg-red-600">🔒 불변</Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4 mb-6">
            <div className="bg-slate-900/50 rounded-lg p-4">
              <p className="text-slate-400 text-sm mb-2">배분 벡터</p>
              <code className="text-violet-400 text-sm">R_alloc = V_score × [α, β, γ]^T</code>
            </div>
            <div className="bg-slate-900/50 rounded-lg p-4">
              <p className="text-slate-400 text-sm mb-2">유량 제어</p>
              <code className="text-violet-400 text-sm">dQ/dt = α(R_alloc - R_current) - β∇S</code>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

/**
 * C:모듈화 - EXEC
 * 모듈화 실행
 */
export const CExecTab = () => {
  return (
    <div className="space-y-6">
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="p-2 bg-orange-500/20 rounded-lg">
              <Package className="w-6 h-6 text-orange-400" />
            </div>
            <div>
              <CardTitle className="text-slate-100">C:모듈화 - EXEC</CardTitle>
              <CardDescription className="text-slate-400">
                의도 모듈화 및 자원 배분 실행
              </CardDescription>
            </div>
            <Badge className="ml-auto bg-red-600">🔒 불변</Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="bg-slate-900/50 rounded-lg p-4 mb-6">
            <p className="text-slate-400 text-sm mb-2">집행 자원 수식</p>
            <code className="text-orange-400 text-sm">E_res = β × (M_conv × R_alloc)</code>
          </div>

          <div className="bg-slate-900/30 rounded-lg p-4">
            <p className="text-slate-400 text-sm">
              📦 <strong className="text-slate-300">모듈화</strong>: 
              정제된 의도를 재사용 가능한 모듈 단위로 패키징합니다.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

/**
 * D:축적 - LEDGER
 * 저장, 궤적
 */
export const DLedgerTab = () => {
  return (
    <div className="space-y-6">
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="p-2 bg-teal-500/20 rounded-lg">
              <Database className="w-6 h-6 text-teal-400" />
            </div>
            <div>
              <CardTitle className="text-slate-100">D:축적 - LEDGER</CardTitle>
              <CardDescription className="text-slate-400">
                시계열 궤적 저장 및 이력 보존
              </CardDescription>
            </div>
            <Badge className="ml-auto bg-red-600">🔒 불변</Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="bg-slate-900/50 rounded-lg p-4 mb-6">
            <p className="text-slate-400 text-sm mb-2">궤적 적층 함수</p>
            <code className="text-teal-400 text-sm">H(T) = Σ[S(t) · G + L(V_proof(t))]</code>
          </div>

          <div className="bg-slate-900/30 rounded-lg p-4">
            <p className="text-slate-400 text-sm">
              📚 <strong className="text-slate-300">지속적 축적</strong>: 
              모듈화된 의도를 시계열로 저장합니다. 기여자 정보도 함께 기록됩니다.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

/**
 * I:무결성 - INTEGRITY
 * 무결성 증명
 */
export const IIntegrityTab = () => {
  return (
    <div className="space-y-6">
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="p-2 bg-indigo-500/20 rounded-lg">
              <Lock className="w-6 h-6 text-indigo-400" />
            </div>
            <div>
              <CardTitle className="text-slate-100">I:무결성 - INTEGRITY</CardTitle>
              <CardDescription className="text-slate-400">
                데이터 무결성 비가역적 증명
              </CardDescription>
            </div>
            <Badge className="ml-auto bg-red-600">🔒 불변</Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="bg-slate-900/50 rounded-lg p-4 mb-6">
            <p className="text-slate-400 text-sm mb-2">무결성 증명값</p>
            <code className="text-indigo-400 text-sm">V_proof(t) = Hash(Σ(t) ⊕ E(t) + V_proof(t-1))</code>
          </div>

          <div className="bg-slate-900/30 rounded-lg p-4">
            <p className="text-slate-400 text-sm">
              🔐 <strong className="text-slate-300">변조 방지</strong>: 
              해시 체인으로 저장된 의도의 변조를 방지하고, 기여 이력을 증명합니다.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

/**
 * F:상품화 - FIELD
 * 상품 생성
 */
export const FFieldTab = () => {
  return (
    <div className="space-y-6">
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="p-2 bg-pink-500/20 rounded-lg">
              <Factory className="w-6 h-6 text-pink-400" />
            </div>
            <div>
              <CardTitle className="text-slate-100">F:상품화 - FIELD</CardTitle>
              <CardDescription className="text-slate-400">
                상품 생성 및 물리 계층 실행
              </CardDescription>
            </div>
            <Badge className="ml-auto bg-yellow-600">👤 운영자 결정</Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="bg-slate-900/50 rounded-lg p-4 mb-6">
            <p className="text-slate-400 text-sm mb-2">물리 실행 수식</p>
            <code className="text-pink-400 text-sm">E_i(t) = ∫(R_alloc · F_i - κ × dS_i/dt) dt</code>
          </div>

          <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4">
            <p className="text-yellow-400 text-sm">
              ⏳ <strong>운영자 판단 영역</strong>: 
              축적된 의도가 충분해지면 운영자가 상품화 시점을 결정합니다.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

/**
 * 출력 - 결과 출력
 */
export const OutputTab = () => {
  return (
    <div className="space-y-6">
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="p-2 bg-sky-500/20 rounded-lg">
              <Download className="w-6 h-6 text-sky-400" />
            </div>
            <div>
              <CardTitle className="text-slate-100">출력</CardTitle>
              <CardDescription className="text-slate-400">
                결과 출력 및 요구자 인터페이스
              </CardDescription>
            </div>
            <Badge className="ml-auto bg-green-600">🔓 개방</Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4 mb-6">
            <div className="bg-slate-900/50 rounded-lg p-4">
              <Download className="w-8 h-8 text-sky-400 mb-2" />
              <p className="text-slate-200 font-medium">상품 다운로드</p>
              <p className="text-slate-400 text-sm">패키징된 자산 다운로드</p>
            </div>
            <div className="bg-slate-900/50 rounded-lg p-4">
              <Zap className="w-8 h-8 text-amber-400 mb-2" />
              <p className="text-slate-200 font-medium">API 제공</p>
              <p className="text-slate-400 text-sm">외부 시스템 연동</p>
            </div>
          </div>

          <div className="bg-slate-900/30 rounded-lg p-4">
            <p className="text-slate-400 text-sm">
              💡 <strong className="text-slate-300">완전 개방 원칙</strong>: 
              어떤 형태로든 출력 가능합니다. 제한 없음.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
