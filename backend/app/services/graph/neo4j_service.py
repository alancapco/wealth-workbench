"""Wealth knowledge graph. Neo4j is the store when it is reachable; otherwise the same shape is built locally."""
from __future__ import annotations

import csv
import json
import logging
from pathlib import Path
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.client_data import ClientPortfolioHolding, DemoClient
from app.services.journey.llm import complete

logger = logging.getLogger(__name__)

_MERGE = {
    "Person": "MERGE (n:Person {node_id: $node_id}) SET n.name = $name",
    "Trust": "MERGE (n:Trust {node_id: $node_id}) SET n.name = $name",
    "HoldingEntity": "MERGE (n:HoldingEntity {node_id: $node_id}) SET n.name = $name",
    "CustodyAccount": "MERGE (n:CustodyAccount {node_id: $node_id}) SET n.name = $name",
    "Holding": "MERGE (n:Holding {node_id: $node_id}) SET n.name = $name",
    "WealthRule": "MERGE (n:WealthRule {node_id: $node_id}) SET n.name = $name",
    "Advisor": "MERGE (n:Advisor {node_id: $node_id}) SET n.name = $name",
}
_LABELS = {
    "Person": 1,
    "Trust": 2,
    "HoldingEntity": 3,
    "CustodyAccount": 4,
    "Holding": 5,
    "WealthRule": 6,
    "Advisor": 1,
    "WealthClient": 0,
}
_driver = None

_REPO_DATA = Path(__file__).resolve().parents[4] / "demo_data"


def _driver_or_none():
    global _driver
    if not settings.NEO4J_ENABLED:
        return None
    if _driver is not None:
        return _driver
    try:
        from neo4j import GraphDatabase

        driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
        )
        driver.verify_connectivity()
        _driver = driver
        return driver
    except Exception:
        logger.warning("Neo4j is not reachable; the wealth graph will use the local fallback", exc_info=True)
        return None


def _tan_structure() -> tuple[list[dict], list[dict]]:
    nodes_path = _REPO_DATA / "graph_nodes.csv"
    edges_path = _REPO_DATA / "graph_edges.csv"
    if not nodes_path.exists() or not edges_path.exists():
        return [], []
    nodes = []
    with nodes_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            kind = {
                "person": "Person",
                "trust": "Trust",
                "holding_entity": "HoldingEntity",
                "account": "CustodyAccount",
                "advisor": "Advisor",
            }.get(row.get("node_class") or "", "Person")
            nodes.append({
                "local_id": row["node_id"],
                "name": row.get("label") or row.get("synthetic_name") or row["node_id"],
                "kind": kind,
            })
    edges = []
    with edges_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            edges.append({
                "source": row["from_node_id"],
                "target": row["to_node_id"],
                "relationship_type": row.get("edge_type") or "RELATED",
            })
    return nodes, edges


