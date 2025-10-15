from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from src.routers.transaction import router as transaction_router
from src.routers.sse import router as sse_router


app = FastAPI(
    title="Anomaly Detector",
    description="Transaction anomaly detection",
)

app.include_router(transaction_router)
app.include_router(sse_router)


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


@app.get("/health")
async def health():
    return {"health": "ok"}
