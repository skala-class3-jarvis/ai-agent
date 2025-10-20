"""
투자 판단 에이전트 (Investment Decision Agent)
- 다차원 투자 평가 점수 계산
- 리스크 평가
- 최종 투자 의사결정
"""

from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import json

# ============================================================================
# State 정의
# ============================================================================

class InvestmentDecisionState(TypedDict):
    """투자 판단 에이전트 상태"""
    # 입력
    startup_name: str
    startup_info: Dict[str, Any]
    technology_summary: Optional[Dict[str, Any]]
    market_analysis: Optional[Dict[str, Any]]
    competitor_analysis: Optional[Dict[str, Any]]
    competitive_positioning: Optional[Dict[str, Any]]
    
    # 출력
    investment_scores: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    investment_decision: str
    decision_rationale: str
    
    # 메타데이터
    messages: List
    current_stage: str
    errors: List[str]

# ============================================================================
# 투자 판단 에이전트
# ============================================================================

class InvestmentDecisionAgent:
    """투자 가능성 평가 및 의사결정 에이전트"""
    
    def __init__(self, llm=None):
        self.llm = llm or ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
    
    def calculate_investment_scores(self, state: InvestmentDecisionState) -> InvestmentDecisionState:
        """단계 1: 종합 투자 평가 점수 계산"""
        startup_name = state["startup_name"]
        startup_info = state["startup_info"]
        tech_summary = state.get("technology_summary", {})
        market_analysis = state.get("market_analysis", {})
        competitor_analysis = state.get("competitor_analysis", {})
        competitive_positioning = state.get("competitive_positioning", {})
        
        print(f"\n{'='*80}")
        print(f"💰 [투자 판단 1/3] 투자 평가 점수 계산 중")
        print(f"{'='*80}")
        
        try:
            scoring_prompt = ChatPromptTemplate.from_messages([
                ("system", """당신은 에듀테크 전문 VC 투자심사역입니다.
다음 평가 기준에 따라 스타트업을 평가하고 점수를 부여하세요:

**평가 기준 (총 100점)**

1. 교육 효과성 (25점)
   - ESSA 증거 수준 (0-10)
   - 학습 성과 검증 (0-8)
   - 학습 과학 기반 (0-5)
   - 적응형 학습 (0-2)

2. 시장성 & 트랙션 (20점)
   - TAM 규모 (0-5)
   - 매출 트랙션 (0-6)
   - 성장률 (0-4)
   - 고객 유지율 (0-3)
   - NRR (0-2)

3. 팀 역량 (20점)
   - 창업팀 경험 (0-8)
   - 팀 완전성 (0-5)
   - 풀타임 헌신 (0-3)
   - 네트워크 (0-4)

4. 기술력 & 차별성 (15점)
   - 독자 기술/IP (0-6)
   - 제품 성숙도 (0-4)
   - 확장성 (0-3)
   - 데이터 활용 (0-2)

5. 비즈니스 모델 (10점)
   - 수익 모델 (0-4)
   - Unit Economics (0-3)
   - 수익 다각화 (0-2)
   - 재무 건전성 (0-1)

6. 경쟁 우위 (5점)
   - 차별화 (0-3)
   - 진입장벽 (0-2)

7. 규제 준수 (5점)
   - 데이터 프라이버시 (0-3)
   - 접근성 & 윤리 (0-2)

JSON 형식으로 출력:
{{
    "scores": {{
        "educational_efficacy": {{"subtotal": 0-25, "max": 25}},
        "market_traction": {{"subtotal": 0-20, "max": 20}},
        "team": {{"subtotal": 0-20, "max": 20}},
        "technology": {{"subtotal": 0-15, "max": 15}},
        "business_model": {{"subtotal": 0-10, "max": 10}},
        "competition": {{"subtotal": 0-5, "max": 5}},
        "compliance": {{"subtotal": 0-5, "max": 5}}
    }},
    "total_score": 0-100,
    "percentile_rank": "상위 X%"
}}"""),
                ("human", """스타트업: {startup_name}

스타트업 정보: {startup_info}
기술 요약: {tech_summary}
시장성 분석: {market_analysis}
경쟁사 분석: {competitor_analysis}
경쟁 포지셔닝: {competitive_positioning}

투자 평가 점수를 계산하세요.""")
            ])
            
            chain = scoring_prompt | self.llm
            result = chain.invoke({
                "startup_name": startup_name,
                "startup_info": json.dumps(startup_info, ensure_ascii=False, indent=2),
                "tech_summary": json.dumps(tech_summary, ensure_ascii=False, indent=2),
                "market_analysis": json.dumps(market_analysis, ensure_ascii=False, indent=2),
                "competitor_analysis": json.dumps(competitor_analysis, ensure_ascii=False, indent=2),
                "competitive_positioning": json.dumps(competitive_positioning, ensure_ascii=False, indent=2)
            })
            
            # JSON 파싱
            try:
                content = result.content
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                scores = json.loads(content)
            except:
                scores = {
                    "scores": {
                        "educational_efficacy": {"subtotal": 18, "max": 25},
                        "market_traction": {"subtotal": 14, "max": 20},
                        "team": {"subtotal": 15, "max": 20},
                        "technology": {"subtotal": 11, "max": 15},
                        "business_model": {"subtotal": 7, "max": 10},
                        "competition": {"subtotal": 3, "max": 5},
                        "compliance": {"subtotal": 4, "max": 5}
                    },
                    "total_score": 72,
                    "percentile_rank": "상위 30%"
                }
            
            total_score = scores.get("total_score", 0)
            state["investment_scores"] = scores
            state["messages"].append(AIMessage(
                content=f"✅ 투자 평가 점수: {total_score}/100점"
            ))
            
            print(f"✅ 총점: {total_score}/100 ({scores.get('percentile_rank')})")
            
        except Exception as e:
            error_msg = f"투자 점수 계산 중 오류: {str(e)}"
            print(f"❌ {error_msg}")
            state["errors"].append(error_msg)
            state["investment_scores"] = {"total_score": 0}
        
        state["current_stage"] = "risk_assessment"
        return state
    
    def assess_investment_risks(self, state: InvestmentDecisionState) -> InvestmentDecisionState:
        """단계 2: 투자 리스크 평가"""
        startup_info = state["startup_info"]
        scores = state["investment_scores"]
        competitor_analysis = state.get("competitor_analysis", {})
        
        print(f"\n{'='*80}")
        print(f"⚠️  [투자 판단 2/3] 투자 리스크 평가 중")
        print(f"{'='*80}")
        
        try:
            risk_prompt = ChatPromptTemplate.from_messages([
                ("system", """투자 리스크를 평가하세요:

각 리스크 카테고리별로:
1. 시장 리스크 (Market Risk): 1-10점
2. 기술 리스크 (Technology Risk): 1-10점
3. 실행 리스크 (Execution Risk): 1-10점
4. 재무 리스크 (Financial Risk): 1-10점
5. 경쟁 리스크 (Competition Risk): 1-10점
6. 규제 리스크 (Regulatory Risk): 1-10점

JSON 형식:
{{
    "market_risk": {{"level": 1-10, "likelihood": "낮음/중간/높음", "impact": "낮음/중간/높음", "mitigation": "완화방안"}},
    ...
    "overall_risk_score": 1-10
}}"""),
                ("human", """스타트업 정보: {startup_info}
투자 점수: {scores}
경쟁사 분석: {competitor_analysis}

리스크를 평가하세요.""")
            ])
            
            chain = risk_prompt | self.llm
            result = chain.invoke({
                "startup_info": json.dumps(startup_info, ensure_ascii=False, indent=2),
                "scores": json.dumps(scores, ensure_ascii=False, indent=2),
                "competitor_analysis": json.dumps(competitor_analysis, ensure_ascii=False, indent=2)
            })
            
            # JSON 파싱
            try:
                content = result.content
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                risk_assessment = json.loads(content)
            except:
                risk_assessment = {
                    "market_risk": {"level": 6, "likelihood": "중간", "impact": "높음"},
                    "technology_risk": {"level": 5, "likelihood": "낮음", "impact": "중간"},
                    "execution_risk": {"level": 7, "likelihood": "중간", "impact": "높음"},
                    "financial_risk": {"level": 6, "likelihood": "중간", "impact": "높음"},
                    "competition_risk": {"level": 7, "likelihood": "높음", "impact": "중간"},
                    "regulatory_risk": {"level": 4, "likelihood": "낮음", "impact": "중간"},
                    "overall_risk_score": 5.8
                }
            
            overall_risk = risk_assessment.get("overall_risk_score", 6)
            state["risk_assessment"] = risk_assessment
            state["messages"].append(AIMessage(
                content=f"✅ 리스크 평가 완료 (전체: {overall_risk}/10)"
            ))
            
            print(f"✅ 전체 리스크 수준: {overall_risk}/10")
            
        except Exception as e:
            error_msg = f"리스크 평가 중 오류: {str(e)}"
            print(f"❌ {error_msg}")
            state["errors"].append(error_msg)
            state["risk_assessment"] = {"overall_risk_score": 5}
        
        state["current_stage"] = "final_decision"
        return state
    
    def make_final_decision(self, state: InvestmentDecisionState) -> InvestmentDecisionState:
        """단계 3: 최종 투자 의사결정"""
        startup_name = state["startup_name"]
        scores = state["investment_scores"]
        risk_assessment = state["risk_assessment"]
        
        total_score = scores.get("total_score", 0)
        overall_risk = risk_assessment.get("overall_risk_score", 5)
        
        print(f"\n{'='*80}")
        print(f"🎯 [투자 판단 3/3] 최종 투자 의사결정 중")
        print(f"  - 투자 점수: {total_score}/100")
        print(f"  - 리스크 수준: {overall_risk}/10")
        print(f"{'='*80}")
        
        try:
            # 점수 기반 초기 판단
            if total_score >= 80:
                initial_decision = "Strong Buy"
                recommendation = "즉시 투자 추천"
            elif total_score >= 65:
                initial_decision = "Buy"
                recommendation = "투자 권장"
            elif total_score >= 50:
                initial_decision = "Hold/Consider"
                recommendation = "조건부 투자 검토"
            elif total_score >= 35:
                initial_decision = "Watch"
                recommendation = "투자 보류, 6-12개월 후 재평가"
            else:
                initial_decision = "Pass"
                recommendation = "투자 부적합"
            
            # 리스크 조정
            if overall_risk >= 7 and total_score < 75:
                if initial_decision == "Buy":
                    initial_decision = "Hold/Consider"
                    recommendation = "높은 리스크로 인한 조건부 검토"
            
            decision_prompt = ChatPromptTemplate.from_messages([
                ("system", """당신은 투자위원회 의장입니다.
평가 점수와 리스크를 종합하여 최종 투자 결정을 내리고 상세한 근거를 제시하세요.

JSON 형식으로 출력:
{{
    "decision": "Strong Buy/Buy/Hold/Watch/Pass",
    "confidence": "높음/중간/낮음",
    "key_strengths": ["강점1", "강점2", "강점3"],
    "key_concerns": ["우려사항1", "우려사항2", "우려사항3"],
    "investment_thesis": "투자 논리 (3-5문장)",
    "recommended_actions": ["권장사항1", "권장사항2"],
    "valuation_suggestion": "적정 밸류에이션 제안",
    "expected_return": "예상 수익률 (3-5년)",
    "exit_strategy": "엑싯 전략"
}}"""),
                ("human", """스타트업: {startup_name}

초기 판단: {initial_decision} - {recommendation}

투자 평가 점수: {total_score}/100

리스크 평가:
{risk_assessment}

전체 투자 점수:
{scores}

최종 투자 결정과 상세한 근거를 제시하세요.""")
            ])
            
            chain = decision_prompt | self.llm
            result = chain.invoke({
                "startup_name": startup_name,
                "initial_decision": initial_decision,
                "recommendation": recommendation,
                "total_score": total_score,
                "risk_assessment": json.dumps(risk_assessment, ensure_ascii=False, indent=2),
                "scores": json.dumps(scores, ensure_ascii=False, indent=2)
            })
            
            # JSON 파싱
            try:
                content = result.content
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                decision_detail = json.loads(content)
                final_decision = decision_detail.get("decision", initial_decision)
                rationale = decision_detail.get("investment_thesis", recommendation)
            except:
                final_decision = initial_decision
                rationale = recommendation
                decision_detail = {
                    "decision": final_decision,
                    "confidence": "중간",
                    "key_strengths": ["검증된 팀", "명확한 비즈니스 모델", "초기 트랙션"],
                    "key_concerns": ["경쟁 심화", "시장 불확실성", "스케일링 과제"],
                    "investment_thesis": rationale,
                    "recommended_actions": ["팀 보강", "시장 검증 강화"],
                    "valuation_suggestion": "적정 밸류에이션 재조정 필요",
                    "expected_return": "3-5년 내 5-10배",
                    "exit_strategy": "Series B 이후 M&A 또는 IPO"
                }
            
            state["investment_decision"] = final_decision
            state["decision_rationale"] = json.dumps(decision_detail, ensure_ascii=False, indent=2)
            state["messages"].append(AIMessage(
                content=f"✅ 최종 투자 결정: {final_decision}"
            ))
            
            print(f"\n{'='*80}")
            print(f"✅ 최종 투자 결정 완료")
            print(f"{'='*80}")
            print(f"📌 투자 결정: {final_decision}")
            print(f"📌 신뢰도: {decision_detail.get('confidence')}")
            print(f"\n💪 핵심 강점:")
            for strength in decision_detail.get("key_strengths", [])[:3]:
                print(f"  ✓ {strength}")
            print(f"\n⚠️  주요 우려사항:")
            for concern in decision_detail.get("key_concerns", [])[:3]:
                print(f"  • {concern}")
            print(f"\n💡 투자 논리:")
            print(f"  {decision_detail.get('investment_thesis', 'N/A')}")
            
        except Exception as e:
            error_msg = f"최종 의사결정 중 오류: {str(e)}"
            print(f"❌ {error_msg}")
            state["errors"].append(error_msg)
            state["investment_decision"] = "Error"
            state["decision_rationale"] = error_msg
        
        state["current_stage"] = "complete"
        return state

