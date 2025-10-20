# EduTech Startup Investment Evaluation Agent

에듀테크 스타트업에 대한 투자 가능성을 자동으로 평가하는 AI 에이전트 시스템입니다.

## Overview

- **Objective**: 에듀테크 스타트업의 기술력, 시장성, 리스크 등을 기준으로 투자 적합성 분석
- **Method**: AI Agent + Agentic RAG
- **Tools**: LLM (OpenAI), External Web Search, Vector Retrieval

## Business Strengths

- **모듈화 설계**: 코드 블록을 기능별로 분리하여 확장성, 유지보수성, 모듈 교체 용이성 확보
- **복합 지표 기반 평가**: 시장성 지수, 기업 판단 지수 등 다양한 평가 지표를 종합하여 객관적이고 일관된 투자 분석 제공
- **정량적 평가 체계**: 명확한 평가 기준을 통해 투자 판단의 불확실성 감소 및 실패 확률 최소화

## Features

- PDF 자료 기반 정보 추출 (경제동향지표, KERIS 디지털교육 동향, 교육부 에듀테크 진흥방안)
- 투자 기준별 판단 분류 (시장성, 기술력, 경쟁사 비교)
- 종합 투자 요약 출력 (Local CLI: JSON / Main Generation: PDF)

## Tech Stack

| Category   | Details                                                    |
|------------|------------------------------------------------------------|
| Framework  | LangGraph, LangChain, Python                               |
| LLM        | GPT-4o-mini via OpenAI API                                 |
| Retrieval  | FAISS                                                      |
| Embedding  | HuggingFace - dragonkue/multilingual-e5-small-ko           |

## Agent Architecture

### 1. Startup Search Agent

스타트업 탐색 에이전트

**Purpose**: 사용자 질의에 따라 시장 내 유망 스타트업 후보를 검색 및 구조화

**Tools**

| Tool Name          | Library              | 역할                           |
|--------------------|----------------------|--------------------------------|
| TavilySearchResults| Tavily               | 스타트업 정보 웹 검색          |
| ChatOpenAI         | OpenAI               | GPT-4o-mini 모델 호출          |
| PromptTemplate     | LangChain            | 검색 쿼리 프롬프트 생성        |
| JSON Parser        | Python               | 검색 결과 구조화 및 파싱       |

**Nodes**

| Node               | 역할                                      |
|--------------------|-------------------------------------------|
| startup_search_node| 스타트업 검색 및 정보 구조화 메인 노드   |

---

### 2. Tech Summary Agent

기술 요약 에이전트

**Purpose**: 스타트업의 기술력 및 핵심 역량을 요약 분석

**Workflow**: prepare → llm_call → parse

**Tools**

| Tool Name            | Library              | 역할                                  |
|----------------------|----------------------|---------------------------------------|
| TechSummaryAgent     | LangGraph StateGraph | 기술 요약 워크플로우 오케스트레이션   |
| OpenAI Responses API | openai               | gpt-4o-mini 모델 호출                 |
| TechSummarySchema    | Pydantic             | LLM 응답 구조 검증 및 정규화          |

**Nodes**

| Node          | 역할                                      |
|---------------|-------------------------------------------|
| tech_summary  | 기술 요약 담당 진입 노드                  |
| prepare       | 입력 정보 정리 및 프롬프트 생성           |
| llm_call      | OpenAI API 호출로 초기 요약 생성          |
| parse         | JSON 파싱 및 Pydantic 검증, 결과 반환     |

---

### 3. Market Evaluation Agent

시장성 평가 에이전트

**Purpose**: 시장 규모, 성장성, 경쟁 구도, 리스크 분석을 통한 종합 시장성 평가

**Tools**

| Tool Name        | Library                       | 역할                                |
|------------------|-------------------------------|-------------------------------------|
| retriever        | FAISS + HuggingFace Embedding | 내부 PDF 기반 RAG 검색              |
| search_tool      | DuckDuckGo Search             | 최신 시장 데이터 보강을 위한 웹 검색|


**Nodes**

| Node                    | 역할                                                |
|-------------------------|-----------------------------------------------------|
| classify_query          | 쿼리 분류 (시장 주제, 분석 깊이, 웹 검색 여부)      |
| retrieve_internal       | FAISS 벡터DB에서 PDF 기반 RAG 검색                  |
| web_search              | DuckDuckGo 검색으로 최신 시장 트렌드 확보           |
| analyze_market_size     | 시장 규모 분석 (규모, CAGR, 세그먼트, 지역별 현황)  |
| analyze_growth          | 성장 전망 분석 (CAGR, 성장 동력, 트렌드)            |
| analyze_competition     | 경쟁 구도 분석 (Porter 5 Forces, 경쟁 강도)         |
| analyze_risks           | 시장 리스크 분석 (기술/경쟁/규제/수요)              |
| calculate_score         | 시장성 점수(0~100) 산출                             |