def assemble_graph(client: dict, holdings: list[dict]) -> dict:
    """Build the D3 payload for one client. Structure for the Tan book comes from the demo graph files."""
    root = str(client["id"])
    name = client["name"]
    nodes = [{
        "id": root,
        "name": name,
        "symbolSize": 52,
        "category": 0,
        "kind": "WealthClient",
        "label": {"show": True},
        "entitlement": "RM",
        "is_root": True,
    }]
    links = []
    office = (client.get("family_office_name") or "")
    if "tan" in office.lower() or "family office" in name.lower():
        structure, edges = _tan_structure()
        local_to_id = {}
        for item in structure:
            node_id = f"{root}:{item['local_id']}"
            local_to_id[item["local_id"]] = node_id
            nodes.append({
                "id": node_id,
                "name": item["name"],
                "symbolSize": 36,
                "category": _LABELS.get(item["kind"], 1),
                "kind": item["kind"],
                "label": {"show": True},
                "entitlement": None,
                "is_root": False,
            })
        if structure:
            links.append({
                "source": root,
                "target": local_to_id[structure[0]["local_id"]],
                "relationship_type": "HOUSEHOLD",
                "value": 1,
            })
        for edge in edges:
            if edge["source"] in local_to_id and edge["target"] in local_to_id:
                links.append({
                    "source": local_to_id[edge["source"]],
                    "target": local_to_id[edge["target"]],
                    "relationship_type": edge["relationship_type"],
                    "value": 1,
                })
    else:
        person_id = f"{root}:person"
        nodes.append({
            "id": person_id,
            "name": name,
            "symbolSize": 34,
            "category": 1,
            "kind": "Person",
            "label": {"show": True},
            "entitlement": None,
            "is_root": False,
        })
        links.append({"source": root, "target": person_id, "relationship_type": "IS", "value": 1})

    account_id = f"{root}:account"
    nodes.append({
        "id": account_id,
        "name": "Custody account",
        "symbolSize": 30,
        "category": 4,
        "kind": "CustodyAccount",
        "label": {"show": True},
        "entitlement": None,
        "is_root": False,
    })
    links.append({"source": root, "target": account_id, "relationship_type": "HOLDS_ACCOUNT", "value": 1})
    for index, holding in enumerate(holdings[:8]):
        hid = f"{root}:h{index}"
        nodes.append({
            "id": hid,
            "name": holding.get("asset_name") or "Holding",
            "symbolSize": 24,
            "category": 5,
            "kind": "Holding",
            "label": {"show": True},
            "entitlement": None,
            "is_root": False,
        })
        links.append({"source": account_id, "target": hid, "relationship_type": "HOLDS", "value": 1})

    jurisdiction = (client.get("country") or "Singapore").lower()
    rules = [("MAS Notice FAA-N16", "SG")]
    if "hong" in jurisdiction:
        rules = [("SFC suitability requirement", "HK")]
    if client.get("shariah_compliant"):
        rules.append(("AAOIFI Shariah screening", "AAOIFI"))
    for offset, (rule_name, _code) in enumerate(rules):
        rid = f"{root}:rule{offset}"
        nodes.append({
            "id": rid,
            "name": rule_name,
            "symbolSize": 28,
            "category": 6,
            "kind": "WealthRule",
            "label": {"show": True},
            "entitlement": None,
            "is_root": False,
        })
        links.append({"source": root, "target": rid, "relationship_type": "GOVERNED_BY", "value": 1})

    categories = [{"name": name} for name in (
        "Client", "Person", "Trust", "Entity", "Account", "Holding", "Regulation",
    )]
    lookthrough = {
        "trusts": sum(1 for node in nodes if node["kind"] == "Trust"),
        "entities": sum(1 for node in nodes if node["kind"] == "HoldingEntity"),
        "holdings": sum(1 for node in nodes if node["kind"] == "Holding"),
        "rules": sum(1 for node in nodes if node["kind"] == "WealthRule"),
    }
    return {
        "nodes": nodes,
        "links": links,
        "categories": categories,
        "root_id": root,
        "stats": {"nodes": len(nodes), "links": len(links)},
        "lookthrough_summary": lookthrough,
        "source": "postgres_fallback",
    }


def _write_neo4j(graph: dict, client_id: str) -> bool:
    driver = _driver_or_none()
    if driver is None:
        return False
    try:
        with driver.session(database=settings.NEO4J_DATABASE) as session:
            session.run(
                "MATCH (n) WHERE n.node_id STARTS WITH $prefix DETACH DELETE n",
                prefix=f"{client_id}:",
            )
            session.run(
                "MERGE (c:WealthClient {client_id: $client_id}) "
                "SET c.node_id = $client_id, c.name = $name, c.payload = $payload",
                client_id=client_id,
                name=next(node["name"] for node in graph["nodes"] if node["id"] == client_id),
                payload=json.dumps(graph),
            )
            for node in graph["nodes"]:
                statement = _MERGE.get(node["kind"])
                if statement is None:
                    continue
                session.run(statement, node_id=node["id"], name=node["name"])
            for link in graph["links"]:
                session.run(
                    "MATCH (a {node_id: $source}), (b {node_id: $target}) "
                    "MERGE (a)-[r:WEALTH_LINK {kind: $kind}]->(b)",
                    source=link["source"],
                    target=link["target"],
                    kind=link["relationship_type"],
                )
            row = session.run(
                "MATCH (c:WealthClient {client_id: $client_id}) RETURN c.payload AS payload",
                client_id=client_id,
            ).single()
        return bool(row and row["payload"])
    except Exception:
        logger.warning("Neo4j wealth-graph write failed", exc_info=True)
        return False


