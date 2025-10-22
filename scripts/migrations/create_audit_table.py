"""
Database migration script to create the audit_logs table.

Run this script to add audit logging capabilities to your database.
"""

from src.database import engine
from src.database.audit_models import AuditLog

def create_audit_logs_table():
    """Create the audit_logs table in the database"""
    try:
        print("Creating audit_logs table...")
        AuditLog.__table__.create(engine, checkfirst=True)
        print("✅ audit_logs table created successfully!")
        print("\nTable structure:")
        print("- id: Primary key (auto-increment)")
        print("- timestamp: Event timestamp (indexed)")
        print("- event_type: Type of event (indexed)")
        print("- event_category: Category of event (indexed)")
        print("- severity: Event severity level (indexed)")
        print("- user_id: User who performed action (indexed)")
        print("- username: Username for quick reference (indexed)")
        print("- ip_address: Client IP address")
        print("- user_agent: Browser/client information")
        print("- request_method: HTTP method (GET, POST, etc.)")
        print("- request_path: URL path")
        print("- action: Human-readable description")
        print("- resource_type: Type of affected resource")
        print("- resource_id: ID of affected resource")
        print("- changes: JSON string of changes")
        print("- metadata: JSON string of additional context")
        print("- success: Whether action succeeded (indexed)")
        print("- error_message: Error details if failed")
        print("- session_id: Session identifier")
        print("\nIndexes created:")
        print("- idx_audit_user_timestamp (user_id, timestamp)")
        print("- idx_audit_event_timestamp (event_type, timestamp)")
        print("- idx_audit_category_timestamp (event_category, timestamp)")
        print("- idx_audit_resource (resource_type, resource_id)")
        print("- idx_audit_timestamp_desc (timestamp DESC)")
        
    except Exception as e:
        print(f"❌ Error creating audit_logs table: {e}")
        raise

if __name__ == '__main__':
    create_audit_logs_table()
