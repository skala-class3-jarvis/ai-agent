# AI Startup Investment Evaluation Agent
본 프로젝트는 에듀테크 스타트업에 대한 투자 가능성을 자동으로 평가하는 에이전트를 설계하고 구현한 실습 프로젝트입니다.

## Overview

- Objective : 에듀테크 스타트업의 기술력, 시장성, 리스크 등을 기준으로 투자 적합성 분석
- Method : AI Agent + Agentic RAG
- Tools : LLM-OpenAI, External web search tool, Retrival

## Features

- PDF 자료 기반 정보 추출 ( 경제동향지표, KERIS 디지털교육 동향 199호, 209호, 교육부 주관 에듀테크 진흥방안 정책자료(23.09) )
- 투자 기준별 판단 분류 ( 시장성, 기술력, 경쟁사 비교 )
- 종합 투자 요약 출력 ( Json : / PDF : )

## Tech Stack 

| Category   | Details                                                      |
|------------|--------------------------------------------------------------|
| Framework  | LangGraph, LangChain, Python                                 |
| LLM        | GPT-4o-mini via OpenAI API                                   |
| Retrieval  | FAISS                                                        |
| Embedding  | HuggingFaceEmbedding - dragonkue/multilingual-e5-small-ko    |

## Agents
 
- Agent A : Assesses technical competitiveness
- Agent B : Evaluates market opportunity and team capability
- Agent C : Comparison of opponent company which have similar technic

## Architecture
(그래프 이미지)

## Directory Structure
├── data/                  # 스타트업 PDF 문서
├── agents/                # 평가 기준별 Agent 모듈
├── prompts/               # 프롬프트 템플릿
├── outputs/               # 평가 결과 저장
├── app.py                 # 실행 스크립트
└── README.md

## Contributors 
- 정재민 : Evaluation market size RAG Agent Design
- 장소민 : Company Comparison and Investment decision Agent Design
- 한정석 : Main Agent Design and all Agent Combination, PDF Generate and checking
- 이정엽 : Company Technical skill Set Summary