"""
F: FIELD - 실행 특허 모듈
판매 등록 및 마켓플레이스 관리
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import logging

router = APIRouter(prefix="/api/patent/f", tags=["F:FIELD"])
logger = logging.getLogger(__name__)

class SaleRegistration(BaseModel):
    """판매 등록 요청"""
    module_id: str
    price: float
    title: str
    description: str = ""
    tags: List[str] = []

class MarketplaceFilter(BaseModel):
    """마켓플레이스 필터"""
    category: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    tags: List[str] = []

# ==================== 판매 등록 ====================

@router.post("/register")
async def register_for_sale(request: SaleRegistration):
    """모듈 판매 등록"""
    from server import db
    
    # 모듈 존재 확인
    module = await db.asset_modules.find_one({"module_id": request.module_id}, {"_id": 0})
    
    if not module:
        raise HTTPException(status_code=404, detail="모듈을 찾을 수 없습니다")
    
    # 판매 등록
    sale_listing = {
        "listing_id": f"LIST_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "module_id": request.module_id,
        "title": request.title,
        "description": request.description,
        "price": request.price,
        "tags": request.tags,
        "status": "active",
        "views": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.marketplace_listings.insert_one(sale_listing)
    
    # 모듈 상태 업데이트
    await db.asset_modules.update_one(
        {"module_id": request.module_id},
        {"$set": {"status": "on_sale", "listing_id": sale_listing["listing_id"]}}
    )
    
    return {
        "success": True,
        "listing_id": sale_listing["listing_id"],
        "message": "판매 등록 완료"
    }

@router.post("/unregister/{listing_id}")
async def unregister_from_sale(listing_id: str):
    """판매 등록 해제"""
    from server import db
    
    listing = await db.marketplace_listings.find_one({"listing_id": listing_id}, {"_id": 0})
    
    if not listing:
        raise HTTPException(status_code=404, detail="판매 등록을 찾을 수 없습니다")
    
    # 판매 등록 비활성화
    await db.marketplace_listings.update_one(
        {"listing_id": listing_id},
        {"$set": {"status": "inactive", "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # 모듈 상태 복원
    await db.asset_modules.update_one(
        {"module_id": listing["module_id"]},
        {"$set": {"status": "completed"}, "$unset": {"listing_id": ""}}
    )
    
    return {"success": True, "message": "판매 등록 해제됨"}

# ==================== 마켓플레이스 ====================

@router.get("/marketplace")
async def browse_marketplace(
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    sort_by: str = "created_at",
    order: str = "desc",
    limit: int = 20,
    offset: int = 0
):
    """마켓플레이스 브라우징"""
    from server import db
    
    query = {"status": "active"}
    
    if category:
        query["category"] = category
    if min_price is not None:
        query["price"] = {"$gte": min_price}
    if max_price is not None:
        query.setdefault("price", {})["$lte"] = max_price
    
    sort_order = -1 if order == "desc" else 1
    
    listings = await db.marketplace_listings.find(
        query,
        {"_id": 0}
    ).sort(sort_by, sort_order).skip(offset).limit(limit).to_list(limit)
    
    total = await db.marketplace_listings.count_documents(query)
    
    return {
        "success": True,
        "listings": listings,
        "total": total,
        "limit": limit,
        "offset": offset
    }

@router.get("/listing/{listing_id}")
async def get_listing_detail(listing_id: str):
    """판매 상세 조회"""
    from server import db
    
    listing = await db.marketplace_listings.find_one({"listing_id": listing_id}, {"_id": 0})
    
    if not listing:
        raise HTTPException(status_code=404, detail="판매 등록을 찾을 수 없습니다")
    
    # 조회수 증가
    await db.marketplace_listings.update_one(
        {"listing_id": listing_id},
        {"$inc": {"views": 1}}
    )
    
    # 모듈 정보 조회
    module = await db.asset_modules.find_one(
        {"module_id": listing["module_id"]},
        {"_id": 0}
    )
    
    return {
        "success": True,
        "listing": listing,
        "module": module
    }

@router.post("/update-price/{listing_id}")
async def update_listing_price(listing_id: str, new_price: float):
    """가격 수정"""
    from server import db
    
    if new_price < 0:
        raise HTTPException(status_code=400, detail="가격은 0 이상이어야 합니다")
    
    result = await db.marketplace_listings.update_one(
        {"listing_id": listing_id},
        {"$set": {"price": new_price, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="판매 등록을 찾을 수 없습니다")
    
    return {"success": True, "new_price": new_price}

@router.get("/stats")
async def get_marketplace_stats():
    """마켓플레이스 통계"""
    from server import db
    
    total_listings = await db.marketplace_listings.count_documents({"status": "active"})
    total_sales = await db.module_sales.count_documents({})
    
    # 매출 합계
    sales_pipeline = [
        {"$group": {"_id": None, "total": {"$sum": "$price"}}}
    ]
    sales_result = await db.module_sales.aggregate(sales_pipeline).to_list(1)
    total_revenue = sales_result[0]["total"] if sales_result else 0
    
    # 인기 태그
    tag_pipeline = [
        {"$unwind": "$tags"},
        {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    popular_tags = await db.marketplace_listings.aggregate(tag_pipeline).to_list(10)
    
    return {
        "success": True,
        "stats": {
            "total_listings": total_listings,
            "total_sales": total_sales,
            "total_revenue": round(total_revenue, 2),
            "popular_tags": [{"tag": t["_id"], "count": t["count"]} for t in popular_tags]
        }
    }

@router.get("/my-listings")
async def get_my_listings(user_id: str):
    """내 판매 목록"""
    from server import db
    
    listings = await db.marketplace_listings.find(
        {"seller_id": user_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return {"success": True, "listings": listings}
