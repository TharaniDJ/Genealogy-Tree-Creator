from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as api_router

app = FastAPI(title='User Service')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    # Initialize DB connections here if needed
    pass


@app.on_event("shutdown")
async def shutdown_event():
    pass

app.include_router(api_router, prefix="/api/users")


@app.get('/')
async def root():
    return {"message": "User service is running"}
