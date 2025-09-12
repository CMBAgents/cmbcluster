#!/usr/bin/env python3
"""
Test script to verify admin role detection works properly
"""
import sys
import os
sys.path.append('./backend')

from backend.auth import determine_user_role
from backend.models import UserRole
from backend.config import settings
import asyncio

class MockDB:
    def __init__(self, users_count=0):
        self.users_count = users_count
    
    async def list_all_users(self):
        return ['mock_user'] * self.users_count if self.users_count > 0 else []

async def test_admin_detection():
    print("🧪 Testing Admin Role Detection")
    print("=" * 50)
    
    # Test 1: First user should be admin
    print("\n1️⃣ Testing first user detection...")
    mock_db = MockDB(users_count=0)  # No existing users
    role = await determine_user_role("test@example.com", mock_db)
    print(f"   First user role: {role.value}")
    assert role == UserRole.ADMIN, f"Expected ADMIN, got {role.value}"
    print("   ✅ PASS: First user correctly assigned admin role")
    
    # Test 2: Configured admin email should be admin
    print("\n2️⃣ Testing configured admin email...")
    mock_db = MockDB(users_count=1)  # Has existing users
    admin_emails = settings.get_admin_emails()
    print(f"   Configured admin emails: {admin_emails}")
    
    if admin_emails:
        test_email = admin_emails[0]  # Use the first configured admin email
        role = await determine_user_role(test_email, mock_db)
        print(f"   Admin email '{test_email}' role: {role.value}")
        assert role == UserRole.ADMIN, f"Expected ADMIN, got {role.value}"
        print("   ✅ PASS: Admin email correctly assigned admin role")
    
    # Test 3: Regular user should get user role
    print("\n3️⃣ Testing regular user...")
    mock_db = MockDB(users_count=1)  # Has existing users
    role = await determine_user_role("regular@example.com", mock_db)
    print(f"   Regular user role: {role.value}")
    assert role == UserRole.USER, f"Expected USER, got {role.value}"
    print("   ✅ PASS: Regular user correctly assigned user role")
    
    # Test 4: Case insensitive admin email matching
    print("\n4️⃣ Testing case insensitive admin email...")
    if admin_emails:
        test_email = admin_emails[0].upper()  # Test uppercase version
        role = await determine_user_role(test_email, mock_db)
        print(f"   Uppercase admin email '{test_email}' role: {role.value}")
        assert role == UserRole.ADMIN, f"Expected ADMIN, got {role.value}"
        print("   ✅ PASS: Case insensitive matching works")
    
    print("\n🎉 All tests passed! Admin detection is working correctly.")
    print("\n📋 Summary:")
    print(f"   - First user is admin: {settings.first_user_is_admin}")
    print(f"   - Admin emails: {settings.get_admin_emails()}")
    
    return True

if __name__ == "__main__":
    try:
        asyncio.run(test_admin_detection())
        print("\n✅ Test completed successfully!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)