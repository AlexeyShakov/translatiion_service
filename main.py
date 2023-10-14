from fastapi import FastAPI

from src.config import SERVICE_NAME
from src.endpoints import router

app = FastAPI(
    openapi_url=f"/api/{SERVICE_NAME}/openapi.json",
    docs_url=f"/api/{SERVICE_NAME}/docs"
)

app.include_router(router)
