"""
GVIC 특허 간 유기적 플로우 PDF 생성 스크립트
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import os

# PDF 파일 경로
output_path = "/app/frontend/public/GVIC_Patent_Flow.pdf"

# 문서 생성
doc = SimpleDocTemplate(
    output_path,
    pagesize=A4,
    rightMargin=2*cm,
    leftMargin=2*cm,
    topMargin=2*cm,
    bottomMargin=2*cm
)

# 스타일 정의
styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    'CustomTitle',
    parent=styles['Heading1'],
    fontSize=24,
    spaceAfter=30,
    alignment=TA_CENTER,
    textColor=colors.HexColor('#1e3a5f')
)

heading_style = ParagraphStyle(
    'CustomHeading',
    parent=styles['Heading2'],
    fontSize=16,
    spaceBefore=20,
    spaceAfter=10,
    textColor=colors.HexColor('#2c5282')
)

subheading_style = ParagraphStyle(
    'CustomSubheading',
    parent=styles['Heading3'],
    fontSize=12,
    spaceBefore=15,
    spaceAfter=8,
    textColor=colors.HexColor('#4a5568')
)

body_style = ParagraphStyle(
    'CustomBody',
    parent=styles['Normal'],
    fontSize=10,
    spaceAfter=8,
    leading=14
)

code_style = ParagraphStyle(
    'CodeStyle',
    parent=styles['Code'],
    fontSize=9,
    backColor=colors.HexColor('#f7fafc'),
    borderColor=colors.HexColor('#e2e8f0'),
    borderWidth=1,
    borderPadding=5,
    spaceAfter=10
)

# 콘텐츠 구성
content = []

# 제목
content.append(Paragraph("GVIC Patent Flow Architecture", title_style))
content.append(Paragraph("Global Value Integration & Convergence System", styles['Normal']))
content.append(Spacer(1, 20))

# 1. 시스템 개요
content.append(Paragraph("1. System Overview", heading_style))
content.append(Paragraph(
    "GVIC is an integrated system based on 12 patents that systematically defines, analyzes, "
    "and assetizes the types, sentiments, and relationships of existing signals for decision-making support.",
    body_style
))
content.append(Spacer(1, 10))

# 결이론 테이블
content.append(Paragraph("Gyeoliron (5:3:2 Ratio)", subheading_style))
gyeoliron_data = [
    ['Domain', 'Ratio', 'Meaning'],
    ['Public', '50%', 'Social Value'],
    ['Production', '30%', 'Business Value'],
    ['Individual', '20%', 'Personal Value'],
]
gyeoliron_table = Table(gyeoliron_data, colWidths=[4*cm, 3*cm, 6*cm])
gyeoliron_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('FONTSIZE', (0, 0), (-1, 0), 11),
    ('FONTSIZE', (0, 1), (-1, -1), 10),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
    ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f7fafc')),
    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
]))
content.append(gyeoliron_table)
content.append(Spacer(1, 15))

content.append(Paragraph("Mathematical Expression: Sigma = [0.5, 0.3, 0.2]^T", code_style))

# 2. 특허 목록
content.append(Paragraph("2. Patent List (12 Patents)", heading_style))

patent_data = [
    ['Patent', 'Node', 'Core Function'],
    ['H', 'CORE', 'Global Convergence Control (Gyeoliron 5:3:2)'],
    ['A', 'GATE', 'Data Recognition, Conformity Verification'],
    ['E', 'SHIELD', 'Toxic Data Quarantine'],
    ['G', 'REFINE', 'Value Refinement, Noise Removal'],
    ['B', 'CALC', 'Value Calculation, 5:3:2 Distribution'],
    ['C', 'EXEC', 'Resource Execution, Allocation'],
    ['F', 'FIELD', 'Physical Layer Execution, Entropy Control'],
    ['D', 'LEDGER', 'Trajectory Storage, History Preservation'],
    ['I', 'INTEGRITY', 'Integrity Proof, Hash Chain'],
    ['J', 'PLATFORM', 'External API Integration'],
    ['LL', 'INTELLIGENCE', 'Contribution Quantification'],
]

patent_table = Table(patent_data, colWidths=[2*cm, 3*cm, 8*cm])
patent_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ('ALIGN', (0, 0), (1, -1), 'CENTER'),
    ('ALIGN', (2, 0), (2, -1), 'LEFT'),
    ('FONTSIZE', (0, 0), (-1, 0), 10),
    ('FONTSIZE', (0, 1), (-1, -1), 9),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
    ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f7fafc')),
    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f7fafc'), colors.white]),
]))
content.append(patent_table)

# 페이지 나누기
content.append(PageBreak())

# 3. 시스템 플로우
content.append(Paragraph("3. System Flow Architecture", heading_style))
content.append(Spacer(1, 10))

# 플로우 다이어그램 (텍스트 버전)
flow_text = """
[External Signal Input]
        |
        v
