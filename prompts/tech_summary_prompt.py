# ai-agent/prompts/tech_summary_prompt.py

TECH_SUMMARY_PROMPT_TEMPLATE = """
너는 기술 분석 전문가야.
아래 스타트업 정보를 기반으로 기술적 요약을 생성해.

스타트업 정보:
{startup_info}

다음 형식의 **JSON만 출력**해.
불필요한 문장 없이 JSON만 출력해야 한다.

{{
  "summary": "핵심 기술 요약 (2~3문장)",
  "highlights": ["기술적 강점 1", "기술적 강점 2"],
  "gaps": ["보완이 필요한 부분 1", "보완이 필요한 부분 2"]
}}
"""
