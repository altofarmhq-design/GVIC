"""
GVIC Patents Module - 14개 특허 기반 모듈 패키지

특허 구조:
- J: PLATFORM (입력)
- LL: INTELLIGENCE (의도)
- H: CORE (코어)
- A: GATE (게이트)
- E: SHIELD (방어막)
- G: REFINE (정제)
- B: CALC (산출)
- C: EXEC (집행)
- F: FIELD (실행)
- D: LEDGER (원장)
- I: INTEGRITY (무결성)
"""

from .j_platform import router as j_platform_router
from .ll_intelligence import router as ll_intelligence_router
from .h_core import router as h_core_router
from .a_gate import router as a_gate_router
from .e_shield import router as e_shield_router
from .g_refine import router as g_refine_router
from .b_calc import router as b_calc_router
from .c_exec import router as c_exec_router
from .f_field import router as f_field_router
from .d_ledger import router as d_ledger_router
from .i_integrity import router as i_integrity_router

__all__ = [
    "j_platform_router",
    "ll_intelligence_router", 
    "h_core_router",
    "a_gate_router",
    "e_shield_router",
    "g_refine_router",
    "b_calc_router",
    "c_exec_router",
    "f_field_router",
    "d_ledger_router",
    "i_integrity_router"
]
