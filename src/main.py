from fastapi import FastAPI

from endpoints import router

app = FastAPI(
    openapi_url="/api/openapi.json",
    docs_url="/api/docs")

app.include_router(router)