def _paths(client_id: str) -> list[str]:
    driver = _driver_or_none()
    if driver is None:
        return []
    try:
        with driver.session(database=settings.NEO4J_DATABASE) as session:
            rows = session.run(
                "MATCH (c:WealthClient {client_id: $client_id})-[r:WEALTH_LINK]-(n) "
                "RETURN c.name AS client, r.kind AS rel, n.name AS other LIMIT 40",
                client_id=client_id,
            )
            return [f"{row['client']} -[{row['rel']}]-> {row['other']}" for row in rows]
    except Exception:
        logger.warning("Neo4j path read failed", exc_info=True)
        return []


async def client_graph(db: AsyncSession, client_id: UUID) -> dict | None:
    client = await db.get(DemoClient, client_id)
    if client is None:
        return None
    holdings = (
        await db.execute(select(ClientPortfolioHolding).where(ClientPortfolioHolding.client_id == client_id))
    ).scalars().all()
    graph = assemble_graph(
        {
            "id": str(client.id),
            "name": f"{client.firstname} {client.lastname}".strip(),
            "family_office_name": client.family_office_name,
            "country": client.country,
            "shariah_compliant": bool(client.shariah_compliant),
        },
        [{"asset_name": row.asset_name, "allocation_pct": row.allocation_pct} for row in holdings],
    )
    stored = dict(graph)
    stored["source"] = "neo4j"
    if _write_neo4j(stored, str(client.id)):
        return stored
    return graph


def _local_answer(question: str, graph: dict, paths: list[str]) -> dict:
    rules = [node["name"] for node in graph["nodes"] if node["kind"] == "WealthRule"]
    trusts = [node["name"] for node in graph["nodes"] if node["kind"] == "Trust"]
    entities = [node["name"] for node in graph["nodes"] if node["kind"] == "HoldingEntity"]
    lines = [
        f"The graph has {graph['stats']['nodes']} nodes and {graph['stats']['links']} links ({graph['source']}).",
    ]
    if trusts:
        lines.append("Trusts: " + ", ".join(trusts) + ".")
    if entities:
        lines.append("Holding entities: " + ", ".join(entities) + ".")
    if rules:
        lines.append("Rules linked to this client: " + ", ".join(rules) + ".")
    if paths:
        lines.append("Paths: " + "; ".join(paths[:6]) + ".")
    if "succession" in question.lower() or "spv" in question.lower():
        lines.append("Succession sits on the next-generation beneficiary and the trust settlement. Confirm the mandate before any subscription.")
    return {
        "answered": True,
        "text": " ".join(lines),
        "citations": rules or ["wealth-graph"],
        "source": "deterministic",
        "paths": paths[:12],
    }


async def ask_graph(db: AsyncSession, client_id: UUID, question: str) -> dict | None:
    graph = await client_graph(db, client_id)
    if graph is None:
        return None
    paths = _paths(str(client_id)) if graph.get("source") == "neo4j" else [
        f"{link['source']} -[{link['relationship_type']}]-> {link['target']}" for link in graph["links"][:12]
    ]
    local = _local_answer(question, graph, paths)
    context = json.dumps({
        "question": question,
        "nodes": [{"name": node["name"], "kind": node["kind"]} for node in graph["nodes"]],
        "paths": paths[:20],
        "local_answer": local["text"],
    })
    rewritten = await complete(
        "Answer the relationship manager using only the graph context. Cite node names. "
        "If the context does not contain the fact, say so. Do not invent regulation text.",
        context,
        timeout_s=20,
    )
    if not rewritten:
        return local
    return {
        "answered": True,
        "text": rewritten.strip(),
        "citations": local["citations"],
        "source": "llm",
        "model": settings.LLM_MODEL,
        "paths": paths[:12],
    }
