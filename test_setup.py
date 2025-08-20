#!/usr/bin/env python3
import sys
import os

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from database import db
    print("✅ Database module imported successfully")
    
    db.init_db()
    print("✅ Database initialized successfully")
    
    # Test database connection
    session = db.get_session()
    services = session.query(db.Service).all()
    print(f"✅ Found {len(services)} services in database")
    session.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()