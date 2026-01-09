# -*- coding: utf-8 -*-
"""Reset database - clear all data and reset ID sequence"""
import sys
sys.path.insert(0, '/app')

from database.connection import db_manager

print("🗑️  Resetting database...")

# Delete all data
db_manager.execute_query("DELETE FROM webhook_logs", fetch=False)
print("   ✅ Cleared webhook_logs")

db_manager.execute_query("DELETE FROM processing_history", fetch=False)
print("   ✅ Cleared processing_history")

db_manager.execute_query("DELETE FROM collision_documents", fetch=False)
print("   ✅ Cleared collision_documents")

# Reset ID sequence
db_manager.execute_query("ALTER SEQUENCE collision_documents_id_seq RESTART WITH 1", fetch=False)
print("   ✅ Reset ID sequence to 1")

# Verify
result = db_manager.execute_query("SELECT COUNT(*) as count FROM collision_documents")
print(f"\n✅ Database reset complete! Records: {result[0]['count']}")