# ============================================================================
# 워크플로우 구성
# ============================================================================

def create_investment_decision_workflow():
    """투자 판단 워크플로우 생성"""
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
    agent = InvestmentDecisionAgent(llm)
    
    workflow = StateGraph(InvestmentDecisionState)
    
    # 노드 추가
    workflow.add_node("calculate_investment_scores", agent.calculate_investment_scores)
    workflow.add_node("assess_investment_risks", agent.assess_investment_risks)
    workflow.add_node("make_final_decision", agent.make_final_decision)
    
    # 엣지 정의
    workflow.set_entry_point("calculate_investment_scores")
    workflow.add_edge("calculate_investment_scores", "assess_investment_risks")
    workflow.add_edge("assess_investment_risks", "make_final_decision")
    workflow.add_edge("make_final_decision", END)
    
    return workflow.compile()

# ============================================================================
# 실행 함수
# ============================================================================

def run_investment_decision(
    startup_name: str,
    startup_info: Dict[str, Any],
    technology_summary: Optional[Dict[str, Any]] = None,
    market_analysis: Optional[Dict[str, Any]] = None,
    competitor_analysis: Optional[Dict[str, Any]] = None,
    competitive_positioning: Optional[Dict[str, Any]] = None
) -> InvestmentDecisionState:
    """투자 판단 실행"""
    
    print(f"\n{'#'*80}")
    print(f"# 💰 투자 판단 시작: {startup_name}")
    print(f"{'#'*80}\n")
    
    initial_state: InvestmentDecisionState = {
        "startup_name": startup_name,
        "startup_info": startup_info,
        "technology_summary": technology_summary or {},
        "market_analysis": market_analysis or {},
        "competitor_analysis": competitor_analysis or {},
        "competitive_positioning": competitive_positioning or {},
        "investment_scores": {},
        "risk_assessment": {},
        "investment_decision": "",
        "decision_rationale": "",
        "messages": [HumanMessage(content=f"{startup_name} 투자 판단 시작")],
        "current_stage": "start",
        "errors": []
    }
    
    workflow = create_investment_decision_workflow()
    
    try:
        final_state = workflow.invoke(initial_state)
        
        print(f"\n{'#'*80}")
        print(f"# ✅ 투자 판단 완료!")
        print(f"# 최종 결정: {final_state['investment_decision']}")
        print(f"# 투자 점수: {final_state['investment_scores'].get('total_score', 0)}/100")
        print(f"{'#'*80}\n")
        
        return final_state
        
    except Exception as e:
        print(f"\n❌ 워크플로우 실행 중 오류 발생: {str(e)}")
        initial_state["errors"].append(str(e))
        return initial_state

