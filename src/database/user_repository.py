"""
User repository for authentication
"""

import uuid
from typing import Optional
from sqlalchemy.orm import Session
from src.database import get_session, close_session
from src.database.models import User as DBUser


class UserRepository:
    """Repository for User operations"""
    
    @staticmethod
    def create(username: str, email: str, password: str) -> DBUser:
        """Create a new user"""
        session = get_session()
        try:
            user = DBUser(
                id=f"user_{uuid.uuid4().hex[:8]}",
                username=username,
                email=email
            )
            user.set_password(password)
            
            session.add(user)
            session.commit()
            session.refresh(user)
            
            return user
        finally:
            close_session()
    
    @staticmethod
    def get(user_id: str) -> Optional[DBUser]:
        """Get user by ID"""
        session = get_session()
        try:
            return session.query(DBUser).filter(DBUser.id == user_id).first()
        finally:
            close_session()
    
    @staticmethod
    def get_by_username(username: str) -> Optional[DBUser]:
        """Get user by username"""
        session = get_session()
        try:
            return session.query(DBUser).filter(DBUser.username == username).first()
        finally:
            close_session()
    
    @staticmethod
    def get_by_email(email: str) -> Optional[DBUser]:
        """Get user by email"""
        session = get_session()
        try:
            return session.query(DBUser).filter(DBUser.email == email).first()
        finally:
            close_session()
    
    @staticmethod
    def update_last_login(user_id: str) -> None:
        """Update user's last login timestamp"""
        from datetime import datetime
        session = get_session()
        try:
            user = session.query(DBUser).filter(DBUser.id == user_id).first()
            if user:
                user.last_login = datetime.utcnow()
                session.commit()
        finally:
            close_session()
