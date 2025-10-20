from dotenv import load_dotenv
load_dotenv()

import os
import json
from typing import Annotated, Sequence, TypedDict, Dict, Any, List, Literal
from pydantic import BaseModel, Field

# LangChain imports
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_openai import ChatOpenAI

# LangGraph imports
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

# Vector DB (faiss) and document loader imports
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain_core.tools.retriever import create_retriever_tool

# External web search tool
from langchain_community.tools import DuckDuckGoSearchRun

# HuggingFace sentence transformers
from langchain_huggingface import HuggingFaceEmbeddings

# =============================================================================
# 1. 데이터 로딩 및 벡터스토어 세팅
# =============================================================================
DATA_DIR = "data"
PERSIST_PATH = "db_faiss"
EMBEDDINGS_MODEL = HuggingFaceEmbeddings(
    model_name="dragonkue/multilingual-e5-small-ko",
    model_kwargs={"device": "cpu"}
)

def build_vector_db():
    loader = DirectoryLoader(DATA_DIR, glob="**/*.pdf", loader_cls=PyPDFLoader)
    docs = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    docs_split = splitter.split_documents(docs)
    db = FAISS.from_documents(docs_split, EMBEDDINGS_MODEL)
    db.save_local(PERSIST_PATH)
    return db

if os.path.exists(PERSIST_PATH):
    db = FAISS.load_local(
        PERSIST_PATH, 
        EMBEDDINGS_MODEL,
        allow_dangerous_deserialization=True
    )
else:
    db = build_vector_db()

retriever = db.as_retriever(search_type="similarity", search_kwargs={"k": 5})
search_tool = DuckDuckGoSearchRun()

# =============================================================================
# 2. 고도화된 상태 정의 (AgentState)
# =============================================================================
class MarketAnalysisState(TypedDict):
    """시장성 평가 에이전트의 상태"""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    query: str  # 원본 사용자 쿼리
    query_type: str  # 쿼리 분류 결과 (market_size, trend, competition, forecast 등)
    rag_data: str  # 내부 DB 검색 결과
    web_data: str  # 외부 웹 검색 결과
    market_size: str  # 시장 규모 분석
    growth_trend: str  # 성장 추세 분석
    competition: str  # 경쟁 환경 분석
    risk_factors: str  # 리스크 요인 분석
    final_score: int  # 최종 시장성 점수 (0-100)
    final_report: str  # 최종 종합 리포트
    needs_web_search: bool  # 웹 검색 필요 여부
    analysis_depth: str  # 분석 깊이 (basic, intermediate, advanced)

# =============================================================================
# 3. LLM 모델 정의
# =============================================================================
MODEL_NAME = "gpt-4o-mini"
llm = ChatOpenAI(temperature=0.3, model=MODEL_NAME, streaming=True)
llm_creative = ChatOpenAI(temperature=0.7, model=MODEL_NAME, streaming=True)

# =============================================================================
# 4. 쿼리 분류 및 라우팅을 위한 Pydantic 모델
# =============================================================================
class QueryClassification(BaseModel):
    """쿼리 분류 결과"""
    query_type: Literal["market_size", "trend", "competition", "forecast", "general"] = Field(
        description="쿼리의 주요 관심사 분류"
    )
    needs_web_search: bool = Field(
        description="최신 정보가 필요한지 여부"
    )
    analysis_depth: Literal["basic", "intermediate", "advanced"] = Field(
        description="필요한 분석 깊이"
    )

# =============================================================================
# 5. 노드 함수들 정의
# =============================================================================

def classify_query_node(state: MarketAnalysisState) -> Dict[str, Any]:
    """
    Step 1: 사용자 쿼리를 분석하여 분류하고 분석 전략 결정
    """
    query = state["query"]
    
    classification_prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 시장 분석 쿼리 분류 전문가입니다. 
