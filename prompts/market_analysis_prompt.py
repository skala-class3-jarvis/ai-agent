# ai-agent/prompts/market_analysis_prompt.py

MARKET_ANALYSIS_PROMPT_TEMPLATE = """
너는 시장 분석 전문가야.
다음 스타트업의 시장성과 산업 성장 가능성을 내부 RAG 데이터와 외부 검색을 바탕으로 평가해.

스타트업 정보:
{startup_info}

내부 데이터(RAG):
{rag_context}

외부 뉴스/리포트 검색 결과:
{search_context}

아래 JSON 형식으로만 출력해.
불필요한 설명 없이 JSON만 반환해야 한다.

{{
  "summary": "시장 성장 가능성 및 수요 요약 (2~3문장)",
  "size_estimate": "시장 규모 예측",
  "growth": "연평균 성장률 또는 성장 전망",
  "competition": "경쟁 강도 수준",
  "risks": ["리스크 1", "리스크 2"]
}}
"""
