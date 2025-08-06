#!/usr/bin/env python3
"""
Simple starter for EnergyRush
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import app
    
    print("🚀 EnergyRush E-Commerce Platform")
    print("=" * 40)
    print("✅ Starting server...")
    print("🌐 Customer Site: http://127.0.0.1:8080")
    print("🛠️  Admin Panel:  http://127.0.0.1:8080/admin") 
    print("💡 Press Ctrl+C to stop")
    print("=" * 40)
    
    app.run(host='127.0.0.1', port=8080, debug=True)
    
except KeyboardInterrupt:
    print("\n🛑 Server stopped")
except Exception as e:
    print(f"❌ Error: {e}")
    print("Make sure you're in the virtual environment:")
    print("source venv/bin/activate")