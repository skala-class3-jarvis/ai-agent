from fastapi import FastAPI, Response
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from pydantic import BaseModel
from urllib.parse import quote
from typing import Any, Dict, List, Tuple
import os
import unicodedata
import io
import re

# -----------------------------------
# FastAPI App
# -----------------------------------
app = FastAPI()

# ----------- Data Schema (LangGraph 결과 매핑) -----------
class TechEval(BaseModel):
    innovation: str
    scalability: str
    stability: str
    summary: str

class MarketEval(BaseModel):
    size: str
    growth: str
    competition: str
    summary: str

class ReportInput(BaseModel):
    company_name: str
    domain: str
    tech_eval: TechEval
    market_eval: MarketEval
    decision: str
    decision_reason: str
    market_eval_detail: Dict[str, Any] = {}
    competitor_list: List[Dict[str, Any]] = []
    competitor_analysis: Dict[str, Any] = {}
    competitive_positioning: Dict[str, Any] = {}
    investment_scores: Dict[str, Any] = {}
    risk_assessment: Dict[str, Any] = {}
    investment_decision: Dict[str, Any] = {}
    llm_summary: Dict[str, Any] = {}
    headline_metrics: Dict[str, Any] = {}


# ----------- Jinja2 Environment -----------
env = Environment(loader=FileSystemLoader("templates"))


def build_filenames(company_name: str) -> Tuple[str, str]:
    base_filename = f"{company_name}_report.pdf"
    encoded = quote(base_filename)
    fallback = "report.pdf"  # 영문 fallback
    return fallback, encoded



# ----------- Endpoint -----------
@app.post("/generate-report")
def generate_report(data: ReportInput):
    """
    LangGraph 결과(JSON) → PDF 보고서 자동 생성
    """
    template_name = os.getenv("REPORT_TEMPLATE", "report_template.html")
    template = env.get_template(template_name)
    html_out = template.render(data=data.dict())

    # PDF 메모리에 생성
    pdf_bytes = io.BytesIO()
    HTML(string=html_out).write_pdf(pdf_bytes)
    pdf_bytes.seek(0)

    ascii_filename, encoded_filename = build_filenames(data.company_name)
    headers = {
        "Content-Disposition": (
            f"attachment; filename=\"{ascii_filename}\"; "
            f"filename*=UTF-8''{encoded_filename}"
        )
    }

    return Response(
        content=pdf_bytes.read(),
        media_type="application/pdf",
        headers=headers
    )
