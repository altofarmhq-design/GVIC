"""
D: LEDGER - 원장 특허 모듈
거래 기록 및 분산원장 관리
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import hashlib
import logging

router = APIRouter(prefix="/api/patent/d", tags=["D:LEDGER"])
logger = logging.getLogger(__name__)

class Transaction(BaseModel):
    """거래 기록"""
    transaction_type: str  # purchase, reward, transfer, refund
    from_account: str
    to_account: str
    amount: float
    asset_id: Optional[str] = None
    metadata: Dict[str, Any] = {}

class LedgerQuery(BaseModel):
    """원장 조회 쿼리"""
    account_id: Optional[str] = None
    transaction_type: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None

# ==================== 거래 기록 ====================

@router.post("/record")
async def record_transaction(transaction: Transaction):
    """거래 기록"""
    from server import db
    
    # 거래 ID 생성
    tx_data = f"{transaction.from_account}:{transaction.to_account}:{transaction.amount}:{datetime.now().isoformat()}"
    tx_id = f"TX_{hashlib.sha256(tx_data.encode()).hexdigest()[:16].upper()}"
    
    # 이전 블록 해시 조회
    last_tx = await db.ledger.find_one({}, {"_id": 0}, sort=[("block_number", -1)])
    prev_hash = last_tx.get("block_hash", "GENESIS") if last_tx else "GENESIS"
    block_number = (last_tx.get("block_number", 0) + 1) if last_tx else 1
    
    # 현재 블록 해시 생성
    block_data = f"{tx_id}:{prev_hash}:{transaction.amount}"
    block_hash = hashlib.sha256(block_data.encode()).hexdigest()
    
    tx_record = {
        "transaction_id": tx_id,
        "block_number": block_number,
        "block_hash": block_hash,
        "prev_hash": prev_hash,
        "transaction_type": transaction.transaction_type,
        "from_account": transaction.from_account,
        "to_account": transaction.to_account,
        "amount": transaction.amount,
        "asset_id": transaction.asset_id,
        "metadata": transaction.metadata,
        "status": "confirmed",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    await db.ledger.insert_one(tx_record)
    
    # 계정 잔액 업데이트
    if transaction.transaction_type != "transfer":
        await db.account_balances.update_one(
            {"account_id": transaction.to_account},
            {"$inc": {"balance": transaction.amount}},
            upsert=True
        )
    
    return {
        "success": True,
        "transaction_id": tx_id,
        "block_number": block_number,
        "block_hash": block_hash
    }

@router.get("/transaction/{tx_id}")
async def get_transaction(tx_id: str):
    """거래 상세 조회"""
    from server import db
    
    tx = await db.ledger.find_one({"transaction_id": tx_id}, {"_id": 0})
    
    if not tx:
        raise HTTPException(status_code=404, detail="거래를 찾을 수 없습니다")
    
    return {"success": True, "transaction": tx}

@router.post("/query")
async def query_ledger(query: LedgerQuery, limit: int = 50, offset: int = 0):
    """원장 조회"""
    from server import db
    
    filter_query = {}
    
    if query.account_id:
        filter_query["$or"] = [
            {"from_account": query.account_id},
            {"to_account": query.account_id}
        ]
    
    if query.transaction_type:
        filter_query["transaction_type"] = query.transaction_type
    
    if query.start_date:
        filter_query["timestamp"] = {"$gte": query.start_date}
    
    if query.end_date:
        filter_query.setdefault("timestamp", {})["$lte"] = query.end_date
    
    transactions = await db.ledger.find(
        filter_query,
        {"_id": 0}
    ).sort("block_number", -1).skip(offset).limit(limit).to_list(limit)
    
    total = await db.ledger.count_documents(filter_query)
    
    return {
        "success": True,
        "transactions": transactions,
        "total": total,
        "limit": limit,
        "offset": offset
    }

# ==================== 계정 관리 ====================

@router.get("/balance/{account_id}")
async def get_account_balance(account_id: str):
    """계정 잔액 조회"""
    from server import db
    
    account = await db.account_balances.find_one({"account_id": account_id}, {"_id": 0})
    
    if not account:
        return {"success": True, "account_id": account_id, "balance": 0}
    
    return {"success": True, "account_id": account_id, "balance": account.get("balance", 0)}

@router.get("/account-history/{account_id}")
async def get_account_history(account_id: str, limit: int = 50):
    """계정 거래 이력"""
    from server import db
    
    transactions = await db.ledger.find(
        {"$or": [{"from_account": account_id}, {"to_account": account_id}]},
        {"_id": 0}
    ).sort("timestamp", -1).limit(limit).to_list(limit)
    
    # 수입/지출 분류
    for tx in transactions:
        if tx["to_account"] == account_id:
            tx["direction"] = "income"
        else:
            tx["direction"] = "expense"
    
    return {"success": True, "account_id": account_id, "transactions": transactions}

# ==================== 블록체인 검증 ====================

@router.get("/verify-chain")
async def verify_blockchain():
    """블록체인 무결성 검증"""
    from server import db
    
    blocks = await db.ledger.find({}, {"_id": 0}).sort("block_number", 1).to_list(1000)
    
    if not blocks:
        return {"success": True, "valid": True, "message": "원장이 비어있습니다"}
    
    invalid_blocks = []
    prev_hash = "GENESIS"
    
    for block in blocks:
        # 이전 해시 검증
        if block["prev_hash"] != prev_hash:
            invalid_blocks.append({
                "block_number": block["block_number"],
                "expected_prev_hash": prev_hash,
                "actual_prev_hash": block["prev_hash"]
            })
        prev_hash = block["block_hash"]
    
    return {
        "success": True,
        "valid": len(invalid_blocks) == 0,
        "total_blocks": len(blocks),
        "invalid_blocks": invalid_blocks,
        "verified_at": datetime.now(timezone.utc).isoformat()
    }

@router.get("/latest-blocks")
async def get_latest_blocks(limit: int = 10):
    """최근 블록 조회"""
    from server import db
    
    blocks = await db.ledger.find(
        {},
        {"_id": 0}
    ).sort("block_number", -1).limit(limit).to_list(limit)
    
    return {"success": True, "blocks": blocks}

# ==================== 통계 ====================

@router.get("/stats")
async def get_ledger_stats():
    """원장 통계"""
    from server import db
    
    total_transactions = await db.ledger.count_documents({})
    
    # 거래 유형별 통계
    type_pipeline = [
        {"$group": {"_id": "$transaction_type", "count": {"$sum": 1}, "total_amount": {"$sum": "$amount"}}}
    ]
    type_stats = await db.ledger.aggregate(type_pipeline).to_list(10)
    
    # 총 거래액
    total_pipeline = [
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    total_result = await db.ledger.aggregate(total_pipeline).to_list(1)
    total_amount = total_result[0]["total"] if total_result else 0
    
    return {
        "success": True,
        "stats": {
            "total_transactions": total_transactions,
            "total_amount": round(total_amount, 2),
            "by_type": {t["_id"]: {"count": t["count"], "amount": round(t["total_amount"], 2)} for t in type_stats}
        }
    }

@router.get("/532-distribution")
async def get_532_distribution():
    """5:3:2 분배 현황"""
    from server import db
    
    # 플랫폼 펀드 조회
    operation_fund = await db.platform_funds.find_one({"fund_type": "operation"}, {"_id": 0})
    management_fund = await db.platform_funds.find_one({"fund_type": "management"}, {"_id": 0})
    
    # 공공 환원 (사용자들에게 분배된 금액)
    public_pipeline = [
        {"$match": {"transaction_type": "reward", "metadata.distribution_type": "public"}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    public_result = await db.ledger.aggregate(public_pipeline).to_list(1)
    public_distributed = public_result[0]["total"] if public_result else 0
    
    return {
        "success": True,
        "distribution_532": {
            "public": {
                "label": "공공 환원 (5)",
                "amount": round(public_distributed, 2)
            },
            "operation": {
                "label": "플랫폼 운영 (3)",
                "amount": operation_fund.get("total_amount", 0) if operation_fund else 0
            },
            "management": {
                "label": "기획/관리 (2)",
                "amount": management_fund.get("total_amount", 0) if management_fund else 0
            }
        }
    }
