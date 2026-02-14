"""
GVIC 엔진 실제 데이터 테스트
- 올리브영 상품 후기 1000건 처리
- 특허 기반 모듈 전체 파이프라인 검증
"""
import sys
sys.path.insert(0, '/app/backend')

import pandas as pd
import numpy as np
from datetime import datetime
import json
import os

# GVIC 엔진 및 모듈 임포트
from core.engine import GVICEngine
from core.patent1_convergence import ConvergenceController
from core.patent2_signal import SignalPreprocessor, SignalType
from core.patent4_nonconform import NonConformingDataAssetizationSystem
from core.patent5_distribution import WeightedDistributionSystem

# 결과 저장 경로
OUTPUT_DIR = "/app/backend/data/test_results"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_review_data(filepath):
    """리뷰 데이터 로드"""
    print(f"데이터 로드: {filepath}")
    df = pd.read_excel(filepath)
    print(f"총 {len(df)}건 로드됨")
    return df


def analyze_sentiment_distribution(df):
    """감성 분포 분석 (GVIC 입력 전처리)"""
    print("\n" + "=" * 60)
    print("1. 감성 분포 분석 (입력 전처리)")
    print("=" * 60)
    
    # 평점 기반 감성 분류
    df['sentiment'] = df['rating'].apply(lambda x: 'positive' if x >= 4 else ('neutral' if x == 3 else 'negative'))
    
    sentiment_counts = df['sentiment'].value_counts()
    total = len(df)
    
    results = {
        'positive_count': int(sentiment_counts.get('positive', 0)),
        'neutral_count': int(sentiment_counts.get('neutral', 0)),
        'negative_count': int(sentiment_counts.get('negative', 0)),
        'positive_ratio': sentiment_counts.get('positive', 0) / total,
        'neutral_ratio': sentiment_counts.get('neutral', 0) / total,
        'negative_ratio': sentiment_counts.get('negative', 0) / total,
    }
    
    print(f"  긍정 (4-5점): {results['positive_count']}건 ({results['positive_ratio']*100:.1f}%)")
    print(f"  중립 (3점):   {results['neutral_count']}건 ({results['neutral_ratio']*100:.1f}%)")
    print(f"  부정 (1-2점): {results['negative_count']}건 ({results['negative_ratio']*100:.1f}%)")
    
    return df, results


def test_convergence_controller(sentiment_ratios):
    """특허 1: 수렴 제어 시스템 테스트"""
    print("\n" + "=" * 60)
    print("2. 특허 1: 전역 수렴 제어 시스템 테스트")
    print("=" * 60)
    
    # 감성 비율을 3개 영역으로 매핑: [긍정, 중립, 부정]
    V_input = np.array([
        sentiment_ratios['positive_ratio'],
        sentiment_ratios['neutral_ratio'],
        sentiment_ratios['negative_ratio']
    ])
    
    print(f"  입력 벡터: {V_input}")
    
    # 수렴 제어기 초기화 (기본 균형 비율)
    controller = ConvergenceController(
        default_ratio=[0.33, 0.34, 0.33],
        omega={
            'lower_bounds': [0.1, 0.05, 0.01],  # 최소 비율
            'upper_bounds': [0.95, 0.5, 0.5],   # 최대 비율
            'sum_constraint': 1.0
        }
    )
    
    # 수렴 변환 적용
    V_output, metadata = controller.converge(V_input)
    
    print(f"  출력 벡터: {V_output}")
    print(f"  수렴 상태: {metadata['status']}")
    print(f"  변환 여부: {metadata['transformed']}")
    print(f"  균형 지수: {metadata.get('balance_index', 0):.4f}")
    
    # 경계 조건 검증
    is_valid = controller.omega.is_valid(V_output)
    print(f"  경계 조건 만족: {is_valid}")
    
    return {
        'input_vector': V_input.tolist(),
        'output_vector': V_output.tolist(),
        'status': metadata['status'],
        'transformed': metadata['transformed'],
        'balance_index': metadata.get('balance_index', 0),
        'boundary_valid': is_valid
    }


