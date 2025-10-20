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

## Agents
Main Agent : 스타트업 탐색 에이전트 (Startup Search Agent)
- Main Agent의 질의에 따라 시장 내 유망 스타트업 후보를 검색 및 구조화
- Node : startup_search_node
- Tool : TavilySearchResults, ChatOpenAI (GPT-4o-mini), PromptTemplate, JSON Parser
 
- 기업 기술 요약 에이전트 : Main Agent 정보 전달에 따른 기업 기술 요약
    - Node : prepare → llm_call → parse
    - Tool : Responses API(gpt-4o-mini), Pydantic(TechSummarySchema), StateGraph

| Tool Name             | Library / 구성 요소             | 역할                                         |
| --------------------- | ------------------------------- | -------------------------------------------- |
| `TechSummaryAgent`    | LangGraph StateGraph            | 기술 요약 워크플로우 오케스트레이션 (prepare → llm_call → parse) |
| `OpenAI Responses API`| openai                          | gpt-4o-mini 모델 호출                        |
| `TechSummarySchema`   | Pydantic                        | LLM 응답 구조 검증 및 정규화                 |

| Node                   | 역할                                             |
| ---------------------- | ------------------------------------------------ |
| `tech_summary`         | 상위 LangGraph에서 기술 요약 담당 진입 노드            |
| `prepare`              | 입력 스타트업 정보 정리·프롬프트 생성                 |
| `llm_call`             | OpenAI API 호출로 초기 요약 생성                     |
| `parse`                | JSON 파싱 및 Pydantic 검증, 안전한 요약 결과 반환       |


- 기업 시장성 평가 에이전트 : Main Agent 정보 전달에 따른 기업 시장성 평가 세부 지표 파악
    - Node : retriever, search_tool, classify_query, retrieve_internal, web_search, analyze_market_size,
             analyze_growth, analyze_competition, analyze_risks, calculate_score, generate_report
    - Tool : [retriever_tool, search_tool]

| Tool Name            | Library                       | 역할                                  |
| -------------------- | ----------------------------- | --------------------------           |
| `retriever`          | FAISS + HuggingFace Embedding | 내부 PDF 기반 RAG 검색                 |
| `search_tool`        | DuckDuckGo Search             | 최신 시장 데이터 보강을 위한 웹 검색      |
| `llm / llm_creative` | OpenAI Chat Model             | 분석/생성 LLM (정량 분석 & 리포트 생성)   |
| Node                  | 역할                                                                 |
| --------------------- | ---------------------------------------|
| `classify_query`      | 사용자 쿼리를 ① 시장 주제 분류 ② 분석 깊이 ③ 웹 검색 여부 판단 |
| `retrieve_internal`   | FAISS 벡터DB에서 관련 PDF 기반 RAG 검색           |
| `web_search`          | DuckDuckGo 검색으로 최신 시장 트렌드 확보            |
| `analyze_market_size` | 시장 규모 분석 (규모, CAGR, 세그먼트, 지역별 현황)       |
| `analyze_growth`      | 성장 전망 분석 (CAGR, 성장 동력, 트렌드)             |
| `analyze_competition` | 경쟁 구도 분석 (Porter 5 Forces / 경쟁 강도)      |
| `analyze_risks`       | 시장 리스크 분석 (기술/경쟁/규제/수요)                 |
| `calculate_score`     | 시장성 점수(0~100) 산출 (정량 평가)                |
| `generate_report`     | Executive Summary 형태 최종 보고서 생성          |


- 경쟁사 비교 에이전트 (Competitor Analysis Agent) : 웹 검색을 통해 경쟁사를 탐색하고, 경쟁 구도 및 시장 포지셔닝을 자동 분석하는 에이전트
    - Node : identify_competitors, analyze_competitive_landscape, evaluate_competitive_positioning
    - Tool : DuckDuckGoSearchRun, ChatOpenAI (GPT-4o-mini), ChatPromptTemplate, StateGraph

- 투자 판단 에이전트 (Investment Decision Agent) : 7개 평가 영역(100점)과 6개 리스크를 종합 분석하여 투자 의사결 (Strong Buy~Pass)을 내리는 에이전트
    - Node : calculate_investment_scores, assess_investment_risks, make_final_decision
    - Tool : ChatOpenAI (GPT-4o-mini), ChatPromptTemplate, Python Logic, JSON Parser, StateGraph

## Architecture
![이미지](Untitled diagram-2025-10-20-061442.png)

## Directory Structure
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
│   ├── 2024년 KERIS_디지털교육 동향 제199호.pdf
│   ├── KERIS_디지털교육 동향_209호.pdf
│   ├── 에듀테크 진흥방안.pdf
│   └── db_faiss/
│       ├── index.faiss
│       └── index.pkl
├── db_faiss/
│   ├── index.faiss
│   └── index.pkl
├── outputs/
│   
├── prompts/
│   ├── competitor_analysis_prompt.py
│   ├── investment_decision_prompt.py
│   ├── market_analysis_prompt.py
│   ├── search_prompt.py
│   └── tech_summary_prompt.py
└── templates/
    ├── report_template.html
    └── report_test.pdf


## Contributors 
- 정재민 : Evaluation market size RAG Agent Design
- 장소민 : Company Comparison and Investment Evalution decision Agent Design
- 한정석 : Main Agent Design and all Agent Combination, PDF Generate and checking
- 이정엽 : Company Technical skill Set Summary