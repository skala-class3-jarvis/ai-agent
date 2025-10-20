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

#### 시장성 평가 지표

| 평가 항목 | 배점 | 평가 기준 |
|---|---|---|
| 시장 규모 점수 (market_size_score) | 0~25점 | 시장 규모가 클수록 높은 점수 |
| 성장성 점수 (growth_score) | 0~30점 | 성장률(CAGR)이 높을수록 높은 점수 |
| 경쟁 환경 점수 (competition_score) | 0~25점 | 경쟁이 약할수록 높은 점수 (진입장벽 高 = 高점수) |
| 리스크 점수 (risk_score) | 0~20점 | 리스크가 낮을수록 높은 점수 |
| **총점 (total_score)** | **0~100점** | 4개 항목의 합산 점수 |

---

### 4. Competitor Analysis Agent

경쟁사 분석 에이전트

**Purpose**: 웹 검색을 통해 경쟁사를 탐색하고 경쟁 구도 및 시장 포지셔닝 자동 분석

**Tools**

| Tool Name           | Library              | 역할                              |
|---------------------|----------------------|-----------------------------------|
| DuckDuckGoSearchRun | DuckDuckGo           | 경쟁사 정보 웹 검색               |

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
| JSON Parser         | Python               | 결과 구조화 및 파싱               |

**Nodes**

| Node                        | 역할                                      |
|-----------------------------|-------------------------------------------|
| calculate_investment_scores | 7개 영역별 투자 점수 계산 (100점 만점)   |
| assess_investment_risks     | 6개 리스크 요소 평가 및 위험도 산출       |
| make_final_decision         | 종합 점수 기반 최종 투자 결정 도출        |


---

### 투자적합성 평가 지표
### 투자 평가 지표
1. 일반 스타트업이 아닌 교육 분야에 최적화된 평가 지표 
2. 성공한 에듀테크 투자 사례 분석(Khan Academy, Duolingo 등)
3. 단기 성과와 장기 잠재력 균형
4. 객관적으로 측정 가능한 지표 우선

### 평가 영역 및 배점 (총 100점)

| 순위 | 평가 영역 | 배점 | 비중 | 주요 평가 내용 |
|:---:|:---|:---:|:---:|:---|
| 1 | 🎓 **교육 효과성** | 25점 | 25% | ESSA 증거 수준, 학습 성과 검증, 학습 과학 기반, 적응형 학습 |
| 2 | 📈 **시장성 & 트랙션** | 20점 | 20% | TAM 규모, 매출 트랙션, 성장률, 고객 유지율, NRR |
| 3 | 👥 **팀 역량** | 20점 | 20% | 창업팀 경험, 팀 완전성, 풀타임 헌신, 네트워크 |
| 4 | 💻 **기술력 & 차별성** | 15점 | 15% | 독자 기술/IP, 제품 성숙도, 확장성, 데이터 활용 |
| 5 | 💰 **비즈니스 모델** | 10점 | 10% | 수익 모델 명확성, Unit Economics, 수익 다각화, 재무 건전성 |
| 6 | 🎯 **경쟁 우위** | 5점 | 5% | 차별화 요소, 진입장벽 |
| 7 | ⚖️ **규제 준수** | 5점 | 5% | 데이터 프라이버시, 접근성, 윤리적 AI |

### 세부 평가 기준
#### 1. 🎓 교육 효과성 (25점)

| 항목 | 배점 | 평가 내용 |
|:---|:---:|:---|
| ESSA 증거 수준 | 10점 | Strong (9-10) / Moderate (6-8) / Promising (3-5) / No Evidence (0-2) |
| 학습 성과 검증 | 8점 | 학업 성취도(4) + 학습 참여도(2) + 만족도(2) |
| 학습 과학 기반 | 5점 | 인지과학 이론(3) + 교육 전문가 참여(2) |
| 적응형 학습 | 2점 | 개인화/맞춤형 학습 제공 |

#### 2. 📈 시장성 & 트랙션 (20점)

| 항목 | 배점 | 평가 기준 |
|:---|:---:|:---|
| TAM 규모 | 5점 | $10B+ (5점) ~ $100M 미만 (1점) |
| 매출 트랙션 | 6점 | $5M+ (6점) ~ Pre-revenue (0-1점) |
| 성장률 | 4점 | 150%+ YoY (4점) ~ 20% 미만 (0점) |
| 고객 유지율 | 3점 | 95%+ (3점) ~ 80% 미만 (0점) |
| NRR | 2점 | 120%+ (2점) ~ 100% 미만 (0점) |

#### 3. 👥 팀 역량 (20점)

| 항목 | 배점 | 평가 기준 |
|:---|:---:|:---|
| 창업팀 경험 | 8점 | CEO(3) + CTO(3) + 교육전문가(2) |
| 팀 완전성 | 5점 | 핵심 역할 충원(3) + 팀 규모 적정성(2) |
| 풀타임 헌신 | 3점 | 모두 풀타임(3) ~ 대부분 파트타임(0) |
| 네트워크 | 4점 | 유명 VC(2) + 교육계 인사(1) + 전문가(1) |

#### 4. 💻 기술력 & 차별성 (15점)

