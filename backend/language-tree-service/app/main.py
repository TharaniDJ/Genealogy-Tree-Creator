from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as api_router
from app.api.websocket import router as websocket_router
from app.core.websocket_manager import WebSocketManager

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

websocket_manager = WebSocketManager()

@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    pass

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler"""
    pass

app.include_router(api_router)
app.include_router(websocket_router)

@app.get('/')
async def root():
    """Health check endpoint"""
    return {"message": "Language Tree Service is Running", "service": "language-tree"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
