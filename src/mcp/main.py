from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uuid
import time
import sys
import os
from .api.v1 import messages, multi_tenant
from .core.config import settings
from .core.logging import log

# Add root directory to path to import temp.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from temp import llm_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown"""
    log.info("Starting MCP Service...")
    log.info(f"Configuration: port={settings.mcp_port}")
    yield
    log.info("Shutting down MCP Service...")

app = FastAPI(
    title="Mail Communication Platform (MCP)",
    description="Production-ready email microservice",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add correlation ID to all requests"""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    
    with log.contextualize(request_id=request_id):
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time
        
        response.headers["X-Request-ID"] = request_id
        
        log.info(
            f"{request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Duration: {duration:.3f}s"
        )
        
        return response

app.include_router(messages.router)
app.include_router(multi_tenant.router)
app.include_router(llm_router)  # Add LLM inference endpoints

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Mail Communication Platform (MCP)",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for ECS/ALB"""
    return {
        "status": "healthy",
        "service": "EmailMCP",
        "timestamp": time.time()
    }
