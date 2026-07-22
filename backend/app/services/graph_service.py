from app.db.neo4j import get_neo4j

def init_graph_schema():
    conn = get_neo4j()
    queries = [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (e:Equipment) REQUIRE e.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (f:Failure) REQUIRE f.type IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE",
    ]
    for q in queries:
        conn.query(q)

def insert_entities(document_id: int, entities: dict):
    conn = get_neo4j()
    
    # Simple insertion for MVP based on entity types
    equipments = entities.get("Equipment", [])
    failures = entities.get("Failure", [])
    
    # Create Document node
    conn.query("MERGE (d:Document {id: $doc_id})", {"doc_id": document_id})
    
    for eq in equipments:
        conn.query(
            "MERGE (e:Equipment {name: $name}) "
            "MERGE (d:Document {id: $doc_id}) "
            "MERGE (e)-[:MENTIONED_IN]->(d)",
            {"name": eq, "doc_id": document_id}
        )
        
    for f in failures:
        conn.query(
            "MERGE (fail:Failure {type: $type}) "
            "MERGE (d:Document {id: $doc_id}) "
            "MERGE (fail)-[:MENTIONED_IN]->(d)",
            {"type": f, "doc_id": document_id}
        )
        
def get_graph_data():
    conn = get_neo4j()
    query = """
    MATCH (n)-[r]->(m)
    RETURN n, r, m LIMIT 100
    """
    result = conn.query(query)
    
    nodes = {}
    edges = []
    
    if result:
        for record in result:
            n = record["n"]
            m = record["m"]
            r = record["r"]
            
            n_id = str(n.element_id)
            m_id = str(m.element_id)
            
            nodes[n_id] = {"id": n_id, "labels": list(n.labels), "properties": dict(n)}
            nodes[m_id] = {"id": m_id, "labels": list(m.labels), "properties": dict(m)}
            
            edges.append({
                "id": str(r.element_id),
                "source": n_id,
                "target": m_id,
                "type": r.type,
                "properties": dict(r)
            })
            
    return {"nodes": list(nodes.values()), "edges": edges}

def get_equipment_context(equipment: str):
    conn = get_neo4j()
    query = """
    MATCH (e:Equipment {name: $name})-[r]-(connected)
    RETURN e, r, connected LIMIT 20
    """
    result = conn.query(query, {"name": equipment})
    context = []
    if result:
        for record in result:
            connected = record["connected"]
            rel = record["r"]
            context.append(f"{equipment} {rel.type} {list(connected.labels)[0]} ({dict(connected)})")
    return "\\n".join(context)
