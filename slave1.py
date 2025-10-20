from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

import openai


# ---------------------------------------------------------------------------
# Data shapes passed between MASTER and SLAVE1
# ---------------------------------------------------------------------------

@dataclass
class Briefing:
    source: str
    content: str
    url: Optional[str] = None

    def to_prompt_block(self, idx: int) -> str:
        parts = [f"[{idx}] source: {self.source}"]
        if self.url:
            parts.append(f"url: {self.url}")
        header = " | ".join(parts)
        body = self.content.strip()
        return f"{header}\n{body}"


@dataclass
class Task:
    task_id: str
    company: str
    briefings: List[Briefing]
    focus: List[str] = field(default_factory=list)

    def focus_line(self) -> str:
        return ", ".join(self.focus) if self.focus else "general tech summary"


# ---------------------------------------------------------------------------
# GPT-4o wrapper
# ---------------------------------------------------------------------------

class GPT4oClient:
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        openai.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        if not openai.api_key:
            raise ValueError("OPENAI_API_KEY is required for SLAVE1.")
        if base_url or os.getenv("OPENAI_BASE_URL"):
            openai.api_base = base_url or os.getenv("OPENAI_BASE_URL")

    def summarize(self, briefings: str, company: str, focus: str) -> Dict[str, Any]:
        system_prompt = (
            "You are a concise analyst. Only use the given briefings. "
            "Return JSON with keys: summary, highlights, gaps. "
            "Each highlight must be short. Mark unknown facts with '(unknown)'."
        )
        user_prompt = (
            f"Company: {company}\n"
            f"Focus: {focus}\n"
            "Briefings:\n"
            f"{briefings}\n"
        )
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )
        content = response["choices"][0]["message"]["content"]
        return json.loads(content)


# ---------------------------------------------------------------------------
# Tech summary agent
# ---------------------------------------------------------------------------

class TechSummaryAgent:
    def __init__(self, client: GPT4oClient):
        self.client = client

    def run(self, task: Task) -> Dict[str, Any]:
        if not task.briefings:
            return {
                "task_id": task.task_id,
                "company": task.company,
                "error": "NO_BRIEFINGS",
                "message": "No briefings provided.",
            }

        blocks = [b.to_prompt_block(idx) for idx, b in enumerate(task.briefings, start=1)]
        briefing_text = "\n\n".join(blocks)

        result = self.client.summarize(
            briefings=briefing_text,
            company=task.company,
            focus=task.focus_line(),
        )

        return {
            "task_id": task.task_id,
            "company": task.company,
            "summary": result.get("summary", "").strip(),
            "highlights": result.get("highlights", []),
            "gaps": result.get("gaps", []),
            "briefings_used": [asdict(b) for b in task.briefings],
        }


# ---------------------------------------------------------------------------
# CLI helper for local dry-runs
# ---------------------------------------------------------------------------

def read_task(path: str) -> Task:
    with open(path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)

    briefings = [
        Briefing(
            source=item.get("source", "unknown"),
            content=item.get("content", ""),
            url=item.get("url"),
        )
        for item in payload.get("briefings", [])
    ]

    return Task(
        task_id=payload["task_id"],
        company=payload["company"],
        briefings=briefings,
        focus=payload.get("focus", []),
    )


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Run SLAVE1 tech summary agent.")
    parser.add_argument("--task", required=True, help="Path to task JSON file.")
    args = parser.parse_args()

    task = read_task(args.task)
    client = GPT4oClient()
    agent = TechSummaryAgent(client)

    result = agent.run(task)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
