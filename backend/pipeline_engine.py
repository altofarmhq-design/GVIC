"""
GVIC Pipeline Engine
- 시그널 입력 후 전체 파이프라인 자동 실행
- 각 단계별 상태 저장 및 모니터링 지원
"""
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from bson import ObjectId
from enum import Enum
import asyncio
import logging

logger = logging.getLogger(__name__)

class SignalCategory(str, Enum):
    """시그널 평가 분류"""
    WANTED = "wanted"           # 2-1) 사용자가 원하는 것
    UNWANTED = "unwanted"       # 2-2) 사용자가 원하지 않는 것
    NULL = "null"               # 2-3) 쓸모없는 것

class PipelineStage(str, Enum):
    """파이프라인 단계"""
    J_INPUT = "j_input"              # 1. 입력단
    LL_EVALUATE = "ll_evaluate"      # 2. 시그널 평가단
    H_CORE = "h_core"                # 3. 코어 (분석/라우팅)
    ASSET_PROCESS = "asset_process"  # 4. 자산화 (A, E, G)
    D_LEDGER = "d_ledger"            # 4-1. 원장 저장
    OUTPUT = "output"                # 5-1. 출력단 (원하는 것)
    MODULE = "module"                # 5-2. 모듈화/판매/보상 (B, C, F, I)
    COMPLETED = "completed"          # 완료

