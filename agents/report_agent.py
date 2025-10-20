import os
import re
import json
import unicodedata
from typing import Any, Dict, List, Optional

import aiohttp
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI


load_dotenv()


SUMMARY_TEMPLATE = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an investment memo editor creating one-page summaries for edtech startups. "
            "Use the supplied data only. Reply in English. Produce compact prose: "
            "paragraphs must be 2-3 sentences (max 350 characters) and bullet points must be under 70 characters each. "
            "Return a JSON object with keys: \n"
            "{\n"
            "  \"executive_summary\": \"short paragraph\",\n"
            "  \"technology\": {\"paragraph\": \"...\", \"bullets\": []},\n"
            "  \"market_competition\": {\"paragraph\": \"...\", \"bullets\": []},\n"
            "  \"risk\": {\"paragraph\": \"...\", \"bullets\": []},\n"
            "  \"investment\": {\"paragraph\": \"...\", \"bullets\": []},\n"
            "  \"headline_points\": []\n"
            "}\n"
            "Each bullet array should contain up to 3 concise items. Do not include extra fields or commentary.",
        ),
        (
            "human",
            "Company name: {company_name}\n"
            "Technology summary: {tech_summary}\n"
            "Technology highlights: {tech_highlights}\n"
            "Technology gaps: {tech_gaps}\n"
            "Market summary: {market_summary}\n"
            "Market analysis detail: {market_analysis}\n"
            "Competitor insights: {competitor_info}\n"
            "Investment decision: {decision}\n"
            "Investment rationale: {decision_reason}\n"
            "Investment scores: {scores}\n"
            "Risk assessment: {risks}\n"
            "Key metrics: score={score}, confidence={confidence}, overall_risk={overall_risk}\n",
        ),
    ]
)


def _shorten(text: Any, limit: int = 900) -> str:
    if not text:
        return ""
    text = str(text)
    return text if len(text) <= limit else text[: limit - 3] + "..."


def _prepare_competitor_snippet(competitors: List[Dict[str, Any]]) -> str:
    if not competitors:
        return "N/A"
    rows = []
    for comp in competitors[:4]:
        name = comp.get("name", "Unknown")
        category = comp.get("category", "-")
        overlap = comp.get("competitive_overlap", "-")
        stage = comp.get("funding_stage", "-")
        rows.append(f"{name} (cat: {category}, overlap: {overlap}, stage: {stage})")
    return "; ".join(rows)


async def _build_summary(startup: Dict[str, Any], llm: Optional[ChatOpenAI]) -> Dict[str, Any]:
    tech_summary = startup.get("tech_summary", {})
    tech_highlights = tech_summary.get("highlights", startup.get("tech_highlights", []))
    tech_gaps = tech_summary.get("gaps", startup.get("tech_gaps", []))
    if not isinstance(tech_highlights, list):
        tech_highlights = [str(tech_highlights)] if tech_highlights else []
    if not isinstance(tech_gaps, list):
        tech_gaps = [str(tech_gaps)] if tech_gaps else []
    market_eval_detail = startup.get("market_eval_detail", {})
    market_eval = startup.get("market_eval", {})
    competitor_list = startup.get("competitor_list", [])
    decision = startup.get("investment_decision", {})
    scores = startup.get("investment_scores", {})
    risks = startup.get("risk_assessment", {})

    try:
        if llm is None:
            raise RuntimeError("summary llm unavailable")

        messages = SUMMARY_TEMPLATE.format_messages(
            company_name=startup.get("name", "Unknown Startup"),
            tech_summary=_shorten(tech_summary.get("summary") or tech_summary or ""),
            tech_highlights=_shorten(tech_highlights),
            tech_gaps=_shorten(tech_gaps),
            market_summary=_shorten(market_eval.get("summary", "")),
            market_analysis=_shorten(market_eval_detail.get("analysis", "")),
            competitor_info=_prepare_competitor_snippet(competitor_list),
            decision=str(decision.get("decision", "")),
            decision_reason=_shorten(decision.get("investment_thesis") or decision.get("reason", "")),
            scores=json.dumps(scores, ensure_ascii=False),
            risks=json.dumps(risks, ensure_ascii=False),
            score=scores.get("total_score", "N/A"),
            confidence=decision.get("confidence", "N/A"),
            overall_risk=risks.get("overall_risk_score", "N/A"),
        )
        response = await llm.ainvoke(messages)
        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("```", 2)[1].strip()
        summary = json.loads(content)
        for key in ("technology", "market_competition", "risk", "investment"):
            section = summary.get(key)
            if isinstance(section, dict):
                bullets = section.get("bullets")
                if bullets is None:
                    section["bullets"] = []
                elif not isinstance(bullets, list):
                    section["bullets"] = [str(bullets)]
        headline = summary.get("headline_points")
        if headline is None:
            summary["headline_points"] = []
        elif not isinstance(headline, list):
            summary["headline_points"] = [str(headline)]
        return summary
    except Exception:
        # Fallback minimal structure if LLM unavailable or parsing fails
        tech_highlights = tech_summary.get("highlights", []) if isinstance(tech_summary, dict) else []
        market_summary = market_eval.get("summary") if isinstance(market_eval, dict) else str(market_eval)
        return {
            "executive_summary": _shorten(startup.get("investment_decision", {}).get("investment_thesis") or market_summary or "Summary unavailable." , 320),
            "technology": {
                "paragraph": _shorten(tech_summary.get("summary") if isinstance(tech_summary, dict) else str(tech_summary), 280),
                "bullets": tech_highlights[:3] if tech_highlights else [],
            },
            "market_competition": {
                "paragraph": _shorten(market_summary, 280),
                "bullets": [c.get("name", "") for c in competitor_list[:3]],
            },
            "risk": {
                "paragraph": _shorten("Overall risk score: " + str(risks.get("overall_risk_score", "N/A")), 200),
                "bullets": [],
            },
            "investment": {
                "paragraph": _shorten(decision.get("investment_thesis") or decision.get("reason", ""), 260),
                "bullets": decision.get("recommended_actions", [])[:3],
            },
            "headline_points": [],
        }


