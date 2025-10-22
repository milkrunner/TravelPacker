"""
Audit logging models for tracking security-relevant events.

This module provides database models and utilities for comprehensive audit logging
of authentication events, data modifications, and sensitive operations.
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, Index
from sqlalchemy.dialects.postgresql import JSONB
from src.database import Base


class AuditLog(Base):
    """
    Audit log model for tracking security-relevant events.
    
    Tracks authentication, authorization, data modifications, and sensitive operations
    to provide comprehensive security monitoring and compliance capabilities.
    """
    __tablename__ = 'audit_logs'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Event metadata
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)  # login, logout, create, update, delete, etc.
    event_category = Column(String(50), nullable=False, index=True)  # authentication, data_modification, security, etc.
    severity = Column(String(20), default='info', index=True)  # info, warning, error, critical
    
    # User information
    user_id = Column(String, index=True)  # User who performed the action (null for anonymous)
    username = Column(String(80), index=True)  # Username for quick reference
    
    # Request information
    ip_address = Column(String(45))  # IPv4 or IPv6
    user_agent = Column(Text)  # Browser/client information
    request_method = Column(String(10))  # GET, POST, PUT, DELETE, etc.
    request_path = Column(String(500))  # URL path
    
    # Action details
    action = Column(String(200), nullable=False)  # Human-readable description
    resource_type = Column(String(50))  # Type of resource (trip, user, packing_item, etc.)
    resource_id = Column(String)  # ID of affected resource
    
    # Data details
    changes = Column(Text)  # JSON string of changes (before/after values)
    extra_data = Column('metadata', Text)  # JSON string of additional context (renamed to avoid SQLAlchemy conflict)
    
    # Status
    success = Column(Boolean, default=True, nullable=False, index=True)
    error_message = Column(Text)  # Error details if failed
    
    # Session tracking
    session_id = Column(String)  # Session identifier for correlation
    
    # Composite indexes for common queries
    __table_args__ = (
        Index('idx_audit_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_audit_event_timestamp', 'event_type', 'timestamp'),
        Index('idx_audit_category_timestamp', 'event_category', 'timestamp'),
        Index('idx_audit_resource', 'resource_type', 'resource_id'),
        Index('idx_audit_timestamp_desc', timestamp.desc()),
    )
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, event_type='{self.event_type}', user='{self.username}', timestamp='{self.timestamp}')>"
    
    def to_dict(self):
        """Convert audit log to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'event_type': self.event_type,
            'event_category': self.event_category,
            'severity': self.severity,
            'user_id': self.user_id,
            'username': self.username,
            'ip_address': self.ip_address,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'success': self.success,
            'error_message': self.error_message,
        }