+-------------------+
| LL: INTELLIGENCE  | <- Unstructured Contribution Quantification
+--------+----------+
         |  C_i (Contribution Score)
         v
+-------------------+
|   J: PLATFORM     | <- External API Integration, Normalization
+--------+----------+
         |  V_proj (Normalized Vector)
         v
+===================+
|     H: CORE       | <- Global Convergence Control
|                   |    Sigma = [0.5, 0.3, 0.2]^T (Gyeoliron)
+===================+
         |  Sigma Broadcast to All Nodes
         v
+-------------------+
|     A: GATE       | <- Data Recognition, Conformity Check
+--------+----------+
         |
    +----+----+
    |         |
  Conform   Non-Conform
    |         |
    |         v
    |    +-------------------+
    |    |    E: SHIELD      | <- Toxic Data Quarantine
    |    +--------+----------+
    |             |
    |        +----+----+
    |        |         |
    |      Toxic     Pass
    |        |         |
    |    [Isolate]     |
    |                  |
    +--------+---------+
             |
             v
+-------------------+
|    G: REFINE      | <- Value Refinement
+--------+----------+
         |  V_refined
         v
+-------------------+
|     B: CALC       | <- Value Calculation
+--------+----------+
         |  R_alloc = V_score x [0.5, 0.3, 0.2]^T
         v
+-------------------+
|     C: EXEC       | <- Resource Execution
+--------+----------+
         |  E_res (Execution Resources)
         v
+-------------------+
|     F: FIELD      | <- Physical Layer Execution
+--------+----------+
         |
    +----+----+
    |         |
    v         v
+-------+  +------------+
|D:LEDGER|  |I:INTEGRITY |
+-------+  +-----+------+
                 |
                 | V_proof (Integrity Proof)
                 v
         [Feedback to H: CORE]