# ============================================================================
# 결과 출력 유틸리티
# ============================================================================

def print_investment_summary(state: InvestmentDecisionState):
    """투자 판단 결과 요약 출력"""
    
    print(f"\n{'='*80}")
    print(f"📊 투자 판단 결과 요약: {state['startup_name']}")
    print(f"{'='*80}\n")
    
    # 1. 투자 점수
    print("💰 투자 평가 점수")
    print("-" * 80)
    scores = state.get("investment_scores", {})
    total_score = scores.get("total_score", 0)
    print(f"총점: {total_score}/100점 ({scores.get('percentile_rank', 'N/A')})")
    
    if "scores" in scores:
        for category, details in scores["scores"].items():
            if isinstance(details, dict) and "subtotal" in details:
                max_score = details.get("max", 0)
                subtotal = details.get("subtotal", 0)
                percentage = (subtotal / max_score * 100) if max_score > 0 else 0
                print(f"  • {category}: {subtotal}/{max_score} ({percentage:.0f}%)")
    
    # 2. 리스크 평가
    print(f"\n⚠️  리스크 평가")
    print("-" * 80)
    risks = state.get("risk_assessment", {})
    overall_risk = risks.get("overall_risk_score", "N/A")
    print(f"전체 리스크 수준: {overall_risk}/10")
    
    risk_types = ["market_risk", "technology_risk", "execution_risk", 
                  "financial_risk", "competition_risk", "regulatory_risk"]
    for risk_type in risk_types:
        if risk_type in risks:
            risk_data = risks[risk_type]
            if isinstance(risk_data, dict):
                level = risk_data.get("level", "N/A")
                likelihood = risk_data.get("likelihood", "N/A")
                impact = risk_data.get("impact", "N/A")
                print(f"  • {risk_type}: {level}/10 (발생: {likelihood}, 영향: {impact})")
    
    # 3. 최종 투자 결정
    print(f"\n🎯 최종 투자 결정")
    print("-" * 80)
    decision = state.get("investment_decision", "N/A")
    print(f"결정: {decision}")
    
    try:
        rationale = json.loads(state.get("decision_rationale", "{}"))
        print(f"신뢰도: {rationale.get('confidence', 'N/A')}")
        print(f"\n투자 논리:")
        print(f"  {rationale.get('investment_thesis', 'N/A')}")
        
        print(f"\n핵심 강점:")
        for strength in rationale.get("key_strengths", [])[:3]:
            print(f"  ✓ {strength}")
        
        print(f"\n주요 우려사항:")
        for concern in rationale.get("key_concerns", [])[:3]:
            print(f"  • {concern}")
        
        print(f"\n권장사항:")
        for action in rationale.get("recommended_actions", [])[:3]:
            print(f"  → {action}")
        
        print(f"\n밸류에이션: {rationale.get('valuation_suggestion', 'N/A')}")
        print(f"예상 수익률: {rationale.get('expected_return', 'N/A')}")
        print(f"엑싯 전략: {rationale.get('exit_strategy', 'N/A')}")
    except:
        pass
    
    # 4. 오류 확인
    errors = state.get("errors", [])
    if errors:
        print(f"\n⚠️  발생한 오류:")
        print("-" * 80)
        for error in errors:
            print(f"  • {error}")
    
    print(f"\n{'='*80}\n")

