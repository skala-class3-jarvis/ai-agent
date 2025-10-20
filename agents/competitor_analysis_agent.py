import json
import re
from typing import Dict
from dotenv import load_dotenv

from langchain_community.chat_models import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_community.tools import DuckDuckGoSearchRun

from prompts.competitor_analysis_prompt import (
    COMPETITOR_DISCOVERY_PROMPT,
    COMPETITOR_ANALYSIS_PROMPT,
    COMPETITOR_POSITIONING_PROMPT,
)

load_dotenv()

# ---------------------------
# LLM 및 도구 초기화
# ---------------------------
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
search_tool = DuckDuckGoSearchRun()


# ---------------------------
# 유틸: JSON 추출
# ---------------------------
def extract_json(text: str, fallback=None):
    text = text.strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return fallback or {}
    try:
        return json.loads(match.group(0))
    except Exception:
        return fallback or {}


# ---------------------------
# 경쟁사 분석 LangGraph 노드 (단일 스타트업 처리)
# ---------------------------
async def competitor_analysis_node(state: Dict) -> Dict:
    state["stage"] = "Competitor Analysis Node"
    print(f"진행 단계: {state['stage']}")

    current = state.get("current_startup", {})
    if not current:
        print("current_startup 없음 — 스킵")
        return state

    name = current.get("name", "Unknown Startup")
    info_json = json.dumps(current, ensure_ascii=False, indent=2)

    # 1️⃣ 경쟁사 탐색
    try:
        search_query = f"{name} 에듀테크 경쟁사 OR similar edtech companies"
        search_results = search_tool.run(search_query)[:2000]

        prompt_discovery = PromptTemplate(
            input_variables=["startup_info", "search_results"],
            template=COMPETITOR_DISCOVERY_PROMPT.strip(),
        )
        response_1 = await llm.ainvoke(
            prompt_discovery.format(startup_info=info_json, search_results=search_results)
        )
        competitors_obj = extract_json(response_1.content, {"competitors": []})
        competitors = competitors_obj.get("competitors", [])
    except Exception as e:
        print(f"경쟁사 탐색 실패: {e}")
        competitors = []

    # 2️⃣ 경쟁 구도 분석
    try:
        prompt_analysis = PromptTemplate(
            input_variables=["startup_info", "competitors"],
            template=COMPETITOR_ANALYSIS_PROMPT.strip(),
        )
        response_2 = await llm.ainvoke(
            prompt_analysis.format(
                startup_info=info_json,
                competitors=json.dumps(competitors, ensure_ascii=False, indent=2),
            )
        )
        analysis = extract_json(response_2.content, {})
    except Exception as e:
        print(f"경쟁 구도 분석 실패: {e}")
        analysis = {}

    # 3️⃣ 포지셔닝 평가
    try:
        prompt_position = PromptTemplate(
            input_variables=["startup_name", "competitors", "analysis"],
            template=COMPETITOR_POSITIONING_PROMPT.strip(),
        )
        response_3 = await llm.ainvoke(
            prompt_position.format(
                startup_name=name,
                competitors=json.dumps(competitors, ensure_ascii=False, indent=2),
                analysis=json.dumps(analysis, ensure_ascii=False, indent=2),
            )
        )
        positioning = extract_json(response_3.content, {})
    except Exception as e:
        print(f"포지셔닝 평가 실패: {e}")
        positioning = {}

    # 결과 합치기
    current["competitor_list"] = competitors
    current["competitor_analysis"] = analysis
    current["competitive_positioning"] = positioning

    print(f"[{name}] 경쟁사 분석 완료")
    return {"current_startup": current}