def test_signal_preprocessor(df):
    """특허 2: 신호 전처리 시스템 테스트"""
    print("\n" + "=" * 60)
    print("3. 특허 2: 다단계 신호 전처리 시스템 테스트")
    print("=" * 60)
    
    preprocessor = SignalPreprocessor(dimension=64, threshold=0.7)
    
    # 리뷰 데이터를 신호로 처리
    sample_size = min(100, len(df))  # 샘플 100건
    
    results = {
        'total_processed': 0,
        'conforming_count': 0,
        'non_conforming_count': 0,
        'unclassified_count': 0,
        'modules_generated': 0
    }
    
    for idx, row in df.head(sample_size).iterrows():
        # 리뷰를 신호 데이터로 변환
        signal_data = {
            'rating': row['rating'],
            'review_length': row['review_length'],
            'helpful_count': row['helpful_count'],
            'is_repurchase': 1 if row['is_repurchase'] else 0,
            'mentions_effect': 1 if row['mentions_effect'] else 0,
            'mentions_package': 1 if row['mentions_package'] else 0
        }
        
        # 신호 처리
        modules = preprocessor.process(signal_data, SignalType.BEHAVIOR)
        
        results['total_processed'] += 1
        results['modules_generated'] += len(modules)
        
        for module in modules:
            if module.conformance_status.value == 'conforming':
                results['conforming_count'] += 1
            elif module.conformance_status.value == 'non_conforming':
                results['non_conforming_count'] += 1
            else:
                results['unclassified_count'] += 1
    
    print(f"  처리된 신호: {results['total_processed']}건")
    print(f"  생성된 모듈: {results['modules_generated']}개")
    print(f"  정합 모듈: {results['conforming_count']}개")
    print(f"  비정합 모듈: {results['non_conforming_count']}개")
    print(f"  미분류 모듈: {results['unclassified_count']}개")
    
    conformance_rate = results['conforming_count'] / results['modules_generated'] if results['modules_generated'] > 0 else 0
    print(f"  정합률: {conformance_rate*100:.1f}%")
    
    results['conformance_rate'] = conformance_rate
    return results


def test_nonconform_handler(df):
    """특허 5: 비적합 데이터 자산화 시스템 테스트"""
    print("\n" + "=" * 60)
    print("4. 특허 5: 비적합 데이터 자산화 시스템 테스트")
    print("=" * 60)
    
    nc_system = NonConformingDataAssetizationSystem(
        value_threshold=0.5,
        retention_days=30
    )
    
    results = {
        'total_processed': 0,
        'conforming_data': 0,
        'nonconforming_data': 0,
        'assets_created': 0,
        'nc_types': {}
    }
    
    sample_size = min(200, len(df))
    
    for idx, row in df.head(sample_size).iterrows():
        # 데이터 유효성 검증 컨텍스트 설정
        context = {
            'required_fields': ['rating', 'content'],
            'bounds': (1, 5),  # 평점 범위
            'business_relevance': 0.7
        }
        
        # 리뷰 데이터
        review_data = {
            'rating': row['rating'],
            'content': row['content'],
            'review_length': row['review_length'],
            'helpful_count': row['helpful_count']
        }
        
        # 비적합 처리
        result = nc_system.process(review_data, context)
        
        results['total_processed'] += 1
        
        if result['is_conforming']:
            results['conforming_data'] += 1
        else:
            results['nonconforming_data'] += 1
            
            for nc in result['non_conformances']:
                nc_type = nc['type']
                results['nc_types'][nc_type] = results['nc_types'].get(nc_type, 0) + 1
            
            results['assets_created'] += len(result['assets_created'])
    
    print(f"  처리된 데이터: {results['total_processed']}건")
    print(f"  정합 데이터: {results['conforming_data']}건")
    print(f"  비적합 데이터: {results['nonconforming_data']}건")
    print(f"  생성된 2차 자산: {results['assets_created']}개")
    
    if results['nc_types']:
        print(f"  비적합 유형별:")
        for nc_type, count in results['nc_types'].items():
            print(f"    - {nc_type}: {count}건")
    
    return results


