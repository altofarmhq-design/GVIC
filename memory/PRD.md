# GVIC 시그널 온톨로지 자산화 플랫폼 - PRD

## 1. 제품 개요

### 1.1 비전
GVIC는 12개 특허를 기반으로 한 AI 기반 시그널 분석 및 자산화 플랫폼입니다.
모든 입력 시그널의 "의도"를 핵심 자산으로 취급하여, 자동 분석/축적/상품화/가치 교환을 수행합니다.

### 1.2 핵심 철학
- **Intent as Asset**: 입력 데이터가 아닌 "의도"를 자산으로 인식
- **결이론 5:3:2**: 가치 분배 비율 (공공:생산:개인)
- **Operator-in-the-Loop**: 인간 운영자가 상품화 결정

## 2. 현재 구현 상태 (MVP)

### 2.1 완료된 기능 ✅

#### 핵심 기능
| 기능 | 상태 | 설명 |
|------|------|------|
| 14개 특허 기반 탭 UI | ✅ 완료 | J:입력 ~ I:무결성 + 대시보드, 설정, 사용자 |
| AI 시그널 분석 | ✅ 완료 | Gemini 3 Flash 연동 |
| 의도 추출 | ✅ 완료 | 시그널 유형 감지, 감성 분석 |
| 자산화 저장 | ✅ 완료 | MongoDB 저장/조회/삭제 |
| 대시보드 | ✅ 완료 | 실시간 통계, 시그널 유형별 분포 |

#### J:입력 채널 (시그널 유입)
| 채널 | 상태 | 설명 |
|------|------|------|
| 텍스트 | ✅ 활성화 | 직접 입력 |
| 파일 | ✅ 활성화 | Excel, CSV, PDF, TXT, 이미지 |
| URL | ✅ 활성화 | 웹페이지 텍스트 추출 |
| API | ⏸️ 준비중 | 다음 단계 |

#### 인증/권한
| 기능 | 상태 | 설명 |
|------|------|------|
| JWT 인증 | ✅ 완료 | 로그인/로그아웃 |
| Google OAuth | ✅ 완료 | Emergent Auth 연동 |
| 역할 기반 권한 | ✅ 완료 | super_admin/admin/operator/visitor |

#### 시스템 설정
| 기능 | 상태 | 설명 |
|------|------|------|
| Σ (시그마) 설정 | ✅ 완료 | 5:3:2 비율 조정 |
| Ω (오메가) 경계 조건 | ✅ 완료 | 값 범위 설정 |

### 2.2 14개 특허 탭 구조

```
┌─────────────────────────────────────────────────────────────┐
│  대시보드 │ J:입력 │ LL:의도 │ H:코어 │ A:게이트 │ E:방어막 │ G:정제 │
├─────────────────────────────────────────────────────────────┤
│  B:산출 │ C:집행 │ F:실행 │ D:원장 │ I:무결성 │ 설정 │ 사용자 │
└─────────────────────────────────────────────────────────────┘
```

| 탭 코드 | 기능 | 특허명 | 구현 상태 |
|--------|------|--------|----------|
| J | 입력 | PLATFORM | ✅ UI 완료 |
| LL | 의도 | INTELLIGENCE | ✅ AI 분석 연동 |
| H | 코어 | CORE | ✅ 시그마 설정 |
| A | 게이트 | GATE | ✅ UI 완료 |
| E | 방어막 | SHIELD | ✅ UI 완료 |
| G | 정제 | REFINE | ✅ UI 완료 |
| B | 산출 | CALC | ✅ UI 완료 |
| C | 집행 | EXEC | ✅ UI 완료 |
| F | 실행 | FIELD | ✅ UI 완료 |
| D | 원장 | LEDGER | ✅ UI 완료 |
| I | 무결성 | INTEGRITY | ✅ UI 완료 |

## 3. 기술 스택

### Frontend
- React 18+
- Tailwind CSS + Shadcn/UI
- React Router v6
- Axios

### Backend  
- FastAPI (Python)
- MongoDB
- JWT Authentication
- Emergent Integration (Gemini 3 Flash)

### 배포
- App Preview: https://gvic-platform-1.preview.emergentagent.com
- 로컬 환경: D:\GVIC

## 4. API 엔드포인트

### 인증
- `POST /api/auth/register` - 회원가입
- `POST /api/auth/login` - 로그인
- `GET /api/auth/me` - 현재 사용자 정보
- `POST /api/auth/logout` - 로그아웃

### 시그널 분석
- `POST /api/signal-tracer/ai-analyze` - AI 분석 실행
- `GET /api/gvic-assets` - 자산 목록 조회
- `POST /api/gvic-assets` - 자산 저장
- `DELETE /api/gvic-assets/{id}` - 자산 삭제

### 설정
- `GET/PUT /api/config/sigma` - 시그마 설정
- `GET/PUT /api/config/omega` - 오메가 설정

### 대시보드
- `GET /api/dashboard` - 대시보드 데이터
- `GET /api/dashboard/realstats` - 실시간 통계

## 5. 로컬 환경 설정

### 디렉토리 구조
```
D:\GVIC\
├── backend\
│   ├── server.py
│   ├── auth.py
│   ├── .env
│   └── requirements.txt
├── frontend\
│   ├── src\
│   │   ├── App.js
│   │   └── components\tabs\patent\
│   └── package.json
├── data\db\         (MongoDB 데이터)
├── scripts\
│   ├── start_all.bat
│   └── install_full.bat
└── docs\
```

### 실행 방법
```batch
cd /d D:\GVIC
scripts\start_all.bat
```

## 6. 향후 계획

### P0 (필수)
- [ ] 각 특허 탭 실제 로직 연결
- [ ] 운영자 대시보드 기능 강화 (산업 분류별 자산 축적)

### P1 (중요)
- [ ] 자산 상품화 기능
- [ ] 가치 교환 시스템
- [ ] 보상 분배 로직

### P2 (개선)
- [ ] PDF 리포트 생성
- [ ] 데이터 시각화 강화
- [ ] 성능 최적화

## 7. 테스트 계정
- Email: admin@gvic.com
- Password: password
- Role: super_admin

---
*Last Updated: 2025-02-16*
*Version: 2.0.0*
