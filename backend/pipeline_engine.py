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
        """LL:의도 - 시그널 평가 단계 (5:3:2 비율 적용)"""
        await self._update_stage(signal_id, PipelineStage.LL_EVALUATE, PipelineStatus.PROCESSING)
        
        content = signal.get("content", "")
        metadata = signal.get("metadata", {})
        
        # 사용자 설정 비율 가져오기 (기본값: 5:3:2)
        ratio = metadata.get("classification_ratio", {"wanted": 5, "unwanted": 3, "null": 2})
        wanted_ratio = ratio.get("wanted", 5)
        unwanted_ratio = ratio.get("unwanted", 3)
        null_ratio = ratio.get("null", 2)
        total_ratio = wanted_ratio + unwanted_ratio + null_ratio
        
        # AI 분석 결과에서 신뢰도 가져오기
        ai_analysis = metadata.get("ai_analysis", {})
        ai_confidence = ai_analysis.get("confidence", 0.5)
        analysis_type = metadata.get("analysis_type", "general")
        
        # 분류 기준:
        # 1. 내용이 충분하고 목적이 명확하면 wanted
        # 2. 내용은 있지만 숨겨진 가치가 있으면 unwanted (자산화 대상)
        # 3. 내용이 부족하거나 가치가 없으면 null
        
        evaluation = {
            "category": SignalCategory.WANTED.value,
            "confidence": ai_confidence,
            "keywords": [],
            "intent_detected": True,
            "analysis_notes": "",
            "ratio_applied": f"{wanted_ratio}:{unwanted_ratio}:{null_ratio}"
        }
        
        content_length = len(content.strip())
        purpose = metadata.get("purpose", "")
        expected_result = metadata.get("expected_result", "")
        
        # 분류 로직 (비율 기반 확률적 분류)
        import random
        
        # 기본 점수 계산
        base_score = 0
        
        # 1. 내용 길이 점수
        if content_length < 10:
            base_score -= 3
        elif content_length < 50:
            base_score += 1
        else:
            base_score += 3
        
        # 2. 목적/기대결과 명시 여부
        if purpose and len(purpose) > 5:
            base_score += 2
        if expected_result and len(expected_result) > 5:
            base_score += 2
        
        # 3. AI 신뢰도
        if ai_confidence >= 0.8:
            base_score += 2
        elif ai_confidence >= 0.5:
            base_score += 1
        
        # 4. 분석 유형 (코드, 특허는 wanted 가능성 높음)
        if analysis_type in ["code", "patent_idea"]:
            base_score += 1
        
        # 비율 기반 임계값 계산
        wanted_threshold = (wanted_ratio / total_ratio) * 10  # 5:3:2 → 5
        null_threshold = -((null_ratio / total_ratio) * 5)    # 5:3:2 → -2
        
        # 최종 분류
        if base_score >= wanted_threshold:
            evaluation["category"] = SignalCategory.WANTED.value
            evaluation["analysis_notes"] = f"직접 분석 대상 (점수: {base_score}, 임계: {wanted_threshold:.1f})"
        elif base_score <= null_threshold:
            evaluation["category"] = SignalCategory.NULL.value
            evaluation["analysis_notes"] = f"가치 판정 불가 (점수: {base_score})"
        else:
            evaluation["category"] = SignalCategory.UNWANTED.value
            evaluation["analysis_notes"] = f"자산화 대상 - 숨겨진 가치 추출 (점수: {base_score})"
        
        # 추가 랜덤 요소 (비율 반영)
        if evaluation["category"] == SignalCategory.WANTED.value and random.random() > (wanted_ratio / total_ratio * 1.2):
            evaluation["category"] = SignalCategory.UNWANTED.value
            evaluation["analysis_notes"] += " [비율 조정 적용]"
        
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
        """자산화 단계 - 원하지 않는 것 / null 처리
        
        특허 A, E, G 단계:
        - A: 데이터 라벨링 (분류/태깅)
        - E: 가치 측정 (신규성, 활용가능성)
        - G: 저장 및 연결
        """
        
        await self._update_stage(signal_id, PipelineStage.ASSET_PROCESS, PipelineStatus.PROCESSING)
        
        category = eval_result.get("category", SignalCategory.NULL.value)
        content = signal.get("content", "")
        metadata = signal.get("metadata", {})
        ai_analysis = metadata.get("ai_analysis", {})
        
        # ===== A단계: 데이터 라벨링 =====
        labels = []
        tags = []
        
        # 분석 유형에 따른 태그
        analysis_type = metadata.get("analysis_type", "general")
        tags.append(f"type:{analysis_type}")
        
        # 내용 기반 키워드 추출 (간단 버전)
        words = content.split()
        for word in words:
            if len(word) >= 3 and word.isalnum():
                labels.append(word.lower())
        labels = list(set(labels))[:10]  # 상위 10개만
        
        # 카테고리 태그
        tags.append(f"category:{category}")
        
        # ===== E단계: 가치 측정 =====
        value_score = 0.0
        novelty_score = 0.0
        utility_score = 0.0
        
        # 길이 기반 기본 가치
        content_length = len(content.strip())
        if content_length >= 100:
            value_score += 0.3
        elif content_length >= 50:
            value_score += 0.2
        else:
            value_score += 0.1
        
        # AI 분석 결과 기반 가치 추가
        if ai_analysis.get("success"):
            ai_confidence = ai_analysis.get("confidence", 0.5)
            value_score += ai_confidence * 0.3
            
            # 특허/아이디어 분석의 경우 신규성/실현가능성 점수 활용
            if analysis_type == "patent_idea":
                novelty = ai_analysis.get("novelty_assessment", {})
                novelty_score = novelty.get("novelty_score", 0.5)
                feasibility = ai_analysis.get("feasibility", {})
                utility_score = feasibility.get("technical_feasibility_score", 0.5)
                value_score += (novelty_score + utility_score) * 0.2
            
            # 코드 분석의 경우 코드 품질 점수 활용
            elif analysis_type == "code":
                code_quality = ai_analysis.get("code_quality", {})
                overall_score = code_quality.get("overall_score", 0.5)
                value_score += overall_score * 0.2
        
        # 목적/기대결과 명시 시 추가 가치
        if metadata.get("purpose"):
            value_score += 0.1
            tags.append("has_purpose")
        if metadata.get("expected_result"):
            value_score += 0.1
            tags.append("has_expected_result")
        
        # 최종 가치 점수 정규화 (0~1)
        value_score = min(max(value_score, 0), 1.0)
        
        # ===== 자산화 가능 여부 판정 =====
        can_assetize = value_score >= 0.2 or category == SignalCategory.UNWANTED.value
        
        asset_result = {
            "can_assetize": can_assetize,
            "value_score": round(value_score, 2),
            "novelty_score": round(novelty_score, 2),
            "utility_score": round(utility_score, 2),
            "category": category,
            "labels": labels,
            "tags": tags,
            "stage_a_labeling": {"labels": labels, "tags": tags},
            "stage_e_valuation": {
                "value_score": round(value_score, 2),
                "novelty_score": round(novelty_score, 2),
                "utility_score": round(utility_score, 2)
            }
        }
        
        await self._update_stage(signal_id, PipelineStage.ASSET_PROCESS, PipelineStatus.COMPLETED, asset_result)
        
        if can_assetize:
            # ===== G단계 + D:원장 - 자산 저장 =====
            await self._update_stage(signal_id, PipelineStage.D_LEDGER, PipelineStatus.PROCESSING)
            
            asset_id = self._generate_id("AST")
            
            asset_doc = {
                "asset_id": asset_id,
                "signal_id": signal_id,
                "content": content,
                "content_summary": content[:200] + "..." if len(content) > 200 else content,
                "source": signal.get("source", ""),
                "category": category,
                "analysis_type": analysis_type,
                # 가치 측정 결과
                "value_score": round(value_score, 2),
                "novelty_score": round(novelty_score, 2),
                "utility_score": round(utility_score, 2),
                # 라벨링
                "labels": labels,
                "tags": tags,
                # AI 분석 요약
                "ai_summary": ai_analysis.get("analysis_summary", ""),
                # 메타데이터
                "purpose": metadata.get("purpose", ""),
                "expected_result": metadata.get("expected_result", ""),
                # 상태
                "created_at": datetime.now(timezone.utc),
                "status": "stored",
                "module_ready": value_score >= 0.5,  # 가치 0.5 이상이면 모듈화 준비
                "module_status": "pending" if value_score >= 0.5 else "not_ready"
            }
            
            await self.assets_collection.insert_one(asset_doc)
            
            await self._update_stage(signal_id, PipelineStage.D_LEDGER, PipelineStatus.COMPLETED, {
                "asset_id": asset_id,
                "stored": True,
                "value_score": round(value_score, 2),
                "module_ready": asset_doc["module_ready"]
            })
            
            # 모듈화 단계로 전달 (가치 충분 시)
            if asset_doc["module_ready"]:
                await self._stage_module(signal_id, asset_doc)
            else:
                await self._update_stage(signal_id, PipelineStage.MODULE, PipelineStatus.SKIPPED, {
                    "reason": f"가치 점수 부족 ({value_score:.2f} < 0.5)"
                })
        else:
            await self._update_stage(signal_id, PipelineStage.D_LEDGER, PipelineStatus.SKIPPED, {
                "reason": f"자산화 불가 (가치: {value_score:.2f})"
            })
            await self._update_stage(signal_id, PipelineStage.MODULE, PipelineStatus.SKIPPED, {
                "reason": "자산화 단계 스킵됨"
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
    
    async def find_related_assets(self, content: str, purpose: str = "") -> List[Dict[str, Any]]:
        """관련 모듈화 자산 찾기"""
        try:
            # 간단한 키워드 매칭으로 관련 자산 찾기
            # 실제로는 벡터 유사도 검색 등 고도화 필요
            keywords = set()
            
            # 내용에서 키워드 추출 (간단 버전)
            for word in (content + " " + purpose).split():
                if len(word) >= 2:
                    keywords.add(word.lower())
            
            # 자산 검색
            related = []
            cursor = self.assets_collection.find(
                {"status": "stored"},
                {"_id": 0}
            ).limit(50)
            
            async for asset in cursor:
                asset_content = asset.get("content", "").lower()
                
                # 키워드 매칭 점수 계산
                match_count = sum(1 for kw in keywords if kw in asset_content)
                if match_count > 0:
                    relevance = min(match_count / len(keywords), 1.0) if keywords else 0
                    related.append({
                        "asset_id": asset.get("asset_id"),
                        "relevance": round(relevance, 2),
                        "summary": asset_content[:100] + "..." if len(asset_content) > 100 else asset_content,
                        "category": asset.get("category")
                    })
            
            # 관련도 순 정렬
            related.sort(key=lambda x: x["relevance"], reverse=True)
            return related[:5]  # 상위 5개만 반환
            
        except Exception as e:
            logger.error(f"Error finding related assets: {str(e)}")
            return []
    
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
        
        # 단계별 통과한 시그널 수 (각 단계가 completed인 시그널 수)
        stage_counts = {}
        for stage in PipelineStage:
            # stages.{stage}.status가 completed인 시그널 수
            count = await self.signals_collection.count_documents({
                f"stages.{stage.value}.status": "completed"
            })
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
                "metadata": doc.get("metadata", {}),
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
        """특정 단계를 통과한 시그널 목록 (현재 + 완료)"""
        # 해당 단계를 통과한 모든 시그널 조회
        cursor = self.signals_collection.find(
            {f"stages.{stage}": {"$exists": True}},
            {"_id": 0}
        ).sort("created_at", -1).limit(limit)
        
        signals = []
        async for doc in cursor:
            if doc.get("created_at"):
                doc["created_at"] = doc["created_at"].isoformat()
            if doc.get("completed_at"):
                doc["completed_at"] = doc["completed_at"].isoformat()
            signals.append(doc)
        
        return signals