async def report_node(state: Dict) -> Dict:
    """
    LangGraph 마지막 단계:
    1️⃣ 각 스타트업 결과를 JSON payload로 report_server에 POST
    2️⃣ PDF를 로컬 outputs 폴더에 저장
    3️⃣ 결과 리스트 반환
    """
    # --- 상태 관리 ---
    current = state.get("current_startup")
    startups: List[Dict] = state.get("startups", [])
    processed: List[Dict] = state.get("processed_startups", [])
    pdf_results: List[Dict] = state.get("reports", [])

    # 처리 대상이 하나만 있을 경우도 포함
    targets = []
    if current:
        targets.append(current)
    if startups:
        targets.extend(startups)
    if processed:
        targets.extend(processed)

    if not targets:
        print("⚠️ 보고서 생성 대상이 없습니다.")
        return state

    unique_targets: List[Dict] = []
    seen_keys = set()
    for item in targets:
        if not isinstance(item, dict):
            continue
        key = (item.get("name"), item.get("task_id"))
        if key in seen_keys:
            continue
        seen_keys.add(key)
        unique_targets.append(item)
    targets = unique_targets

    # --- 서버 주소 설정 ---
    report_url = os.getenv("REPORT_SERVER_URL", "http://localhost:8000/generate-report")
    os.makedirs("outputs", exist_ok=True)

    llm_model = os.getenv("REPORT_SUMMARY_MODEL", "gpt-4o-mini")
    try:
        summary_llm = ChatOpenAI(model=llm_model, temperature=0.2)
    except Exception:
        summary_llm = None

    async with aiohttp.ClientSession() as session:
        for s in targets:
            # --- 기술 요약 ---
            tech = s.get("tech_summary", {})
            tech_summary = tech.get("summary", "기술 요약 없음")
            tech_highlights = tech.get("highlights", [])
            tech_gaps = tech.get("gaps", [])

            # --- 시장성 평가 ---
            market = s.get("market_eval", {})
            market_summary = market.get("summary", "시장성 요약 없음")
            market_size = market.get("size", "시장 규모 데이터 없음")
            market_growth = market.get("growth", "성장률 정보 없음")
            market_competition = market.get("competition", "경쟁 환경 정보 없음")

            # --- 투자 판단 ---
            decision_data = s.get("investment_decision", {})
            decision = decision_data.get("decision", "검토 중")
            reason = decision_data.get("reason", "추가 검토 필요")

            summary = await _build_summary(s, summary_llm)

            payload = {
                "company_name": s.get("name", "Unknown"),
                "domain": s.get("domain", "에듀테크"),
                "tech_eval": {
                    "innovation": ", ".join(tech_highlights[:2]) if tech_highlights else "평가 대기",
                    "scalability": "평가 대기",
                    "stability": "평가 대기",
                    "summary": tech_summary,
                    "highlights": tech_highlights,
                    "gaps": tech_gaps,
                    "readiness_score": 72,
                },
                "market_eval": {
                    "size": market_size,
                    "growth": market_growth,
                    "competition": market_competition,
                    "summary": market_summary,
                },
                "market_eval_detail": s.get("market_eval_detail", {}),
                "competitor_list": s.get("competitor_list", []),
                "competitor_analysis": s.get("competitor_analysis", {}),
                "competitive_positioning": s.get("competitive_positioning", {}),
                "investment_scores": s.get("investment_scores", {}),
                "risk_assessment": s.get("risk_assessment", {}),
                "investment_decision": decision_data,
                "decision": decision,
                "decision_reason": reason,
                "llm_summary": summary,
                "headline_metrics": {
                    "decision": decision,
                    "score": s.get("investment_scores", {}).get("total_score", "N/A"),
                    "confidence": decision_data.get("confidence", "N/A"),
                    "overall_risk": s.get("risk_assessment", {}).get("overall_risk_score", "N/A"),
                },
            }


            # --- PDF 생성 요청 ---
            try:
                async with session.post(report_url, json=payload) as res:
                    if res.status == 200:
                        content = await res.read()

                        safe_name = unicodedata.normalize("NFKD", s.get("name", "startup"))
                        safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", safe_name)
                        file_name = f"{safe_name}_report.pdf"
                        file_path = os.path.join("outputs", file_name)

                        with open(file_path, "wb") as f:
                            f.write(content)

                        pdf_results.append({"name": s.get("name", "Unknown"), "pdf": file_name})
                    else:
                        text = await res.text()
                        pdf_results.append({"name": s.get("name", "Unknown"), "error": text})
            except Exception as e:
                pdf_results.append({"name": s.get("name", "Unknown"), "error": str(e)})

    print(f"총 {len(pdf_results)}개 보고서 생성 완료")
    state["reports"] = pdf_results
    state["current_startup"] = current
    return state
