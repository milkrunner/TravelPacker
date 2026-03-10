"""
Initialize or reset the database for development
"""

from src.database import Base, engine

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
