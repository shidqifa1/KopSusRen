"""M0 entry point; business features belong to later milestones."""

from fastapi import FastAPI

app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