사용자의 쿼리를 분석하여 다음을 판단하세요:
1. query_type: 주요 관심사 (market_size, trend, competition, forecast, general)
2. needs_web_search: 최신 데이터가 필요한지 (true/false)
3. analysis_depth: 필요한 분석 깊이 (basic, intermediate, advanced)"""),
        ("human", "{query}")
    ])
    
    structured_llm = llm.with_structured_output(QueryClassification)
    classification = structured_llm.invoke(classification_prompt.format_messages(query=query))
    
    return {
        "query_type": classification.query_type,
        "needs_web_search": classification.needs_web_search,
        "analysis_depth": classification.analysis_depth,
        "messages": [AIMessage(content=f"쿼리 분석 완료: {classification.query_type} (깊이: {classification.analysis_depth})")]
    }

def retrieve_internal_data_node(state: MarketAnalysisState) -> Dict[str, Any]:
    """
    Step 2: 내부 벡터 DB에서 관련 데이터 검색
    """
    query = state["query"]
    query_type = state.get("query_type", "general")
    
    # 쿼리 타입에 따른 검색 쿼리 확장
    enhanced_query = f"{query} {query_type} 시장 분석"
    
    rag_docs = retriever.invoke(enhanced_query)
    rag_data = "\n\n---\n\n".join([
        f"[문서 {i+1}]\n{doc.page_content[:600]}" 
        for i, doc in enumerate(rag_docs)
    ]) if rag_docs else "관련 내부 데이터 없음"
    
    return {
        "rag_data": rag_data[:3000],
        "messages": [AIMessage(content=f"내부 DB 검색 완료: {len(rag_docs)}개 문서 발견")]
    }

def web_search_node(state: MarketAnalysisState) -> Dict[str, Any]:
    """
    Step 3: 외부 웹 검색 (조건부 실행)
    """
    query = state["query"]
    
    # 다양한 검색 쿼리 구성
    search_queries = [
        f"{query} 시장 규모 전망 2024 2025",
        f"{query} 산업 동향 리포트",
        f"{query} 경쟁사 분석"
    ]
    
    web_results = []
    for sq in search_queries[:2]:  # 최대 2개 쿼리만 실행
        try:
            result = search_tool.run(sq)
            web_results.append(f"[검색: {sq}]\n{result[:800]}")
        except:
            continue
    
    web_data = "\n\n---\n\n".join(web_results) if web_results else "웹 검색 결과 없음"
    
    return {
        "web_data": web_data[:2500],
        "messages": [AIMessage(content="웹 검색 완료")]
    }

def analyze_market_size_node(state: MarketAnalysisState) -> Dict[str, Any]:
    """
    Step 4a: 시장 규모 분석
    """
    prompt = PromptTemplate(
        input_variables=["query", "rag_data", "web_data"],
        template="""시장 규모 분석 전문가로서, 다음 정보를 바탕으로 시장 규모를 분석하세요:

쿼리: {query}

내부 데이터:
{rag_data}

외부 데이터:
{web_data}

다음 항목을 포함하여 분석하세요:
1. 현재 시장 규모 (금액, 단위 명시)
2. 최근 3-5년 성장률
3. 주요 세그먼트별 비중
4. 지역별 시장 분포 (해당시)

간결하고 정량적인 분석을 제공하세요."""
    )
    
    response = llm.invoke([HumanMessage(
        content=prompt.format(
            query=state["query"],
            rag_data=state.get("rag_data", "N/A"),
            web_data=state.get("web_data", "N/A")
        )
    )])
    
    return {
        "market_size": response.content,
        "messages": [AIMessage(content="시장 규모 분석 완료")]
    }

def analyze_growth_trend_node(state: MarketAnalysisState) -> Dict[str, Any]:
    """
    Step 4b: 성장 추세 및 트렌드 분석
    """
    prompt = PromptTemplate(
        input_variables=["query", "rag_data", "web_data"],
        template="""성장 트렌드 분석 전문가로서, 다음 정보를 바탕으로 시장 성장 추세를 분석하세요:

쿼리: {query}

내부 데이터:
{rag_data}

외부 데이터:
{web_data}

다음 항목을 포함하여 분석하세요:
1. 향후 5년 성장 전망 (CAGR)
2. 주요 성장 동력 (기술, 규제, 소비자 행동 등)
3. 시장 성숙도 (도입기/성장기/성숙기/쇠퇴기)
4. 최신 트렌드 및 혁신

구체적인 수치와 근거를 포함하세요."""
    )
    
    response = llm.invoke([HumanMessage(
        content=prompt.format(
            query=state["query"],
            rag_data=state.get("rag_data", "N/A"),
            web_data=state.get("web_data", "N/A")
        )
    )])
    
    return {
        "growth_trend": response.content,
        "messages": [AIMessage(content="성장 추세 분석 완료")]
    }

def analyze_competition_node(state: MarketAnalysisState) -> Dict[str, Any]:
    """
    Step 4c: 경쟁 환경 분석
    """
    prompt = PromptTemplate(
        input_variables=["query", "rag_data", "web_data"],
        template="""경쟁 분석 전문가로서, 다음 정보를 바탕으로 경쟁 환경을 분석하세요:

쿼리: {query}

내부 데이터:
{rag_data}

외부 데이터:
{web_data}

다음 항목을 포함하여 분석하세요:
1. 주요 경쟁사 및 시장 점유율
2. 시장 집중도 (HHI 또는 CRn 지수 언급 가능시)
3. 진입 장벽 (높음/중간/낮음) 및 이유
4. 경쟁 강도 평가

