from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

env = Environment(loader=FileSystemLoader("templates"))
template = env.get_template("edutech_report_template.html")

sample = {
"company_name": "Aurora Learn",
"domain": "EdTech",
"tech_eval": {
"summary": "Adaptive AI tutoring with curriculum-aligned content.",
"highlights": ["Reinforcement learning tutor", "Real-time analytics"],
"gaps": ["Limited STEM coverage"],
"readiness_score": 82,
},
"market_eval": {
"size": "$3.8B TAM (K12 APAC)",
"growth": "17% CAGR (2024-2028)",
"competition": "Moderate density; legacy LMS incumbents",
"summary": "High growth in hybrid learning spend across East Asia.",
},
"market_eval_detail": {
"analysis": "Demand accelerated by public-private digital initiatives.",
"demand_drivers": ["Curriculum digitization mandates", "AI-first parenting trend"],
"risks": ["Regulatory scrutiny on student data", "High onboarding friction"],
},
"investment_decision": {
"decision": "Invest",
"confidence": "78",
"score": 74,
"reason": "Scalable platform with differentiated AI tutoring IP.",
"risks": ["Data compliance", "Sales cycle length"],
"next_steps": ["Commission privacy audit", "Pilot in Singapore schools"],
},
"investment_scores": {
"total_score": 74,
"percentile_rank": "Top 30%",
"scores": {
    "educational_efficacy": {"subtotal": 18, "max": 25},
    "market_traction": {"subtotal": 12, "max": 20},
    "team": {"subtotal": 15, "max": 20},
},
},
"risk_assessment": {
"overall_risk_score": 4.8,
"market_risk": {"level": 5, "likelihood": "Medium", "impact": "High"},
"technology_risk": {"level": 3, "likelihood": "Low", "impact": "Medium"},
},
"competitor_list": [
{"name": "LearnNova", "description": "AI LMS for public schools", "category": "B2G", "competitive_overlap": "Medium",
"funding_stage": "Series B"},
{"name": "TutorPulse", "description": "One-on-one AI tutors", "category": "B2C", "competitive_overlap": "Low",
"funding_stage": "Series A"},
],
"competitor_analysis": {
"competition_intensity": 6,
"market_positioning": "Niche Market",
},
"competitive_positioning": {
"competitive_moat": {"overall": 6.5, "technology": 8, "brand": 5, "network_effect": 4, "data": 6},
"recommendations": ["Strengthen channel partnerships", "Expand curriculum coverage"],
},
}

html = template.render(data=sample)
output = Path("reports/aurora_edutech_preview.pdf")
output.parent.mkdir(exist_ok=True)
HTML(string=html, base_url=".").write_pdf(output)
print(f"Generated {output}")