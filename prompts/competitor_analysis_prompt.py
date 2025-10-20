# ai-agent/prompts/competitor_analysis_prompt.py

COMPETITOR_DISCOVERY_PROMPT = """
너는 에듀테크 시장 분석 전문가야.
다음 스타트업 정보를 기반으로 주요 경쟁사를 식별하고 간단한 설명을 제공해.

스타트업 정보:
{startup_info}

검색 결과:
{search_results}

결과를 아래 JSON 형식으로만 출력해. 불필요한 텍스트는 포함하지 마.

{{
  "competitors": [
    {{
      "name": "회사명",
      "description": "간단한 설명 (1-2문장)",
      "category": "B2B/B2C/B2B2C",
      "founded_year": "설립연도",
      "estimated_revenue": "추정 매출 (모르면 Unknown)",
      "key_products": ["제품1", "제품2"],
      "target_market": "타겟 시장",
      "funding_stage": "Seed/Series A/B/C/IPO/Unknown",
      "competitive_overlap": "높음/중간/낮음"
    }}
  ]
}}
"""


COMPETITOR_ANALYSIS_PROMPT = """
너는 에듀테크 VC 투자심사역이야.
아래 스타트업과 경쟁사들을 바탕으로 경쟁 구도를 분석해.

스타트업 정보:
{startup_info}

경쟁사 목록:
{competitors}

아래 JSON 형식으로만 출력해.

{{
  "competition_intensity": 1-10,
  "market_positioning": "Blue Ocean/Red Ocean/Niche Market",
  "differentiation_factors": ["요소1", "요소2", "요소3"],
  "competitive_advantages": ["Technology", "Price", "Network Effect"],
  "entry_barriers": "높음/중간/낮음",
  "key_threats": ["위협1", "위협2"],
  "market_share_potential": 1-10
}}
"""


COMPETITOR_POSITIONING_PROMPT = """
너는 경쟁 전략 분석 전문가야.
다음 정보를 기반으로 스타트업의 경쟁 포지셔닝을 평가해.

스타트업 이름: {startup_name}
경쟁사 목록: {competitors}
경쟁 구도 분석: {analysis}

아래 JSON 형식으로만 출력해.

{{
  "positioning_score": 0-10,
  "differentiation_score": 0-10,
  "competitive_moat": {{
    "technology": 0-10,
    "brand": 0-10,
    "network_effect": 0-10,
    "data": 0-10,
    "overall": 0-10
  }},
  "sustainability": {{
    "score": 0-10,
    "reasoning": "지속 가능성 평가 이유"
  }},
  "recommendations": ["권장사항1", "권장사항2"]
}}
"""
