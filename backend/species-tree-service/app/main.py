from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as api_router
from app.core.config import config

# Create FastAPI instance
app = FastAPI(
    title=config.SERVICE_NAME,
    version=config.VERSION,
    description="A FastAPI service for exploring taxonomic relationships and species hierarchies",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    print(f"🌟 {config.SERVICE_NAME} v{config.VERSION} is starting up...")
    print(f"🔬 Ready to explore taxonomic relationships!")

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler"""
    print(f"🛑 {config.SERVICE_NAME} is shutting down...")

# Include API routes
app.include_router(api_router, prefix=config.API_PREFIX)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": f"{config.SERVICE_NAME} is running",
        "version": config.VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
        "status": "healthy"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": config.SERVICE_NAME,
        "version": config.VERSION
    }