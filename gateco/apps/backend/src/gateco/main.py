"""
gateco Backend API

FastAPI application entry point with admin wizard and database health routes.
"""

# Load .env into os.environ BEFORE any other imports read env vars
from dotenv import load_dotenv
load_dotenv()

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from gateco.exceptions import register_exception_handlers
from gateco.middleware.observability import add_observability_middleware
from gateco.routes.admin_db import router as admin_db_router
from gateco.routes.audit import router as audit_router
from gateco.routes.auth import router as auth_router
from gateco.routes.billing import router as billing_router
from gateco.routes.connectors import router as connectors_router
from gateco.routes.dashboard import router as dashboard_router
from gateco.routes.data_catalog import router as data_catalog_router
from gateco.routes.health_db import router as health_db_router
from gateco.routes.identity_providers import router as identity_providers_router
from gateco.routes.ingestion import router as ingestion_router
from gateco.routes.pipelines import router as pipelines_router
from gateco.routes.retroactive import router as retroactive_router
from gateco.routes.policies import router as policies_router
from gateco.routes.principals import router as principals_router
from gateco.routes.retrievals import router as retrievals_router
from gateco.routes.simulator import router as simulator_router
from gateco.routes.users import router as users_router

# Configure logging — DEBUG when DEBUG=true in .env, else INFO
import os
_log_level = logging.DEBUG if os.getenv("DEBUG", "").lower() in ("true", "1") else logging.INFO
logging.basicConfig(level=_log_level, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="gateco API",
    description="Backend API for gateco",
    version="1.0.0",
)

# Register custom exception handlers
register_exception_handlers(app)

# Observability: request-id + timing
add_observability_middleware(app)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(admin_db_router)
app.include_router(health_db_router)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(billing_router)
app.include_router(connectors_router)
app.include_router(identity_providers_router)
app.include_router(policies_router)
app.include_router(data_catalog_router)
app.include_router(pipelines_router)
app.include_router(dashboard_router)
app.include_router(audit_router)
app.include_router(principals_router)
app.include_router(simulator_router)
app.include_router(retrievals_router)
app.include_router(ingestion_router)
app.include_router(retroactive_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "message": "Backend is running",
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to gateco API",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
