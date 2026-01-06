"""
Main FastAPI application entry point for Coliseum.

This is the core application file that:
- Initializes FastAPI with lifespan management
- Configures CORS for frontend integration
- Sets up Logfire observability
- Provides health check endpoints

Note: API routers will be added as business logic is implemented.
"""

from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logfire

from config import settings
from database import init_db, close_db, check_db_connection, get_db_info
from observability.logfire_config import LogfireConfig


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Initialize Logfire first so we can use structured logging
    LogfireConfig.initialize(token=settings.logfire_token)

    # Startup logging
    logfire.info(
        "Starting Coliseum API Server",
        environment=settings.environment,
        debug=settings.debug,
    )

    # Initialize MongoDB connection
    await init_db()
    
    # Check database connection on startup
    db_connected = await check_db_connection()
    db_info = get_db_info()
    if db_connected:
        logfire.info(
            "MongoDB connection successful",
            url=db_info['url'],
            database=db_info['database'],
        )
    else:
        logfire.error(
            "MongoDB connection failed",
            url=db_info['url'],
            database=db_info['database'],
        )

    logfire.info("Coliseum API Server startup complete")

    yield

    # Shutdown
    logfire.info("Shutting down Coliseum API Server")
    await close_db()


# Initialize FastAPI app
app = FastAPI(
    title="Coliseum API",
    description="Backend API for Coliseum - AI Prediction Market Arena",
    version="0.1.0",
    lifespan=lifespan,
    debug=settings.debug,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Health Check Endpoints
# ============================================================================

@app.get("/health", tags=["Health"])
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint for load balancers and monitoring.

    Returns:
        dict: Health status of the application and database
    """
    db_connected = await check_db_connection()

    return {
        "status": "healthy" if db_connected else "degraded",
        "service": "coliseum-api",
        "version": "0.1.0",
        "database": "connected" if db_connected else "disconnected",
        "environment": settings.environment,
    }


@app.get("/", tags=["Root"])
async def root() -> Dict[str, str]:
    """
    Root endpoint - API information.

    Returns:
        dict: Basic API information
    """
    return {
        "name": "Coliseum API",
        "version": "0.1.0",
        "description": "Backend API for AI Prediction Market Arena",
        "docs": "/docs",
        "health": "/health",
    }


# ============================================================================
# API Routers
# ============================================================================

# API routers will be included here as business logic is implemented
# Example:
# from api.routes import events_router
# app.include_router(events_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.is_development,
        log_level=settings.log_level.lower(),
    )