Porter의 5 Forces 관점을 활용하여 분석하세요."""
    )
    
    response = llm.invoke([HumanMessage(
        content=prompt.format(
            query=state["query"],
            rag_data=state.get("rag_data", "N/A"),
            web_data=state.get("web_data", "N/A")
        )
    )])
    
    return {
        "competition": response.content,
        "messages": [AIMessage(content="경쟁 환경 분석 완료")]
    }

def analyze_risk_factors_node(state: MarketAnalysisState) -> Dict[str, Any]:
    """
    Step 4d: 리스크 요인 분석
    """
    prompt = PromptTemplate(
        input_variables=["query", "market_size", "growth_trend", "competition"],
        template="""리스크 분석 전문가로서, 다음 분석 결과를 종합하여 주요 리스크 요인을 식별하세요:

시장: {query}

시장 규모 분석:
{market_size}

성장 추세 분석:
{growth_trend}

경쟁 환경 분석:
{competition}

다음 리스크를 평가하세요:
1. 시장 리스크 (수요 변동성, 경기 민감도)
2. 기술 리스크 (기술 변화, 대체재 위협)
3. 규제 리스크 (법규 변화, 정책 리스크)
4. 경쟁 리스크 (신규 진입자, 가격 경쟁)

각 리스크를 높음/중간/낮음으로 평가하고 근거를 제시하세요."""
    )
    
    response = llm.invoke([HumanMessage(
        content=prompt.format(
            query=state["query"],
            market_size=state.get("market_size", "N/A"),
            growth_trend=state.get("growth_trend", "N/A"),
            competition=state.get("competition", "N/A")
        )
    )])
    
    return {
        "risk_factors": response.content,
        "messages": [AIMessage(content="리스크 요인 분석 완료")]
    }

def calculate_market_score_node(state: MarketAnalysisState) -> Dict[str, Any]:
    """
    Step 5: 종합 시장성 점수 산출
    """
    class MarketScore(BaseModel):
        """시장성 점수 모델"""
        market_size_score: int = Field(description="시장 규모 점수 (0-25)")
        growth_score: int = Field(description="성장성 점수 (0-30)")
        competition_score: int = Field(description="경쟁 환경 점수 (0-25, 낮은 경쟁=높은 점수)")
        risk_score: int = Field(description="리스크 점수 (0-20, 낮은 리스크=높은 점수)")
        total_score: int = Field(description="총점 (0-100)")
        justification: str = Field(description="점수 산정 근거")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 시장성 평가 전문가입니다. 
다음 분석 결과를 바탕으로 객관적인 시장성 점수를 산출하세요:
- 시장 규모 점수: 0-25점 (규모가 클수록 높음)
- 성장성 점수: 0-30점 (성장률이 높을수록 높음)
- 경쟁 환경 점수: 0-25점 (경쟁이 약할수록 높음)
- 리스크 점수: 0-20점 (리스크가 낮을수록 높음)
합계: 0-100점"""),
        ("human", """
시장: {query}

시장 규모: {market_size}
성장 추세: {growth_trend}
경쟁 환경: {competition}
리스크 요인: {risk_factors}

위 정보를 바탕으로 점수를 산출하세요.""")
    ])
    
    structured_llm = llm.with_structured_output(MarketScore)
    score_result = structured_llm.invoke(prompt.format_messages(
        query=state["query"],
        market_size=state.get("market_size", "N/A"),
        growth_trend=state.get("growth_trend", "N/A"),
        competition=state.get("competition", "N/A"),
        risk_factors=state.get("risk_factors", "N/A")
    ))
    
    return {
        "final_score": score_result.total_score,
        "messages": [AIMessage(content=f"시장성 점수 산출 완료: {score_result.total_score}/100점\n\n{score_result.justification}")]
    }

def generate_final_report_node(state: MarketAnalysisState) -> Dict[str, Any]:
    """
    Step 6: 최종 종합 리포트 생성
    """
    prompt = PromptTemplate(
        input_variables=["query", "market_size", "growth_trend", "competition", 
                        "risk_factors", "final_score", "analysis_depth"],
        template="""종합 시장 분석 리포트를 작성하세요.

시장: {query}
분석 깊이: {analysis_depth}
최종 시장성 점수: {final_score}/100

=== 분석 결과 ===

1. 시장 규모 분석
{market_size}

2. 성장 추세 분석
{growth_trend}

3. 경쟁 환경 분석
{competition}

4. 리스크 요인 분석
{risk_factors}

=== 종합 리포트 작성 지침 ===
다음 구조로 executive summary 형식의 리포트를 작성하세요:

1. 핵심 요약 (2-3문단)
2. 시장 기회 평가
3. 주요 성공 요인
4. 권고사항 (진입 전략, 주의사항)
5. 결론

명확하고 실행 가능한 인사이트를 제공하세요."""
    )
    
    response = llm_creative.invoke([HumanMessage(
        content=prompt.format(
            query=state["query"],
            market_size=state.get("market_size", "N/A"),
            growth_trend=state.get("growth_trend", "N/A"),
            competition=state.get("competition", "N/A"),
            risk_factors=state.get("risk_factors", "N/A"),
            final_score=state.get("final_score", "N/A"),
            analysis_depth=state.get("analysis_depth", "intermediate")
        )
    )])
    
    return {
        "final_report": response.content,
        "messages": [AIMessage(content="최종 리포트 생성 완료")]
    }

