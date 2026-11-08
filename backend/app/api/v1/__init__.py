"""
API Router - Main router aggregating all endpoints
"""
from fastapi import APIRouter
from app.api.v1.endpoints import (
    clients, market, briefs, workflow, dashboard, priorities, products,
    actions, messages, admin, shariah, family,
    session, calendar, meetings, memory, artifacts, telemetry, demo_clients,
)

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(session.router, tags=["session"])
api_router.include_router(clients.router, prefix="/clients", tags=["clients"])
api_router.include_router(market.router, prefix="/market", tags=["market"])
api_router.include_router(briefs.router, prefix="/briefs", tags=["briefs"])
api_router.include_router(workflow.router, prefix="/workflow", tags=["workflow"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(priorities.router, tags=["priorities"])
api_router.include_router(priorities.convenience_router, tags=["priorities"])
api_router.include_router(products.router, tags=["products"])
api_router.include_router(actions.router, tags=["actions"])
api_router.include_router(messages.router, tags=["messages"])
api_router.include_router(calendar.router, prefix="/calendar", tags=["calendar"])
api_router.include_router(meetings.router, prefix="/meetings", tags=["meetings"])
api_router.include_router(memory.router, tags=["memory"])
api_router.include_router(artifacts.router, prefix="/artifacts", tags=["artifacts"])
api_router.include_router(telemetry.router, prefix="/telemetry", tags=["telemetry"])
api_router.include_router(admin.router, tags=["admin"])
api_router.include_router(shariah.router, tags=["shariah-pilot"])
api_router.include_router(family.router, tags=["family-pilot"])
api_router.include_router(demo_clients.router, tags=["demo-clients"])
