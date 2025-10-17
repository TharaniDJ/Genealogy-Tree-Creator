from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.api.routes import router as api_router
from app.api.graph_routes import router as graph_router
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title='User Service')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Custom validation  error handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    logger.error(f"Validation error on {request.url}: {errors}")
    
    # Format error messages for better readability
    error_messages = []
    for error in errors:
        field = " -> ".join(str(loc) for loc in error["loc"])
        msg = error["msg"]
        error_messages.append(f"{field}: {msg}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": error_messages,
            "raw_errors": errors
        }
    )


@app.on_event("startup")
async def startup_event():
    # Initialize DB connections here if needed
    pass


@app.on_event("shutdown")
async def shutdown_event():
    pass

app.include_router(api_router, prefix="/api/users")
app.include_router(graph_router, prefix="/api/users", tags=["graphs"])


@app.get('/')
async def root():
    return {"message": "User service is running"}
