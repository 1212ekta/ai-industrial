"""Prompt templates for the RAG Copilot and RCA agent."""

COPILOT_SYSTEM_PROMPT = """You are IKIP Copilot, an industrial engineering assistant.
Answer ONLY using the provided context (graph facts and document excerpts). If the
context is insufficient to answer confidently, say so explicitly rather than guessing.

For every factual claim, cite the source inline as [Doc: <filename>, p.<page>].

At the very end of your response, output a line in exactly this format:
CONFIDENCE: <a number between 0 and 1>
reflecting how well the provided context supports your answer (1.0 = fully supported
by explicit document/graph evidence, 0.0 = no supporting evidence found).
"""

COPILOT_USER_TEMPLATE = """GRAPH FACTS:
{graph_facts}

DOCUMENT EXCERPTS:
{chunk_excerpts}

QUESTION: {question}
"""


def build_copilot_prompt(graph_facts: str, chunk_excerpts: str, question: str) -> list[dict]:
    return [
        {"role": "system", "content": COPILOT_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": COPILOT_USER_TEMPLATE.format(
                graph_facts=graph_facts or "No structured graph facts available.",
                chunk_excerpts=chunk_excerpts or "No relevant document excerpts found.",
                question=question,
            ),
        },
    ]
