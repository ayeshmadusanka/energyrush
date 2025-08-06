#!/usr/bin/env python3
"""
EnergyRush - Production Runner
Quick start script for the EnergyRush e-commerce platform
"""

import os
import sys
import subprocess

def check_virtual_env():
    """Check if running in virtual environment"""
    return hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)

def main():
    print("🚀 Starting EnergyRush E-Commerce Platform")
    print("=" * 50)
    
    # Check if we're in virtual environment
    if not check_virtual_env():
        print("⚠️  Virtual environment not detected")
        print("Run: source venv/bin/activate (or venv\\Scripts\\activate on Windows)")
        print("Then: python run.py")
        return
    
    # Check if database exists
    db_exists = os.path.exists('energyrush.db')
    if not db_exists:
        print("📁 Creating database and sample data...")
    else:
        print("📁 Database found, starting application...")
    
    # Import and run the app
    try:
        from app import app
        print("✅ EnergyRush loaded successfully!")
        print("\n🌐 Application URLs:")
        print("   • Customer Site: http://localhost:8080")
        print("   • Admin Panel:   http://localhost:8080/admin")
        print("\n🤖 Features Available:")
        print("   • Product Management")
        print("   • Order Processing")
        print("   • ML Sales Forecasting")
        print("   • AI Chatbot Assistant")
        print("\n💡 Press Ctrl+C to stop the server")
        print("=" * 50)
        
        app.run(host='0.0.0.0', port=8080, debug=True)
        
    except ImportError as e:
        print(f"❌ Error importing app: {e}")
        print("Make sure all dependencies are installed: pip install -r requirements.txt")
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

if __name__ == "__main__":
    main()