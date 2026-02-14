"""
GVIC 데이터 모델 - 시그널, 모듈, 자산의 ID 체계
"""
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
import uuid


def generate_id(prefix: str) -> str:
    """고유 ID 생성"""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    unique = uuid.uuid4().hex[:6].upper()
    return f"{prefix}_{timestamp}_{unique}"


# ==================== 개별 시그널 ====================
class Signal(BaseModel):
    """발견된 개별 시그널"""
    signal_id: str = Field(default_factory=lambda: generate_id("SIG"))
    text: str                          # 원문에서 추출된 텍스트
    type: str                          # 시그널 종류 (효과, 가격, 서비스 등)
    sentiment: str                     # positive, negative, neutral, mixed
    intensity: float = 0.5             # 강도 (0.0 ~ 1.0)
    context: str = ""                  # 맥락 설명
    hidden_meaning: Optional[str] = None  # 숨겨진 의미
    
    # 메타데이터
    position_start: Optional[int] = None  # 원문에서의 시작 위치
    position_end: Optional[int] = None    # 원문에서의 끝 위치
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


# ==================== 모듈 (시그널 그룹) ====================
class SignalModule(BaseModel):
    """시그널들의 묶음 (모듈)"""
    module_id: str = Field(default_factory=lambda: generate_id("MOD"))
    input_id: str                      # 소속된 입력 ID
    
    # 모듈 정보
    signal_type: str                   # product_review, requirement, complaint 등
    signal_type_label: str             # 한글 라벨
    signal_type_confidence: float      # 분류 신뢰도
    signal_type_reason: str            # 분류 이유
    
    # 포함된 시그널들
    signals: List[Signal] = []
    
    # 분석 결과
    overall_sentiment: str = "neutral"
    key_themes: List[str] = []
    summary: str = ""
    
    # 3관점 적용 가능 여부
    applicable_perspectives: Dict[str, bool] = {
        "society": False,
        "production": False,
        "consumer": False
    }
    perspective_relevance: str = ""
    
    # 메타데이터
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def add_signal(self, signal: Signal):
        """시그널 추가"""
        self.signals.append(signal)
    
    def get_signal_count(self) -> int:
        return len(self.signals)
    
    def to_dict(self) -> Dict[str, Any]:
        data = self.model_dump()
        data["signal_count"] = self.get_signal_count()
        return data


# ==================== 입력 (원본 데이터) ====================
class SignalInput(BaseModel):
    """사용자가 입력한 원본 데이터"""
    input_id: str = Field(default_factory=lambda: generate_id("INP"))
    requester_id: str                  # 요구자 ID (user_id)
    
    # 원본 데이터
    raw_content: str                   # 원본 텍스트
    content_type: str = "text"         # text, file, url 등
    content_length: int = 0            # 텍스트 길이
    
    # 연결된 모듈들
    modules: List[SignalModule] = []
    
    # 메타데이터
    source: str = "direct_input"       # 입력 소스
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: Optional[str] = None
    
    # 상태
    status: str = "pending"            # pending, processing, completed, failed
    
    def add_module(self, module: SignalModule):
        """모듈 추가"""
        module.input_id = self.input_id
        self.modules.append(module)
    
    def get_all_signals(self) -> List[Signal]:
        """모든 시그널 반환"""
        all_signals = []
        for module in self.modules:
            all_signals.extend(module.signals)
        return all_signals
    
    def to_dict(self) -> Dict[str, Any]:
        data = self.model_dump()
        data["module_count"] = len(self.modules)
        data["total_signal_count"] = len(self.get_all_signals())
        return data


# ==================== 자산 (Asset) ====================
class GVICAsset(BaseModel):
    """GVIC 자산 - 분석 완료된 데이터"""
    asset_id: str = Field(default_factory=lambda: generate_id("AST"))
    
    # 연결 정보
    input_id: str                      # 원본 입력 ID
    module_id: str                     # 소속 모듈 ID
    requester_id: str                  # 요구자 ID
    
    # 자산 데이터
    content: str                       # 원본 내용
    signal_type: str                   # 시그널 유형
    signals: List[Dict[str, Any]] = [] # 포함된 시그널들
    
    # 분석 결과
    overall_sentiment: str = "neutral"
    score: Optional[int] = None        # 종합 점수 (0-100)
    classification: str = "미분류"     # 긍정/중립/부정
    
    # 3관점 분포
    v_pub: float = 0.0                 # 사회·규제 관점
    v_pro: float = 0.0                 # 기업·생산 관점
    v_ind: float = 0.0                 # 소비자·고객 관점
    
    # 활용 추적
    used_count: int = 0
    used_for: List[Dict[str, Any]] = []
    
    # 메타데이터
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: Optional[str] = None
    
    # 연결된 자산들 (사일로 방지)
    related_assets: List[str] = []     # 관련 자산 ID 목록
    
    def record_usage(self, usage_type: str):
        """사용 기록"""
        self.used_count += 1
        self.used_for.append({
            "type": usage_type,
            "at": datetime.now(timezone.utc).isoformat()
        })
        self.updated_at = datetime.now(timezone.utc).isoformat()
    
    def add_related_asset(self, asset_id: str):
        """관련 자산 연결"""
        if asset_id not in self.related_assets:
            self.related_assets.append(asset_id)
            self.updated_at = datetime.now(timezone.utc).isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


# ==================== ID 체계 요약 ====================
"""
ID 체계:
- USR_YYYYMMDDHHMMSS_XXXXXX : 사용자 (기존 user_id 사용)
- INP_YYYYMMDDHHMMSS_XXXXXX : 입력
- MOD_YYYYMMDDHHMMSS_XXXXXX : 모듈
- SIG_YYYYMMDDHHMMSS_XXXXXX : 시그널
- AST_YYYYMMDDHHMMSS_XXXXXX : 자산

관계:
User (1) → Input (N)
Input (1) → Module (N)
Module (1) → Signal (N)
Input + Module + Signals → Asset (변환)

추적성:
Asset → Module → Input → User
Signal → Module → Input → User
"""
