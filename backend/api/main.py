"""Main FastAPI application entry point for TrafficIQ."""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from backend.core.logger import logger
from backend.api.routes import upload, processing, analytics, history, results

app = FastAPI(
    title="TrafficIQ API",
    description="REST API for TrafficIQ - AI-Powered Intelligent Traffic Management System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers for logging unhandled API exceptions
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception during request {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"Internal server error: {exc}"}
    )

# Include route routers
app.include_router(upload.router)
app.include_router(processing.router)
app.include_router(analytics.router)
app.include_router(history.router)
app.include_router(results.router)

@app.get("/", tags=["Root"])
async def root():
    """Root API endpoint indicating service health."""
    return {
        "app": "TrafficIQ API",
        "status": "healthy",
        "version": "1.0.0"
    }
