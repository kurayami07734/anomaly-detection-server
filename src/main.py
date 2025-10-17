from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from src.routers.transaction import router as transaction_router
from src.routers.sse import router as sse_router
from src.routers.users import router as users_router


app = FastAPI(
    title="Anomaly Detector",
    description="Transaction anomaly detection",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET"],
)

app.include_router(transaction_router)
app.include_router(sse_router)
app.include_router(users_router)


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


@app.get("/health")
async def health():
    return {"health": "ok"}
