"""
API Router - Main router aggregating all endpoints
"""
from fastapi import APIRouter
from app.api.v1.endpoints import clients, market, briefs, workflow, dashboard, crm, priorities, products, actions, messages

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(clients.router, prefix="/clients", tags=["clients"])
api_router.include_router(market.router, prefix="/market", tags=["market"])
api_router.include_router(briefs.router, prefix="/briefs", tags=["briefs"])
api_router.include_router(workflow.router, prefix="/workflow", tags=["workflow"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(crm.router, prefix="/crm", tags=["crm"])
api_router.include_router(priorities.router, tags=["priorities"])
api_router.include_router(products.router, tags=["products"])
api_router.include_router(actions.router, tags=["actions"])
api_router.include_router(messages.router, tags=["messages"])