def test_distribution_system(sentiment_ratios, total_value=1000000):
    """특허 6: 가중 분배 시스템 테스트"""
    print("\n" + "=" * 60)
    print("5. 특허 6: 가중 분배 모델 시스템 테스트")
    print("=" * 60)
    
    # 감성 비율을 배분 비율로 사용
    base_ratio = [
        sentiment_ratios['positive_ratio'],
        sentiment_ratios['neutral_ratio'] + 0.1,  # 중립 보정
        sentiment_ratios['negative_ratio'] + 0.1   # 부정 보정
    ]
    
    # 정규화
    total = sum(base_ratio)
    base_ratio = [r / total for r in base_ratio]
    
    distributor = WeightedDistributionSystem(base_ratio=base_ratio)
    
    # 배분 실행
    distribution = distributor.distribute(total_value)
    
    print(f"  총 배분 가치: {total_value:,}원")
    print(f"  배분 비율: {[f'{r:.2%}' for r in base_ratio]}")
    print(f"  배분 결과:")
    
    if isinstance(distribution, dict):
        for domain, value in distribution.items():
            if isinstance(value, (int, float)):
                print(f"    - {domain}: {value:,.0f}원")
    
    # 소비 시뮬레이션 후 동적 조정
    consumptions = {
        'public': distribution.get('public', 0) * 0.9,      # 90% 소비
        'productive': distribution.get('productive', 0) * 1.2,  # 120% 초과 소비
        'individual': distribution.get('individual', 0) * 0.8   # 80% 소비
    }
    
    adjustment_result = distributor.update_with_consumption(consumptions)
    
    print(f"\n  동적 조정:")
    print(f"    조정 발생: {adjustment_result.get('adjusted', False)}")
    
    if adjustment_result.get('new_weights'):
        print(f"    새 가중치: {adjustment_result['new_weights']}")
    
    analytics = distributor.get_analytics()
    print(f"\n  분석 지표:")
    print(f"    공정성 지수: {analytics.get('fairness_index', 0):.4f}")
    print(f"    가중 공정성: {analytics.get('weighted_fairness', 0):.4f}")
    
    return {
        'total_value': total_value,
        'base_ratio': base_ratio,
        'distribution': distribution,
        'adjusted': adjustment_result.get('adjusted', False),
        'analytics': analytics
    }


def test_full_pipeline(df):
    """전체 GVIC 파이프라인 테스트"""
    print("\n" + "=" * 60)
    print("6. 전체 GVIC 엔진 파이프라인 테스트")
    print("=" * 60)
    
    # GVIC 엔진 초기화
    engine = GVICEngine(
        sigma=[0.33, 0.34, 0.33],
        omega={
            'V_pub_min': 0.1, 'V_pub_max': 0.8,
            'V_pro_min': 0.1, 'V_pro_max': 0.6,
            'V_ind_min': 0.05, 'V_ind_max': 0.5
        }
    )
    
    results = {
        'total_processed': 0,
        'success_count': 0,
        'failure_count': 0,
        'balance_scores': [],
        'distribution_totals': {'public': 0, 'productive': 0, 'individual': 0}
    }
    
    sample_size = min(50, len(df))  # 50건 샘플
    
    print(f"  {sample_size}건 처리 중...")
    
    for idx, row in df.head(sample_size).iterrows():
        # 리뷰 데이터를 GVIC 입력으로 변환
        input_data = {
            'value': row['rating'] * 20,  # 평점을 100점 만점으로 변환
            'amount': row['helpful_count'],
            'quality': row['review_length'] / 100,
            'metadata': {
                'is_repurchase': row['is_repurchase'],
                'mentions_effect': row['mentions_effect']
            }
        }
        
        # GVIC 엔진 처리
        result = engine.process(input_data, source_type="review")
        
        results['total_processed'] += 1
        
        if result.success:
            results['success_count'] += 1
            results['balance_scores'].append(result.data.get('balance_score', 0))
            
            dist = result.data.get('distribution', {})
            for key in ['public', 'productive', 'individual']:
                results['distribution_totals'][key] += dist.get(key, 0)
        else:
            results['failure_count'] += 1
    
    print(f"  처리 완료: {results['total_processed']}건")
    print(f"  성공: {results['success_count']}건")
    print(f"  실패: {results['failure_count']}건")
    
    if results['balance_scores']:
        avg_balance = np.mean(results['balance_scores'])
        print(f"  평균 균형 지수: {avg_balance:.4f}")
        results['avg_balance_score'] = avg_balance
    
    print(f"\n  누적 분배:")
    for key, value in results['distribution_totals'].items():
        print(f"    - {key}: {value:.2f}")
    
    # 시스템 상태
    status = engine.get_system_status()
    print(f"\n  시스템 상태:")
    print(f"    총 처리: {status['total_processed']}건")
    print(f"    성공률: {status['success_rate']*100:.1f}%")
    
    return results


