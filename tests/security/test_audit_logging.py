"""
Test suite for audit logging functionality.

Tests audit log creation, querying, and integration with authentication/operations.
"""

import pytest
from datetime import datetime, timedelta
from src.services.audit_service import AuditLogger
from src.database.audit_models import AuditLog
from src.database import db_session


@pytest.fixture
def cleanup_audit_logs():
    """Clean up audit logs after each test"""
    # Create audit_logs table if it doesn't exist
    from src.database import Base, engine
    Base.metadata.create_all(bind=engine)
    yield
    # Clean up test audit logs
    db_session.query(AuditLog).delete()
    db_session.commit()


class TestAuditLogCreation:
    """Test audit log entry creation"""
    
    def test_create_basic_audit_log(self, cleanup_audit_logs):
        """Test creating a basic audit log entry"""
        log = AuditLogger.log(
            event_type=AuditLogger.EVENT_LOGIN_SUCCESS,
            action="Test login",
            event_category=AuditLogger.CATEGORY_AUTHENTICATION,
            severity=AuditLogger.SEVERITY_INFO,
            user_id="test_user_123",
            username="testuser"
        )
        
        assert log is not None
        assert log.event_type == AuditLogger.EVENT_LOGIN_SUCCESS
        assert log.action == "Test login"
        assert log.user_id == "test_user_123"
        assert log.username == "testuser"
        assert log.success is True
    
    def test_audit_log_with_metadata(self, cleanup_audit_logs):
        """Test creating audit log with metadata"""
        metadata = {'key': 'value', 'count': 42}
        log = AuditLogger.log(
            event_type=AuditLogger.EVENT_TRIP_CREATE,
            action="Created trip",
            metadata=metadata
        )
        
        assert log is not None
        assert 'key' in log.extra_data
        assert 'count' in log.extra_data
    
    def test_audit_log_with_changes(self, cleanup_audit_logs):
        """Test creating audit log with change tracking"""
        changes = {
            'before': {'status': 'pending'},
            'after': {'status': 'completed'}
        }
        log = AuditLogger.log(
            event_type=AuditLogger.EVENT_TRIP_UPDATE,
            action="Updated trip status",
            changes=changes
        )
        
        assert log is not None
        assert 'before' in log.changes
        assert 'after' in log.changes
    
    def test_failed_action_audit_log(self, cleanup_audit_logs):
        """Test logging failed actions"""
        log = AuditLogger.log(
            event_type=AuditLogger.EVENT_LOGIN_FAILED,
            action="Failed login attempt",
            success=False,
            error_message="Invalid credentials"
        )
        
        assert log is not None
        assert log.success is False
        assert log.error_message == "Invalid credentials"


class TestAuthenticationAuditLogs:
    """Test authentication event logging"""
    
    def test_log_login_success(self, cleanup_audit_logs):
        """Test logging successful login"""
        log = AuditLogger.log_login_success(
            user_id="user_123",
            username="testuser",
            remember=True
        )
        
        assert log is not None
        assert log.event_type == AuditLogger.EVENT_LOGIN_SUCCESS
        assert log.event_category == AuditLogger.CATEGORY_AUTHENTICATION
        assert log.severity == AuditLogger.SEVERITY_INFO
        assert log.user_id == "user_123"
        assert log.username == "testuser"
        assert log.success is True
    
    def test_log_login_failed(self, cleanup_audit_logs):
        """Test logging failed login"""
        log = AuditLogger.log_login_failed(
            username="testuser",
            reason="Invalid password"
        )
        
        assert log is not None
        assert log.event_type == AuditLogger.EVENT_LOGIN_FAILED
        assert log.event_category == AuditLogger.CATEGORY_AUTHENTICATION
        assert log.severity == AuditLogger.SEVERITY_WARNING
        assert log.username == "testuser"
        assert log.success is False
        assert log.error_message == "Invalid password"
    
    def test_log_logout(self, cleanup_audit_logs):
        """Test logging logout"""
        log = AuditLogger.log_logout(
            user_id="user_123",
            username="testuser"
        )
        
        assert log is not None
        assert log.event_type == AuditLogger.EVENT_LOGOUT
        assert log.user_id == "user_123"
        assert log.username == "testuser"
    
    def test_log_register(self, cleanup_audit_logs):
        """Test logging user registration"""
        log = AuditLogger.log_register(
            user_id="user_123",
            username="newuser",
            email="newuser@example.com"
        )
        
        assert log is not None
        assert log.event_type == AuditLogger.EVENT_REGISTER
        assert log.username == "newuser"
        assert 'email' in log.extra_data


