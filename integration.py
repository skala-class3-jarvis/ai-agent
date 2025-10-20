from langgraph.graph import StateGraph, END
from typing import Dict
import asyncio

# === [1] 에이전트 import ===
from agents.search_agent import startup_search_node
from agents.tech_summary_agent import tech_summary_node
from agents.market_analysis_agent import market_analysis_node
from agents.competitor_analysis_agent import competitor_analysis_node
from agents.investment_decision_agent import investment_decision_node
from agents.report_agent import report_node


# === [2] 스타트업별 순차 처리 노드 ===
async def process_next_startup_node(state: Dict) -> Dict:
    """startups 리스트에서 하나씩 꺼내 current_startup에 할당"""
    startups = list(state.get("startups", []))
    processed = list(state.get("processed_startups", []))

    if not startups:
        print("\n모든 스타트업 처리 완료")
        state["done"] = True
        return state

    current = startups.pop(0)
    processed.append(current)
    print(f"\n[진행중] {current.get('name', 'Unknown')} 처리 시작")

    state["current_startup"] = current
    state["startups"] = startups
    state["processed_startups"] = processed
    state["done"] = False
    return state


# === [3] 투자 판단 분기 ===
def route_decision(state: Dict) -> str:
    """투자 판단 결과에 따라 다음 흐름 제어"""
    current = state.get("current_startup")
    if not current:
        return "continue"

    decision = ""
    inv_decision = current.get("investment_decision", {})
    if isinstance(inv_decision, dict):
        decision = inv_decision.get("decision", "")

    decision_lower = str(decision).lower()
    if "유치" in decision_lower or "확정" in decision_lower:
        print(f"투자 확정 감지 → {decision}")
        return "invested"

    print(f"투자 미확정: {decision}")
    return "continue"


# === [4] 완료 여부 확인 ===
def check_done(state: Dict) -> str:
    """모든 스타트업을 처리했는지 여부 확인"""
    return "done" if state.get("done") else "continue"


# === [5] 그래프 구성 ===
graph = StateGraph(dict)

graph.add_node("startup_search", startup_search_node)
graph.add_node("next_startup", process_next_startup_node)
graph.add_node("tech_summary", tech_summary_node)
graph.add_node("market_eval", market_analysis_node)
graph.add_node("competitor_analysis", competitor_analysis_node)
graph.add_node("investment_decision", investment_decision_node)
graph.add_node("report", report_node)

graph.set_entry_point("startup_search")

# 검색 후 순차 처리 시작
graph.add_edge("startup_search", "next_startup")

# next_startup → 처리 or 종료
graph.add_conditional_edges(
    "next_startup",
    check_done,
    {
        "done": END,
        "continue": "tech_summary",
    }
)

# 기본 처리 단계
graph.add_edge("tech_summary", "market_eval")
graph.add_edge("market_eval", "competitor_analysis")
graph.add_edge("competitor_analysis", "investment_decision")

# 투자 판단 → 분기
graph.add_conditional_edges(
    "investment_decision",
    route_decision,
    {
        "invested": "report",
        "continue": "next_startup",
    }
)

# 보고서 생성 후 다음 스타트업 or 종료
graph.add_conditional_edges(
    "report",
    check_done,
    {
        "done": END,
        "continue": "next_startup",
    }
)

investment_graph = graph.compile()

# === [6] 실행 ===
if __name__ == "__main__":
    result = asyncio.run(
        investment_graph.ainvoke(
            {"query": "국내 에듀테크 스타트업", "count": 1},
            config={"recursion_limit": 100}
        )
    )

    print("\n\n=== 보고서 생성 결과 ===\n")
    reports = result.get("reports", [])
    for r in reports:
        if "pdf" in r:
            print(f"{r['name']} → {r['pdf']}")
        else:
            print(f"{r['name']} → {r.get('error', 'Unknown error')}")
