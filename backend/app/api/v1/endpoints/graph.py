"""Wealth knowledge graph API."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.graph.neo4j_service import ask_graph, client_graph

router = APIRouter(prefix="/graph", tags=["graph"])


class AskBody(BaseModel):
    question: str


def _ok(data):
    return {"data": data, "meta": {"source": data.get("source") if isinstance(data, dict) else "graph"}}


@router.get("/clients/{client_id}")
async def get_client_graph(client_id: UUID, db: AsyncSession = Depends(get_db)):
    graph = await client_graph(db, client_id)
    if graph is None:
        raise HTTPException(404, "Client is not in the demo book")
    return _ok(graph)


@router.post("/clients/{client_id}/ask")
async def post_ask(client_id: UUID, body: AskBody, db: AsyncSession = Depends(get_db)):
    answer = await ask_graph(db, client_id, body.question)
    if answer is None:
        raise HTTPException(404, "Client is not in the demo book")
    return {"data": answer, "meta": {"source": answer.get("source")}}
