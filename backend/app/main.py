"""Main FastAPI application for the Economic Research Platform."""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.routers import data, forecasting, chat, datasets

load_dotenv()

app = FastAPI(
    title="EconSight - Economic Research Platform",
    description="Interactive economic research and forecasting platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(data.router, prefix="/api/data", tags=["Data"])
app.include_router(forecasting.router, prefix="/api/forecast", tags=["Forecasting"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(datasets.router, prefix="/api/datasets", tags=["Datasets"])


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0"}
