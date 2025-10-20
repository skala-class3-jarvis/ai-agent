from langchain_community.chat_models import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from typing import Dict
import json
import re
from dotenv import load_dotenv
from prompts.tech_summary_prompt import TECH_SUMMARY_PROMPT_TEMPLATE

load_dotenv()

# ---------------------------
# LLM 초기화
# ---------------------------
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

prompt = PromptTemplate(
    input_variables=["startup_info"],
    template=TECH_SUMMARY_PROMPT_TEMPLATE.strip()
)

# ---------------------------
# LangGraph 노드 함수
# ---------------------------
async def tech_summary_node(state: Dict) -> Dict:
    """
    LangGraph용 기술 요약 노드
    Input: {"current_startup": {...}}
    Output: {"current_startup": {... + tech_summary}}
    """
    state["stage"] = "Tech Summary Node"
    print(f"진행 단계: {state['stage']}")

    current = state.get("current_startup", {})
    if not current:
        print("current_startup 없음 — 스킵")
        return state

    try:
        startup_info = json.dumps(current, ensure_ascii=False, indent=2)
        formatted_prompt = prompt.format(startup_info=startup_info)
        response = await llm.ainvoke(formatted_prompt)
        text = response.content.strip()

        # JSON만 추출
        match = re.search(r"\{.*\}", text, re.DOTALL)
        json_str = match.group(0) if match else text
        json_str = json_str.replace("```json", "").replace("```", "").strip()

        parsed = json.loads(json_str)
    except Exception as e:
        parsed = {
            "summary": f"요약 실패: {e}",
            "highlights": [],
            "gaps": []
        }

    current["tech_summary"] = parsed

    print(f"[{current.get('name', 'Unknown')}] 기술 요약 완료")
    state["current_startup"] = current
    return state

