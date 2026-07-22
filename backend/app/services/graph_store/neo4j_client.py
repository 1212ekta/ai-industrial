"""Thin wrapper around the Neo4j driver for graph writes and reads."""
from __future__ import annotations

from app.core.config import get_settings
from app.core.logging import logger


class Neo4jService:
    def __init__(self):
        from neo4j import GraphDatabase

        settings = get_settings()
        self._driver = GraphDatabase.driver(
            settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
        )
        self._database = settings.neo4j_database

    def close(self) -> None:
        self._driver.close()

    def _run(self, query: str, **params):
        with self._driver.session(database=self._database) as session:
            return list(session.run(query, **params))

    # ---------------------------------------------------------- Document/Equipment
    def upsert_document_node(self, document_id: str, filename: str, doc_type: str | None) -> None:
        self._run(
            """
            MERGE (d:Document {id: $document_id})
            SET d.filename = $filename, d.type = $doc_type
            """,
            document_id=document_id,
            filename=filename,
            doc_type=doc_type or "unknown",
        )

    def upsert_equipment(
        self, tag: str, equipment_type: str | None, plant: str | None, risk_level: str | None
    ) -> None:
        self._run(
            """
            MERGE (e:Equipment {tag: $tag})
            SET e.type = coalesce($equipment_type, e.type),
                e.plant = coalesce($plant, e.plant),
                e.risk_level = coalesce($risk_level, e.risk_level)
            """,
            tag=tag,
            equipment_type=equipment_type,
            plant=plant,
            risk_level=risk_level,
        )

    def link_equipment_mentioned_in(self, tag: str, document_id: str, page: int | None) -> None:
        self._run(
            """
            MATCH (e:Equipment {tag: $tag})
            MATCH (d:Document {id: $document_id})
            MERGE (e)-[r:MENTIONED_IN]->(d)
            SET r.page = $page
            """,
            tag=tag,
            document_id=document_id,
            page=page,
        )

    # ---------------------------------------------------------------- Engineer
    def upsert_engineer(self, name: str, department: str | None = None) -> None:
        self._run(
            "MERGE (p:Engineer {name: $name}) SET p.department = coalesce($department, p.department)",
            name=name,
            department=department,
        )

    def link_inspected_by(self, equipment_tag: str, engineer_name: str, date: str | None) -> None:
        self._run(
            """
            MATCH (e:Equipment {tag: $tag})
            MATCH (p:Engineer {name: $name})
            MERGE (e)-[r:INSPECTED_BY]->(p)
            SET r.date = $date
            """,
            tag=equipment_tag,
            name=engineer_name,
            date=date,
        )

    def link_maintained_by(self, equipment_tag: str, engineer_name: str, date: str | None) -> None:
        self._run(
            """
            MATCH (e:Equipment {tag: $tag})
            MATCH (p:Engineer {name: $name})
            MERGE (e)-[r:MAINTAINED_BY]->(p)
            SET r.date = $date
            """,
            tag=equipment_tag,
            name=engineer_name,
            date=date,
        )

    # ----------------------------------------------------------------- Vendor
    def upsert_vendor(self, name: str) -> None:
        self._run("MERGE (v:Vendor {name: $name})", name=name)

    def link_supplied_by(self, equipment_tag: str, vendor_name: str) -> None:
        self._run(
            """
            MATCH (e:Equipment {tag: $tag})
            MATCH (v:Vendor {name: $name})
            MERGE (e)-[:SUPPLIED_BY]->(v)
            """,
            tag=equipment_tag,
            name=vendor_name,
        )

    # ---------------------------------------------------------------- Failure
    def create_failure(
        self,
        failure_id: str,
        equipment_tag: str,
        failure_type: str,
        document_id: str,
        page: int | None,
    ) -> None:
        self._run(
            """
            MATCH (e:Equipment {tag: $tag})
            MATCH (d:Document {id: $document_id})
            MERGE (f:Failure {id: $failure_id})
            SET f.failure_type = $failure_type
            MERGE (e)-[:HAS_FAILURE]->(f)
            MERGE (f)-[r:MENTIONED_IN]->(d)
            SET r.page = $page
            """,
            failure_id=failure_id,
            tag=equipment_tag,
            failure_type=failure_type,
            document_id=document_id,
            page=page,
        )

    # ------------------------------------------------------------- Inspection
    def create_inspection(
        self, inspection_id: str, equipment_tag: str, document_id: str, page: int | None
    ) -> None:
        self._run(
            """
            MATCH (e:Equipment {tag: $tag})
            MATCH (d:Document {id: $document_id})
            MERGE (i:Inspection {id: $inspection_id})
            MERGE (i)-[:PERFORMED_ON]->(e)
            MERGE (i)-[r:MENTIONED_IN]->(d)
            SET r.page = $page
            """,
            inspection_id=inspection_id,
            tag=equipment_tag,
            document_id=document_id,
            page=page,
        )

    # ------------------------------------------------------------ Maintenance
    def create_maintenance(
        self, maintenance_id: str, equipment_tag: str, document_id: str, page: int | None
    ) -> None:
        self._run(
            """
            MATCH (e:Equipment {tag: $tag})
            MATCH (d:Document {id: $document_id})
            MERGE (m:Maintenance {id: $maintenance_id})
            MERGE (m)-[:PERFORMED_ON]->(e)
            MERGE (m)-[r:MENTIONED_IN]->(d)
            SET r.page = $page
            """,
            maintenance_id=maintenance_id,
            tag=equipment_tag,
            document_id=document_id,
            page=page,
        )

    def connect_equipment(self, tag_a: str, tag_b: str) -> None:
        self._run(
            """
            MATCH (a:Equipment {tag: $tag_a})
            MATCH (b:Equipment {tag: $tag_b})
            MERGE (a)-[:CONNECTED_TO]->(b)
            """,
            tag_a=tag_a,
            tag_b=tag_b,
        )

    # ------------------------------------------------------------------ Reads
    def get_equipment_subgraph(self, tag: str) -> dict:
        rows = self._run(
            """
            MATCH (e:Equipment {tag: $tag})
            OPTIONAL MATCH (e)-[:HAS_FAILURE]->(f:Failure)
            OPTIONAL MATCH (e)-[:INSPECTED_BY]->(insp:Engineer)
            OPTIONAL MATCH (e)-[:MAINTAINED_BY]->(maint:Engineer)
            OPTIONAL MATCH (e)-[:SUPPLIED_BY]->(v:Vendor)
            OPTIONAL MATCH (e)-[:MENTIONED_IN]->(d:Document)
            RETURN e AS equipment,
                   collect(DISTINCT f) AS failures,
                   collect(DISTINCT insp) AS inspectors,
                   collect(DISTINCT maint) AS maintainers,
                   collect(DISTINCT v) AS vendors,
                   collect(DISTINCT d) AS documents
            """,
            tag=tag,
        )
        if not rows:
            return {}
        record = rows[0]
        return {
            "equipment": dict(record["equipment"]) if record["equipment"] else None,
            "failures": [dict(f) for f in record["failures"] if f],
            "inspectors": [dict(i) for i in record["inspectors"] if i],
            "maintainers": [dict(m) for m in record["maintainers"] if m],
            "vendors": [dict(v) for v in record["vendors"] if v],
            "documents": [dict(d) for d in record["documents"] if d],
        }

    def get_maintenance_history(self, tag: str) -> list[dict]:
        rows = self._run(
            """
            MATCH (e:Equipment {tag: $tag})<-[:PERFORMED_ON]-(m:Maintenance)-[r:MENTIONED_IN]->(d:Document)
            RETURN m, d.filename AS filename, d.id AS document_id, r.page AS page
            """,
            tag=tag,
        )
        return [
            {
                "maintenance": dict(row["m"]),
                "filename": row["filename"],
                "document_id": row["document_id"],
                "page": row["page"],
            }
            for row in rows
        ]

    def get_inspection_history(self, tag: str) -> list[dict]:
        rows = self._run(
            """
            MATCH (e:Equipment {tag: $tag})<-[:PERFORMED_ON]-(i:Inspection)-[r:MENTIONED_IN]->(d:Document)
            RETURN i, d.filename AS filename, d.id AS document_id, r.page AS page
            """,
            tag=tag,
        )
        return [
            {
                "inspection": dict(row["i"]),
                "filename": row["filename"],
                "document_id": row["document_id"],
                "page": row["page"],
            }
            for row in rows
        ]

    def get_failure_history(self, tag: str) -> list[dict]:
        rows = self._run(
            """
            MATCH (e:Equipment {tag: $tag})-[:HAS_FAILURE]->(f:Failure)-[r:MENTIONED_IN]->(d:Document)
            RETURN f, d.filename AS filename, d.id AS document_id, r.page AS page
            ORDER BY f.failure_type
            """,
            tag=tag,
        )
        return [
            {
                "failure": dict(row["f"]),
                "filename": row["filename"],
                "document_id": row["document_id"],
                "page": row["page"],
            }
            for row in rows
        ]

    def get_graph_stats(self) -> dict:
        rows = self._run(
            """
            MATCH (e:Equipment) WITH count(e) AS equipment_count
            MATCH (f:Failure) WITH equipment_count, count(f) AS failure_count
            MATCH (m:Maintenance) WITH equipment_count, failure_count, count(m) AS maintenance_count
            RETURN equipment_count, failure_count, maintenance_count
            """
        )
        if not rows:
            return {"equipment_count": 0, "failure_count": 0, "maintenance_count": 0}
        row = rows[0]
        return {
            "equipment_count": row["equipment_count"],
            "failure_count": row["failure_count"],
            "maintenance_count": row["maintenance_count"],
        }

    def delete_document_and_orphans(self, document_id: str) -> None:
        """Detach-delete a Document node. Connected entity nodes (Equipment etc.)
        are left in place since they may be referenced by other documents."""
        self._run("MATCH (d:Document {id: $document_id}) DETACH DELETE d", document_id=document_id)