"""

# 플로우를 여러 줄로 분할하여 표시
flow_lines = flow_text.strip().split('\n')
for line in flow_lines:
    if line.strip():
        content.append(Paragraph(line.replace(' ', '&nbsp;'), ParagraphStyle(
            'FlowLine',
            parent=styles['Code'],
            fontSize=8,
            leading=10,
            fontName='Courier'
        )))

content.append(PageBreak())

# 4. 입출력 관계
content.append(Paragraph("4. Input/Output Relationships", heading_style))

io_data = [
    ['Patent', 'Node', 'Input (From)', 'Output (To)'],
    ['LL', 'INTELLIGENCE', 'External Unstructured Data', 'C_i -> J'],
    ['J', 'PLATFORM', 'External API, LL Output', 'V_proj -> H'],
    ['H', 'CORE', 'J Output, All Node Status', 'Sigma -> All Nodes'],
    ['A', 'GATE', 'External Signal, Sigma', 'Conform/Non-Conform -> E or G'],
    ['E', 'SHIELD', 'Non-Conform Data, Sigma', 'Isolate or Pass -> G'],
    ['G', 'REFINE', 'Passed Data, Sigma', 'V_refined -> B'],
    ['B', 'CALC', 'G Output, Sigma', 'R_alloc -> C'],
    ['C', 'EXEC', 'B Output, Sigma', 'E_res -> F'],
    ['F', 'FIELD', 'C Output, Physical State', 'Execution Result -> D, I'],
    ['D', 'LEDGER', 'F Output, All History', 'H(T) -> I'],
    ['I', 'INTEGRITY', 'D Output, Sigma, All Data', 'V_proof -> H (Feedback)'],
]

io_table = Table(io_data, colWidths=[1.5*cm, 2.5*cm, 4.5*cm, 4.5*cm])
io_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('FONTSIZE', (0, 0), (-1, 0), 9),
    ('FONTSIZE', (0, 1), (-1, -1), 8),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
    ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f7fafc')),
    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f7fafc'), colors.white]),
]))
content.append(io_table)

content.append(Spacer(1, 20))

# 5. 핵심 수학 모델
content.append(Paragraph("5. Core Mathematical Models", heading_style))

math_data = [
    ['Patent', 'Formula', 'Description'],
    ['H', 'Sigma = [0.5, 0.3, 0.2]^T', 'Gyeoliron Convergence Index'],
    ['A', 'S_idx = (V_i . Sigma) / (||V_i|| x ||Sigma||)', 'Conformity Index'],
    ['E', 'Delta_S = -Sum P(x_i|Sigma) log P(x_i|Sigma)', 'Entropy Change (Toxic Detection)'],
    ['G', 'D_idx = Integral|V_cand . Sigma| dt - sigma_noise', 'Value Discrimination Index'],
    ['B', 'R_alloc = V_score x [0.5, 0.3, 0.2]^T', 'Allocation Vector'],
    ['C', 'E_res = beta x (M_conv x R_alloc)', 'Execution Resource'],
    ['F', 'E_i(t) = Integral(R_alloc . F_i - kappa x dS_i/dt) dt', 'Physical Execution'],
    ['D', 'H(T) = Sum[S(t) . G + L(V_proof(t))]', 'Trajectory Stacking'],
    ['I', 'V_proof(t) = Hash(Sigma(t) XOR E(t) + V_proof(t-1))', 'Integrity Proof'],
    ['LL', 'C_i = H(D_un) x cos(theta_ref)', 'Contribution Quantification'],
]

math_table = Table(math_data, colWidths=[1.5*cm, 6*cm, 5.5*cm])
math_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ('ALIGN', (0, 0), (0, -1), 'CENTER'),
    ('ALIGN', (1, 0), (-1, -1), 'LEFT'),
    ('FONTSIZE', (0, 0), (-1, 0), 9),
    ('FONTSIZE', (0, 1), (-1, -1), 8),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
    ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f7fafc')),
    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f7fafc'), colors.white]),
]))
content.append(math_table)

content.append(PageBreak())

# 6. 시스템 생존 임계 조건
content.append(Paragraph("6. System Survival Threshold (Omega)", heading_style))

omega_data = [
    ['Condition', 'Formula', 'Meaning'],
    ['1', '0.2 <= V_pub <= 0.8', 'Public Infrastructure Maintenance'],
    ['2', 'V_ind <= 0.5', 'Individual Occupation Limit'],
    ['3', 'Sum V_i = 1.0', 'Value Conservation Normalization'],
]

omega_table = Table(omega_data, colWidths=[2*cm, 5*cm, 6*cm])
omega_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#c53030')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('FONTSIZE', (0, 0), (-1, 0), 10),
    ('FONTSIZE', (0, 1), (-1, -1), 9),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
    ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#fff5f5')),
    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#feb2b2')),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
]))
content.append(omega_table)

content.append(Spacer(1, 20))

# 7. 피드백 루프
content.append(Paragraph("7. Feedback Loops", heading_style))

feedback_data = [
    ['Path', 'Data', 'Purpose'],
    ['I -> H', 'V_proof (Integrity Proof)', 'System Integrity Monitoring'],
    ['F -> H', 'Entropy Information', 'Physical State Feedback'],
    ['E -> H', 'Toxic Detection Info', 'Security Status Feedback'],
    ['D -> H', 'Historical Trajectory', 'Convergence Analysis'],
]

feedback_table = Table(feedback_data, colWidths=[3*cm, 5*cm, 5*cm])
feedback_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2f855a')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('FONTSIZE', (0, 0), (-1, 0), 10),
    ('FONTSIZE', (0, 1), (-1, -1), 9),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
    ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f0fff4')),
    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#9ae6b4')),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
]))
content.append(feedback_table)

content.append(Spacer(1, 30))

# 8. 문서 정보
content.append(Paragraph("8. Document Information", heading_style))
content.append(Paragraph("Version: 1.0.0", body_style))
content.append(Paragraph("Date: 2026-02-15", body_style))
content.append(Paragraph("System: GVIC (Global Value Integration & Convergence)", body_style))

# PDF 빌드
doc.build(content)

print(f"PDF generated successfully: {output_path}")