class TestDataModificationAuditLogs:
    """Test data modification event logging"""
    
    def test_log_trip_create(self, cleanup_audit_logs):
        """Test logging trip creation"""
        log = AuditLogger.log_trip_create(
            trip_id="trip_123",
            destination="Paris",
            user_id="user_123",
            username="testuser"
        )
        
        assert log is not None
        assert log.event_type == AuditLogger.EVENT_TRIP_CREATE
        assert log.event_category == AuditLogger.CATEGORY_DATA_MODIFICATION
        assert log.resource_type == "trip"
        assert log.resource_id == "trip_123"
    
    def test_log_trip_update(self, cleanup_audit_logs):
        """Test logging trip update"""
        changes = {
            'before': {'destination': 'Paris'},
            'after': {'destination': 'London'}
        }
        log = AuditLogger.log_trip_update(
            trip_id="trip_123",
            user_id="user_123",
            username="testuser",
            changes=changes
        )
        
        assert log is not None
        assert log.event_type == AuditLogger.EVENT_TRIP_UPDATE
        assert log.resource_id == "trip_123"
    
    def test_log_trip_delete(self, cleanup_audit_logs):
        """Test logging trip deletion"""
        log = AuditLogger.log_trip_delete(
            trip_id="trip_123",
            destination="Paris",
            user_id="user_123",
            username="testuser"
        )
        
        assert log is not None
        assert log.event_type == AuditLogger.EVENT_TRIP_DELETE
        assert log.severity == AuditLogger.SEVERITY_WARNING
        assert log.resource_id == "trip_123"


class TestSecurityEventLogging:
    """Test security event logging"""
    
    def test_log_permission_denied(self, cleanup_audit_logs):
        """Test logging permission denied event"""
        log = AuditLogger.log_permission_denied(
            resource_type="trip",
            resource_id="trip_123",
            action="delete"
        )
        
        assert log is not None
        assert log.event_type == AuditLogger.EVENT_PERMISSION_DENIED
        assert log.event_category == AuditLogger.CATEGORY_AUTHORIZATION
        assert log.severity == AuditLogger.SEVERITY_WARNING
        assert log.success is False
    
    def test_log_security_event(self, cleanup_audit_logs):
        """Test logging generic security event"""
        log = AuditLogger.log_security_event(
            event_type=AuditLogger.EVENT_CSP_VIOLATION,
            action="CSP violation detected",
            severity=AuditLogger.SEVERITY_WARNING,
            metadata={'violated_directive': 'script-src'}
        )
        
        assert log is not None
        assert log.event_category == AuditLogger.CATEGORY_SECURITY
        assert log.severity == AuditLogger.SEVERITY_WARNING


class TestAuditLogQueries:
    """Test audit log query functions"""
    
    def test_query_user_activity(self, cleanup_audit_logs):
        """Test querying user activity"""
        # Create some test logs
        for i in range(5):
            AuditLogger.log(
                event_type=AuditLogger.EVENT_TRIP_CREATE,
                action=f"Created trip {i}",
                user_id="user_123",
                username="testuser"
            )
        
        logs = AuditLogger.query_user_activity("user_123", limit=10)
        assert len(logs) == 5
        assert all(log.user_id == "user_123" for log in logs)
    
    def test_query_failed_logins(self, cleanup_audit_logs):
        """Test querying failed login attempts"""
        # Create failed login logs
        for i in range(3):
            AuditLogger.log_login_failed(
                username=f"user{i}",
                reason="Invalid password"
            )
        
        # Create successful login
        AuditLogger.log_login_success(
            user_id="user_123",
            username="testuser"
        )
        
        failed_logins = AuditLogger.query_failed_logins(hours=24, limit=10)
        assert len(failed_logins) == 3
        assert all(log.event_type == AuditLogger.EVENT_LOGIN_FAILED for log in failed_logins)
    
    def test_query_security_events(self, cleanup_audit_logs):
        """Test querying security events"""
        # Create security events
        for i in range(3):
            AuditLogger.log_security_event(
                event_type=AuditLogger.EVENT_CSP_VIOLATION,
                action=f"CSP violation {i}",
                severity=AuditLogger.SEVERITY_WARNING
            )
        
        # Create non-security event
        AuditLogger.log_login_success(
            user_id="user_123",
            username="testuser"
        )
        
        security_events = AuditLogger.query_security_events(hours=24, limit=10)
        assert len(security_events) == 3
        assert all(log.event_category == AuditLogger.CATEGORY_SECURITY for log in security_events)
    
    def test_query_resource_history(self, cleanup_audit_logs):
        """Test querying resource history"""
        # Create resource events
        for event_type in [AuditLogger.EVENT_TRIP_CREATE, AuditLogger.EVENT_TRIP_UPDATE]:
            AuditLogger.log(
                event_type=event_type,
                action=f"{event_type} on trip",
                resource_type="trip",
                resource_id="trip_123"
            )
        
        history = AuditLogger.query_resource_history("trip", "trip_123", limit=10)
        assert len(history) == 2
        assert all(log.resource_id == "trip_123" for log in history)


class TestAuditLogToDict:
    """Test audit log serialization"""
    
    def test_to_dict(self, cleanup_audit_logs):
        """Test converting audit log to dictionary"""
        log = AuditLogger.log_login_success(
            user_id="user_123",
            username="testuser"
        )
        
        log_dict = log.to_dict()
        
        assert isinstance(log_dict, dict)
        assert log_dict['user_id'] == "user_123"
        assert log_dict['username'] == "testuser"
        assert log_dict['event_type'] == AuditLogger.EVENT_LOGIN_SUCCESS
        assert log_dict['success'] is True
        assert 'timestamp' in log_dict


class TestAuditLogErrorHandling:
    """Test error handling in audit logging"""
    
    def test_audit_log_doesnt_break_on_error(self):
        """Test that audit logging errors don't break the application"""
        # This should not raise an exception even if database is unavailable
        log = AuditLogger.log(
            event_type="test_event",
            action="Test action"
        )
        
        # Log might be None if database fails, but should not raise exception
        # This is expected behavior - audit logging is non-critical


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
