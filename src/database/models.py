"""
SQLAlchemy database models with performance optimizations
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text, Enum as SQLEnum, Index
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from src.database import Base
from src.models.trip import TravelStyle, TransportMethod
from src.models.packing_item import ItemCategory


class User(Base, UserMixin):
    """User model for authentication"""
    __tablename__ = 'users'
    
    id = Column(String, primary_key=True)
    username = Column(String(80), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)  # Nullable for OAuth users
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    
    # OAuth fields
    oauth_provider = Column(String(50), nullable=True)  # 'google', 'github', etc.
    oauth_id = Column(String(255), nullable=True, index=True)  # Provider's user ID
    profile_picture = Column(String(500), nullable=True)  # Profile image URL
    
    # Relationships
    trips = relationship('Trip', back_populates='user', cascade='all, delete-orphan', lazy='dynamic')
    
    # Composite index for OAuth lookups
    __table_args__ = (
        Index('idx_user_oauth', 'oauth_provider', 'oauth_id'),
    )
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password against hash"""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f"<User(id='{self.id}', username='{self.username}')>"


class Trip(Base):
    """Trip database model with optimized indexes"""
    __tablename__ = 'trips'
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    destination = Column(String, nullable=False, index=True)  # Indexed for search
    start_date = Column(String, nullable=False, index=True)  # Indexed for date queries
    end_date = Column(String, nullable=False)
    duration = Column(Integer, default=1)
    travel_style = Column(SQLEnum(TravelStyle), default=TravelStyle.LEISURE, index=True)
    transportation = Column(SQLEnum(TransportMethod), default=TransportMethod.FLIGHT)
    activities = Column(Text)  # JSON string
    special_notes = Column(Text)
    weather_conditions = Column(String)
    is_template = Column(Boolean, default=False, index=True)  # Mark as template
    template_name = Column(String)  # Name for the template
    created_at = Column(DateTime, default=datetime.utcnow, index=True)  # Indexed for sorting
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='trips')
    travelers = relationship('Traveler', back_populates='trip', cascade='all, delete-orphan', lazy='selectin')
    packing_items = relationship('PackingItem', back_populates='trip', cascade='all, delete-orphan', lazy='selectin')
    
    # Composite indexes for common queries
    __table_args__ = (
        Index('idx_trip_destination_date', 'destination', 'start_date'),
        Index('idx_trip_created_desc', created_at.desc()),
    )
    
    def __repr__(self):
        return f"<Trip(id='{self.id}', destination='{self.destination}')>"


class Traveler(Base):
    """Traveler database model"""
    __tablename__ = 'travelers'
    
    id = Column(String, primary_key=True)
    trip_id = Column(String, ForeignKey('trips.id', ondelete='CASCADE'), nullable=False, index=True)
    name = Column(String, nullable=False)
    traveler_type = Column(String, nullable=False)  # adult, child, infant, pet
    age = Column(Integer)
    special_needs = Column(Text)  # JSON string
    preferences = Column(Text)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    trip = relationship('Trip', back_populates='travelers')
    
    def __repr__(self):
        return f"<Traveler(id='{self.id}', name='{self.name}')>"


class PackingItem(Base):
    """Packing item database model with optimized indexes"""
    __tablename__ = 'packing_items'
    
    id = Column(String, primary_key=True)
    trip_id = Column(String, ForeignKey('trips.id', ondelete='CASCADE'), nullable=False, index=True)
    name = Column(String, nullable=False)
    category = Column(SQLEnum(ItemCategory), default=ItemCategory.OTHER, index=True)
    quantity = Column(Integer, default=1)
    is_packed = Column(Boolean, default=False, index=True)  # Indexed for progress queries
    is_essential = Column(Boolean, default=False, index=True)
    notes = Column(Text)
    ai_suggested = Column(Boolean, default=False)
    display_order = Column(Integer, default=0)  # For drag-and-drop ordering
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    trip = relationship('Trip', back_populates='packing_items')
    
    # Composite indexes for common queries
    __table_args__ = (
        Index('idx_item_trip_category', 'trip_id', 'category'),
        Index('idx_item_trip_packed', 'trip_id', 'is_packed'),
    )
    
    def __repr__(self):
        return f"<PackingItem(id='{self.id}', name='{self.name}')>"
