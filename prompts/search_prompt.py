SEARCH_PROMPT_TEMPLATE = """
너는 스타트업 분석 전문가야.
다음 Tavily 검색 결과를 기반으로 국내 에듀테크 스타트업을 탐색해.

검색 결과:
{results}

반드시 아래 형식의 **JSON만 출력**해. 불필요한 문장 없이 JSON만.
[
  {{
    "name": "기업명",
    "tech": ["핵심 기술1", "핵심 기술2"],
    "market": "타겟 시장 및 고객",
    "competitors": ["경쟁사1", "경쟁사2"]
  }}
]
"""
