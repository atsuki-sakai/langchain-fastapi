from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.schemas.user import User as UserSchema
from app.models.user import UserCreate, UserUpdate, UserInDB, UserChangePassword
from app.core.security import get_password_hash, verify_password
from app.core.exceptions import NotFoundError, ConflictError, ValidationError
from app.core.logging import get_logger

logger = get_logger(__name__)


async def get_user_by_id(db: Session, user_id: int) -> Optional[UserInDB]:
    """Get user by ID."""
    try:
        if isinstance(db, AsyncSession):
            result = await db.execute(select(UserSchema).where(UserSchema.id == user_id))
            user = result.scalar_one_or_none()
        else:
            user = db.query(UserSchema).filter(UserSchema.id == user_id).first()
        
        if user:
            return UserInDB.from_orm(user)
        return None
    
    except Exception as e:
        logger.error(f"Error getting user by ID {user_id}: {str(e)}")
        raise


async def get_user_by_email(db: Session, email: str) -> Optional[UserInDB]:
    """Get user by email."""
    try:
        if isinstance(db, AsyncSession):
            result = await db.execute(select(UserSchema).where(UserSchema.email == email))
            user = result.scalar_one_or_none()
        else:
            user = db.query(UserSchema).filter(UserSchema.email == email).first()
        
        if user:
            return UserInDB.from_orm(user)
        return None
    
    except Exception as e:
        logger.error(f"Error getting user by email {email}: {str(e)}")
        raise


async def get_user_by_username(db: Session, username: str) -> Optional[UserInDB]:
    """Get user by username."""
    try:
        if isinstance(db, AsyncSession):
            result = await db.execute(select(UserSchema).where(UserSchema.username == username))
            user = result.scalar_one_or_none()
        else:
            user = db.query(UserSchema).filter(UserSchema.username == username).first()
        
        if user:
            return UserInDB.from_orm(user)
        return None
    
    except Exception as e:
        logger.error(f"Error getting user by username {username}: {str(e)}")
        raise


async def create_user(db: Session, user_create: UserCreate) -> UserInDB:
    """Create a new user."""
    try:
        # Check if user already exists
        existing_user = await get_user_by_email(db, user_create.email)
        if existing_user:
            raise ConflictError("User with this email already exists")
        
        existing_username = await get_user_by_username(db, user_create.username)
        if existing_username:
            raise ConflictError("User with this username already exists")
        
        # Create new user
        hashed_password = get_password_hash(user_create.password)
        
        user_data = {
            "email": user_create.email,
            "username": user_create.username,
            "full_name": user_create.full_name,
            "hashed_password": hashed_password,
            "is_active": user_create.is_active,
        }
        
        db_user = UserSchema(**user_data)
        
        if isinstance(db, AsyncSession):
            db.add(db_user)
            await db.commit()
            await db.refresh(db_user)
        else:
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
        
        logger.info(f"User created: {user_create.email}")
        return UserInDB.from_orm(db_user)
    
    except (ConflictError, ValidationError):
        raise
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        raise


async def update_user(db: Session, user_id: int, user_update: UserUpdate) -> UserInDB:
    """Update user information."""
    try:
        # Get existing user
        db_user = await get_user_by_id(db, user_id)
        if not db_user:
            raise NotFoundError("User not found")
        
        # Prepare update data
        update_data = {}
        if user_update.full_name is not None:
            update_data["full_name"] = user_update.full_name
        if user_update.is_active is not None:
            update_data["is_active"] = user_update.is_active
        
        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            
            if isinstance(db, AsyncSession):
                await db.execute(
                    update(UserSchema)
                    .where(UserSchema.id == user_id)
                    .values(**update_data)
                )
                await db.commit()
            else:
                db.query(UserSchema).filter(UserSchema.id == user_id).update(update_data)
                db.commit()
        
        # Return updated user
        updated_user = await get_user_by_id(db, user_id)
        logger.info(f"User updated: {user_id}")
        return updated_user
    
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {str(e)}")
        raise


async def change_password(
    db: Session, 
    user_id: int, 
    password_change: UserChangePassword
) -> UserInDB:
    """Change user password."""
    try:
        # Get existing user
        db_user = await get_user_by_id(db, user_id)
        if not db_user:
            raise NotFoundError("User not found")
        
        # Verify current password
        if not verify_password(password_change.current_password, db_user.hashed_password):
            raise ValidationError("Current password is incorrect")
        
        # Hash new password
        new_hashed_password = get_password_hash(password_change.new_password)
        
        # Update password
        update_data = {
            "hashed_password": new_hashed_password,
            "updated_at": datetime.utcnow()
        }
        
        if isinstance(db, AsyncSession):
            await db.execute(
                update(UserSchema)
                .where(UserSchema.id == user_id)
                .values(**update_data)
            )
            await db.commit()
        else:
            db.query(UserSchema).filter(UserSchema.id == user_id).update(update_data)
            db.commit()
        
        # Return updated user
        updated_user = await get_user_by_id(db, user_id)
        logger.info(f"Password changed for user: {user_id}")
        return updated_user
    
    except (NotFoundError, ValidationError):
        raise
    except Exception as e:
        logger.error(f"Error changing password for user {user_id}: {str(e)}")
        raise


async def authenticate_user(db: Session, email: str, password: str) -> Optional[UserInDB]:
    """Authenticate user with email and password."""
    try:
        user = await get_user_by_email(db, email)
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        if not user.is_active:
            return None
        
        # Update last login
        update_data = {"last_login": datetime.utcnow()}
        
        if isinstance(db, AsyncSession):
            await db.execute(
                update(UserSchema)
                .where(UserSchema.id == user.id)
                .values(**update_data)
            )
            await db.commit()
        else:
            db.query(UserSchema).filter(UserSchema.id == user.id).update(update_data)
            db.commit()
        
        logger.info(f"User authenticated: {email}")
        return user
    
    except Exception as e:
        logger.error(f"Error authenticating user {email}: {str(e)}")
        return None


async def get_users(
    db: Session,
    skip: int = 0,
    limit: int = 100
) -> List[UserInDB]:
    """Get list of users with pagination."""
    try:
        if isinstance(db, AsyncSession):
            result = await db.execute(
                select(UserSchema)
                .offset(skip)
                .limit(limit)
            )
            users = result.scalars().all()
        else:
            users = db.query(UserSchema).offset(skip).limit(limit).all()
        
        return [UserInDB.from_orm(user) for user in users]
    
    except Exception as e:
        logger.error(f"Error getting users: {str(e)}")
        raise