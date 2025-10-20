from fastapi import FastAPI, Response
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from pydantic import BaseModel
from urllib.parse import quote
from typing import Tuple
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


# ----------- Jinja2 Environment -----------
env = Environment(loader=FileSystemLoader("templates"))


def build_filenames(company_name: str) -> Tuple[str, str]:
    """Return ASCII-safe fallback and RFC 5987 encoded filenames."""
    base_filename = f"{company_name}_report.pdf"

    normalized = unicodedata.normalize("NFKD", company_name)
    ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^A-Za-z0-9_-]+", "_", ascii_name).strip("_")
    fallback = f"{slug or 'report'}_report.pdf"

    encoded = quote(base_filename)
    return fallback, encoded


# ----------- Endpoint -----------
@app.post("/generate-report")
def generate_report(data: ReportInput):
    """
    LangGraph 결과(JSON) → PDF 보고서 자동 생성
    """
    template = env.get_template("report_template.html")
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
