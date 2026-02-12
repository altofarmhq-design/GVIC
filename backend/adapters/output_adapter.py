"""
GVIC Output Adapter - 출력부 표준화 모듈
========================================
GVIC 엔진의 분석 결과를 다양한 형태로 출력

출력 유형:
- PDF 리포트 (요인별/유형별 모듈화)
- Excel 데이터 내보내기
- JSON API 응답
- 외부 시스템 전송 (Webhook, API)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime
import json
import os
import logging

logger = logging.getLogger(__name__)


class OutputType(Enum):
    """출력 유형"""
    PDF_REPORT = "pdf_report"
    EXCEL_EXPORT = "excel_export"
    JSON_API = "json_api"
    WEBHOOK = "webhook"


@dataclass
class AnalysisFactor:
    """분석 요인 (긍정/부정 요인 모듈)"""
    factor_id: str
    factor_type: str           # "positive" or "negative"
    category: str              # 요인 카테고리 (효과, 포장, 가격 등)
    description: str           # 요인 설명
    count: int                 # 발생 건수
    ratio: float               # 비율
    sample_contents: List[str] # 샘플 내용
    keywords: List[str]        # 관련 키워드
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "factor_id": self.factor_id,
            "factor_type": self.factor_type,
            "category": self.category,
            "description": self.description,
            "count": self.count,
            "ratio": self.ratio,
            "sample_contents": self.sample_contents,
            "keywords": self.keywords
        }


@dataclass
class ModularAnalysisResult:
    """모듈화된 분석 결과"""
    result_id: str
    analysis_type: str           # 분석 유형
    created_at: str
    
    # 입력 데이터 요약
    input_summary: Dict[str, Any]
    
    # 감성 분석 결과
    sentiment_distribution: Dict[str, Any]
    
    # 긍정 요인 모듈
    positive_factors: List[AnalysisFactor]
    
    # 부정 요인 모듈  
    negative_factors: List[AnalysisFactor]
    
    # GVIC 엔진 처리 결과
    gvic_results: Dict[str, Any]
    
    # 종합 인사이트
    insights: List[str]
    
    # 권장 조치
    recommendations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "result_id": self.result_id,
            "analysis_type": self.analysis_type,
            "created_at": self.created_at,
            "input_summary": self.input_summary,
            "sentiment_distribution": self.sentiment_distribution,
            "positive_factors": [f.to_dict() for f in self.positive_factors],
            "negative_factors": [f.to_dict() for f in self.negative_factors],
            "gvic_results": self.gvic_results,
            "insights": self.insights,
            "recommendations": self.recommendations
        }


class OutputAdapter(ABC):
    """출력 어댑터 추상 클래스"""
    
    @abstractmethod
    def format(self, result: ModularAnalysisResult) -> Any:
        """결과 포맷팅"""
        pass
    
    @abstractmethod
    def export(self, formatted_data: Any, destination: str) -> str:
        """결과 내보내기"""
        pass


class PDFReportAdapter(OutputAdapter):
    """
    PDF 리포트 출력 어댑터
    - 긍정/부정 요인을 모듈화하여 시각적 리포트 생성
    """
    
    def __init__(self):
        self.output_type = OutputType.PDF_REPORT
        
    def format(self, result: ModularAnalysisResult) -> Dict[str, Any]:
        """PDF용 데이터 구조화"""
        return {
            "title": f"GVIC 분석 리포트 - {result.analysis_type}",
            "generated_at": datetime.now().isoformat(),
            "sections": [
                {
                    "id": "summary",
                    "title": "1. 분석 요약",
                    "content": result.input_summary
                },
                {
                    "id": "sentiment",
                    "title": "2. 감성 분포",
                    "content": result.sentiment_distribution
                },
                {
                    "id": "positive_factors",
                    "title": "3. 긍정 평가 요인",
                    "content": [f.to_dict() for f in result.positive_factors]
                },
                {
                    "id": "negative_factors",
                    "title": "4. 부정 평가 요인",
                    "content": [f.to_dict() for f in result.negative_factors]
                },
                {
                    "id": "gvic_analysis",
                    "title": "5. GVIC 엔진 분석 결과",
                    "content": result.gvic_results
                },
                {
                    "id": "insights",
                    "title": "6. 종합 인사이트",
                    "content": result.insights
                },
                {
                    "id": "recommendations",
                    "title": "7. 권장 조치 사항",
                    "content": result.recommendations
                }
            ]
        }
    
    def export(self, formatted_data: Dict[str, Any], destination: str) -> str:
        """PDF 파일 생성"""
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
        from reportlab.lib.units import cm
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        
        # PDF 생성
        doc = SimpleDocTemplate(
            destination, 
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
            textColor=colors.HexColor('#1e293b')
        )
        heading_style = ParagraphStyle(
            'CustomHeading', 
            parent=styles['Heading2'], 
            fontSize=16, 
            spaceAfter=12, 
            spaceBefore=20,
            textColor=colors.HexColor('#334155')
        )
        subheading_style = ParagraphStyle(
            'CustomSubheading', 
            parent=styles['Heading3'], 
            fontSize=13, 
            spaceAfter=8, 
            textColor=colors.HexColor('#475569')
        )
        normal_style = ParagraphStyle(
            'CustomNormal', 
            parent=styles['Normal'], 
            fontSize=11, 
            spaceAfter=8
        )
        positive_style = ParagraphStyle(
            'PositiveStyle', 
            parent=styles['Normal'], 
            fontSize=11, 
            textColor=colors.HexColor('#16a34a'),
            spaceAfter=6
        )
        negative_style = ParagraphStyle(
            'NegativeStyle', 
            parent=styles['Normal'], 
            fontSize=11, 
            textColor=colors.HexColor('#dc2626'),
            spaceAfter=6
        )
        
        elements = []
        
        # 제목
        elements.append(Paragraph(formatted_data["title"], title_style))
        elements.append(Paragraph(f"Generated: {formatted_data['generated_at']}", normal_style))
        elements.append(Spacer(1, 20))
        
        # 각 섹션 처리
        for section in formatted_data["sections"]:
            elements.append(Paragraph(section["title"], heading_style))
            
            content = section["content"]
            
            if section["id"] == "summary":
                # 요약 테이블
                summary_data = [
                    ["항목", "값"],
                    ["총 데이터 수", str(content.get("total_records", 0))],
                    ["평균 평점", f"{content.get('avg_rating', 0):.2f}"],
                    ["데이터 소스", content.get("source", "N/A")],
                    ["분석 일시", content.get("analysis_date", "N/A")]
                ]
                table = Table(summary_data, colWidths=[6*cm, 10*cm])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTSIZE', (0, 0), (-1, 0), 11),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0'))
                ]))
                elements.append(table)
                
            elif section["id"] == "sentiment":
                # 감성 분포
                dist = content
                sent_data = [
                    ["감성", "건수", "비율"],
                    ["긍정 (Positive)", str(dist.get("positive", {}).get("count", 0)), 
                     f"{dist.get('positive', {}).get('ratio', 0)*100:.1f}%"],
                    ["중립 (Neutral)", str(dist.get("neutral", {}).get("count", 0)), 
                     f"{dist.get('neutral', {}).get('ratio', 0)*100:.1f}%"],
                    ["부정 (Negative)", str(dist.get("negative", {}).get("count", 0)), 
                     f"{dist.get('negative', {}).get('ratio', 0)*100:.1f}%"]
                ]
                table = Table(sent_data, colWidths=[6*cm, 5*cm, 5*cm])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6366f1')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#dcfce7')),
                    ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#fef3c7')),
                    ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor('#fee2e2')),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0'))
                ]))
                elements.append(table)
                
            elif section["id"] == "positive_factors":
                # 긍정 요인 모듈
                if content:
                    for factor in content:
                        elements.append(Paragraph(
                            f"<b>[{factor['category']}]</b> {factor['description']} - {factor['count']}건 ({factor['ratio']*100:.1f}%)", 
                            positive_style
                        ))
                        if factor.get('keywords'):
                            elements.append(Paragraph(
                                f"  키워드: {', '.join(factor['keywords'][:5])}", 
                                normal_style
                            ))
                        if factor.get('sample_contents'):
                            elements.append(Paragraph(
                                f"  대표 내용: \"{factor['sample_contents'][0][:50]}...\"" if len(factor['sample_contents'][0]) > 50 else f"  대표 내용: \"{factor['sample_contents'][0]}\"", 
                                normal_style
                            ))
                        elements.append(Spacer(1, 8))
                else:
                    elements.append(Paragraph("긍정 요인이 없습니다.", normal_style))
                    
            elif section["id"] == "negative_factors":
                # 부정 요인 모듈
                if content:
                    for factor in content:
                        elements.append(Paragraph(
                            f"<b>[{factor['category']}]</b> {factor['description']} - {factor['count']}건 ({factor['ratio']*100:.1f}%)", 
                            negative_style
                        ))
                        if factor.get('keywords'):
                            elements.append(Paragraph(
                                f"  키워드: {', '.join(factor['keywords'][:5])}", 
                                normal_style
                            ))
                        if factor.get('sample_contents'):
                            elements.append(Paragraph(
                                f"  대표 내용: \"{factor['sample_contents'][0][:50]}...\"" if len(factor['sample_contents'][0]) > 50 else f"  대표 내용: \"{factor['sample_contents'][0]}\"", 
                                normal_style
                            ))
                        elements.append(Spacer(1, 8))
                else:
                    elements.append(Paragraph("부정 요인이 없습니다.", normal_style))
                    
            elif section["id"] == "gvic_analysis":
                # GVIC 분석 결과
                gvic = content
                
                # 수렴 제어 결과
                if "convergence" in gvic:
                    elements.append(Paragraph("5.1 수렴 제어 (특허 1)", subheading_style))
                    conv = gvic["convergence"]
                    elements.append(Paragraph(f"상태: {conv.get('status', 'N/A')}", normal_style))
                    elements.append(Paragraph(f"균형 지수: {conv.get('balance_index', 0):.4f}", normal_style))
                
                # 신호 처리 결과
                if "signal" in gvic:
                    elements.append(Paragraph("5.2 신호 전처리 (특허 2)", subheading_style))
                    sig = gvic["signal"]
                    elements.append(Paragraph(f"처리: {sig.get('total_processed', 0)}건, 정합률: {sig.get('conformance_rate', 0)*100:.1f}%", normal_style))
                
                # 분배 결과
                if "distribution" in gvic:
                    elements.append(Paragraph("5.3 가중 분배 (특허 6)", subheading_style))
                    dist = gvic["distribution"]
                    elements.append(Paragraph(f"공공: {dist.get('public', 0):,.0f}원 | 생산: {dist.get('productive', 0):,.0f}원 | 개인: {dist.get('individual', 0):,.0f}원", normal_style))
                    elements.append(Paragraph(f"공정성 지수: {gvic.get('fairness_index', 0):.4f}", normal_style))
                    
            elif section["id"] == "insights":
                # 인사이트
                if content:
                    for i, insight in enumerate(content, 1):
                        elements.append(Paragraph(f"{i}. {insight}", normal_style))
                else:
                    elements.append(Paragraph("생성된 인사이트가 없습니다.", normal_style))
                    
            elif section["id"] == "recommendations":
                # 권장 사항
                if content:
                    for i, rec in enumerate(content, 1):
                        elements.append(Paragraph(f"{i}. {rec}", normal_style))
                else:
                    elements.append(Paragraph("권장 사항이 없습니다.", normal_style))
            
            elements.append(Spacer(1, 15))
        
        # PDF 빌드
        doc.build(elements)
        logger.info(f"PDF report generated: {destination}")
        
        return destination


class FactorExtractor:
    """
    요인 추출기
    - 리뷰 내용에서 긍정/부정 요인을 추출하고 분류
    """
    
    # 긍정 요인 키워드 매핑
    POSITIVE_KEYWORDS = {
        "효과": ["효과", "좋아", "도움", "개선", "완화", "나아", "좋은"],
        "포장": ["포장", "개별", "휴대", "꼼꼼", "위생"],
        "가격": ["가격", "합리", "저렴", "가성비", "할인"],
        "배송": ["배송", "빠르", "빨리", "도착"],
        "재구매": ["재구매", "또", "다시", "계속"],
        "맛/향": ["맛", "먹기", "냄새", "향"],
        "크기": ["크기", "사이즈", "적당", "작은"]
    }
    
    # 부정 요인 키워드 매핑
    NEGATIVE_KEYWORDS = {
        "효과없음": ["효과없", "효과가 없", "안 들", "소용없"],
        "가격비쌈": ["비싸", "비쌈", "가격이 높"],
        "배송지연": ["늦", "지연", "오래"],
        "품질불만": ["불량", "손상", "파손", "깨진"],
        "맛/향 불만": ["맛없", "냄새가 나", "역겨"],
        "크기 불만": ["커요", "크다", "작아요", "작다"]
    }
    
    def extract_factors(self, records: List[Dict[str, Any]]) -> tuple:
        """긍정/부정 요인 추출"""
        positive_factors = {}
        negative_factors = {}
        
        total_positive = 0
        total_negative = 0
        
        for record in records:
            content = record.get("content", "")
            rating = record.get("primary_value", record.get("rating", 3))
            
            # 정규화된 값이 아닌 경우 처리
            if rating > 5:
                rating = rating / 20  # 0-100 -> 0-5 스케일
            
            # 긍정 리뷰 (평점 4점 이상)
            if rating >= 4:
                total_positive += 1
                for category, keywords in self.POSITIVE_KEYWORDS.items():
                    for keyword in keywords:
                        if keyword in content:
                            if category not in positive_factors:
                                positive_factors[category] = {
                                    "count": 0,
                                    "samples": [],
                                    "keywords_found": set()
                                }
                            positive_factors[category]["count"] += 1
                            positive_factors[category]["keywords_found"].add(keyword)
                            if len(positive_factors[category]["samples"]) < 3:
                                positive_factors[category]["samples"].append(content)
                            break
            
            # 부정 리뷰 (평점 2점 이하)
            elif rating <= 2:
                total_negative += 1
                for category, keywords in self.NEGATIVE_KEYWORDS.items():
                    for keyword in keywords:
                        if keyword in content:
                            if category not in negative_factors:
                                negative_factors[category] = {
                                    "count": 0,
                                    "samples": [],
                                    "keywords_found": set()
                                }
                            negative_factors[category]["count"] += 1
                            negative_factors[category]["keywords_found"].add(keyword)
                            if len(negative_factors[category]["samples"]) < 3:
                                negative_factors[category]["samples"].append(content)
                            break
        
        # AnalysisFactor 객체로 변환
        pos_factors = []
        for category, data in sorted(positive_factors.items(), key=lambda x: x[1]["count"], reverse=True):
            pos_factors.append(AnalysisFactor(
                factor_id=f"POS_{category}",
                factor_type="positive",
                category=category,
                description=f"{category} 관련 긍정 평가",
                count=data["count"],
                ratio=data["count"] / total_positive if total_positive > 0 else 0,
                sample_contents=data["samples"],
                keywords=list(data["keywords_found"])
            ))
        
        neg_factors = []
        for category, data in sorted(negative_factors.items(), key=lambda x: x[1]["count"], reverse=True):
            neg_factors.append(AnalysisFactor(
                factor_id=f"NEG_{category}",
                factor_type="negative",
                category=category,
                description=f"{category} 관련 부정 평가",
                count=data["count"],
                ratio=data["count"] / total_negative if total_negative > 0 else 0,
                sample_contents=data["samples"],
                keywords=list(data["keywords_found"])
            ))
        
        return pos_factors, neg_factors


class OutputAdapterFactory:
    """출력 어댑터 팩토리"""
    
    _adapters = {
        OutputType.PDF_REPORT: PDFReportAdapter,
    }
    
    @classmethod
    def get_adapter(cls, output_type: OutputType) -> OutputAdapter:
        """출력 유형에 맞는 어댑터 반환"""
        adapter_class = cls._adapters.get(output_type)
        if not adapter_class:
            raise ValueError(f"No adapter for output type: {output_type}")
        return adapter_class()


if __name__ == "__main__":
    # 테스트
    extractor = FactorExtractor()
    
    sample_records = [
        {"content": "효과가 좋아요 재구매했어요", "rating": 5},
        {"content": "포장이 꼼꼼해요 배송도 빠르네요", "rating": 5},
        {"content": "효과 없어요 비싸기만 하고", "rating": 1},
    ]
    
    pos, neg = extractor.extract_factors(sample_records)
    
    print("긍정 요인:")
    for f in pos:
        print(f"  {f.category}: {f.count}건")
    
    print("부정 요인:")
    for f in neg:
        print(f"  {f.category}: {f.count}건")
