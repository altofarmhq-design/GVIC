"""
GVIC 전체 파이프라인 실행
==========================
입력 어댑터 → GVIC 엔진 분석 → 출력 어댑터 (PDF 리포트)

사용 사례: 올리브영 상품 후기 1000건 분석
"""
import sys
sys.path.insert(0, '/app/backend')

import os
import uuid
from datetime import datetime
import numpy as np
import pandas as pd

# 어댑터 임포트
from adapters.input_adapter import (
    ProductReviewAdapter, 
    DataDomain, 
    InputAdapterFactory
)
from adapters.output_adapter import (
    PDFReportAdapter,
    OutputType,
    OutputAdapterFactory,
    ModularAnalysisResult,
    FactorExtractor
)

# GVIC 엔진 모듈 임포트
from core.engine import GVICEngine
from core.patent1_convergence import ConvergenceController
from core.patent2_signal import SignalPreprocessor, SignalType
from core.patent5_distribution import WeightedDistributionSystem


def run_full_pipeline(data_file: str, output_dir: str = "/app/backend/data/reports"):
    """전체 파이프라인 실행"""
    
    print("=" * 70)
    print("GVIC 전체 파이프라인 실행")
    print("=" * 70)
    print(f"시작 시간: {datetime.now().isoformat()}")
    print()
    
    # ==================== 1. 입력 어댑터 ====================
    print("[STEP 1] 입력 어댑터 - 데이터 로드 및 표준화")
    print("-" * 50)
    
    input_adapter = InputAdapterFactory.get_adapter(DataDomain.PRODUCT_REVIEW)
    input_batch = input_adapter.process(data_file)
    
    print(f"  입력 파일: {os.path.basename(data_file)}")
    print(f"  배치 ID: {input_batch.batch_id}")
    print(f"  총 레코드: {input_batch.total_count}건")
    print(f"  유효 레코드: {input_batch.valid_count}건")
    print(f"  무효 레코드: {input_batch.invalid_count}건")
    print()
    
    # ==================== 2. 감성 분석 ====================
    print("[STEP 2] 감성 분석")
    print("-" * 50)
    
    sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}
    ratings = []
    
    for record in input_batch.records:
        ratings.append(record.metadata.get("original_rating", 3))
        sentiment_counts[record.sentiment_hint] += 1
    
    total = len(input_batch.records)
    sentiment_distribution = {
        "positive": {"count": sentiment_counts["positive"], "ratio": sentiment_counts["positive"] / total},
        "neutral": {"count": sentiment_counts["neutral"], "ratio": sentiment_counts["neutral"] / total},
        "negative": {"count": sentiment_counts["negative"], "ratio": sentiment_counts["negative"] / total}
    }
    
    print(f"  긍정: {sentiment_counts['positive']}건 ({sentiment_counts['positive']/total*100:.1f}%)")
    print(f"  중립: {sentiment_counts['neutral']}건 ({sentiment_counts['neutral']/total*100:.1f}%)")
    print(f"  부정: {sentiment_counts['negative']}건 ({sentiment_counts['negative']/total*100:.1f}%)")
    print(f"  평균 평점: {np.mean(ratings):.2f}")
    print()
    
    # ==================== 3. 요인 추출 ====================
    print("[STEP 3] 긍정/부정 요인 추출")
    print("-" * 50)
    
    factor_extractor = FactorExtractor()
    records_for_extraction = [r.to_dict() for r in input_batch.records]
    positive_factors, negative_factors = factor_extractor.extract_factors(records_for_extraction)
    
    print(f"  추출된 긍정 요인: {len(positive_factors)}개")
    for f in positive_factors[:5]:
        print(f"    - {f.category}: {f.count}건 ({f.ratio*100:.1f}%)")
    
    print(f"  추출된 부정 요인: {len(negative_factors)}개")
    for f in negative_factors[:5]:
        print(f"    - {f.category}: {f.count}건 ({f.ratio*100:.1f}%)")
    print()
    
    # ==================== 4. GVIC 엔진 처리 ====================
    print("[STEP 4] GVIC 엔진 분석")
    print("-" * 50)
    
    gvic_results = {}
    
    # 4.1 수렴 제어 (특허 1)
    print("  4.1 수렴 제어 (특허 1)...")
    V_input = np.array([
        sentiment_distribution["positive"]["ratio"],
        sentiment_distribution["neutral"]["ratio"],
        sentiment_distribution["negative"]["ratio"]
    ])
    
    controller = ConvergenceController(
        default_ratio=[0.33, 0.34, 0.33],
        omega={
            'lower_bounds': [0.1, 0.05, 0.01],
            'upper_bounds': [0.95, 0.5, 0.5],
            'sum_constraint': 1.0
        }
    )
    V_output, conv_metadata = controller.converge(V_input)
    
    gvic_results["convergence"] = {
        "input_vector": V_input.tolist(),
        "output_vector": V_output.tolist(),
        "status": conv_metadata.get("status"),
        "balance_index": conv_metadata.get("balance_index", 0)
    }
    print(f"      상태: {conv_metadata.get('status')}, 균형지수: {conv_metadata.get('balance_index', 0):.4f}")
    
    # 4.2 신호 전처리 (특허 2)
    print("  4.2 신호 전처리 (특허 2)...")
    preprocessor = SignalPreprocessor(dimension=64, threshold=0.7)
    conforming_count = 0
    sample_size = min(100, len(input_batch.records))
    
    for record in input_batch.records[:sample_size]:
        signal_data = {
            'rating': record.metadata.get("original_rating", 3),
            'review_length': record.metadata.get("review_length", 0),
            'helpful_count': record.metadata.get("engagement_score", 0)
        }
        modules = preprocessor.process(signal_data, SignalType.BEHAVIOR)
        for m in modules:
            if m.conformance_status.value == 'conforming':
                conforming_count += 1
    
    conformance_rate = conforming_count / sample_size if sample_size > 0 else 0
    gvic_results["signal"] = {
        "total_processed": sample_size,
        "conforming_count": conforming_count,
        "conformance_rate": conformance_rate
    }
    print(f"      처리: {sample_size}건, 정합률: {conformance_rate*100:.1f}%")
    
    # 4.3 가중 분배 (특허 6)
    print("  4.3 가중 분배 (특허 6)...")
    base_ratio = [
        sentiment_distribution["positive"]["ratio"],
        sentiment_distribution["neutral"]["ratio"] + 0.1,
        sentiment_distribution["negative"]["ratio"] + 0.1
    ]
    total_ratio = sum(base_ratio)
    base_ratio = [r / total_ratio for r in base_ratio]
    
    distributor = WeightedDistributionSystem(base_ratio=base_ratio)
    total_value = 1000000
    distribution = distributor.distribute(total_value)
    analytics = distributor.get_analytics()
    
    gvic_results["distribution"] = distribution
    gvic_results["fairness_index"] = analytics.get("fairness_index", 0)
    gvic_results["efficiency"] = analytics.get("efficiency", 0)
    
    print(f"      배분: 공공 {distribution.get('public', 0):,.0f}원 / 생산 {distribution.get('productive', 0):,.0f}원 / 개인 {distribution.get('individual', 0):,.0f}원")
    print(f"      공정성 지수: {analytics.get('fairness_index', 0):.4f}")
    print()
    
    # ==================== 5. 인사이트 생성 ====================
    print("[STEP 5] 인사이트 생성")
    print("-" * 50)
    
    insights = []
    recommendations = []
    
    # 감성 기반 인사이트
    if sentiment_distribution["positive"]["ratio"] > 0.8:
        insights.append(f"전체 리뷰의 {sentiment_distribution['positive']['ratio']*100:.0f}%가 긍정적으로, 매우 높은 고객 만족도를 보입니다.")
    elif sentiment_distribution["positive"]["ratio"] > 0.6:
        insights.append(f"긍정 리뷰 비율이 {sentiment_distribution['positive']['ratio']*100:.0f}%로 양호한 수준입니다.")
    
    # 요인 기반 인사이트
    if positive_factors:
        top_positive = positive_factors[0]
        insights.append(f"가장 많이 언급된 긍정 요인은 '{top_positive.category}'으로, {top_positive.count}건의 리뷰에서 언급되었습니다.")
    
    if negative_factors:
        top_negative = negative_factors[0]
        insights.append(f"주요 개선 필요 요인은 '{top_negative.category}'으로, {top_negative.count}건의 부정 리뷰에서 언급되었습니다.")
        recommendations.append(f"'{top_negative.category}' 관련 고객 불만을 우선적으로 해결하는 것이 권장됩니다.")
    
    # GVIC 기반 인사이트
    if gvic_results["convergence"]["balance_index"] > 0.3:
        insights.append(f"GVIC 균형 지수가 {gvic_results['convergence']['balance_index']:.2f}로, 데이터 분포가 특정 방향으로 치우쳐 있습니다.")
    
    recommendations.append("긍정 요인을 마케팅에 적극 활용하여 구매 전환율을 높이세요.")
    recommendations.append("정기적인 리뷰 모니터링을 통해 고객 피드백을 추적하세요.")
    
    for i, insight in enumerate(insights, 1):
        print(f"  {i}. {insight}")
    print()
    
    # ==================== 6. 출력 어댑터 - PDF 생성 ====================
    print("[STEP 6] 출력 어댑터 - PDF 리포트 생성")
    print("-" * 50)
    
    # 결과 객체 생성
    analysis_result = ModularAnalysisResult(
        result_id=str(uuid.uuid4())[:8],
        analysis_type="상품 후기 분석",
        created_at=datetime.now().isoformat(),
        input_summary={
            "total_records": input_batch.total_count,
            "valid_records": input_batch.valid_count,
            "avg_rating": float(np.mean(ratings)),
            "source": os.path.basename(data_file),
            "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M")
        },
        sentiment_distribution=sentiment_distribution,
        positive_factors=positive_factors,
        negative_factors=negative_factors,
        gvic_results=gvic_results,
        insights=insights,
        recommendations=recommendations
    )
    
    # PDF 출력
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(
        output_dir, 
        f"GVIC_Analysis_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    )
    
    output_adapter = OutputAdapterFactory.get_adapter(OutputType.PDF_REPORT)
    formatted_data = output_adapter.format(analysis_result)
    pdf_path = output_adapter.export(formatted_data, output_file)
    
    print(f"  PDF 저장: {pdf_path}")
    print()
    
    # ==================== 7. 완료 ====================
    print("=" * 70)
    print("파이프라인 완료")
    print("=" * 70)
    print(f"완료 시간: {datetime.now().isoformat()}")
    print(f"입력: {data_file}")
    print(f"출력: {pdf_path}")
    print()
    
    return {
        "input_batch_id": input_batch.batch_id,
        "total_records": input_batch.total_count,
        "sentiment_distribution": sentiment_distribution,
        "positive_factors_count": len(positive_factors),
        "negative_factors_count": len(negative_factors),
        "gvic_results": gvic_results,
        "output_pdf": pdf_path
    }


if __name__ == "__main__":
    # 실행
    data_dir = "/app/backend/data"
    
    # 가장 최신 리뷰 파일 찾기
    review_files = [f for f in os.listdir(data_dir) if f.endswith('.xlsx') and 'oliveyoung' in f]
    if not review_files:
        print("오류: 리뷰 데이터 파일이 없습니다.")
        exit(1)
    
    latest_file = os.path.join(data_dir, sorted(review_files)[-1])
    
    # 파이프라인 실행
    result = run_full_pipeline(latest_file)
    
    print("\n최종 결과:")
    print(f"  배치 ID: {result['input_batch_id']}")
    print(f"  처리 건수: {result['total_records']}")
    print(f"  긍정 요인: {result['positive_factors_count']}개")
    print(f"  부정 요인: {result['negative_factors_count']}개")
    print(f"  PDF 리포트: {result['output_pdf']}")