---

### 4. Competitor Analysis Agent

경쟁사 분석 에이전트

**Purpose**: 웹 검색을 통해 경쟁사를 탐색하고 경쟁 구도 및 시장 포지셔닝 자동 분석

**Tools**

| Tool Name           | Library              | 역할                              |
|---------------------|----------------------|-----------------------------------|
| DuckDuckGoSearchRun | DuckDuckGo           | 경쟁사 정보 웹 검색               |
| ChatOpenAI          | OpenAI               | GPT-4o-mini 모델 호출             |
| ChatPromptTemplate  | LangChain            | 경쟁 분석 프롬프트 생성           |
| StateGraph          | LangGraph            | 경쟁 분석 워크플로우 관리         |

**Nodes**

| Node                              | 역할                                      |
|-----------------------------------|-------------------------------------------|
| identify_competitors              | 주요 경쟁사 식별 및 리스트업              |
| analyze_competitive_landscape     | 경쟁 구도 분석 (시장 점유율, 전략 등)     |
| evaluate_competitive_positioning  | 시장 내 포지셔닝 평가 및 차별화 요소 도출 |

---

### 5. Investment Decision Agent

투자 의사결정 에이전트

**Purpose**: 7개 평가 영역(100점)과 6개 리스크를 종합 분석하여 투자 의사결정 도출 (Strong Buy ~ Pass)

**Tools**

| Tool Name           | Library              | 역할                              |
|---------------------|----------------------|-----------------------------------|
| ChatOpenAI          | OpenAI               | GPT-4o-mini 모델 호출             |
| ChatPromptTemplate  | LangChain            | 투자 결정 프롬프트 생성           |
| Python Logic        | Python               | 점수 계산 및 의사결정 로직        |
| JSON Parser         | Python               | 결과 구조화 및 파싱               |
| StateGraph          | LangGraph            | 투자 결정 워크플로우 관리         |

**Nodes**

| Node                        | 역할                                      |
|-----------------------------|-------------------------------------------|
| calculate_investment_scores | 7개 영역별 투자 점수 계산 (100점 만점)   |
| assess_investment_risks     | 6개 리스크 요소 평가 및 위험도 산출       |
| make_final_decision         | 종합 점수 기반 최종 투자 결정 도출        |

---

## System Architecture

<img src="https://github.com/user-attachments/assets/01e9d8d3-3cc6-4255-87b4-079bd1c60e39" alt="Architecture Diagram" width="100%">

## Directory Structure

```text
ai-agent/
├── README.md
├── requirements.txt
├── integration.py
├── report_server.py
├── report_test.py
├── agents/
│   ├── competitor_analysis_agent.py
│   ├── investment_decision_agent.py
│   ├── market_analysis_agent.py
│   ├── market_analysis_graph.py
│   ├── report_agent.py
│   ├── search_agent.py
│   └── tech_summary_agent.py
├── data/
│   ├── 2024년_KERIS_디지털교육_동향_제199호.pdf
│   ├── KERIS_디지털교육_동향_209호.pdf
│   ├── 에듀테크_진흥방안.pdf
│   └── db_faiss/
│       ├── index.faiss
│       └── index.pkl
├── db_faiss/
│   ├── index.faiss
│   └── index.pkl
├── outputs/
├── prompts/
│   ├── competitor_analysis_prompt.py
│   ├── investment_decision_prompt.py
│   ├── market_analysis_prompt.py
│   ├── search_prompt.py
│   └── tech_summary_prompt.py
└── templates/
    ├── report_template.html
    └── report_test.pdf
```

## Contributors

- **정재민**: Market Size Evaluation RAG Agent Design
- **장소민**: Company Comparison and Investment Evaluation Decision Agent Design
- **한정석**: Main Agent Design, Agent Integration, PDF Generation
- **이정엽**: Company Technical Skill Set Summary Agent Design

## References

- [KDI 경제교육 정보센터](https://eiec.kdi.re.kr/)
- [KERIS 한국교육학술정보원](https://www.keris.or.kr/main/ad/pblcte/selectPblcteOVSEAList.do?mi=1143)
- [ESSA Evidence Standards](https://essa.ed.gov/)
- [EdTech Investment Trends - HolonIQ](https://www.holoniq.com/)


