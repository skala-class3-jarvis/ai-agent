# EduTech Startup Investment Evaluation Agent
본 프로젝트는 에듀테크 스타트업에 대한 투자 가능성을 자동으로 평가하는 에이전트를 설계하고 구현한 실습 프로젝트입니다.

## Overview

- Objective : 에듀테크 스타트업의 기술력, 시장성, 리스크 등을 기준으로 투자 적합성 분석
- Method : AI Agent + Agentic RAG
- Tools : LLM-OpenAI, External web search tool, Retrival

## Features

- PDF 자료 기반 정보 추출 ( 경제동향지표, KERIS 디지털교육 동향 199호, 209호, 교육부 주관 에듀테크 진흥방안 정책자료(23.09) )
- 투자 기준별 판단 분류 ( 시장성, 기술력, 경쟁사 비교 )
- 종합 투자 요약 출력 ( Local CLI : Json / Main Generation : PDF[ ___.pdf ] )

## Tech Stack 

| Category   | Details                                                      |
|------------|--------------------------------------------------------------|
| Framework  | LangGraph, LangChain, Python                                 |
| LLM        | GPT-4o-mini via OpenAI API                                   |
| Retrieval  | FAISS                                                        |
| Embedding  | HuggingFaceEmbedding - dragonkue/multilingual-e5-small-ko    |

### Agents
## Agent A — 스타트업 탐색 에이전트 (Startup Search Agent)

- **역할** : 사용자의 질의(query)를 기반으로 시장 내 유망 스타트업을 탐색 및 구조화  
- **Node** : `startup_search_node`  
- **Tool** : TavilySearchResults, ChatOpenAI (GPT-4o-mini), PromptTemplate, JSON Parser  

| Tool Name        | Library / 구성 요소             | 역할                            |
| ---------------- | ------------------------------- | ------------------------------- |
| `tavily_tool`    | TavilySearchResults (LangChain)  | 스타트업 후보 탐색 (Web API)     |
| `llm`            | ChatOpenAI (GPT-4o-mini)         | 탐색 결과 요약 및 정규화         |
| `prompt`         | PromptTemplate                   | 질의 기반 검색 프롬프트 구성     |
| `json_parser`    | Python JSON                      | LLM 결과 파싱 및 구조화          |

| Node              | 역할                              |
| ----------------- | --------------------------------- |
| `startup_search`  | Tavily 검색 실행 및 스타트업 리스트 생성 |

---

## Agent B — 기술 요약 에이전트 (Tech Summary Agent)

- **역할** : 탐색된 스타트업의 기술 역량을 요약 및 정규화  
- **Node** : `prepare → llm_call → parse`  
- **Tool** : Responses API (gpt-4o-mini), Pydantic (TechSummarySchema), StateGraph  

| Tool Name             | Library / 구성 요소     | 역할                                       |
| --------------------- | ----------------------- | ------------------------------------------ |
| `TechSummaryAgent`    | LangGraph StateGraph    | 기술 요약 워크플로우 오케스트레이션 (prepare → llm_call → parse) |
| `OpenAI Responses API`| openai                  | gpt-4o-mini 호출                           |
| `TechSummarySchema`   | Pydantic                | LLM 응답 구조 검증 및 정규화               |

| Node          | 역할                                        |
| ------------- | ------------------------------------------- |
| `tech_summary`| 상위 LangGraph 내 기술 요약 담당 진입 노드    |
| `prepare`     | 입력 스타트업 정보 정리 및 프롬프트 생성      |
| `llm_call`    | OpenAI API 호출로 요약 생성                  |
| `parse`       | JSON 파싱 및 Pydantic 검증                   |

---

## Agent C — 시장성 평가 에이전트 (Market Analysis Agent)

- **역할** : 내부 PDF 데이터(RAG) 및 외부 검색을 결합하여 시장성, 성장성, 경쟁 강도, 리스크 등을 정량 분석  
- **Node** :  
  `retriever`, `search_tool`, `classify_query`, `retrieve_internal`, `web_search`,  
  `analyze_market_size`, `analyze_growth`, `analyze_competition`,  
  `analyze_risks`, `calculate_score`, `generate_report`  