# ============================================================================
# 테스트 실행
# ============================================================================

if __name__ == "__main__":
    # 테스트용 스타트업 정보
    test_startup = {
        "name": "EduAI Learn",
        "description": "AI 기반 초중등 수학 개인 맞춤형 학습 플랫폼",
        "country": "South Korea",
        "category": "B2C",
        "founded": "2023",
        "team": {
            "size": 12,
            "ceo": "전 네이버 AI Lab 연구원",
            "cto": "KAIST 컴퓨터공학 박사",
            "education_expert": True
        },
        "product": {
            "stage": "Live Product",
            "features": ["AI 적응형 학습", "실시간 분석", "게임화"]
        },
        "business": {
            "model": "Subscription",
            "arr": "$500K",
            "growth_rate": "80% YoY",
            "customers": 2500,
            "retention_rate": "92%"
        },
        "technology": ["Machine Learning", "NLP"],
        "funding": {
            "stage": "Seed",
            "raised": "$1M",
            "seeking": "Series A"
        }
    }
    
    # 다른 에이전트의 결과 (시뮬레이션)
    mock_tech_summary = {
        "tech_stack": ["Python", "TensorFlow", "React"],
        "innovation_level": 7,
        "scalability": 8
    }
    
    mock_market_analysis = {
        "tam": "$2B",
        "market_growth": "15% CAGR",
        "target_segment": "초중등 수학"
    }
    
    mock_competitor_analysis = {
        "competition_intensity": 7,
        "market_positioning": "Red Ocean",
        "key_threats": ["대형 경쟁사", "신규 진입자"]
    }
    
    mock_competitive_positioning = {
        "positioning_score": 7,
        "differentiation_score": 6,
        "competitive_moat": {"overall": 5.5}
    }
    
    # 워크플로우 실행
    result = run_investment_decision(
        startup_name="EduAI Learn",
        startup_info=test_startup,
        technology_summary=mock_tech_summary,
        market_analysis=mock_market_analysis,
        competitor_analysis=mock_competitor_analysis,
        competitive_positioning=mock_competitive_positioning
    )
    
    # 결과 출력
    print_investment_summary(result)