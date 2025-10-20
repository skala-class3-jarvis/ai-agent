"""
경쟁사 분석 + 투자 판단 통합 테스트
"""

from typing import Dict, Any
import os
from dotenv import load_dotenv

# .env 파일 로드 (raw string 사용)
load_dotenv(r"C:\somin\skala_gai\.env")

# ============================================================================
# 간단한 테스트 함수
# ============================================================================

def simple_test():
    """간단한 통합 테스트"""
    
    print("\n" + "="*80)
    print("🚀 에듀테크 스타트업 투자 평가 시스템 테스트")
    print("="*80 + "\n")
    
    # 테스트용 스타트업 데이터
    test_startup_info = {
        "name": "MathGenius AI",
        "description": "AI 기반 수학 학습 플랫폼",
        "country": "South Korea",
        "category": "B2C",
        "founded": "2023",
        "team_size": 8,
        "stage": "Seed",
        "arr": "$300K",
        "growth_rate": "60% YoY"
    }
    
    print("📝 테스트 스타트업 정보:")
    print(f"  - 이름: {test_startup_info['name']}")
    print(f"  - 설명: {test_startup_info['description']}")
    print(f"  - 국가: {test_startup_info['country']}")
    print(f"  - 단계: {test_startup_info['stage']}")
    
    # ========================================================================
    # 1단계: 경쟁사 분석
    # ========================================================================
    
    print("\n" + "="*80)
    print("STEP 1: 경쟁사 분석 실행")
    print("="*80)
    
    try:
        from competitor_analysis_agent import run_competitor_analysis
        
        competitor_result = run_competitor_analysis(
            startup_name=test_startup_info["name"],
            startup_info=test_startup_info
        )
        
        print("\n✅ 경쟁사 분석 완료!")
        print(f"  - 발견된 경쟁사: {len(competitor_result['competitor_list'])}개")
        print(f"  - 경쟁 강도: {competitor_result['competitor_analysis'].get('competition_intensity', 'N/A')}/10")
        print(f"  - 포지셔닝: {competitor_result['competitor_analysis'].get('market_positioning', 'N/A')}")
        
    except Exception as e:
        print(f"\n❌ 경쟁사 분석 실패: {e}")
        competitor_result = {
            "competitor_list": [],
            "competitor_analysis": {"competition_intensity": 7},
            "competitive_positioning": {"positioning_score": 6}
        }
    
    # ========================================================================
    # 2단계: 투자 판단
    # ========================================================================
    
    print("\n" + "="*80)
    print("STEP 2: 투자 판단 실행")
    print("="*80)
    
    try:
        from investment_decision_agent import run_investment_decision
        
        # 간단한 Mock 데이터
        mock_tech = {"innovation_level": 7, "scalability": 8}
        mock_market = {"tam": "$2B", "market_growth": "15%"}
        
        investment_result = run_investment_decision(
            startup_name=test_startup_info["name"],
            startup_info=test_startup_info,
            technology_summary=mock_tech,
            market_analysis=mock_market,
            competitor_analysis=competitor_result.get("competitor_analysis", {}),
            competitive_positioning=competitor_result.get("competitive_positioning", {})
        )
        
        print("\n✅ 투자 판단 완료!")
        print(f"  - 총점: {investment_result['investment_scores'].get('total_score', 0)}/100")
        print(f"  - 리스크: {investment_result['risk_assessment'].get('overall_risk_score', 0)}/10")
        print(f"  - 결정: {investment_result['investment_decision']}")
        
    except Exception as e:
        print(f"\n❌ 투자 판단 실패: {e}")
        investment_result = None
    
    # ========================================================================
    # 최종 결과 요약
    # ========================================================================
    
    print("\n" + "="*80)
    print("📊 최종 결과 요약")
    print("="*80 + "\n")
    
    if investment_result:
        try:
            from investment_decision_agent import print_investment_summary
            print_investment_summary(investment_result)
        except:
            print("결과 요약 출력 실패")
    
    print("\n✅ 테스트 완료!\n")