# =============================================================================
# 6. 조건부 라우팅 함수
# =============================================================================

def should_do_web_search(state: MarketAnalysisState) -> Literal["web_search", "skip_web_search"]:
    """웹 검색 필요 여부 판단"""
    if state.get("needs_web_search", False):
        return "web_search"
    return "skip_web_search"

def route_by_analysis_depth(state: MarketAnalysisState) -> Literal["detailed_analysis", "basic_analysis"]:
    """분석 깊이에 따른 라우팅"""
    depth = state.get("analysis_depth", "intermediate")
    if depth == "advanced":
        return "detailed_analysis"
    return "basic_analysis"

# =============================================================================
# 7. LangGraph 워크플로우 구성
# =============================================================================

def create_market_analysis_graph():
    """시장성 평가 그래프 생성"""
    workflow = StateGraph(MarketAnalysisState)
    
    # 노드 추가
    workflow.add_node("classify_query", classify_query_node)
    workflow.add_node("retrieve_internal", retrieve_internal_data_node)
    workflow.add_node("web_search", web_search_node)
    workflow.add_node("analyze_market_size", analyze_market_size_node)
    workflow.add_node("analyze_growth", analyze_growth_trend_node)
    workflow.add_node("analyze_competition", analyze_competition_node)
    workflow.add_node("analyze_risks", analyze_risk_factors_node)
    workflow.add_node("calculate_score", calculate_market_score_node)
    workflow.add_node("generate_report", generate_final_report_node)
    
    # 엣지 구성
    workflow.add_edge(START, "classify_query")
    workflow.add_edge("classify_query", "retrieve_internal")
    
    # 조건부 엣지: 웹 검색 여부
    workflow.add_conditional_edges(
        "retrieve_internal",
        should_do_web_search,
        {
            "web_search": "web_search",
            "skip_web_search": "analyze_market_size"
        }
    )
    
    workflow.add_edge("web_search", "analyze_market_size")
    
    # 순차적 분석 단계
    workflow.add_edge("analyze_market_size", "analyze_growth")
    workflow.add_edge("analyze_growth", "analyze_competition")
    workflow.add_edge("analyze_competition", "analyze_risks")
    workflow.add_edge("analyze_risks", "calculate_score")
    workflow.add_edge("calculate_score", "generate_report")
    workflow.add_edge("generate_report", END)
    
    return workflow.compile()

# =============================================================================
# 8. 메인 실행 부분
# =============================================================================

def run_market_analysis(query: str, verbose: bool = True):
    """시장성 평가 실행"""
    graph = create_market_analysis_graph()
    
    initial_state = {
        "messages": [HumanMessage(content=query)],
        "query": query,
        "query_type": "",
        "rag_data": "",
        "web_data": "",
        "market_size": "",
        "growth_trend": "",
        "competition": "",
        "risk_factors": "",
        "final_score": 0,
        "final_report": "",
        "needs_web_search": False,
        "analysis_depth": "intermediate"
    }
    
    result = graph.invoke(initial_state)
    
    if verbose:
        print("\n" + "="*60)
        print(f"📌 시장 분석 요청: {query}")
        print("="*60)
        print(f"\n[📊] 최종 시장성 점수: \033[1m{result['final_score']}/100\033[0m")
        print("\n[📝] 종합 리포트\n" + "-"*40)
        print(result['final_report'])
        print("-"*40)
        print("\n[전체 결과를 JSON으로 표시]")
        print(json.dumps({k: v for k, v in result.items() if k not in ("messages",)}, ensure_ascii=False, indent=2))
        print("="*60 + "\n")
    
    return result

# 사용 예시
if __name__ == "__main__":
    # 예시 1: 기본 시장 분석
    result1 = run_market_analysis("에듀테크 시장 분석해줘")

    # 보기 좋게 요약 출력
    print("\n\n[🔎 에듀테크 시장 분석 요약]")
    print(f"최종 점수: {result1['final_score']}/100")
    print("\n<< 요약본 >>\n")
    print(result1['final_report'])
    print("\n[JSON 결과]\n")
    print(json.dumps({k: v for k, v in result1.items() if k not in ("messages",)}, ensure_ascii=False, indent=2))


    # 예시 2: 경쟁 환경 중심 분석
    # result2 = run_market_analysis("AI 챗봇 시장의 경쟁 구도는?")
    
    # 예시 3: 성장 전망 중심 분석
    # result3 = run_market_analysis("전기차 배터리 시장 5년 후 전망")