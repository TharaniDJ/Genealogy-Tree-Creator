from fastapi import APIRouter, Depends, HTTPException, status, Request
from app.api import schemas, crud
from app.core.auth import authenticate_user, create_access_token, get_current_user
import logging
import traceback

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post('/register', response_model=schemas.UserOut)
async def register(user_in: schemas.UserCreate, request: Request):
    try:
        # Log incoming request
        logger.info(f"Registration attempt for email: {user_in.email}")
        logger.info(f"Full name: {user_in.full_name}")
        logger.info(f"Password length: {len(user_in.password)}")
        
        # Check if email already exists
        existing = await crud.get_user_by_email(user_in.email)
        if existing:
            logger.warning(f"Registration failed: Email {user_in.email} already registered")
            raise HTTPException(
                status_code=400, 
                detail=f"Email '{user_in.email}' is already registered. Please use a different email or try logging in."
            )
        
        # Create user
        logger.info(f"Creating new user for email: {user_in.email}")
        user = await crud.create_user(user_in)
        logger.info(f"User created successfully with ID: {user['id']}")
        return user
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log unexpected errors with full traceback
        logger.error(f"Unexpected error during registration: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Registration failed due to server error: {str(e)}"
        )


@router.post('/login', response_model=schemas.Token)
async def login(form_data: schemas.UserLogin):
    user = await authenticate_user(form_data.email, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": str(user["_id"])})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get('/me', response_model=schemas.UserOut)
async def me(current=Depends(get_current_user)):
    return current