# ============================================================================
# 더 간단한 버전 (외부 검색 없이)
# ============================================================================

def mock_test():
    """Mock 데이터로 빠른 테스트 (검색 없이)"""
    
    print("\n" + "="*80)
    print("🧪 Mock 데이터 테스트 (검색 없음)")
    print("="*80 + "\n")
    
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate
    import json
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
    
    # 테스트 데이터
    startup_name = "EduAI Learn"
    startup_info = {
        "description": "AI 기반 수학 학습 플랫폼",
        "stage": "Seed",
        "arr": "$500K",
        "team_size": 12
    }
    
    # ========================================================================
    # 간단한 투자 점수 계산
    # ========================================================================
    
    print("💰 투자 점수 계산 중...")
    
    scoring_prompt = ChatPromptTemplate.from_messages([
        ("system", """에듀테크 VC로서 스타트업을 100점 만점으로 평가하세요.

JSON 형식:
{{
    "total_score": 0-100,
    "team": 0-20,
    "market": 0-20,
    "technology": 0-15,
    "business_model": 0-10,
    "recommendation": "Strong Buy/Buy/Hold/Watch/Pass"
}}"""),
        ("human", "스타트업: {name}\n정보: {info}\n\n평가하세요.")
    ])
    
    try:
        chain = scoring_prompt | llm
        result = chain.invoke({
            "name": startup_name,
            "info": json.dumps(startup_info, ensure_ascii=False)
        })
        
        content = result.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        scores = json.loads(content)
        
        print("\n✅ 평가 완료!")
        print(f"  - 총점: {scores.get('total_score', 0)}/100")
        print(f"  - 팀: {scores.get('team', 0)}/20")
        print(f"  - 시장: {scores.get('market', 0)}/20")
        print(f"  - 기술: {scores.get('technology', 0)}/15")
        print(f"  - 비즈니스: {scores.get('business_model', 0)}/10")
        print(f"  - 추천: {scores.get('recommendation', 'N/A')}")
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
    
    print("\n✅ Mock 테스트 완료!\n")


# ============================================================================
# 최소 버전 (LLM 호출만)
# ============================================================================

def minimal_test():
    """최소한의 테스트 (LLM 연결 확인)"""
    
    print("\n🔍 LLM 연결 테스트...\n")
    
    try:
        from langchain_openai import ChatOpenAI
        
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        response = llm.invoke("Hello! 간단히 '연결 성공'이라고만 답변해주세요.")
        
        print(f"✅ LLM 응답: {response.content}\n")
        print("✅ 연결 성공! 본격적인 테스트를 진행할 수 있습니다.\n")
        
        return True
        
    except Exception as e:
        print(f"❌ 연결 실패: {e}\n")
        print("💡 OPENAI_API_KEY 환경변수를 확인해주세요.\n")
        return False


# ============================================================================
# 메인 실행
# ============================================================================

if __name__ == "__main__":
    import sys
    
    print("\n" + "="*80)
    print("에듀테크 투자 평가 시스템 - 테스트 메뉴")
    print("="*80)
    print("\n선택하세요:")
    print("  1. 최소 테스트 (LLM 연결 확인만)")
    print("  2. Mock 테스트 (검색 없이 빠른 테스트)")
    print("  3. 전체 테스트 (경쟁사 분석 + 투자 판단)")
    
    choice = input("\n선택 (1/2/3): ").strip()
    
    if choice == "1":
        minimal_test()
    elif choice == "2":
        mock_test()
    elif choice == "3":
        simple_test()
    else:
        print("\n기본 테스트를 실행합니다...\n")
        minimal_test()
        
        if input("\nMock 테스트를 진행하시겠습니까? (y/n): ").lower() == 'y':
            mock_test()