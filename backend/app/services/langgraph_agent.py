from langgraph.graph import Graph, StateGraph
from typing import TypedDict, Annotated, Sequence
import operator
import json
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from openai import OpenAI
from app.core.config import settings
from app.services.embeddings import search_chunks
from app.services.graph_service import get_equipment_context

client = OpenAI(api_key=settings.OPENAI_API_KEY)

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    search_queries: list
    vector_context: str
    graph_context: str
    citations: list
    confidence: float
    final_answer: str

def planner(state: AgentState):
    query = state["messages"][-1].content
    # Simple planner: extract search terms for vector db and equipment name for graph
    prompt = f"""
    You are an AI planner.
    Extract search terms from the user query. Also extract any equipment names.
    Query: {query}
    Respond in JSON: {{"search_terms": ["term1", "term2"], "equipment_names": ["Pump A"]}}
    """
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        plan = json.loads(response.choices[0].message.content)
        return {"search_queries": plan.get("search_terms", [query]) + plan.get("equipment_names", [])}
    except:
        return {"search_queries": [query]}

def vector_retriever(state: AgentState):
    queries = state.get("search_queries", [])
    if not queries:
        queries = [state["messages"][-1].content]
        
    context = ""
    citations = []
    
    # Retrieve top K for the first query
    results = search_chunks(queries[0], limit=4)
    
    for res in results:
        payload = res.payload
        context += f"Document: {payload['filename']}, Page: {payload['page_number']}\nContent: {payload['text']}\n\n"
        citations.append({
            "document_name": payload['filename'],
            "page_number": payload['page_number'],
            "text_snippet": payload['text'][:150] + "..."
        })
        
    return {"vector_context": context, "citations": citations}

def graph_retriever(state: AgentState):
    queries = state.get("search_queries", [])
    graph_context = ""
    for query in queries:
        context = get_equipment_context(query)
        if context:
            graph_context += context + "\n"
    return {"graph_context": graph_context}

def generator(state: AgentState):
    query = state["messages"][-1].content
    v_context = state.get("vector_context", "")
    g_context = state.get("graph_context", "")
    
    prompt = f"""
    Answer the user's question based ONLY on the provided context.
    If the answer is not in the context, say "I don't know based on the provided documents."
    
    Vector Context:
    {v_context}
    
    Graph Context:
    {g_context}
    
    Question: {query}
    
    Respond in JSON format:
    {{
        "answer": "Your detailed answer",
        "confidence_score": 0.85
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful industrial AI assistant. Always return valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        return {
            "final_answer": result.get("answer", "Error generating answer."),
            "confidence": result.get("confidence_score", 0.0),
            "messages": [AIMessage(content=result.get("answer", ""))]
        }
    except Exception as e:
        return {
            "final_answer": "Error generating answer.",
            "confidence": 0.0,
            "messages": [AIMessage(content="Error")]
        }

def create_workflow():
    workflow = StateGraph(AgentState)
    workflow.add_node("planner", planner)
    workflow.add_node("vector_retriever", vector_retriever)
    workflow.add_node("graph_retriever", graph_retriever)
    workflow.add_node("generator", generator)
    
    workflow.set_entry_point("planner")
    workflow.add_edge("planner", "vector_retriever")
    workflow.add_edge("vector_retriever", "graph_retriever")
    workflow.add_edge("graph_retriever", "generator")
    workflow.set_finish_point("generator")
    return workflow.compile()

graph_app = create_workflow()

def run_copilot(query: str):
    inputs = {
        "messages": [HumanMessage(content=query)],
        "search_queries": [],
        "vector_context": "",
        "graph_context": "",
        "citations": [],
        "confidence": 0.0,
        "final_answer": ""
    }
    result = graph_app.invoke(inputs)
    
    return {
        "answer": result.get("final_answer", ""),
        "confidence_score": result.get("confidence", 0.0),
        "sources": result.get("citations", [])
    }
