from langchain_community.chat_models import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_community.tools.tavily_search.tool import TavilySearchResults
from typing import Dict, List
import json, re
from dotenv import load_dotenv
from prompts.search_prompt import SEARCH_PROMPT_TEMPLATE

load_dotenv()

# Tavily 초기화
tavily_tool = TavilySearchResults(k=5)  # 검색 결과 문서 수 (필요 시 늘리기)
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

# 프롬프트 템플릿 (count 추가)
prompt = PromptTemplate(
    input_variables=["query", "results", "count"],
    template=SEARCH_PROMPT_TEMPLATE.strip()
)


# ---------------------------
# LangGraph 첫 노드 (수정본)
# ---------------------------
async def startup_search_node(state: Dict) -> Dict:
    """LangGraph 첫 노드 — 스타트업 탐색 (count 적용, 다른 노드 영향 없음)"""
    state["stage"] = "Startup Search"
    print(f"진행 단계: {state['stage']}")

    # 🎯 이 노드에서만 사용할 count
    count = state.get("count", 3)  # 기본 3개
    query = state.get("query", f"국내 에듀테크 스타트업 {count}개")

    # Tavily 검색 실행
    search_results = tavily_tool.run(query)

    # count 전달 포함한 프롬프트 구성
    formatted_prompt = prompt.format(query=query, results=search_results, count=count)

    # LLM 호출
    response = await llm.ainvoke(formatted_prompt)
    text = response.content.strip()

    # JSON 블록 추출
    match = re.search(r"\[.*\]", text, re.DOTALL)
    json_str = match.group(0) if match else text
    json_str = json_str.replace("```json", "").replace("```", "").strip()

    try:
        parsed = json.loads(json_str)
    except Exception:
        parsed = [{"raw_output": text}]

    # LLM 결과가 list가 아닐 경우 보정
    if not isinstance(parsed, list):
        parsed = [parsed]

    # ✅ 스타트업 개수 강제 제한
    startups = []
    for idx, item in enumerate(parsed[:count], start=1):
        if isinstance(item, dict):
            startups.append(item)
        else:
            startups.append({"name": f"startup-{idx}", "raw_output": item})

    print(f"탐색 완료 — {len(startups)}개 스타트업 발견")

    current = startups[0] if startups else {}

    return {
        "startups": startups,
        "current_startup": current,
        "processed_startups": [],
        "done": False,
    }
