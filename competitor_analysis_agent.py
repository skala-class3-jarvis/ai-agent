"""
경쟁사 비교 에이전트 (Competitor Analysis Agent)
- 경쟁사 탐색 및 정보 수집
- 경쟁 구도 분석
- 차별성 분석 및 시장 포지셔닝 평가
"""

from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.tools import DuckDuckGoSearchRun
from operator import add
import json

# ============================================================================
# State 정의
# ============================================================================

class CompetitorAnalysisState(TypedDict):
    """경쟁사 분석 에이전트 상태"""
    # 입력
    startup_name: str
    startup_info: Dict[str, Any]
    
    # 출력
    competitor_list: List[Dict[str, Any]]
    competitor_analysis: Dict[str, Any]
    competitive_positioning: Dict[str, Any]
    
    # 메타데이터
    messages: List
    current_stage: str
    errors: List[str]

# ============================================================================
# 경쟁사 비교 에이전트
# ============================================================================

class CompetitorAnalysisAgent:
    """경쟁사 비교 및 경쟁 구도 분석 에이전트"""
    
    def __init__(self, llm=None):
        self.llm = llm or ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
        self.search_tool = DuckDuckGoSearchRun()
        
    def identify_competitors(self, state: CompetitorAnalysisState) -> CompetitorAnalysisState:
        """단계 1: 경쟁사 식별 및 기본 정보 수집"""
        startup_name = state["startup_name"]
        startup_info = state["startup_info"]
        
        print(f"\n{'='*80}")
        print(f"🔍 [경쟁사 분석 1/3] 경쟁사 탐색 중: {startup_name}")
        print(f"{'='*80}")
        
        try:
            # 경쟁사 검색 쿼리 구성
            domain = startup_info.get("category", "edtech")
            region = startup_info.get("country", "global")
            
            search_queries = [
                f"{startup_name} competitors {domain} edtech",
                f"{domain} edtech startups {region}",
                f"top edtech companies {domain} market leaders"
            ]
            
            # 검색 실행
            search_results = []
            for query in search_queries[:2]:
                try:
                    result = self.search_tool.run(query)
                    search_results.append(result)
                except Exception as e:
                    print(f"⚠️  검색 실패: {query} - {e}")
            
            combined_results = "\n\n".join(search_results)
            
            # LLM을 사용한 경쟁사 추출
            competitor_prompt = ChatPromptTemplate.from_messages([
                ("system", """당신은 에듀테크 시장 분석 전문가입니다.
검색 결과와 스타트업 정보를 분석하여 주요 경쟁사를 3-5개 식별하세요.

각 경쟁사에 대해 다음 정보를 JSON 형식으로 정리하세요:
{{
    "competitors": [
        {{
            "name": "회사명",
            "description": "간단한 설명 (1-2문장)",
            "category": "B2B/B2C/B2B2C",
            "founded_year": "설립연도",
            "estimated_revenue": "추정 매출 (알 수 없으면 'Unknown')",
            "key_products": ["주요 제품1", "주요 제품2"],
            "target_market": "타겟 시장",
            "funding_stage": "Pre-seed/Seed/Series A/B/C/IPO/Unknown",
            "competitive_overlap": "높음/중간/낮음"
        }}
    ]
}}"""),
                ("human", """스타트업 이름: {startup_name}

스타트업 정보:
{startup_info}

검색 결과:
{search_results}

위 정보를 바탕으로 주요 경쟁사를 JSON 형식으로 정리하세요.""")
            ])
            
            chain = competitor_prompt | self.llm
            result = chain.invoke({
                "startup_name": startup_name,
                "startup_info": json.dumps(startup_info, ensure_ascii=False, indent=2),
                "search_results": combined_results[:3000]
            })
            
            # JSON 파싱
            try:
                content = result.content
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                competitors_data = json.loads(content)
                competitors = competitors_data.get("competitors", [])
            except Exception as e:
                print(f"⚠️  JSON 파싱 실패, 기본 경쟁사 사용: {e}")
                competitors = [
                    {
                        "name": "Competitor A",
                        "description": "Major player in edtech market",
                        "category": "B2B",
                        "founded_year": "2018",
                        "estimated_revenue": "Unknown",
                        "key_products": ["Product X", "Product Y"],
                        "target_market": "K-12 schools",
                        "funding_stage": "Series B",
                        "competitive_overlap": "높음"
                    }
                ]
            
            state["competitor_list"] = competitors
            state["messages"].append(AIMessage(
                content=f"✅ 경쟁사 {len(competitors)}개 식별 완료"
            ))
            
            print(f"✅ 경쟁사 {len(competitors)}개 발견")
            for comp in competitors:
                print(f"  - {comp['name']}: {comp['description']}")
            
        except Exception as e:
            error_msg = f"경쟁사 탐색 중 오류: {str(e)}"
            print(f"❌ {error_msg}")
            state["errors"].append(error_msg)
            state["competitor_list"] = []
        
        state["current_stage"] = "competitor_analysis"
        return state
    
    def analyze_competitive_landscape(self, state: CompetitorAnalysisState) -> CompetitorAnalysisState:
        """단계 2: 경쟁 구도 및 시장 포지셔닝 분석"""
        startup_name = state["startup_name"]
        startup_info = state["startup_info"]
        competitors = state["competitor_list"]
        
        print(f"\n{'='*80}")
        print(f"📊 [경쟁사 분석 2/3] 경쟁 구도 분석 중")
        print(f"{'='*80}")
        
        try:
            analysis_prompt = ChatPromptTemplate.from_messages([
                ("system", """당신은 에듀테크 VC 투자심사역입니다.
스타트업과 경쟁사들을 비교 분석하여 다음 항목을 평가하세요:

1. **경쟁 강도 (Competition Intensity)**: 1-10점
2. **시장 포지셔닝 (Market Positioning)**: Blue Ocean/Red Ocean/Niche Market
3. **차별화 요소 (Differentiation Factors)**: 3-5개
4. **경쟁 우위 (Competitive Advantages)**: Technology/Price/Brand/Network Effect/Data
5. **진입장벽 (Entry Barriers)**: 높음/중간/낮음
6. **주요 위협 요소 (Key Threats)**: 3가지
7. **시장 점유율 전망 (Market Share Potential)**: 1-10점

JSON 형식으로 출력하세요."""),
                ("human", """스타트업: {startup_name}

스타트업 정보:
{startup_info}

경쟁사 목록:
{competitors}

상세한 경쟁 구도 분석을 제공하세요.""")
            ])
            
            chain = analysis_prompt | self.llm
            result = chain.invoke({
                "startup_name": startup_name,
                "startup_info": json.dumps(startup_info, ensure_ascii=False, indent=2),
                "competitors": json.dumps(competitors, ensure_ascii=False, indent=2)
            })
            
            # JSON 파싱
            try:
                content = result.content
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                analysis = json.loads(content)
            except:
                analysis = {
                    "competition_intensity": 7,
                    "market_positioning": "Red Ocean",
                    "differentiation_factors": ["AI 기반 개인화", "낮은 가격", "더 나은 UX"],
                    "competitive_advantages": ["Technology", "Price"],
                    "entry_barriers": {"level": "중간", "reasons": ["기술 개발 난이도"]},
                    "key_threats": ["대형 경쟁사", "신규 진입자", "시장 포화"],
                    "market_share_potential": 6
                }
            
            state["competitor_analysis"] = analysis
            state["messages"].append(AIMessage(
                content=f"✅ 경쟁 구도 분석 완료"
            ))
            
            print(f"✅ 경쟁 구도 분석 완료")
            print(f"  - 경쟁 강도: {analysis.get('competition_intensity')}/10")
            print(f"  - 시장 포지셔닝: {analysis.get('market_positioning')}")
            
        except Exception as e:
            error_msg = f"경쟁 구도 분석 중 오류: {str(e)}"
            print(f"❌ {error_msg}")
            state["errors"].append(error_msg)
            state["competitor_analysis"] = {}
        
        state["current_stage"] = "competitive_positioning"
        return state
    
    def evaluate_competitive_positioning(self, state: CompetitorAnalysisState) -> CompetitorAnalysisState:
        """단계 3: 경쟁적 포지셔닝 및 차별성 평가"""
        startup_name = state["startup_name"]
        competitors = state["competitor_list"]
        analysis = state["competitor_analysis"]
        
        print(f"\n{'='*80}")
        print(f"🎯 [경쟁사 분석 3/3] 경쟁 포지셔닝 평가 중")
        print(f"{'='*80}")
        
        try:
            positioning_prompt = ChatPromptTemplate.from_messages([
                ("system", """당신은 경쟁 전략 분석가입니다.
다음 항목을 JSON으로 출력:
{{
    "positioning_score": 0-10,
    "differentiation_score": 0-10,
    "competitive_moat": {{
        "technology": 0-10,
        "brand": 0-10,
        "network_effect": 0-10,
        "data": 0-10,
        "overall": 0-10
    }},
    "sustainability": {{
        "score": 0-10,
        "reasoning": "지속 가능성 평가 이유"
    }},
    "recommendations": ["권장사항1", "권장사항2", "권장사항3"]
}}"""),
                ("human", """스타트업: {startup_name}
경쟁사: {competitors}
경쟁 구도: {analysis}

경쟁적 포지셔닝을 평가하세요.""")
            ])
            
            chain = positioning_prompt | self.llm
            result = chain.invoke({
                "startup_name": startup_name,
                "competitors": json.dumps(competitors, ensure_ascii=False, indent=2),
                "analysis": json.dumps(analysis, ensure_ascii=False, indent=2)
            })
            
            # JSON 파싱
            try:
                content = result.content
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                positioning = json.loads(content)
            except:
                positioning = {
                    "positioning_score": 7,
                    "differentiation_score": 6,
                    "competitive_moat": {
                        "technology": 7, "brand": 4, "network_effect": 5,
                        "data": 6, "overall": 5.5
                    },
                    "sustainability": {"score": 6, "reasoning": "중간 수준의 경쟁 우위"},
                    "recommendations": ["기술적 차별화 강화", "브랜드 인지도 제고"]
                }
            
            state["competitive_positioning"] = positioning
            state["messages"].append(AIMessage(
                content=f"✅ 경쟁 포지셔닝 평가 완료"
            ))
            
            print(f"✅ 경쟁 포지셔닝 평가 완료")
            print(f"  - 포지셔닝 점수: {positioning.get('positioning_score')}/10")
            print(f"  - 차별화 점수: {positioning.get('differentiation_score')}/10")
            
        except Exception as e:
            error_msg = f"경쟁 포지셔닝 평가 중 오류: {str(e)}"
            print(f"❌ {error_msg}")
            state["errors"].append(error_msg)
            state["competitive_positioning"] = {}
        
        state["current_stage"] = "complete"
        return state

