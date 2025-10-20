# ai-agent/agents/market_analysis_agent.py
import json
from typing import Dict
from langchain_core.messages import HumanMessage
from agents.market_analysis_graph import create_market_analysis_graph  # version2 파일을 import

# ---------------------------
# market_analysis_node (ver.2 wrapper)
# ---------------------------
async def market_analysis_node(state: Dict) -> Dict:
    """
    LangGraph용 시장성 평가 노드 (ver.2 내부 그래프 호출)
    Input: {"current_startup": {...}}
    Output: {"current_startup": {... + market_eval}}
    """
    state["stage"] = "Market Analysis Node"
    print(f"진행 단계: {state['stage']}")

    current = state.get("current_startup")
    if not current:
        print("current_startup 없음 — 스킵")
        return state

    name = current.get("name", "Unknown Startup")
    query = current.get("market", name)
    print(f"[시장성 평가 시작] {name}")

    # 내부 ver.2 그래프 불러오기
    graph = create_market_analysis_graph()

    # 초기 상태 정의
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

    # 내부 그래프 실행
    try:
        result = await graph.ainvoke(initial_state)
    except Exception as e:
        print(f"시장 분석 실패: {e}")
        current["market_eval"] = {
            "summary": f"시장성 분석 실패: {e}",
            "size_estimate": "N/A",
            "growth": "N/A",
            "competition": "N/A",
            "risks": [],
            "score": 0,
        }
        state["current_startup"] = current
        return state

    # 결과 병합
    current["market_eval"] = {
        "summary": result.get("final_report", ""),
        "size_estimate": result.get("market_size", ""),
        "growth": result.get("growth_trend", ""),
        "competition": result.get("competition", ""),
        "risks": result.get("risk_factors", ""),
        "score": result.get("final_score", 0),
    }

    print(f"[시장성 평가 완료] {name}")
    state["current_startup"] = current
    return state
