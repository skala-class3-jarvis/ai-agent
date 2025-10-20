import json, re
from typing import Dict
from dotenv import load_dotenv
from langchain_community.chat_models import ChatOpenAI
from langchain_core.prompts import PromptTemplate

from prompts.investment_decision_prompt import (
    INVESTMENT_SCORING_PROMPT,
    INVESTMENT_RISK_PROMPT,
    INVESTMENT_DECISION_PROMPT,
)

load_dotenv()

# ---------------------------
# LLM 초기화
# ---------------------------
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)

# ---------------------------
# JSON 추출 유틸
# ---------------------------
def extract_json(text: str, fallback=None):
    match = re.search(r"\{.*\}", text.strip(), re.DOTALL)
    if not match:
        return fallback or {}
    try:
        return json.loads(match.group(0))
    except Exception:
        return fallback or {}

# ---------------------------
# 투자 판단 노드 (단일 스타트업)
# ---------------------------
async def investment_decision_node(state: Dict) -> Dict:
    """
    LangGraph 투자 판단 노드
    Input: {"current_startup": {...}}
    Output: {"current_startup": {... + investment_decision}}
    """
    state["stage"] = "Investment Decision Node"
    print(f"진행 단계: {state['stage']}")

    current = state.get("current_startup", {})
    if not current:
        print("current_startup 없음 — 스킵")
        return state

    name = current.get("name", "Unknown Startup")

    # 1️⃣ 투자 점수 계산
    try:
        prompt_score = PromptTemplate(
            input_variables=[
                "startup_info", "tech_summary", "market_analysis",
                "competitor_analysis", "competitive_positioning"
            ],
            template=INVESTMENT_SCORING_PROMPT.strip(),
        )
        formatted_score = prompt_score.format(
            startup_info=json.dumps(current, ensure_ascii=False, indent=2),
            tech_summary=json.dumps(current.get("tech_summary", {}), ensure_ascii=False, indent=2),
            market_analysis=json.dumps(current.get("market_eval", {}), ensure_ascii=False, indent=2),
            competitor_analysis=json.dumps(current.get("competitor_analysis", {}), ensure_ascii=False, indent=2),
            competitive_positioning=json.dumps(current.get("competitive_positioning", {}), ensure_ascii=False, indent=2),
        )
        resp1 = await llm.ainvoke(formatted_score)
        scores = extract_json(resp1.content, {"total_score": 60})
    except Exception as e:
        print(f"투자 점수 계산 실패: {e}")
        scores = {"total_score": 60}

    # 2️⃣ 리스크 평가
    try:
        prompt_risk = PromptTemplate(
            input_variables=["startup_info", "scores", "competitor_analysis"],
            template=INVESTMENT_RISK_PROMPT.strip(),
        )
        formatted_risk = prompt_risk.format(
            startup_info=json.dumps(current, ensure_ascii=False, indent=2),
            scores=json.dumps(scores, ensure_ascii=False, indent=2),
            competitor_analysis=json.dumps(current.get("competitor_analysis", {}), ensure_ascii=False, indent=2),
        )
        resp2 = await llm.ainvoke(formatted_risk)
        risks = extract_json(resp2.content, {"overall_risk_score": 5.5})
    except Exception as e:
        print(f"리스크 평가 실패: {e}")
        risks = {"overall_risk_score": 5.5}

    # 3️⃣ 최종 의사결정
    try:
        total_score = scores.get("total_score", 0)
        prompt_decision = PromptTemplate(
            input_variables=["startup_name", "total_score", "risk_assessment"],
            template=INVESTMENT_DECISION_PROMPT.strip(),
        )
        formatted_decision = prompt_decision.format(
            startup_name=name,
            total_score=total_score,
            risk_assessment=json.dumps(risks, ensure_ascii=False, indent=2),
        )
        resp3 = await llm.ainvoke(formatted_decision)
        decision = extract_json(resp3.content, {"decision": "Hold"})
    except Exception as e:
        print(f"투자 의사결정 실패: {e}")
        decision = {"decision": "Hold"}

    # 결과 병합
    current["investment_scores"] = scores
    current["risk_assessment"] = risks
    current["investment_decision"] = decision

    print(f"[{name}] 투자 판단 완료: {decision.get('decision', 'Unknown')}")
    return {"current_startup": current}
