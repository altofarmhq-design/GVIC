import streamlit as st
import numpy as np
import json
from pathlib import Path
import sys

# 경로 설정
sys.path.insert(0, str(Path(__file__).parent))

from utils.config_manager import ConfigManager
from utils.progress_tracker import ProgressTracker

# 페이지 설정
st.set_page_config(
    page_title="GVIC 통합 시스템",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 매니저 초기화
@st.cache_resource
def get_config_manager():
    return ConfigManager("config/settings.json")

@st.cache_resource
def get_progress_tracker():
    return ProgressTracker("data/progress_log.json")

config_mgr = get_config_manager()
tracker = get_progress_tracker()

# ============ 사이드바 ============
with st.sidebar:
    st.image("https://via.placeholder.com/150x50?text=GVIC", width=150)
    st.title("🔬 GVIC")
    st.caption("결이론 기반 통합 시스템")
    
    st.divider()
    
    # 수렴 지표 Σ
    sigma = config_mgr.get_sigma()
    st.metric("수렴 지표 Σ", f"{int(sigma[0]*10)}:{int(sigma[1]*10)}:{int(sigma[2]*10)}")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.caption(f"공공\n{sigma[0]*100:.0f}%")
    with col2:
        st.caption(f"생산\n{sigma[1]*100:.0f}%")
    with col3:
        st.caption(f"개인\n{sigma[2]*100:.0f}%")
    
    st.divider()
    
    # 진행 현황 요약
    st.subheader("📊 진행 현황")
    phases = config_mgr.get_phases()
    
    total_progress = sum(p.get('progress', 0) for p in phases.values()) / len(phases)
    st.progress(total_progress / 100)
    st.caption(f"전체 진행률: {total_progress:.0f}%")
    
    st.divider()
    
    # 특허 상태 요약
    st.subheader("📋 특허 상태")
    patents = config_mgr.get_patents()
    
    status_emoji = {
        "pending": "⚪",
        "in_progress": "🟡", 
        "completed": "🟢",
        "error": "🔴"
    }
    
    for pid, patent in patents.items():
        emoji = status_emoji.get(patent.get('status', 'pending'), '⚪')
        st.caption(f"{emoji} {patent['id']}: {patent['name'][:10]}...")

# ============ 메인 영역 ============
st.title("🔬 GVIC 통합 시스템 대시보드")
st.markdown("**6개 특허 기반 결이론(結理論) 통합 플랫폼 개발 워크벤치**")

# 메인 탭
tabs = st.tabs([
    "📈 진행 현황",
    "⚙️ 설정 관리",
    "📑 특허 관리",
    "🏗️ 시스템 구조",
    "🧪 테스트",
    "📝 로그"
])

# ============ TAB 1: 진행 현황 ============
with tabs[0]:
    st.header("📈 프로젝트 진행 현황")
    
    # 단계별 진행률
    phases = config_mgr.get_phases()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("단계별 진행률")
        
        for phase_id, phase in phases.items():
            status = phase.get('status', 'pending')
            progress = phase.get('progress', 0)
            
            status_text = {"pending": "대기", "in_progress": "진행중", "completed": "완료"}
            status_color = {"pending": "gray", "in_progress": "orange", "completed": "green"}
            
            st.markdown(f"**{phase_id}단계: {phase['name']}** - :{status_color.get(status, 'gray')}[{status_text.get(status, '대기')}]")
            st.progress(progress / 100)
            
            # 진행률 조정
            new_progress = st.slider(
                f"{phase_id}단계 진행률",
                0, 100, progress,
                key=f"progress_{phase_id}",
                label_visibility="collapsed"
            )
            
            if new_progress != progress:
                new_status = "completed" if new_progress == 100 else ("in_progress" if new_progress > 0 else "pending")
                config_mgr.update_phase(phase_id, status=new_status, progress=new_progress)
                tracker.add_log(f"{phase_id}단계", "진행률 변경", f"{progress}% → {new_progress}%")
                st.rerun()
            
            st.markdown("---")
    
    with col2:
        st.subheader("전체 현황")
        
        # 통계
        completed = sum(1 for p in phases.values() if p.get('status') == 'completed')
        in_progress = sum(1 for p in phases.values() if p.get('status') == 'in_progress')
        pending = sum(1 for p in phases.values() if p.get('status') == 'pending')
        
        st.metric("완료", f"{completed}/{len(phases)}")
        st.metric("진행중", in_progress)
        st.metric("대기", pending)
        
        # 전체 진행률
        total = sum(p.get('progress', 0) for p in phases.values()) / len(phases)
        st.metric("전체 진행률", f"{total:.1f}%")

# ============ TAB 2: 설정 관리 ============
with tabs[1]:
    st.header("⚙️ 설정 관리")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Σ (시그마) - 수렴 비율")
        st.markdown("결이론의 핵심 배분 비율")
        
        sigma = config_mgr.get_sigma()
        
        v_pub = st.slider("V_pub (공공)", 0.0, 1.0, sigma[0], 0.05, key="sigma_pub")
        v_pro = st.slider("V_pro (생산)", 0.0, 1.0, sigma[1], 0.05, key="sigma_pro")
        v_ind = st.slider("V_ind (개인)", 0.0, 1.0, sigma[2], 0.05, key="sigma_ind")
        
        # 합계 검증
        total = v_pub + v_pro + v_ind
        if abs(total - 1.0) > 0.01:
            st.warning(f"⚠️ 합계가 1.0이 아닙니다: {total:.2f}")
        else:
            st.success(f"✅ 합계: {total:.2f}")
        
        if st.button("Σ 저장", key="save_sigma"):
            if abs(total - 1.0) <= 0.01:
                old_sigma = config_mgr.get_sigma()
                config_mgr.set_sigma([v_pub, v_pro, v_ind])
                tracker.add_log("설정", "Σ 변경", f"{old_sigma} → [{v_pub}, {v_pro}, {v_ind}]")
                st.success("✅ 저장되었습니다!")
                st.rerun()
            else:
                st.error("합계가 1.0이어야 합니다.")
    
    with col2:
        st.subheader("Ω (오메가) - 제약 조건")
        st.markdown("운영 경계 조건")
        
        omega = config_mgr.get_omega()
        
        v_pub_min = st.number_input("V_pub 최소", 0.0, 1.0, omega.get('V_pub_min', 0.2), 0.05)
        v_pub_max = st.number_input("V_pub 최대", 0.0, 1.0, omega.get('V_pub_max', 0.8), 0.05)
        v_ind_max = st.number_input("V_ind 최대", 0.0, 1.0, omega.get('V_ind_max', 0.5), 0.05)
        
        # 제약조건 검증
        st.markdown("**제약 조건 상태:**")
        sigma = config_mgr.get_sigma()
        
        check1 = v_pub_min <= sigma[0] <= v_pub_max
        check2 = sigma[2] <= v_ind_max
        check3 = abs(sum(sigma) - 1.0) <= 0.01
        
        st.write(f"{'✅' if check1 else '❌'} {v_pub_min} ≤ V_pub({sigma[0]}) ≤ {v_pub_max}")
        st.write(f"{'✅' if check2 else '❌'} V_ind({sigma[2]}) ≤ {v_ind_max}")
        st.write(f"{'✅' if check3 else '❌'} Σ = 1.0")
        
        if st.button("Ω 저장", key="save_omega"):
            new_omega = {
                "V_pub_min": v_pub_min,
                "V_pub_max": v_pub_max,
                "V_ind_max": v_ind_max,
                "sum_constraint": 1.0
            }
            config_mgr.set_omega(new_omega)
            tracker.add_log("설정", "Ω 변경", str(new_omega))
            st.success("✅ 저장되었습니다!")
    
    st.divider()
    
    # 설정 이력
    st.subheader("📜 설정 변경 이력")
    
    history = config_mgr.get_history()
    if history:
        selected_history = st.selectbox("이전 설정 불러오기", ["현재"] + history)
        
        if selected_history != "현재":
            if st.button("이 설정으로 복원"):
                old_config = config_mgr.load_history(selected_history)
                if old_config:
                    config_mgr.save(old_config)
                    tracker.add_log("설정", "복원", f"From {selected_history}")
                    st.success("✅ 복원되었습니다!")
                    st.rerun()
    else:
        st.info("변경 이력이 없습니다.")

# ============ TAB 3: 특허 관리 ============
with tabs[2]:
    st.header("📑 특허 관리")
    
    patents = config_mgr.get_patents()
    
    # 특허 카드
    cols = st.columns(3)
    
    for i, (pid, patent) in enumerate(patents.items()):
        with cols[i % 3]:
            status = patent.get('status', 'pending')
            status_emoji = {"pending": "⚪", "in_progress": "🟡", "completed": "🟢", "error": "🔴"}
            status_text = {"pending": "대기", "in_progress": "진행중", "completed": "완료", "error": "오류"}
            
            st.markdown(f"""
            ### {status_emoji.get(status, '⚪')} 특허 {pid}
            **ID:** {patent['id']}  
            **이름:** {patent['name']}  
            **상태:** {status_text.get(status, '대기')}
            """)
            
            new_status = st.selectbox(
                "상태 변경",
                ["pending", "in_progress", "completed", "error"],
                index=["pending", "in_progress", "completed", "error"].index(status),
                key=f"patent_status_{pid}"
            )
            
            if new_status != status:
                config_mgr.update_patent_status(pid, new_status)
                tracker.add_log("특허", f"특허{pid} 상태 변경", f"{status} → {new_status}")
                st.rerun()
            
            st.markdown("---")
    
    # 특허 파일 연결
    st.subheader("📁 특허 문서 연결")
    
    patent_dir = Path("../patents")
    if patent_dir.exists():
        patent_files = list(patent_dir.glob("*.md"))
        st.success(f"✅ {len(patent_files)}개 특허 문서 발견")
        
        for pf in patent_files:
            st.caption(f"📄 {pf.name}")
    else:
        st.warning("⚠️ patents 폴더를 찾을 수 없습니다.")
        st.info("특허 문서 경로: /app/patents/")

# ============ TAB 4: 시스템 구조 ============
with tabs[3]:
    st.header("🏗️ 시스템 구조")
    
    st.markdown("""
    ## GVIC 통합 시스템 아키텍처
    
    ```
    ┌─────────────────────────────────────────────────────────────────────┐
    │                      GVIC 통합 플랫폼                                │
    ├─────────────────────────────────────────────────────────────────────┤
    │                                                                     │
    │  ┌─────────────────────────────────────────────────────────────┐   │
    │  │ [입력 계층] 특허 6: 다중 도메인 통합 인터페이스              │   │
    │  │   • 도메인 어댑터 • 시맨틱 매핑 • 라우팅 엔진               │   │
    │  └─────────────────────────────────┬───────────────────────────┘   │
    │                                    │                               │
    │                                    ▼                               │
    │  ┌─────────────────────────────────────────────────────────────┐   │
    │  │ [코어 엔진] 특허 2: 신호 자산화 플랫폼                       │   │
    │  │   • 신호 수집 → 정규화 → 가치 산출 → 자산 생성              │   │
    │  └─────────────────────────────────┬───────────────────────────┘   │
    │                                    │                               │
    │       ┌────────────────────────────┼────────────────────────┐      │
    │       │                            │                        │      │
    │       ▼                            ▼                        ▼      │
    │  ┌───────────┐              ┌───────────┐              ┌───────────┐
    │  │ 특허 3    │              │ 특허 4    │              │ 특허 5    │
    │  │ 재귀적    │              │ 비적합    │              │ 가중      │
    │  │ 모듈화    │              │ 데이터    │              │ 분배      │
    │  └───────────┘              └───────────┘              └───────────┘
    │       │                            │                        │      │
    │       └────────────────────────────┼────────────────────────┘      │
    │                                    │                               │
    │                                    ▼                               │
    │  ┌─────────────────────────────────────────────────────────────┐   │
    │  │ [제어 계층] 특허 1: 전역 수렴 제어 시스템                    │   │
    │  │   • 운영 경계 조건 (Ω) • 파라미터 동기화 • 자동 복구        │   │
    │  │   • 수렴 지표 Σ = 5:3:2 (공공:생산:개인)                    │   │
    │  └─────────────────────────────────────────────────────────────┘   │
    │                                                                     │
    └─────────────────────────────────────────────────────────────────────┘
    ```
    """)
    
    # 특허별 역할
    st.subheader("📋 특허별 역할")
    
    patent_roles = {
        "특허 1 (H)": {"역할": "전역 수렴 제어", "계층": "제어", "핵심": "Σ, Ω 관리"},
        "특허 2 (AEG)": {"역할": "신호 자산화", "계층": "코어 엔진", "핵심": "Signal → Asset 변환"},
        "특허 3 (BC)": {"역할": "재귀적 모듈화", "계층": "처리", "핵심": "파이프라인 조합"},
        "특허 4 (DI)": {"역할": "비적합 데이터", "계층": "처리", "핵심": "예외 처리, 오류 가치화"},
        "특허 5 (F)": {"역할": "가중 분배", "계층": "처리", "핵심": "자원 배분 최적화"},
        "특허 6 (J)": {"역할": "다중 도메인 통합", "계층": "입력", "핵심": "어댑터, 라우팅"},
    }
    
    for name, info in patent_roles.items():
        with st.expander(name):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**역할:** {info['역할']}")
            with col2:
                st.write(f"**계층:** {info['계층']}")
            with col3:
                st.write(f"**핵심:** {info['핵심']}")

# ============ TAB 5: 테스트 ============
with tabs[4]:
    st.header("🧪 테스트 시나리오")
    
    st.subheader("Σ 수렴 테스트")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 입력 벡터")
        
        test_type = st.radio(
            "테스트 유형",
            ["정상 (5:3:2)", "경계 위반", "극단값", "직접 입력"]
        )
        
        if test_type == "정상 (5:3:2)":
            test_input = [0.5, 0.3, 0.2]
        elif test_type == "경계 위반":
            test_input = [0.7, 0.2, 0.1]
        elif test_type == "극단값":
            test_input = [0.9, 0.05, 0.05]
        else:
            t_pub = st.number_input("V_pub", 0.0, 1.0, 0.5, 0.05)
            t_pro = st.number_input("V_pro", 0.0, 1.0, 0.3, 0.05)
            t_ind = st.number_input("V_ind", 0.0, 1.0, 0.2, 0.05)
            test_input = [t_pub, t_pro, t_ind]
        
        st.write(f"**입력:** {test_input}")
        st.write(f"**합계:** {sum(test_input):.2f}")
    
    with col2:
        st.markdown("### Ω 검증 결과")
        
        omega = config_mgr.get_omega()
        sigma = config_mgr.get_sigma()
        
        # 검증
        checks = {
            f"V_pub ≥ {omega.get('V_pub_min', 0.2)}": test_input[0] >= omega.get('V_pub_min', 0.2),
            f"V_pub ≤ {omega.get('V_pub_max', 0.8)}": test_input[0] <= omega.get('V_pub_max', 0.8),
            f"V_ind ≤ {omega.get('V_ind_max', 0.5)}": test_input[2] <= omega.get('V_ind_max', 0.5),
            "Σ = 1.0": abs(sum(test_input) - 1.0) <= 0.01
        }
        
        all_pass = all(checks.values())
        
        for check, passed in checks.items():
            st.write(f"{'✅' if passed else '❌'} {check}")
        
        st.divider()
        
        if all_pass:
            st.success("✅ 모든 조건 통과!")
        else:
            st.error("❌ 조건 위반 - 수렴 변환 필요")
            
            # 수렴 변환 시뮬레이션
            if st.button("수렴 변환 시뮬레이션"):
                alpha = 0.5  # 수렴 강도
                R = np.array(sigma)  # 기본 수렴 비율
                V_in = np.array(test_input)
                
                V_conv = alpha * V_in + (1 - alpha) * R
                V_conv = V_conv / V_conv.sum()  # 정규화
                
                st.write("**수렴 변환 결과:**")
                st.write(f"입력: {test_input}")
                st.write(f"출력: [{V_conv[0]:.3f}, {V_conv[1]:.3f}, {V_conv[2]:.3f}]")

# ============ TAB 6: 로그 ============
with tabs[5]:
    st.header("📝 활동 로그")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        logs = tracker.get_recent_logs(30)
        
        if logs:
            for log in logs:
                timestamp = log.get('timestamp', '')[:19].replace('T', ' ')
                phase = log.get('phase', '')
                action = log.get('action', '')
                details = log.get('details', '')
                
                st.markdown(f"""
                **[{timestamp}]** `{phase}` - {action}  
                {details if details else ''}
                """)
                st.markdown("---")
        else:
            st.info("로그가 없습니다.")
    
    with col2:
        st.subheader("로그 관리")
        
        if st.button("로그 새로고침"):
            st.rerun()
        
        if st.button("로그 초기화", type="secondary"):
            if st.checkbox("정말 초기화하시겠습니까?"):
                tracker.clear_logs()
                st.success("로그가 초기화되었습니다.")
                st.rerun()

# ============ 푸터 ============
st.divider()
col1, col2, col3 = st.columns(3)
with col1:
    st.caption("🔬 GVIC 통합 시스템 v1.0")
with col2:
    st.caption("결이론(結理論) 기반")
with col3:
    st.caption("6개 특허 통합 플랫폼")
