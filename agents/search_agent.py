from langchain_community.chat_models import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_community.tools.tavily_search.tool import TavilySearchResults
from typing import Dict, List
import json
import re
from dotenv import load_dotenv
from prompts.search_prompt import SEARCH_PROMPT_TEMPLATE

load_dotenv()

# ---------------------------
# Tavily 초기화
# ---------------------------
tavily_tool = TavilySearchResults(k=3)

# ---------------------------
# 프롬프트 로드
# ---------------------------
prompt = PromptTemplate(
    input_variables=["query", "results"],
    template=SEARCH_PROMPT_TEMPLATE.strip()
)

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

# ---------------------------
# LangGraph 노드 함수
# ---------------------------
async def startup_search_node(state: Dict) -> Dict:
    """LangGraph 첫 노드 — 스타트업 탐색"""
    state["stage"] = "Startup Search"
    print(f"진행 단계: {state['stage']}")

    query = state.get("query", "국내 에듀테크 스타트업 3개")
    search_results = tavily_tool.run(query)

    formatted_prompt = prompt.format(query=query, results=search_results)
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

    if not isinstance(parsed, list):
        parsed = [parsed]

    # 정규화
    startups: List[Dict] = []
    for idx, item in enumerate(parsed, start=1):
        if isinstance(item, dict):
            startups.append(item)
        else:
            startups.append({"name": f"startup-{idx}", "raw_output": item})

    print(f"탐색 완료 — {len(startups)}개 스타트업 발견")

    # 첫 번째 스타트업부터 처리 시작
    current = startups[0] if startups else {}

    return {
        "startups": startups,
        "current_startup": current,
        "processed_startups": [],
        "done": False,
    }