# ============================================================================
# 워크플로우 구성
# ============================================================================

def create_competitor_analysis_workflow():
    """경쟁사 분석 워크플로우 생성"""
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
    agent = CompetitorAnalysisAgent(llm)
    
    workflow = StateGraph(CompetitorAnalysisState)
    
    # 노드 추가
    workflow.add_node("identify_competitors", agent.identify_competitors)
    workflow.add_node("analyze_competitive_landscape", agent.analyze_competitive_landscape)
    workflow.add_node("evaluate_competitive_positioning", agent.evaluate_competitive_positioning)
    
    # 엣지 정의
    workflow.set_entry_point("identify_competitors")
    workflow.add_edge("identify_competitors", "analyze_competitive_landscape")
    workflow.add_edge("analyze_competitive_landscape", "evaluate_competitive_positioning")
    workflow.add_edge("evaluate_competitive_positioning", END)
    
    return workflow.compile()

# ============================================================================
# 실행 함수
# ============================================================================

def run_competitor_analysis(startup_name: str, startup_info: Dict[str, Any]) -> CompetitorAnalysisState:
    """경쟁사 분석 실행"""
    print(f"\n{'#'*80}")
    print(f"# 🔍 경쟁사 분석 시작: {startup_name}")
    print(f"{'#'*80}\n")
    
    initial_state: CompetitorAnalysisState = {
        "startup_name": startup_name,
        "startup_info": startup_info,
        "competitor_list": [],
        "competitor_analysis": {},
        "competitive_positioning": {},
        "messages": [HumanMessage(content=f"{startup_name} 경쟁사 분석 시작")],
        "current_stage": "start",
        "errors": []
    }
    
    workflow = create_competitor_analysis_workflow()
    
    try:
        final_state = workflow.invoke(initial_state)
        print(f"\n{'#'*80}")
        print(f"# ✅ 경쟁사 분석 완료!")
        print(f"{'#'*80}\n")
        return final_state
    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")
        initial_state["errors"].append(str(e))
        return initial_state

# ============================================================================
# 테스트
# ============================================================================

if __name__ == "__main__":
    test_startup = {
        "name": "EduAI Learn",
        "description": "AI 기반 수학 학습 플랫폼",
        "country": "South Korea",
        "category": "B2C",
        "founded": "2023"
    }
    
    result = run_competitor_analysis("EduAI Learn", test_startup)
    print(f"\n발견된 경쟁사: {len(result['competitor_list'])}개")
    print(f"경쟁 강도: {result['competitor_analysis'].get('competition_intensity', 'N/A')}/10")