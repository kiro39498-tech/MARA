"""Main FastAPI application."""

import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.database import init_db, close_db
from app.api.v1.router import api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def _start_mcp_server() -> asyncio.Task:
    """Start the MARA MCP Planning Server as a background asyncio task.

    The MCP server runs on a separate port (default 8001) and exposes all
    planning capabilities as MCP tools. Agents communicate with it through
    MCPPlanningClient using the streamable-http transport.

    Returns:
        asyncio.Task: The background task running the MCP server.
        Cancel this task on shutdown to stop the server gracefully.
    """
    from app.mcp.server import mcp  # import here to avoid circular imports at module load

    async def _run():
        try:
            logger.info(
                "Starting MCP Planning Server on %s:%s",
                settings.MCP_SERVER_HOST,
                settings.MCP_SERVER_PORT,
            )
            mcp.settings.host = settings.MCP_SERVER_HOST
            mcp.settings.port = settings.MCP_SERVER_PORT
            mcp.settings.stateless_http = True
            await mcp.run_streamable_http_async()
        except asyncio.CancelledError:
            logger.info("MCP Planning Server stopped.")
        except Exception as exc:
            logger.error("MCP Planning Server error: %s", exc)

    task = asyncio.create_task(_run(), name="mcp-planning-server")
    return task


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.

    Handles database initialization and MCP server startup on startup,
    and cleanup on shutdown.
    """
    # Startup
    logger.info("🚀 Application startup initiated")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug Mode: {settings.DEBUG}")

    # Initialize database (for development only - use Alembic in production)
    if settings.DEBUG:
        await init_db()

    # Start MARA MCP Planning Server as a background task
    mcp_task = await _start_mcp_server()
    # Give the MCP server a moment to bind to its port before agents connect
    await asyncio.sleep(0.5)

    logger.info("✅ Application startup complete")
    logger.info(
        "📡 MCP Planning Server: http://%s:%s/mcp",
        settings.MCP_SERVER_HOST,
        settings.MCP_SERVER_PORT,
    )

    yield

    # Shutdown
    logger.info("🛑 Application shutdown initiated")
    mcp_task.cancel()
    try:
        await asyncio.wait_for(mcp_task, timeout=5.0)
    except (asyncio.CancelledError, asyncio.TimeoutError):
        pass
    await close_db()
    logger.info("✅ Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)


# CORS Middleware - Allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=False,  # Must be False when using wildcard
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# Trusted Host Middleware (production security)
if settings.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"],  # Configure with actual hosts in production
    )


# Exception Handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
):
    """Handle validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": exc.body},
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handle database errors."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Database error occurred",
            "error": str(exc) if settings.DEBUG else "Internal server error",
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "error": (
                str(exc) if settings.DEBUG else "An unexpected error occurred"
            ),
        },
    )


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint - API health check."""
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "version": settings.VERSION,
        "status": "online",
        "docs": f"{settings.API_V1_STR}/docs",
    }


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "version": settings.VERSION,
    }


# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info",
    )
