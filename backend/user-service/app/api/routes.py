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
    access_token = create_access_token(data={"sub": str(user["_id"]),"full_name": user["full_name"], "email": user["email"]})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get('/me', response_model=schemas.UserOut)
async def me(current=Depends(get_current_user)):
    return current


@router.put('/me/email', response_model=schemas.UserOut)
async def update_email(
    update_data: schemas.UserUpdateEmail,
    current=Depends(get_current_user)
):
    """Update user's email address."""
    try:
        user_id = current['id']
        
        # Update email
        updated_user = await crud.update_user_email(user_id, update_data.new_email)
        
        if not updated_user:
            raise HTTPException(status_code=400, detail="Failed to update email")
            
        return {
            "id": str(updated_user["_id"]),
            "email": updated_user["email"],
            "full_name": updated_user.get("full_name")
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating email: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update email")


@router.put('/me/password')
async def update_password(
    update_data: schemas.UserUpdatePassword,
    current=Depends(get_current_user)
):
    """Update user's password."""
    try:
        user_id = current['id']
        
        # Verify current password
        user = await crud.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        is_valid = await crud.verify_password(update_data.current_password, user['password'])
        if not is_valid:
            raise HTTPException(status_code=400, detail="Current password is incorrect")
        
        # Update password
        await crud.update_user_password(user_id, update_data.new_password)
        
        return {"message": "Password updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating password: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update password")


@router.put('/me/profile', response_model=schemas.UserOut)
async def update_profile(
    update_data: schemas.UserUpdateProfile,
    current=Depends(get_current_user)
):
    """Update user's profile information."""
    try:
        user_id = current['id']
        
        # Update profile
        updated_user = await crud.update_user_profile(
            user_id,
            full_name=update_data.full_name
        )
        
        if not updated_user:
            raise HTTPException(status_code=400, detail="Failed to update profile")
            
        return {
            "id": str(updated_user["_id"]),
            "email": updated_user["email"],
            "full_name": updated_user.get("full_name")
        }
    except Exception as e:
        logger.error(f"Error updating profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update profile")


@router.delete('/me')
async def delete_account(current=Depends(get_current_user)):
    """Delete user account."""
    try:
        user_id = current['id']
        
        success = await crud.delete_user(user_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="User not found")
            
        return {"message": "Account deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting account: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete account")
