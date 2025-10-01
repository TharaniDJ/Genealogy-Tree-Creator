import signal
import asyncio
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as api_router
from app.api.websocket import router as websocket_router
from app.core.shared import websocket_manager
from app.services.graph_repository import graph_repo

app = FastAPI(title='Language Tree Creator', 
              description='A service for exploring language family relationships',
              version='1.0.0')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    # Initialize MongoDB connection for graph repository
    await graph_repo.setup(
        uri="mongodb://localhost:27017/",
        db_name="Genealogy_Tree_Creator",
        collection_name="Language_Trees"
    )

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler"""
    # Cancel all active tasks and disconnect WebSocket connections
    for connection_id in list(websocket_manager.active_connections.keys()):
        websocket_manager.disconnect(connection_id)

app.include_router(api_router)
app.include_router(websocket_router)

@app.get('/')
async def root():
    """Health check endpoint"""
    return {"message": "Language Tree Service is Running", "service": "language-tree"}

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    print(f"\nReceived signal {signum}. Shutting down gracefully...")
    # Cancel all active tasks and disconnect WebSocket connections
    for connection_id in list(websocket_manager.active_connections.keys()):
        websocket_manager.disconnect(connection_id)
    sys.exit(0)

if __name__ == "__main__":
    import uvicorn
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Termination signal
    
    try:
        uvicorn.run(app, host="0.0.0.0", port=8001)
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
        # Cancel all active tasks and disconnect WebSocket connections
        for connection_id in list(websocket_manager.active_connections.keys()):
            websocket_manager.disconnect(connection_id)
