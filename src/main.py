from fastapi import FastAPI
from fastapi.responses import RedirectResponse


app = FastAPI(title="Anomaly Detector", description="Transaction anomaly detection")


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


@app.get("/health")
async def health():
    return {"health": "ok"}
