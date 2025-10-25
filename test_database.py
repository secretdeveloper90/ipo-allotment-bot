#!/usr/bin/env python3
"""
Test script for database.py functions
Run this to verify database operations work correctly
"""

import os
import sys
from database import init_db, add_pan, get_all_pans, delete_pan_by_id, get_pan_count

def test_database():
    print("🧪 Testing Database Functions\n")
    print("=" * 50)
    
    # Test user ID
    test_user_id = 12345
    
    # Clean up any existing test data
    if os.path.exists("users.db"):
        os.remove("users.db")
        print("✅ Cleaned up old database")
    
    # Test 1: Initialize database
    print("\n1️⃣ Testing init_db()...")
    try:
        init_db()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False
    
    # Test 2: Add PAN
    print("\n2️⃣ Testing add_pan()...")
    try:
        add_pan(test_user_id, "John Doe", "ABCDE1234F")
        print("✅ Added PAN: ABCDE1234F (John Doe)")
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False
    
    # Test 3: Get all PANs
    print("\n3️⃣ Testing get_all_pans()...")
    try:
        pans = get_all_pans(test_user_id)
        print(f"✅ Retrieved {len(pans)} PAN(s)")
        for pan in pans:
            print(f"   - {pan['name']}: {pan['pan']}")
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False
    
    # Test 4: Get PAN count
    print("\n4️⃣ Testing get_pan_count()...")
    try:
        count = get_pan_count(test_user_id)
        print(f"✅ PAN count: {count}")
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False
    
    # Test 5: Add more PANs
    print("\n5️⃣ Testing multiple PANs...")
    try:
        add_pan(test_user_id, "Jane Smith", "BVJPC7028R")
        add_pan(test_user_id, "No Name", "XYZAB5678C")
        pans = get_all_pans(test_user_id)
        print(f"✅ Added 2 more PANs. Total: {len(pans)}")
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False
    
    # Test 6: Duplicate PAN detection
    print("\n6️⃣ Testing duplicate PAN detection...")
    try:
        add_pan(test_user_id, "Duplicate", "ABCDE1234F")
        print("❌ Failed: Duplicate PAN was allowed!")
        return False
    except Exception as e:
        if "already added" in str(e):
            print(f"✅ Duplicate PAN correctly rejected: {e}")
        else:
            print(f"❌ Unexpected error: {e}")
            return False
    
    # Test 7: 20 PAN limit
    print("\n7️⃣ Testing 20 PAN limit...")
    try:
        # Add 17 more PANs (we already have 3)
        for i in range(17):
            pan = f"TEST{i:05d}X"
            add_pan(test_user_id, f"Test User {i}", pan)
        
        count = get_pan_count(test_user_id)
        print(f"✅ Added PANs. Total count: {count}")
        
        # Try to add 21st PAN
        try:
            add_pan(test_user_id, "21st User", "LIMIT1234Z")
            print("❌ Failed: 21st PAN was allowed!")
            return False
        except Exception as e:
            if "Maximum 20" in str(e):
                print(f"✅ 20 PAN limit correctly enforced: {e}")
            else:
                print(f"❌ Unexpected error: {e}")
                return False
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False
    
    # Test 8: Delete PAN
    print("\n8️⃣ Testing delete_pan_by_id()...")
    try:
        pans = get_all_pans(test_user_id)
        first_pan_id = pans[0]['id']
        first_pan_number = pans[0]['pan']
        
        delete_pan_by_id(first_pan_id)
        
        new_count = get_pan_count(test_user_id)
        print(f"✅ Deleted PAN {first_pan_number}. New count: {new_count}")
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False
    
    # Test 9: Verify deletion
    print("\n9️⃣ Testing verification after deletion...")
    try:
        pans = get_all_pans(test_user_id)
        deleted_pan_exists = any(p['pan'] == first_pan_number for p in pans)
        
        if deleted_pan_exists:
            print("❌ Failed: Deleted PAN still exists!")
            return False
        else:
            print(f"✅ Deletion verified. Current PANs: {len(pans)}")
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 All database tests passed!")
    print("=" * 50)
    return True

if __name__ == "__main__":
    success = test_database()
    sys.exit(0 if success else 1)