- **Tool** : FAISS Retriever, DuckDuckGo Search, ChatOpenAI (GPT-4o-mini)  

| Tool Name            | Library / 구성 요소              | 역할                                      |
| -------------------- | -------------------------------- | ----------------------------------------- |
| `retriever`          | FAISS + HuggingFace Embeddings   | 내부 PDF 기반 RAG 검색                    |
| `search_tool`        | DuckDuckGo Search                | 최신 시장 데이터 검색                     |
| `llm / llm_creative` | ChatOpenAI (GPT-4o-mini)         | 분석/요약 생성                            |

| Node                   | 역할                                             |
| ----------------------- | ------------------------------------------------ |
| `classify_query`        | 시장 주제, 분석 깊이, 웹 검색 필요성 분류       |
| `retrieve_internal`     | FAISS 기반 내부 RAG 검색                        |
| `web_search`            | DuckDuckGo 검색으로 외부 시장 트렌드 확보       |
| `analyze_market_size`   | 시장 규모 및 세그먼트 분석                      |
| `analyze_growth`        | 성장 전망 (CAGR, 성장 동력, 트렌드) 분석        |
| `analyze_competition`   | 경쟁 강도 및 Porter 5 Forces 기반 분석           |
| `analyze_risks`         | 기술/경쟁/규제/수요 리스크 식별                 |
| `calculate_score`       | 시장성 종합 점수(0~100) 계산                    |
| `generate_report`       | 결과 요약 보고서 생성                           |

---

## Agent D — 경쟁사 분석 에이전트 (Competitor Analysis Agent)

- **역할** : 웹 검색을 통해 경쟁사를 탐색하고 경쟁 구도 및 포지셔닝 자동 분석  
- **Node** : `identify_competitors`, `analyze_competitive_landscape`, `evaluate_competitive_positioning`  
- **Tool** : DuckDuckGoSearchRun, ChatOpenAI (GPT-4o-mini), ChatPromptTemplate, StateGraph  

| Tool Name             | Library / 구성 요소        | 역할                               |
| --------------------- | -------------------------- | ---------------------------------- |
| `search_tool`         | DuckDuckGoSearchRun        | 경쟁사 웹 탐색                     |
| `llm`                 | ChatOpenAI (GPT-4o-mini)   | 경쟁 구도 및 포지셔닝 분석         |
| `prompt_template`     | ChatPromptTemplate         | 경쟁 분석용 프롬프트 구성          |
| `CompetitorGraph`     | LangGraph StateGraph       | 경쟁사 분석 플로우 제어            |

| Node                           | 역할                                  |
| ------------------------------ | ------------------------------------- |
| `identify_competitors`         | 주요 경쟁사 탐색                      |
| `analyze_competitive_landscape`| 시장 경쟁 구조 및 주요 요인 분석      |
| `evaluate_competitive_positioning` | 경쟁 우위, 지속 가능성 평가        |

---

## Agent E — 투자 판단 에이전트 (Investment Decision Agent)

- **역할** : 기술/시장/경쟁 분석 결과를 종합하여 최종 투자 판단 수행 (유치 / 보류)  
- **Node** : `calculate_investment_scores`, `assess_investment_risks`, `make_final_decision`  
- **Tool** : ChatOpenAI (GPT-4o-mini), ChatPromptTemplate, Python Logic, JSON Parser, StateGraph  

| Tool Name              | Library / 구성 요소        | 역할                                        |
| ---------------------- | -------------------------- | ------------------------------------------- |
| `llm`                  | ChatOpenAI (GPT-4o-mini)   | 투자 점수 및 리스크 분석 생성               |
| `PromptTemplate`       | ChatPromptTemplate         | 투자 판단용 프롬프트 구성                  |
| `parser`               | Python JSON                | LLM 응답 파싱 및 정규화                    |
| `StateGraph`           | LangGraph                  | 점수 계산 → 리스크 평가 → 최종 결정 플로우 제어 |