| 항목 | 배점 | 평가 기준 |
|:---|:---:|:---|
| 독자 기술/IP | 6점 | 특허(2) + 핵심 알고리즘(2) + 데이터셋(2) |
| 제품 성숙도 | 4점 | Live & Scaling (4) ~ Idea (0) |
| 확장성 | 3점 | 아키텍처(2) + 비용 구조(1) |
| 데이터 활용 | 2점 | 데이터 축적(1) + 개선 사이클(1) |

#### 5. 💰 비즈니스 모델 (10점)

| 항목 | 배점 | 평가 기준 |
|:---|:---:|:---|
| 수익 모델 | 4점 | B2B SaaS (4) ~ 불명확 (0) |
| Unit Economics | 3점 | LTV/CAC > 3 (3) ~ < 1 (0) |
| 수익 다각화 | 2점 | 2개 이상(2) / 단일(0) |
| 재무 건전성 | 1점 | Runway 12개월+ (1) / 미만 (0) |

#### 6. 🎯 경쟁 우위 (5점)

| 항목 | 배점 | 평가 기준 |
|:---|:---:|:---|
| 차별화 요소 | 3점 | Blue Ocean (3) ~ Me-too (0) |
| 진입장벽 | 2점 | 높음(2) / 중간(1) / 낮음(0) |

#### 7. ⚖️ 규제 준수 (5점)

| 항목 | 배점 | 평가 기준 |
|:---|:---:|:---|
| 데이터 프라이버시 | 3점 | 완벽 준수(3) ~ 미준수(0) |
| 접근성 | 1점 | 장애인/소외계층 고려 |
| 윤리적 AI | 1점 | 편향 제거, 투명성 |

## ⚠️ 리스크 평가

### 6가지 리스크 카테고리

| 리스크 유형 | 평가 요소 | 점수 범위 | 가중치 |
|:---|:---|:---:|:---:|
| 🌍 **시장 리스크** | 시장 규모, 성장성, 경쟁 강도 | 1-10 | 높음 |
| 💻 **기술 리스크** | 기술 검증, 확장성, 개발 난이도 | 1-10 | 높음 |
| 🎯 **실행 리스크** | 팀 역량, 실행 능력, 운영 복잡도 | 1-10 | 높음 |
| 💰 **재무 리스크** | 자금 확보, Runway, Unit Economics | 1-10 | 중간 |
| ⚔️ **경쟁 리스크** | 경쟁 강도, 차별화, 진입장벽 | 1-10 | 높음 |
| ⚖️ **규제 리스크** | 법규 준수, 정책 변화, 규제 이슈 | 1-10 | 낮음 |

### 리스크 수준별 해석

| 전체 점수 | 수준 | 의미 | 투자 권장 |
|:---:|:---:|:---|:---:|
| 9-10점 | 🔴 매우 높음 | 투자 부적합 | ❌ |
| 7-8점 | 🟠 높음 | 신중한 검토 필요 | ⚠️ |
| 5-6점 | 🟡 중간 | 관리 가능한 리스크 | ✅ |
| 3-4점 | 🟢 낮음 | 안전한 투자 | ✅✅ |
| 1-2점 | 🔵 매우 낮음 | 이상적인 투자 | 🌟 |

**전체 리스크 점수** = (6개 리스크 합계) / 6

## 🎯 투자 의사결정

### 투자 등급 체계

| 총점 범위 | 등급 | 투자 결정 | 신뢰도 | 액션 | 예상 성공률 |
|:---:|:---:|:---:|:---:|:---|:---:|
| **80-100점** | S | **Strong Buy** | 높음 | 즉시 투자 추진, 리드 투자 고려 | 80-90% |
| **65-79점** | A | **Buy** | 중-높음 | 투자 권장, 표준 DD 진행 | 60-75% |
| **50-64점** | B | **Hold** | 중간 | 조건부 검토, 3-6개월 관찰 | 40-55% |
| **35-49점** | C | **Watch** | 낮음 | 투자 보류, 6-12개월 후 재평가 | 20-35% |
| **0-34점** | D | **Pass** | 매우 낮음 | 투자하지 않음 | 0-15% |

### 리스크 기반 등급 조정

| 리스크 수준 | 점수 범위 | 조정 규칙 |
|:---:|:---:|:---|
| 매우 높음 (8-10점) | 75점 미만 | **2단계 하향** (Buy → Watch) |
| 높음 (7점 이상) | 80점 미만 | **1단계 하향** (Strong Buy → Buy) |
| 중간 (5-6점) | - | 조정 없음 |
| 낮음 (3-4점) | 60점 이상 | **1단계 상향** 고려 (Hold → Buy) |
| 매우 낮음 (1-2점) | 50점 이상 | **보너스 +3점** |

### 의사결정 프로세스

```
Step 1: 투자 점수 계산 (0-100점)
   ↓
Step 2: 리스크 평가 (1-10점)
   ↓
Step 3: 초기 등급 결정 (S/A/B/C/D)
   ↓
Step 4: 리스크 기반 조정
   ↓
Step 5: 최종 투자 결정
```

## 최종 Score 점수 집계
**점수 현황:**
- 기술력: {tech}/100 (가중치 20%)
- 학습효과: {learning}/100 (가중치 20%)
- 시장성: {market}/100 (가중치 25%)
- 경쟁력: {competition}/100 (가중치 15%)
- 성장가능성: {growth}/100 (가중치 10%)
- 리스크: {risk}/100 (가중치 10%, 높을수록 안전)


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






