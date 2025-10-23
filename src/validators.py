"""
Input validation schemas for NikNotes
Pydantic models to validate user input and prevent injection/data corruption
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime
import re


class TripCreateRequest(BaseModel):
    """Validation schema for trip creation"""
    
    destination: str = Field(..., min_length=1, max_length=200)
    start_date: str = Field(..., min_length=10, max_length=10)
    end_date: str = Field(..., min_length=10, max_length=10)
    travel_style: str = Field(..., min_length=1, max_length=50)
    transport_method: str = Field(..., min_length=1, max_length=50)
    travelers: List[str] = Field(default_factory=list, max_length=20)
    special_notes: Optional[str] = Field(None, max_length=1000)
    
    @field_validator('destination')
    @classmethod
    def validate_destination(cls, v):
        """Validate destination name"""
        if not v or not v.strip():
            raise ValueError('Destination cannot be empty')
        # Remove excessive whitespace
        v = ' '.join(v.split())
        # Check for suspicious patterns
        if re.search(r'[<>{}]', v):
            raise ValueError('Destination contains invalid characters')
        return v.strip()
    
    @field_validator('start_date', 'end_date')
    @classmethod
    def validate_date(cls, v):
        """Validate date format (YYYY-MM-DD)"""
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError(f'Invalid date format. Expected YYYY-MM-DD, got: {v}')
    
    @field_validator('travelers')
    @classmethod
    def validate_travelers(cls, v):
        """Validate travelers list"""
        if not v:
            raise ValueError('At least one traveler is required')
        if len(v) > 20:
            raise ValueError('Maximum 20 travelers allowed')
        
        valid_types = {'Adult', 'Child', 'Infant'}
        for traveler in v:
            if traveler not in valid_types:
                raise ValueError(f'Invalid traveler type: {traveler}')
        return v
    
    @field_validator('travel_style')
    @classmethod
    def validate_travel_style(cls, v):
        """Validate travel style"""
        valid_styles = {
            'Business', 'Leisure', 'Adventure', 'Backpacking',
            'Luxury', 'Budget', 'Family', 'Solo'
        }
        if v not in valid_styles:
            raise ValueError(f'Invalid travel style: {v}')
        return v
    
    @field_validator('transport_method')
    @classmethod
    def validate_transport_method(cls, v):
        """Validate transport method"""
        valid_methods = {
            'Flight', 'Car', 'Train', 'Bus', 'Cruise', 'Other'
        }
        if v not in valid_methods:
            raise ValueError(f'Invalid transport method: {v}')
        return v
    
    @field_validator('special_notes')
    @classmethod
    def validate_special_notes(cls, v):
        """Validate special notes"""
        if v is None:
            return v
        # Remove excessive whitespace
        v = ' '.join(v.split())
        if len(v) > 1000:
            raise ValueError('Special notes too long (max 1000 characters)')
        return v.strip() if v else None


class ItemCreateRequest(BaseModel):
    """Validation schema for packing item creation"""
    
    name: str = Field(..., min_length=1, max_length=200)
    category: str = Field(default='other', min_length=1, max_length=50)
    quantity: int = Field(default=1, ge=1, le=999)
    is_essential: bool = Field(default=False)
    notes: Optional[str] = Field(None, max_length=500)
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate item name"""
        if not v or not v.strip():
            raise ValueError('Item name cannot be empty')
        # Remove excessive whitespace
        v = ' '.join(v.split())
        # Check for suspicious patterns
        if re.search(r'[<>{}]', v):
            raise ValueError('Item name contains invalid characters')
        if len(v) > 200:
            raise ValueError('Item name too long (max 200 characters)')
        return v.strip()
    
    @field_validator('category')
    @classmethod
    def validate_category(cls, v):
        """Validate category"""
        valid_categories = {
            'clothing', 'toiletries', 'electronics', 'documents',
            'medications', 'accessories', 'gear', 'other'
        }
        v_lower = v.lower()
        if v_lower not in valid_categories:
            return 'other'  # Default to 'other' if invalid
        return v_lower
    
    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, v):
        """Validate quantity"""
        if v < 1:
            raise ValueError('Quantity must be at least 1')
        if v > 999:
            raise ValueError('Quantity too large (max 999)')
        return v
    
    @field_validator('notes')
    @classmethod
    def validate_notes(cls, v):
        """Validate notes"""
        if v is None:
            return v
        # Remove excessive whitespace
        v = ' '.join(v.split())
        if len(v) > 500:
            raise ValueError('Notes too long (max 500 characters)')
        return v.strip() if v else None


class ItemToggleRequest(BaseModel):
    """Validation schema for toggling item packed status"""
    
    is_packed: bool = Field(...)


class UserRegistrationRequest(BaseModel):
    """Validation schema for user registration"""
    
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., min_length=5, max_length=120)
    password: str = Field(..., min_length=8, max_length=128)
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        """Validate username"""
        if not v or not v.strip():
            raise ValueError('Username cannot be empty')
        # Only allow alphanumeric, underscore, hyphen
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, underscore, and hyphen')
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters')
        if len(v) > 50:
            raise ValueError('Username too long (max 50 characters)')
        return v.strip()
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        """Validate email format"""
        if not v or not v.strip():
            raise ValueError('Email cannot be empty')
        # Basic email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('Invalid email format')
        if len(v) > 120:
            raise ValueError('Email too long (max 120 characters)')
        return v.strip().lower()
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if len(v) > 128:
            raise ValueError('Password too long (max 128 characters)')
        # Check for at least one letter and one number
        if not re.search(r'[a-zA-Z]', v):
            raise ValueError('Password must contain at least one letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one number')
        return v


class UserLoginRequest(BaseModel):
    """Validation schema for user login"""
    
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=128)
    remember: bool = Field(default=False)
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        """Validate username"""
        if not v or not v.strip():
            raise ValueError('Username cannot be empty')
        return v.strip()
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        """Validate password"""
        if not v:
            raise ValueError('Password cannot be empty')
        return v
