"""Individual LangGraph node functions for the Root Cause Analysis workflow."""
from __future__ import annotations

import json
from typing import TypedDict

from app.core.config import get_settings
from app.core.logging import logger
from app.services.graph_store.neo4j_client import Neo4jService
from app.services.rag.retriever import HybridRetriever

INSUFFICIENT_DATA_MESSAGE = (
    "No historical maintenance, inspection, or failure records were found for this "
    "equipment, and no relevant document excerpts matched the described symptoms."
)

RCA_CAUSE_GENERATION_PROMPT = """You are an industrial reliability engineer performing
root cause analysis. Given the equipment's history and relevant document excerpts,
propose the most likely root causes for the described problem.

Respond with ONLY valid JSON in this shape:
{{
  "causes": [
    {{"cause": "...", "probability": 0.0, "explanation": "..."}}
  ]
}}
Probabilities across all causes should be reasonable relative estimates (they need not
sum to 1). Base every cause on the provided context — do not invent history that isn't
present in the equipment context or excerpts.

EQUIPMENT: {equipment_name}
PROBLEM DESCRIPTION: {problem_description}

EQUIPMENT HISTORY (graph):
{graph_context}

RELEVANT DOCUMENT EXCERPTS:
{chunk_excerpts}
"""

RCA_ACTIONS_PROMPT = """Given these ranked root causes for {equipment_name}, propose
3-6 concrete recommended actions (preventive + corrective), each one short sentence.
Respond with ONLY a JSON array of strings, e.g. ["action 1", "action 2"].

ROOT CAUSES:
{causes_json}
"""


class RCAState(TypedDict, total=False):
    equipment_name: str
    problem_description: str
    graph_context: dict
    retrieved_chunks: list
    candidate_causes: list
    ranked_causes: list
    recommended_actions: list
    overall_confidence: float
    insufficient_data: bool


def fetch_equipment_context(state: RCAState) -> RCAState:
    """Pull failure/maintenance/inspection history from Neo4j."""
    tag = state["equipment_name"].strip().upper().replace(" ", "").replace("-", "")
    neo4j = Neo4jService()
    try:
        context = {
            "subgraph": neo4j.get_equipment_subgraph(tag),
            "maintenance_history": neo4j.get_maintenance_history(tag),
            "inspection_history": neo4j.get_inspection_history(tag),
            "failure_history": neo4j.get_failure_history(tag),
        }
    except Exception as exc:
        logger.warning(f"Neo4j context fetch failed for {tag}: {exc}")
        context = {}
    finally:
        neo4j.close()
    return {**state, "graph_context": context}


def retrieve_relevant_chunks(state: RCAState) -> RCAState:
    """Vector-search for chunks matching equipment + symptoms (OEM manuals, past failure reports)."""
    retriever = HybridRetriever()
    query = f"{state['equipment_name']} {state['problem_description']}"
    chunks = retriever.retrieve_chunks(query, top_k=8, equipment_tag=None)

    has_graph_history = bool(
        state.get("graph_context", {}).get("maintenance_history")
        or state.get("graph_context", {}).get("inspection_history")
        or state.get("graph_context", {}).get("failure_history")
    )
    insufficient = not chunks and not has_graph_history

    return {**state, "retrieved_chunks": chunks, "insufficient_data": insufficient}


def generate_candidate_causes(state: RCAState) -> RCAState:
    if state.get("insufficient_data"):
        return {**state, "candidate_causes": []}

    from openai import OpenAI

    settings = get_settings()
    client = OpenAI(api_key=settings.openai_api_key)
    retriever = HybridRetriever()

    prompt = RCA_CAUSE_GENERATION_PROMPT.format(
        equipment_name=state["equipment_name"],
        problem_description=state["problem_description"],
        graph_context=json.dumps(state.get("graph_context", {}), default=str)[:4000],
        chunk_excerpts=retriever.format_chunk_excerpts(state.get("retrieved_chunks", [])),
    )
    try:
        response = client.chat.completions.create(
            model=settings.openai_chat_model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        parsed = json.loads(response.choices[0].message.content)
        causes = parsed.get("causes", [])
    except Exception as exc:
        logger.error(f"RCA cause generation failed: {exc}")
        causes = []

    return {**state, "candidate_causes": causes}


def score_and_rank_causes(state: RCAState) -> RCAState:
    causes = state.get("candidate_causes", [])
    ranked = sorted(causes, key=lambda c: c.get("probability", 0), reverse=True)

    chunks = state.get("retrieved_chunks", [])
    for cause in ranked:
        cause["supporting_evidence"] = [
            {
                "document_id": c.document_id,
                "filename": c.filename,
                "page_number": c.page_number,
                "excerpt": c.content[:300],
            }
            for c in chunks[:2]
        ]

    overall_confidence = ranked[0]["probability"] if ranked else 0.0
    return {**state, "ranked_causes": ranked, "overall_confidence": overall_confidence}


def generate_recommendations(state: RCAState) -> RCAState:
    if not state.get("ranked_causes"):
        return {
            **state,
            "recommended_actions": [
                "Insufficient historical data — schedule a manual inspection before further action."
            ],
        }

    from openai import OpenAI

    settings = get_settings()
    client = OpenAI(api_key=settings.openai_api_key)

    prompt = RCA_ACTIONS_PROMPT.format(
        equipment_name=state["equipment_name"],
        causes_json=json.dumps(state["ranked_causes"][:5]),
    )
    try:
        response = client.chat.completions.create(
            model=settings.openai_chat_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        raw = response.choices[0].message.content.strip()
        raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        actions = json.loads(raw)
    except Exception as exc:
        logger.error(f"RCA recommendation generation failed: {exc}")
        actions = ["Review equipment history manually and consult OEM documentation."]

    return {**state, "recommended_actions": actions}


def insufficient_data_response(state: RCAState) -> RCAState:
    return {
        **state,
        "ranked_causes": [],
        "recommended_actions": [INSUFFICIENT_DATA_MESSAGE],
        "overall_confidence": 0.0,
    }
