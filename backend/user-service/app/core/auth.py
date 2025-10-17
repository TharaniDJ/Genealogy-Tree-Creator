from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.core.config import settings
from app.api import crud

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/users/login")


async def authenticate_user(email: str, password: str):
    user = await crud.get_user_by_email(email)
    if not user:
        return None
    ok = await crud.verify_password(password, user.get("password"))
    if not ok:
        return None
    # return user document without password
    user_out = {"id": str(user.get("_id")), "email": user.get("email"), "full_name": user.get("full_name"), "_id": user.get("_id")}
    return user_out


def create_access_token(data: dict, expires_delta: int | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + timedelta(minutes=expires_delta)
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = await crud.get_user_by_id(user_id)
    if user is None:
        raise credentials_exception
    return {"id": str(user.get("_id")), "email": user.get("email"), "full_name": user.get("full_name")}
