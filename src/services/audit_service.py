"""
Audit logging service for tracking security-relevant events.

Provides a centralized service for logging authentication events, data modifications,
and sensitive operations with comprehensive context and metadata.
"""

import json
from datetime import datetime
from typing import Optional, Dict, Any
from flask import request, has_request_context
from flask_login import current_user
from src.database import db_session
from src.database.audit_models import AuditLog


class AuditLogger:
    """
    Service for audit logging of security-relevant events.
    
    Provides methods for logging authentication, authorization, and data modification
    events with automatic context capture (IP, user agent, user info, etc.).
    """
    
    # Event types
    EVENT_LOGIN_SUCCESS = 'login_success'
    EVENT_LOGIN_FAILED = 'login_failed'
    EVENT_LOGOUT = 'logout'
    EVENT_REGISTER = 'register'
    EVENT_PASSWORD_CHANGE = 'password_change'
    EVENT_PASSWORD_RESET = 'password_reset'
    
    EVENT_TRIP_CREATE = 'trip_create'
    EVENT_TRIP_UPDATE = 'trip_update'
    EVENT_TRIP_DELETE = 'trip_delete'
    EVENT_TRIP_VIEW = 'trip_view'
    
    EVENT_ITEM_CREATE = 'item_create'
    EVENT_ITEM_UPDATE = 'item_update'
    EVENT_ITEM_DELETE = 'item_delete'
    EVENT_ITEM_TOGGLE = 'item_toggle'
    
    EVENT_PDF_EXPORT = 'pdf_export'
    EVENT_DATA_EXPORT = 'data_export'
    EVENT_DATA_IMPORT = 'data_import'
    
    EVENT_PERMISSION_DENIED = 'permission_denied'
    EVENT_RATE_LIMIT_EXCEEDED = 'rate_limit_exceeded'
    EVENT_CSRF_VIOLATION = 'csrf_violation'
    EVENT_CSP_VIOLATION = 'csp_violation'
    
    EVENT_SECURITY_SCAN = 'security_scan'
    EVENT_SUSPICIOUS_ACTIVITY = 'suspicious_activity'
    
    # Event categories
    CATEGORY_AUTHENTICATION = 'authentication'
    CATEGORY_AUTHORIZATION = 'authorization'
    CATEGORY_DATA_MODIFICATION = 'data_modification'
    CATEGORY_DATA_ACCESS = 'data_access'
    CATEGORY_SECURITY = 'security'
    CATEGORY_EXPORT = 'export'
    CATEGORY_SYSTEM = 'system'
    
    # Severity levels
    SEVERITY_INFO = 'info'
    SEVERITY_WARNING = 'warning'
    SEVERITY_ERROR = 'error'
    SEVERITY_CRITICAL = 'critical'
    
    @staticmethod
    def _get_request_context() -> Dict[str, Any]:
        """
        Extract request context information.
        
        Returns:
            Dictionary with IP address, user agent, request method, and path
        """
        if not has_request_context():
            return {
                'ip_address': None,
                'user_agent': None,
                'request_method': None,
                'request_path': None,
            }
        
        return {
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent'),
            'request_method': request.method,
            'request_path': request.path,
        }
    
    @staticmethod
    def _get_user_context() -> Dict[str, Any]:
        """
        Extract user context information.
        
        Returns:
            Dictionary with user_id and username
        """
        if current_user and current_user.is_authenticated:
            return {
                'user_id': current_user.id,
                'username': current_user.username,
            }
        return {
            'user_id': None,
            'username': None,
        }
    
    @classmethod
    def log(
        cls,
        event_type: str,
        action: str,
        event_category: str = CATEGORY_SYSTEM,
        severity: str = SEVERITY_INFO,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Optional[AuditLog]:
        """
        Create an audit log entry.
        
        Args:
            event_type: Type of event (use EVENT_* constants)
            action: Human-readable description of the action
            event_category: Category of event (use CATEGORY_* constants)
            severity: Severity level (use SEVERITY_* constants)
            user_id: ID of user who performed the action
            username: Username of user who performed the action
            resource_type: Type of resource affected (trip, user, item, etc.)
            resource_id: ID of affected resource
            changes: Dictionary of changes (before/after values)
            metadata: Additional context information
            success: Whether the action succeeded
            error_message: Error message if failed
            session_id: Session identifier for correlation
        
        Returns:
            Created AuditLog entry or None if failed
        """
        try:
            # Get request context
            request_context = cls._get_request_context()
            
            # Get user context if not provided
            if user_id is None or username is None:
                user_context = cls._get_user_context()
                user_id = user_id or user_context['user_id']
                username = username or user_context['username']
            
            # Create audit log entry
            audit_log = AuditLog(
                timestamp=datetime.utcnow(),
                event_type=event_type,
                event_category=event_category,
                severity=severity,
                user_id=user_id,
                username=username,
                ip_address=request_context['ip_address'],
                user_agent=request_context['user_agent'],
                request_method=request_context['request_method'],
                request_path=request_context['request_path'],
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                changes=json.dumps(changes) if changes else None,
                extra_data=json.dumps(metadata) if metadata else None,
                success=success,
                error_message=error_message,
                session_id=session_id,
            )
            
            db_session.add(audit_log)
            db_session.commit()
            
            return audit_log
            
        except Exception as e:
            # Don't let audit logging failures break the application
            print(f"Error creating audit log: {e}")
            db_session.rollback()
            return None
    
    @classmethod
    def log_login_success(cls, user_id: str, username: str, remember: bool = False) -> Optional[AuditLog]:
        """Log successful login"""
        return cls.log(
            event_type=cls.EVENT_LOGIN_SUCCESS,
            action=f"User '{username}' logged in successfully",
            event_category=cls.CATEGORY_AUTHENTICATION,
            severity=cls.SEVERITY_INFO,
            user_id=user_id,
            username=username,
            resource_type='user',
            resource_id=user_id,
            metadata={'remember': remember},
            success=True,
        )
    
    @classmethod
    def log_login_failed(cls, username: str, reason: str = 'Invalid credentials') -> Optional[AuditLog]:
        """Log failed login attempt"""
        return cls.log(
            event_type=cls.EVENT_LOGIN_FAILED,
            action=f"Failed login attempt for username '{username}'",
            event_category=cls.CATEGORY_AUTHENTICATION,
            severity=cls.SEVERITY_WARNING,
            username=username,
            resource_type='user',
            metadata={'reason': reason},
            success=False,
            error_message=reason,
        )
    
    @classmethod
    def log_logout(cls, user_id: str, username: str) -> Optional[AuditLog]:
        """Log user logout"""
        return cls.log(
            event_type=cls.EVENT_LOGOUT,
            action=f"User '{username}' logged out",
            event_category=cls.CATEGORY_AUTHENTICATION,
            severity=cls.SEVERITY_INFO,
            user_id=user_id,
            username=username,
            resource_type='user',
            resource_id=user_id,
            success=True,
        )
    
    @classmethod
    def log_register(cls, user_id: str, username: str, email: str) -> Optional[AuditLog]:
        """Log user registration"""
        return cls.log(
            event_type=cls.EVENT_REGISTER,
            action=f"New user '{username}' registered",
            event_category=cls.CATEGORY_AUTHENTICATION,
            severity=cls.SEVERITY_INFO,
            user_id=user_id,
            username=username,
            resource_type='user',
            resource_id=user_id,
            metadata={'email': email},
            success=True,
        )
    
    @classmethod
    def log_trip_create(cls, trip_id: str, destination: str, user_id: str, username: str) -> Optional[AuditLog]:
        """Log trip creation"""
        return cls.log(
            event_type=cls.EVENT_TRIP_CREATE,
            action=f"Created trip to '{destination}'",
            event_category=cls.CATEGORY_DATA_MODIFICATION,
            severity=cls.SEVERITY_INFO,
            user_id=user_id,
            username=username,
            resource_type='trip',
            resource_id=trip_id,
            metadata={'destination': destination},
            success=True,
        )
    
    @classmethod
    def log_trip_update(
        cls,
        trip_id: str,
        user_id: str,
        username: str,
        changes: Optional[Dict[str, Any]] = None
    ) -> Optional[AuditLog]:
        """Log trip update"""
        return cls.log(
            event_type=cls.EVENT_TRIP_UPDATE,
            action=f"Updated trip {trip_id}",
            event_category=cls.CATEGORY_DATA_MODIFICATION,
            severity=cls.SEVERITY_INFO,
            user_id=user_id,
            username=username,
            resource_type='trip',
            resource_id=trip_id,
            changes=changes,
            success=True,
        )
    
    @classmethod
    def log_trip_delete(cls, trip_id: str, destination: str, user_id: str, username: str) -> Optional[AuditLog]:
        """Log trip deletion"""
        return cls.log(
            event_type=cls.EVENT_TRIP_DELETE,
            action=f"Deleted trip to '{destination}'",
            event_category=cls.CATEGORY_DATA_MODIFICATION,
            severity=cls.SEVERITY_WARNING,
            user_id=user_id,
            username=username,
            resource_type='trip',
            resource_id=trip_id,
            metadata={'destination': destination},
            success=True,
        )
    
    @classmethod
    def log_pdf_export(cls, trip_id: str, destination: str, user_id: str, username: str) -> Optional[AuditLog]:
        """Log PDF export"""
        return cls.log(
            event_type=cls.EVENT_PDF_EXPORT,
            action=f"Exported trip '{destination}' to PDF",
            event_category=cls.CATEGORY_EXPORT,
            severity=cls.SEVERITY_INFO,
            user_id=user_id,
            username=username,
            resource_type='trip',
            resource_id=trip_id,
            metadata={'destination': destination, 'export_format': 'pdf'},
            success=True,
        )
    
    @classmethod
    def log_permission_denied(cls, resource_type: str, resource_id: str, action: str) -> Optional[AuditLog]:
        """Log permission denied event"""
        user_context = cls._get_user_context()
        return cls.log(
            event_type=cls.EVENT_PERMISSION_DENIED,
            action=f"Permission denied: {action} on {resource_type} {resource_id}",
            event_category=cls.CATEGORY_AUTHORIZATION,
            severity=cls.SEVERITY_WARNING,
            user_id=user_context['user_id'],
            username=user_context['username'],
            resource_type=resource_type,
            resource_id=resource_id,
            metadata={'attempted_action': action},
            success=False,
            error_message='Permission denied',
        )
    
    @classmethod
    def log_security_event(
        cls,
        event_type: str,
        action: str,
        severity: str = SEVERITY_WARNING,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[AuditLog]:
        """Log security event (CSP violation, rate limit, etc.)"""
        return cls.log(
            event_type=event_type,
            action=action,
            event_category=cls.CATEGORY_SECURITY,
            severity=severity,
            metadata=metadata,
            success=False,
        )
    
    @classmethod
    def query_user_activity(cls, user_id: str, limit: int = 100):
        """Query audit logs for a specific user"""
        return db_session.query(AuditLog).filter(
            AuditLog.user_id == user_id
        ).order_by(AuditLog.timestamp.desc()).limit(limit).all()
    
    @classmethod
    def query_failed_logins(cls, hours: int = 24, limit: int = 100):
        """Query recent failed login attempts"""
        from datetime import timedelta
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        return db_session.query(AuditLog).filter(
            AuditLog.event_type == cls.EVENT_LOGIN_FAILED,
            AuditLog.timestamp >= cutoff_time
        ).order_by(AuditLog.timestamp.desc()).limit(limit).all()
    
    @classmethod
    def query_security_events(cls, hours: int = 24, limit: int = 100):
        """Query recent security events"""
        from datetime import timedelta
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        return db_session.query(AuditLog).filter(
            AuditLog.event_category == cls.CATEGORY_SECURITY,
            AuditLog.timestamp >= cutoff_time
        ).order_by(AuditLog.timestamp.desc()).limit(limit).all()
    
    @classmethod
    def query_resource_history(cls, resource_type: str, resource_id: str, limit: int = 100):
        """Query audit history for a specific resource"""
        return db_session.query(AuditLog).filter(
            AuditLog.resource_type == resource_type,
            AuditLog.resource_id == resource_id
        ).order_by(AuditLog.timestamp.desc()).limit(limit).all()
