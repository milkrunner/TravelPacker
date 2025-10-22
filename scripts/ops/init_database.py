"""
Initialize or reset the database for development
"""

from src.database import init_db, engine, Base
from src.database.models import User, Trip, PackingItem, Traveler
from src.database.audit_models import AuditLog

print("Initializing database...")

# Create all tables
Base.metadata.create_all(bind=engine)

print("✅ Database initialized successfully!")
print("\nTables created:")
print("  - users")
print("  - trips")
print("  - travelers")
print("  - packing_items")
print("  - audit_logs")