| Node                        | 역할                                            |
| ---------------------------- | ---------------------------------------------- |
| `calculate_investment_scores`| 7개 평가 영역(100점) 기반 정량 점수 계산       |
| `assess_investment_risks`    | 6개 리스크(시장/기술/경쟁/규제/재무/실행) 평가 |
| `make_final_decision`        | 점수 + 리스크 종합 후 최종 투자 의사결정       |

---

## Agent F — 보고서 생성 에이전트 (Report Generation Agent)

- **역할** :  
  LangGraph 워크플로우의 마지막 단계로, 각 스타트업의 기술·시장·경쟁·투자 분석 결과를 LLM 기반으로 요약하고 PDF 형태의 최종 보고서를 자동 생성함.  
  내부 데이터를 요약 LLM(`gpt-4o-mini`)으로 정리한 후, FastAPI 기반 `report_server`에 POST 하여 PDF 파일(`outputs/*.pdf`)을 생성한다.

- **Node** : `report_node`  
- **Tool** : ChatOpenAI (GPT-4o-mini), aiohttp, FastAPI Report Server, ChatPromptTemplate (SUMMARY_TEMPLATE), JSON Parser

| Tool Name            | Library / 구성 요소             | 역할                                                         |
| -------------------- | -------------------------------- | ------------------------------------------------------------ |
| `summary_llm`        | ChatOpenAI (GPT-4o-mini)         | 투자 결과 및 기술/시장 정보를 요약 LLM 요약문 생성            |
| `SUMMARY_TEMPLATE`   | ChatPromptTemplate (LangChain Core) | 1-page investment summary 프롬프트 구성 및 LLM 입력 정의      |
| `aiohttp ClientSession` | aiohttp 라이브러리               | FastAPI report server로 비동기 POST 요청 전송 및 PDF 수신      |
| `report_server`      | FastAPI (`generate-report`) 엔드포인트 | LLM 요약 결과를 HTML(Jinja2 template) → WeasyPrint PDF로 변환 |
| `JSON Parser`        | Python 표준 라이브러리            | LLM 출력 구조 검증 및 후처리 정규화 (불완전한 응답 보정)     |

| Node          | 역할                                                        |
| -------------- | ----------------------------------------------------------- |
| `report_node`  | LangGraph 최종 단계 — 분석 결과를 LLM 요약 및 PDF 보고서 생성 |
| `_build_summary` | LLM을 호출하여 기술/시장/리스크/투자 항목별 compact 요약 JSON 생성 |
| `_prepare_competitor_snippet` | 경쟁사 리스트를 간결한 문장으로 정리 (최대 4개 표시) |
| `_shorten`     | 텍스트 길이 제한 및 ellipsis 처리 (LLM 입력 최적화)         |

---

## 전체 파이프라인 요약

## Architecture
<img width="2345" height="2082" alt="image" src="https://github.com/user-attachments/assets/01e9d8d3-3cc6-4255-87b4-079bd1c60e39" />


## Directory Structure

```text
ai-agent/
├─ README.md
├─ requirements.txt
├─ integration.py
├─ report_server.py
├─ report_test.py
├─ agents/
│  ├─ competitor_analysis_agent.py
│  ├─ investment_decision_agent.py
│  ├─ market_analysis_agent.py
│  ├─ market_analysis_graph.py
│  ├─ report_agent.py
│  ├─ search_agent.py
│  └─ tech_summary_agent.py
├─ data/
│  ├─ 2024년_KERIS_디지털교육_동향_제199호.pdf
│  ├─ KERIS_디지털교육_동향_209호.pdf
│  ├─ 에듀테크_진흥방안.pdf
├─ db_faiss/
│  ├─ index.faiss
│  └─ index.pkl
├─ outputs/
├─ prompts/
│  ├─ competitor_analysis_prompt.py
│  ├─ investment_decision_prompt.py
│  ├─ market_analysis_prompt.py
│  ├─ search_prompt.py
│  └─ tech_summary_prompt.py
└─ templates/
   ├─ report_template.html
   └─ report_test.pdf
```



## Contributors 
- 정재민 : Evaluation market size RAG Agent Design
- 장소민 : Company Comparison and Investment Evalution decision Agent Design
- 한정석 : Main Agent Design and all Agent Combination, PDF Generate and checking
- 이정엽 : Company Technical skill Set Summary
