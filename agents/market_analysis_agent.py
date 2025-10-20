import json
import re
from typing import Dict
from pathlib import Path
from dotenv import load_dotenv

from langchain_community.chat_models import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings

from prompts.market_analysis_prompt import MARKET_ANALYSIS_PROMPT_TEMPLATE

load_dotenv()

# ---------------------------
# 초기화
# ---------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = (BASE_DIR.parent / "data").resolve()
PERSIST_PATH = (DATA_DIR / "db_faiss").resolve()

EMBEDDINGS_MODEL = HuggingFaceEmbeddings(
    model_name="dragonkue/multilingual-e5-small-ko",
    model_kwargs={"device": "cpu"}
)

# ---------------------------
# RAG (Vector DB)
# ---------------------------
def load_or_build_vector_db(data_dir: Path, persist_path: Path) -> FAISS:
    if persist_path.exists():
        return FAISS.load_local(
            str(persist_path),
            EMBEDDINGS_MODEL,
            allow_dangerous_deserialization=True
        )
    loader = DirectoryLoader(str(data_dir), glob="**/*.pdf", loader_cls=PyPDFLoader)  # pyright: ignore
    docs = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    docs_split = splitter.split_documents(docs)
    db = FAISS.from_documents(docs_split, EMBEDDINGS_MODEL)
    db.save_local(str(persist_path))
    return db

try:
    vector_db = load_or_build_vector_db(DATA_DIR, PERSIST_PATH)
    retriever = vector_db.as_retriever(search_type="similarity", search_kwargs={"k": 3})
except Exception:
    retriever = None

# ---------------------------
# LLM 및 도구 초기화
# ---------------------------
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
search_tool = DuckDuckGoSearchRun()

prompt = PromptTemplate(
    input_variables=["startup_info", "rag_context", "search_context"],
    template=MARKET_ANALYSIS_PROMPT_TEMPLATE.strip(),
)

# ---------------------------
# 헬퍼 함수
# ---------------------------
def collect_rag_context(query: str) -> str:
    if not retriever:
        return "내부 데이터 없음"
    try:
        docs = retriever.invoke(query)
        return "\n\n".join([d.page_content[:400] for d in docs])[:1500]
    except Exception as e:
        return f"RAG 실패: {e}"

def collect_search_context(query: str) -> str:
    try:
        result = search_tool.run(f"{query} 시장 성장 OR 산업 리포트 OR 수요 전망")
        return result[:1000] if result else "관련 검색 결과 없음"
    except Exception as e:
        return f"검색 실패: {e}"

# ---------------------------
# LangGraph 노드 (단일 스타트업 처리)
# ---------------------------
async def market_analysis_node(state: Dict) -> Dict:
    """
    LangGraph 시장성 평가 노드
    Input: {"current_startup": {...}}
    Output: {"current_startup": {... + market_eval}}
    """
    state["stage"] = "Market Analysis Node"
    print(f"진행 단계: {state['stage']}")

    current = state.get("current_startup", {})
    if not current:
        print("current_startup 없음 — 스킵")
        return state

    name = current.get("name", "스타트업")
    query = current.get("market", name)

    rag_context = collect_rag_context(query)
    search_context = collect_search_context(query)

    startup_info = json.dumps(current, ensure_ascii=False, indent=2)
    formatted_prompt = prompt.format(
        startup_info=startup_info,
        rag_context=rag_context,
        search_context=search_context,
    )

    try:
        response = await llm.ainvoke(formatted_prompt)
        text = response.content.strip()

        match = re.search(r"\{.*\}", text, re.DOTALL)
        json_str = match.group(0) if match else text
        json_str = json_str.replace("```json", "").replace("```", "").strip()

        parsed = json.loads(json_str)
    except Exception as e:
        parsed = {
            "summary": f"시장성 평가 실패: {e}",
            "size_estimate": "N/A",
            "growth": "N/A",
            "competition": "N/A",
            "risks": [],
        }

    current["market_eval"] = parsed

    print(f"[{current.get('name', 'Unknown')}] 시장성 평가 완료")
    return {"current_startup": current}