class PipelineStatus(str, Enum):
    """단계 상태"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class GVICPipeline:
    """GVIC 파이프라인 엔진"""
    
    def __init__(self, db):
        self.db = db
        self.signals_collection = db.pipeline_signals
        self.stages_collection = db.pipeline_stages
        self.assets_collection = db.gvic_assets
        
    def _generate_id(self, prefix: str = "SIG") -> str:
        """고유 ID 생성"""
        return f"{prefix}_{ObjectId()}"
    
    async def create_signal(self, 
                           signal_type: str,
                           content: str,
                           source: str,
                           metadata: Dict[str, Any] = None,
                           user_id: str = None) -> Dict[str, Any]:
        """새 시그널 생성 및 파이프라인 시작"""
        
        signal_id = self._generate_id("SIG")
        now = datetime.now(timezone.utc)
        
        # 시그널 문서 생성
        signal_doc = {
            "signal_id": signal_id,
            "type": signal_type,  # text, file, url
            "content": content,
            "source": source,
            "metadata": metadata or {},
            "user_id": user_id,
            "created_at": now,
            "current_stage": PipelineStage.J_INPUT.value,
            "status": PipelineStatus.PROCESSING.value,
            "category": None,  # 평가 후 결정
            "stages": {},
            "is_continuous": False,  # 단일성 시그널
        }
        
        await self.signals_collection.insert_one(signal_doc)
        
        # 파이프라인 자동 실행
        result = await self.run_pipeline(signal_id)
        
        return result
    
    async def run_pipeline(self, signal_id: str) -> Dict[str, Any]:
        """전체 파이프라인 자동 실행"""
        
        signal = await self.signals_collection.find_one({"signal_id": signal_id})
        if not signal:
            return {"success": False, "error": "시그널을 찾을 수 없습니다"}
        
        try:
            # Stage 1: J:입력 (이미 완료)
            await self._update_stage(signal_id, PipelineStage.J_INPUT, PipelineStatus.COMPLETED, {
                "received_at": datetime.now(timezone.utc).isoformat(),
                "content_length": len(signal.get("content", ""))
            })
            
            # Stage 2: LL:의도 - 시그널 평가
            eval_result = await self._stage_evaluate(signal_id, signal)
            
            # Stage 3: H:코어 - 분석 및 라우팅
            core_result = await self._stage_core(signal_id, signal, eval_result)
            
            # 분류에 따른 분기 처리
            category = eval_result.get("category", SignalCategory.NULL.value)
            
            if category == SignalCategory.WANTED.value:
                # 원하는 것 → 출력단
                await self._stage_output(signal_id, signal, core_result)
            else:
                # 원하지 않는 것 / null → 자산화
                await self._stage_assetize(signal_id, signal, eval_result, core_result)
            
            # 최종 상태 업데이트
            await self.signals_collection.update_one(
                {"signal_id": signal_id},
                {"$set": {
                    "current_stage": PipelineStage.COMPLETED.value,
                    "status": PipelineStatus.COMPLETED.value,
                    "completed_at": datetime.now(timezone.utc)
                }}
            )
            
            return {
                "success": True,
                "signal_id": signal_id,
                "category": category,
                "stages_completed": await self._get_stages_summary(signal_id)
            }
            
        except Exception as e:
            logger.error(f"Pipeline error for {signal_id}: {str(e)}")
            await self.signals_collection.update_one(
                {"signal_id": signal_id},
                {"$set": {
                    "status": PipelineStatus.FAILED.value,
                    "error": str(e)
                }}
            )
            return {"success": False, "signal_id": signal_id, "error": str(e)}
    
    async def _update_stage(self, signal_id: str, stage: PipelineStage, 
                           status: PipelineStatus, data: Dict[str, Any] = None):
        """단계 상태 업데이트"""
        stage_data = {
            "status": status.value,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "data": data or {}
        }
        
        await self.signals_collection.update_one(
            {"signal_id": signal_id},
            {
                "$set": {
                    f"stages.{stage.value}": stage_data,
                    "current_stage": stage.value
                }
            }
        )
    
    async def _stage_evaluate(self, signal_id: str, signal: Dict) -> Dict[str, Any]:
        """LL:의도 - 시그널 평가 단계"""
        await self._update_stage(signal_id, PipelineStage.LL_EVALUATE, PipelineStatus.PROCESSING)
        
        content = signal.get("content", "")
        
        # 평가 로직 (AI 분석 또는 규칙 기반)
        # 현재는 기본 규칙 적용 (추후 AI 연동)
        evaluation = {
            "category": SignalCategory.WANTED.value,  # 기본값: 분석 대상
            "confidence": 0.8,
            "keywords": [],
            "intent_detected": True,
            "analysis_notes": "자동 평가 완료"
        }
        
        # 간단한 분류 규칙 (예시)
        content_lower = content.lower() if content else ""
        
        # null 판정 조건
        if len(content.strip()) < 10:
            evaluation["category"] = SignalCategory.NULL.value
            evaluation["analysis_notes"] = "내용 부족 (10자 미만)"
            evaluation["confidence"] = 0.95
        
        await self._update_stage(signal_id, PipelineStage.LL_EVALUATE, PipelineStatus.COMPLETED, evaluation)
        
        # 시그널 문서에 카테고리 저장
        await self.signals_collection.update_one(
            {"signal_id": signal_id},
            {"$set": {"category": evaluation["category"]}}
        )
        
        return evaluation
    
    async def _stage_core(self, signal_id: str, signal: Dict, eval_result: Dict) -> Dict[str, Any]:
        """H:코어 - 분석 및 라우팅 단계"""
        await self._update_stage(signal_id, PipelineStage.H_CORE, PipelineStatus.PROCESSING)
        
        category = eval_result.get("category", SignalCategory.NULL.value)
        
        core_result = {
            "category": category,
            "route": "output" if category == SignalCategory.WANTED.value else "assetize",
            "processing_time_ms": 0,
            "sigma_applied": [0.5, 0.3, 0.2],  # 결이론 5:3:2
        }
        
        await self._update_stage(signal_id, PipelineStage.H_CORE, PipelineStatus.COMPLETED, core_result)
        
        return core_result
    
    async def _stage_output(self, signal_id: str, signal: Dict, core_result: Dict):
        """출력단 - 사용자가 원하는 것 처리"""
        await self._update_stage(signal_id, PipelineStage.OUTPUT, PipelineStatus.PROCESSING)
        
        output_result = {
            "delivered": True,
            "output_type": "analysis_result",
            "summary": f"시그널 분석 완료: {len(signal.get('content', ''))}자"
        }
        
        await self._update_stage(signal_id, PipelineStage.OUTPUT, PipelineStatus.COMPLETED, output_result)
    
    async def _stage_assetize(self, signal_id: str, signal: Dict, 
                             eval_result: Dict, core_result: Dict):
        """자산화 단계 - 원하지 않는 것 / null 처리"""
        
        # A, E, G 단계 처리
        await self._update_stage(signal_id, PipelineStage.ASSET_PROCESS, PipelineStatus.PROCESSING)
        
        category = eval_result.get("category", SignalCategory.NULL.value)
        
        # 의미 분석 (null이라도 의미 부여 가능한지 확인)
        can_assetize = True
        asset_value = 0.0
        
        if category == SignalCategory.NULL.value:
            # null이지만 의미 부여 가능한지 추가 분석
            content = signal.get("content", "")
            if len(content.strip()) >= 5:  # 최소 5자 이상이면 의미 부여 시도
                can_assetize = True
                asset_value = 0.3
            else:
                can_assetize = False
        else:
            # unwanted: 자산화 대상
            asset_value = 0.7
        
        asset_result = {
            "can_assetize": can_assetize,
            "asset_value": asset_value,
            "category": category,
        }
        
        await self._update_stage(signal_id, PipelineStage.ASSET_PROCESS, PipelineStatus.COMPLETED, asset_result)
        
        if can_assetize:
            # D:원장 - 자산 저장
            await self._update_stage(signal_id, PipelineStage.D_LEDGER, PipelineStatus.PROCESSING)
            
            asset_doc = {
                "asset_id": self._generate_id("AST"),
                "signal_id": signal_id,
                "content": signal.get("content", ""),
                "source": signal.get("source", ""),
                "category": category,
                "value": asset_value,
                "created_at": datetime.now(timezone.utc),
                "status": "stored",
                "module_ready": False  # 모듈화 대기
            }
            
            await self.assets_collection.insert_one(asset_doc)
            
            await self._update_stage(signal_id, PipelineStage.D_LEDGER, PipelineStatus.COMPLETED, {
                "asset_id": asset_doc["asset_id"],
                "stored": True
            })
            
            # 모듈화 단계 (B, C, F, I)
            await self._update_stage(signal_id, PipelineStage.MODULE, PipelineStatus.PENDING, {
                "note": "모듈화 대기 중"
            })
        else:
            await self._update_stage(signal_id, PipelineStage.D_LEDGER, PipelineStatus.SKIPPED, {
                "reason": "자산화 불가"
            })
    
    async def _get_stages_summary(self, signal_id: str) -> Dict[str, str]:
        """단계별 상태 요약"""
        signal = await self.signals_collection.find_one({"signal_id": signal_id})
        if not signal:
            return {}
        
        stages = signal.get("stages", {})
        summary = {}
        for stage_name, stage_data in stages.items():
            summary[stage_name] = stage_data.get("status", "unknown")
        
        return summary
    
    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """대시보드용 통계"""
        
        # 전체 시그널 수
        total = await self.signals_collection.count_documents({})
        
        # 상태별 카운트
        status_counts = {}
        for status in PipelineStatus:
            count = await self.signals_collection.count_documents({"status": status.value})
            status_counts[status.value] = count
        
        # 카테고리별 카운트
        category_counts = {}
        for cat in SignalCategory:
            count = await self.signals_collection.count_documents({"category": cat.value})
            category_counts[cat.value] = count
        
        # 단계별 현재 시그널 수
        stage_counts = {}
        for stage in PipelineStage:
            count = await self.signals_collection.count_documents({"current_stage": stage.value})
            stage_counts[stage.value] = count
        
        # 자산 통계
        total_assets = await self.assets_collection.count_documents({})
        
        # 최근 시그널
        recent_cursor = self.signals_collection.find({}).sort("created_at", -1).limit(10)
        recent_signals = []
        async for doc in recent_cursor:
            recent_signals.append({
                "signal_id": doc.get("signal_id"),
                "type": doc.get("type"),
                "category": doc.get("category"),
                "status": doc.get("status"),
                "current_stage": doc.get("current_stage"),
                "created_at": doc.get("created_at").isoformat() if doc.get("created_at") else None
            })
        
        return {
            "total_signals": total,
            "status_counts": status_counts,
            "category_counts": category_counts,
            "stage_counts": stage_counts,
            "total_assets": total_assets,
            "recent_signals": recent_signals
        }
    
    async def get_signal_detail(self, signal_id: str) -> Optional[Dict[str, Any]]:
        """시그널 상세 정보"""
        signal = await self.signals_collection.find_one(
            {"signal_id": signal_id},
            {"_id": 0}
        )
        if signal and signal.get("created_at"):
            signal["created_at"] = signal["created_at"].isoformat()
        if signal and signal.get("completed_at"):
            signal["completed_at"] = signal["completed_at"].isoformat()
        return signal
    
    async def get_stage_signals(self, stage: str, limit: int = 50) -> List[Dict[str, Any]]:
        """특정 단계의 시그널 목록"""
        cursor = self.signals_collection.find(
            {"current_stage": stage},
            {"_id": 0}
        ).sort("created_at", -1).limit(limit)
        
        signals = []
        async for doc in cursor:
            if doc.get("created_at"):
                doc["created_at"] = doc["created_at"].isoformat()
            signals.append(doc)
        
        return signals
