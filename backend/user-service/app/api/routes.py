from fastapi import APIRouter, Depends, HTTPException, status
from app.api import schemas, crud
from app.core.auth import authenticate_user, create_access_token, get_current_user

router = APIRouter()


@router.post('/register', response_model=schemas.UserOut)
async def register(user_in: schemas.UserCreate):
    existing = await crud.get_user_by_email(user_in.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = await crud.create_user(user_in)
    return user


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
