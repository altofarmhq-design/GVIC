"""
GVIC MongoDB 초기화 스크립트
테스트 계정 및 기본 데이터 생성
"""
import os
import sys
from datetime import datetime, timezone
import hashlib

# MongoDB 연결
try:
    from pymongo import MongoClient
    import bcrypt
except ImportError:
    print("필요한 패키지 설치 중...")
    os.system("pip install pymongo bcrypt")
    from pymongo import MongoClient
    import bcrypt

def init_database():
    """MongoDB 초기화"""
    
    # 환경변수에서 MongoDB URL 읽기
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    db_name = os.environ.get("DB_NAME", "gvic_database")
    
    print(f"MongoDB 연결 중... ({mongo_url})")
    
    try:
        client = MongoClient(mongo_url, serverSelectionTimeoutMS=5000)
        # 연결 테스트
        client.server_info()
        print("MongoDB 연결 성공!")
    except Exception as e:
        print(f"MongoDB 연결 실패: {e}")
        print("\n해결 방법:")
        print("1. MongoDB가 실행 중인지 확인하세요")
        print("   - Windows: services.msc에서 MongoDB 서비스 확인")
        print("   - 또는: mongod --dbpath C:\\data\\db")
        print("2. MongoDB Atlas 사용 시 backend/.env의 MONGO_URL을 수정하세요")
        return False
    
    db = client[db_name]
    
    # 1. 테스트 사용자 생성
    print("\n[1/3] 테스트 사용자 생성 중...")
    users = db["users"]
    
    admin_email = "admin@gvic.com"
    existing_user = users.find_one({"email": admin_email})
    
    if existing_user:
        print(f"  - 사용자 '{admin_email}' 이미 존재함")
    else:
        # 비밀번호 해시
        password = "gvicgvic!"
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        user_data = {
            "email": admin_email,
            "name": "GVIC Admin",
            "password_hash": password_hash,
            "role": "admin",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "subscription": {
                "plan": "pro",
                "plan_name": "Pro",
                "is_active": True,
                "usage": {
                    "analysis_count": 0,
                    "product_count": 0,
                    "shop_count": 0
                },
                "limits": {
                    "monthly_analysis": 1000,
                    "max_products": 50,
                    "max_shops": 10
                }
            }
        }
        users.insert_one(user_data)
        print(f"  - 관리자 계정 생성됨: {admin_email} / {password}")
    
    # 2. 구독 플랜 데이터 생성
    print("\n[2/3] 구독 플랜 데이터 생성 중...")
    plans = db["subscription_plans"]
    
    default_plans = [
        {
            "plan_id": "free",
            "name": "Free",
            "price": 0,
            "currency": "KRW",
            "features": ["월 10회 분석", "제품 3개", "쇼핑몰 1개", "기본 리포트"],
            "limits": {"monthly_analysis": 10, "max_products": 3, "max_shops": 1}
        },
        {
            "plan_id": "starter",
            "name": "Starter",
            "price": 29000,
            "currency": "KRW",
            "features": ["월 50회 분석", "제품 5개", "쇼핑몰 1개", "상세 리포트", "이메일 알림"],
            "limits": {"monthly_analysis": 50, "max_products": 5, "max_shops": 1}
        },
        {
            "plan_id": "growth",
            "name": "Growth",
            "price": 99000,
            "currency": "KRW",
            "popular": True,
            "features": ["월 200회 분석", "제품 20개", "쇼핑몰 3개", "상세 리포트", "API 접근", "웹훅 알림"],
            "limits": {"monthly_analysis": 200, "max_products": 20, "max_shops": 3}
        },
        {
            "plan_id": "pro",
            "name": "Pro",
            "price": 249000,
            "currency": "KRW",
            "features": ["월 1,000회 분석", "제품 50개", "쇼핑몰 10개", "프리미엄 리포트", "API 무제한", "우선 지원"],
            "limits": {"monthly_analysis": 1000, "max_products": 50, "max_shops": 10}
        }
    ]
    
    for plan in default_plans:
        existing = plans.find_one({"plan_id": plan["plan_id"]})
        if not existing:
            plans.insert_one(plan)
            print(f"  - 플랜 생성됨: {plan['name']}")
        else:
            print(f"  - 플랜 '{plan['name']}' 이미 존재함")
    
    # 3. HS Code 샘플 데이터
    print("\n[3/3] HS Code 샘플 데이터 생성 중...")
    hs_codes = db["hs_codes"]
    
    sample_hs_codes = [
        {"code": "8518", "name": "마이크로폰, 스피커, 헤드폰", "category": "전자기기"},
        {"code": "8471", "name": "컴퓨터 및 주변기기", "category": "전자기기"},
        {"code": "3304", "name": "화장품", "category": "뷰티"},
        {"code": "6110", "name": "니트 의류", "category": "패션"},
        {"code": "9403", "name": "가구", "category": "홈/리빙"},
    ]
    
    for hs in sample_hs_codes:
        existing = hs_codes.find_one({"code": hs["code"]})
        if not existing:
            hs_codes.insert_one(hs)
            print(f"  - HS Code 생성됨: {hs['code']} ({hs['name']})")
        else:
            print(f"  - HS Code '{hs['code']}' 이미 존재함")
    
    print("\n" + "="*50)
    print("MongoDB 초기화 완료!")
    print("="*50)
    print(f"\n테스트 계정:")
    print(f"  Email:    admin@gvic.com")
    print(f"  Password: gvicgvic!")
    print()
    
    return True

if __name__ == "__main__":
    # .env 파일에서 환경변수 로드
    env_file = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip().strip('"')
    
    success = init_database()
    sys.exit(0 if success else 1)
