import os
import re
import unicodedata
import aiohttp
from typing import Dict, List


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

    # --- 서버 주소 설정 ---
    report_url = os.getenv("REPORT_SERVER_URL", "http://localhost:8000/generate-report")
    os.makedirs("outputs", exist_ok=True)

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
                },
                "market_eval": {
                    "size": market_size,
                    "growth": market_growth,
                    "competition": market_competition,
                    "summary": market_summary,
                },
                "competitor_list": s.get("competitor_list", []),
                "competitor_analysis": s.get("competitor_analysis", {}),
                "competitive_positioning": s.get("competitive_positioning", {}),
                "investment_scores": s.get("investment_scores", {}),
                "risk_assessment": s.get("risk_assessment", {}),
                "investment_decision": decision_data,
                "decision": decision,
                "decision_reason": reason,
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
    return state
