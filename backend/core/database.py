"""
데이터베이스 모듈
MongoDB 연동 및 데이터 관리
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import os
import asyncio

class Database:
    """데이터베이스 관리 클래스"""
    
    def __init__(self, mongo_url: str = None, db_name: str = None):
        self.mongo_url = mongo_url or os.environ.get('MONGO_URL')
        self.db_name = db_name or os.environ.get('DB_NAME', 'gvic_db')
        self.client: AsyncIOMotorClient = None
        self.db: AsyncIOMotorDatabase = None
    
    async def connect(self):
        """데이터베이스 연결"""
        if self.client is None:
            self.client = AsyncIOMotorClient(self.mongo_url)
            self.db = self.client[self.db_name]
        return self.db
    
    async def disconnect(self):
        """연결 해제"""
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
    
    # ===== 처리 기록 =====
    async def save_processing_result(self, result: Dict) -> str:
        """처리 결과 저장"""
        await self.connect()
        doc = {
            **result,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        res = await self.db.processing_results.insert_one(doc)
        return str(res.inserted_id)
    
    async def get_processing_results(self, limit: int = 100) -> List[Dict]:
        """처리 결과 조회"""
        await self.connect()
        cursor = self.db.processing_results.find({}, {"_id": 0}).sort("created_at", -1).limit(limit)
        return await cursor.to_list(length=limit)
    
    # ===== 설정 =====
    async def save_config(self, config_type: str, config_data: Dict) -> bool:
        """설정 저장"""
        await self.connect()
        await self.db.configs.update_one(
            {"type": config_type},
            {"$set": {"data": config_data, "updated_at": datetime.now(timezone.utc).isoformat()}},
            upsert=True
        )
        return True
    
    async def get_config(self, config_type: str) -> Optional[Dict]:
        """설정 조회"""
        await self.connect()
        doc = await self.db.configs.find_one({"type": config_type}, {"_id": 0})
        return doc.get("data") if doc else None
    
    # ===== 알림 =====
    async def save_alert(self, alert: Dict) -> str:
        """알림 저장"""
        await self.connect()
        doc = {
            **alert,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        res = await self.db.alerts.insert_one(doc)
        return str(res.inserted_id)
    
    async def get_alerts(self, active_only: bool = False, limit: int = 100) -> List[Dict]:
        """알림 조회"""
        await self.connect()
        query = {"resolved": False} if active_only else {}
        cursor = self.db.alerts.find(query, {"_id": 0}).sort("created_at", -1).limit(limit)
        return await cursor.to_list(length=limit)
    
    async def resolve_alert(self, alert_id: str) -> bool:
        """알림 해결 처리"""
        await self.connect()
        result = await self.db.alerts.update_one(
            {"id": alert_id},
            {"$set": {"resolved": True, "resolved_at": datetime.now(timezone.utc).isoformat()}}
        )
        return result.modified_count > 0
    
    # ===== 메트릭 =====
    async def save_metric(self, name: str, value: float, tags: Dict = None) -> str:
        """메트릭 저장"""
        await self.connect()
        doc = {
            "name": name,
            "value": value,
            "tags": tags or {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        res = await self.db.metrics.insert_one(doc)
        return str(res.inserted_id)
    
    async def get_metrics(self, name: str = None, limit: int = 100) -> List[Dict]:
        """메트릭 조회"""
        await self.connect()
        query = {"name": name} if name else {}
        cursor = self.db.metrics.find(query, {"_id": 0}).sort("timestamp", -1).limit(limit)
        return await cursor.to_list(length=limit)
    
    # ===== 통계 =====
    async def get_statistics(self) -> Dict:
        """데이터베이스 통계"""
        await self.connect()
        return {
            "processing_results": await self.db.processing_results.count_documents({}),
            "configs": await self.db.configs.count_documents({}),
            "alerts": await self.db.alerts.count_documents({}),
            "metrics": await self.db.metrics.count_documents({})
        }
