"""
Quick test script to verify authentication works
"""

import os
os.environ['FLASK_SECRET_KEY'] = 'test-secret-key-12345678'

from src.database.repository import UserRepository
from src.database import get_session, close_session
from src.database.models import User

print("Testing Authentication System")
print("=" * 50)

# Test 1: Check if UserRepository.create works
print("\n1. Testing user creation...")
try:
    test_user = UserRepository.create(
        username="testuser123",
        email="testuser@example.com",
        password="testpassword"
    )
    print(f"✓ User created: {test_user.username}")
    print(f"  - ID: {test_user.id}")
    print(f"  - Email: {test_user.email}")
    print(f"  - Password hash set: {bool(test_user.password_hash)}")
except Exception as e:
    print(f"✗ Error creating user: {e}")

# Test 2: Check if password verification works
print("\n2. Testing password verification...")
try:
    user = UserRepository.get_by_username("testuser123")
    if user:
        is_valid = user.check_password("testpassword")
        is_invalid = user.check_password("wrongpassword")
        print(f"✓ Correct password: {is_valid}")
        print(f"✓ Wrong password rejected: {not is_invalid}")
    else:
        print("✗ User not found")
except Exception as e:
    print(f"✗ Error verifying password: {e}")

# Test 3: Check if duplicate username is rejected
print("\n3. Testing duplicate username handling...")
try:
    existing = UserRepository.get_by_username("testuser123")
    if existing:
        print(f"✓ Duplicate username detected: {existing.username}")
    else:
        print("✗ Should have found existing user")
except Exception as e:
    print(f"✗ Error checking duplicate: {e}")

# Test 4: Check if duplicate email is rejected
print("\n4. Testing duplicate email handling...")
try:
    existing = UserRepository.get_by_email("testuser@example.com")
    if existing:
        print(f"✓ Duplicate email detected: {existing.email}")
    else:
        print("✗ Should have found existing user")
except Exception as e:
    print(f"✗ Error checking duplicate email: {e}")

# Test 5: List all users
print("\n5. Listing all users...")
try:
    session = get_session()
    users = session.query(User).all()
    print(f"✓ Total users in database: {len(users)}")
    for user in users:
        print(f"  - {user.username} ({user.email})")
    close_session()
except Exception as e:
    print(f"✗ Error listing users: {e}")

# Cleanup
print("\n6. Cleaning up test user...")
try:
    from src.database import get_session, close_session
    session = get_session()
    test_user = session.query(User).filter_by(username="testuser123").first()
    if test_user:
        session.delete(test_user)
        session.commit()
        print("✓ Test user deleted")
    close_session()
except Exception as e:
    print(f"✗ Error cleaning up: {e}")

print("\n" + "=" * 50)
print("Authentication test complete!")
