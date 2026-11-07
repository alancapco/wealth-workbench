from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.api.health import router as health_router
from app.api.v1 import api_router
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Relationship Manager Workbench API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Health endpoints are registered without prefix
app.include_router(health_router, prefix="")
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root() -> dict:
    return {"message": settings.PROJECT_NAME, "version": "1.0.0", "status": "active"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
