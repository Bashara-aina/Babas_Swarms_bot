"""RAGAS hallucination evaluation harness for Legiona."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from datasets import Dataset
from ragas import evaluate
from ragas.metrics import answer_relevancy, context_precision, faithfulness

from lib.legiona.minimax_client import LegionaOutput, create_structured_completion
from lib.legiona.rag_retriever import retrieve_context
from lib.legiona.self_evolve import evolve, load_evolved_rules, record_session

RESULTS_DIR = Path("lib/legiona/eval/results")
RESULTS_PATH = RESULTS_DIR / "latest.json"

EVAL_QA = [
    {
        "question": "What file contains the main Telegram bot startup entrypoint?",
        "ground_truth": "main.py",
    },
    {
        "question": "Which module is the compatibility shim that re-exports llm_client package functions?",
        "ground_truth": "llm_client.py",
    },
    {
        "question": "What command is documented in the Makefile for fast tests?",
        "ground_truth": "pytest tests/ -x -q --ignore=tests/test_computer_control.py",
    },
    {
        "question": "Which environment variable controls MiniMax API key access?",
        "ground_truth": "MINIMAX_API_KEY",
    },
    {
        "question": "Where are shared Claude legiona agent definitions located?",
        "ground_truth": ".claude/skills/legiona/",
    },
]


async def _answer_question(question: str) -> LegionaOutput:
    contexts = retrieve_context(question, top_k=10)
    evolved_rules = load_evolved_rules()
    system_prompt = (
        evolved_rules
        + "\nUse retrieved repository context only. "
        "Return concise grounded answer with uncertainty when needed."
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": f"Question: {question}\n\nContext:\n" + "\n---\n".join(contexts),
        },
    ]
    return await create_structured_completion(messages=messages, response_model=LegionaOutput)


async def run_eval() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for item in EVAL_QA:
        question = item["question"]
        contexts = retrieve_context(question, top_k=10)
        result = await _answer_question(question)
        rows.append(
            {
                "question": question,
                "answer": result.answer,
                "contexts": contexts,
                "ground_truth": item["ground_truth"],
            }
        )
        record_session(
            task=question,
            tool_calls=[],
            outcome=result.answer,
            success=result.confidence in ("HIGH", "MEDIUM"),
        )

    dataset = Dataset.from_list(rows)
    eval_result = evaluate(
        dataset=dataset,
        metrics=[faithfulness, answer_relevancy, context_precision],
    )
    summary = eval_result.to_pandas().to_dict(orient="records")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    payload = {"rows": rows, "summary": summary}
    RESULTS_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    evolve(last_n=5)

    print("question_count:", len(rows))
    print("summary:", json.dumps(summary, indent=2))
    print("saved:", str(RESULTS_PATH))
    return payload


if __name__ == "__main__":
    asyncio.run(run_eval())
