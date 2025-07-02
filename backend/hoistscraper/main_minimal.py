"""Minimal FastAPI app for testing deployment."""
from fastapi import FastAPI
import os

app = FastAPI(title="HoistScout API - Minimal", version="0.1.0")

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Minimal API running"}

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "environment": {
            "has_database_url": bool(os.getenv("DATABASE_URL")),
            "has_redis_url": bool(os.getenv("REDIS_URL")),
            "has_passphrase": bool(os.getenv("CREDENTIAL_PASSPHRASE"))
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)