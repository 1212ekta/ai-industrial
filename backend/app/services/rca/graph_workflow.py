"""LangGraph state machine for the Root Cause Analysis agent.

Flow:
  START -> fetch_equipment_context -> retrieve_relevant_chunks
        -> [insufficient_data? -> insufficient_data_response -> END]
        -> generate_candidate_causes -> score_and_rank_causes
        -> generate_recommendations -> END
"""
from __future__ import annotations

from langgraph.graph import END, StateGraph

from app.schemas.rca import RCAResponse, RootCause, SupportingEvidence
from app.services.rca.nodes import (
    RCAState,
    fetch_equipment_context,
    generate_candidate_causes,
    generate_recommendations,
    insufficient_data_response,
    retrieve_relevant_chunks,
    score_and_rank_causes,
)


def _route_after_retrieval(state: RCAState) -> str:
    return "insufficient_data_response" if state.get("insufficient_data") else "generate_candidate_causes"


def build_rca_graph():
    graph = StateGraph(RCAState)

    graph.add_node("fetch_equipment_context", fetch_equipment_context)
    graph.add_node("retrieve_relevant_chunks", retrieve_relevant_chunks)
    graph.add_node("generate_candidate_causes", generate_candidate_causes)
    graph.add_node("score_and_rank_causes", score_and_rank_causes)
    graph.add_node("generate_recommendations", generate_recommendations)
    graph.add_node("insufficient_data_response", insufficient_data_response)

    graph.set_entry_point("fetch_equipment_context")
    graph.add_edge("fetch_equipment_context", "retrieve_relevant_chunks")
    graph.add_conditional_edges(
        "retrieve_relevant_chunks",
        _route_after_retrieval,
        {
            "insufficient_data_response": "insufficient_data_response",
            "generate_candidate_causes": "generate_candidate_causes",
        },
    )
    graph.add_edge("generate_candidate_causes", "score_and_rank_causes")
    graph.add_edge("score_and_rank_causes", "generate_recommendations")
    graph.add_edge("generate_recommendations", END)
    graph.add_edge("insufficient_data_response", END)

    return graph.compile()


class RCAWorkflowService:
    def __init__(self):
        self._app = build_rca_graph()

    def run(self, equipment_name: str, problem_description: str) -> RCAResponse:
        initial_state: RCAState = {
            "equipment_name": equipment_name,
            "problem_description": problem_description,
        }
        final_state = self._app.invoke(initial_state)

        root_causes = [
            RootCause(
                cause=c.get("cause", "Unknown"),
                probability=float(c.get("probability", 0.0)),
                explanation=c.get("explanation", ""),
                supporting_evidence=[
                    SupportingEvidence(**e) for e in c.get("supporting_evidence", [])
                ],
            )
            for c in final_state.get("ranked_causes", [])
        ]

        return RCAResponse(
            equipment_name=equipment_name,
            root_causes=root_causes,
            recommended_actions=final_state.get("recommended_actions", []),
            overall_confidence=float(final_state.get("overall_confidence", 0.0)),
        )