def generate_test_report(all_results, df):
    """테스트 결과 리포트 생성"""
    print("\n" + "=" * 60)
    print("테스트 결과 리포트 생성")
    print("=" * 60)
    
    report = {
        'test_date': datetime.now().isoformat(),
        'data_source': '올리브영 상품 후기',
        'total_reviews': len(df),
        'product_info': {
            'name': '피토틱스 한국인 질 유래 유산균 옐로우',
            'product_no': 'A000000186204',
            'avg_rating': float(df['rating'].mean()),
            'rating_distribution': df['rating'].value_counts().to_dict()
        },
        'test_results': all_results,
        'summary': {
            'convergence_test': 'PASS' if all_results.get('convergence', {}).get('boundary_valid') else 'FAIL',
            'signal_test': 'PASS' if all_results.get('signal', {}).get('conformance_rate', 0) > 0 else 'FAIL',
            'nonconform_test': 'PASS' if all_results.get('nonconform', {}).get('total_processed', 0) > 0 else 'FAIL',
            'distribution_test': 'PASS' if all_results.get('distribution', {}).get('distribution') else 'FAIL',
            'pipeline_test': 'PASS' if all_results.get('pipeline', {}).get('success_count', 0) > 0 else 'FAIL'
        }
    }
    
    # JSON 저장
    report_file = f"{OUTPUT_DIR}/gvic_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"  리포트 저장: {report_file}")
    
    # 요약 출력
    print("\n" + "=" * 60)
    print("테스트 요약")
    print("=" * 60)
    for test_name, status in report['summary'].items():
        emoji = "✅" if status == "PASS" else "❌"
        print(f"  {emoji} {test_name}: {status}")
    
    return report_file


def main():
    print("=" * 60)
    print("GVIC 엔진 실제 데이터 테스트")
    print("=" * 60)
    print(f"테스트 시작: {datetime.now().isoformat()}")
    
    # 1. 데이터 로드
    data_files = [f for f in os.listdir('/app/backend/data') if f.endswith('.xlsx') and 'oliveyoung' in f]
    if not data_files:
        print("오류: 리뷰 데이터 파일을 찾을 수 없습니다.")
        return
    
    filepath = f"/app/backend/data/{sorted(data_files)[-1]}"  # 가장 최신 파일
    df = load_review_data(filepath)
    
    all_results = {}
    
    # 2. 감성 분석
    df, sentiment_results = analyze_sentiment_distribution(df)
    all_results['sentiment'] = sentiment_results
    
    # 3. 특허 1: 수렴 제어 테스트
    convergence_results = test_convergence_controller(sentiment_results)
    all_results['convergence'] = convergence_results
    
    # 4. 특허 2: 신호 전처리 테스트
    signal_results = test_signal_preprocessor(df)
    all_results['signal'] = signal_results
    
    # 5. 특허 5: 비적합 데이터 테스트
    nonconform_results = test_nonconform_handler(df)
    all_results['nonconform'] = nonconform_results
    
    # 6. 특허 6: 분배 시스템 테스트
    distribution_results = test_distribution_system(sentiment_results)
    all_results['distribution'] = distribution_results
    
    # 7. 전체 파이프라인 테스트
    pipeline_results = test_full_pipeline(df)
    all_results['pipeline'] = pipeline_results
    
    # 8. 리포트 생성
    report_file = generate_test_report(all_results, df)
    
    print("\n" + "=" * 60)
    print(f"테스트 완료: {datetime.now().isoformat()}")
    print(f"리포트 파일: {report_file}")
    print("=" * 60)
    
    return all_results


if __name__ == "__main__":
    results = main()
