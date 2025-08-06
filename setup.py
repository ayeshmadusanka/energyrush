#!/usr/bin/env python3
"""
EnergyRush Setup Script
Prepares the environment and runs the application
"""

import subprocess
import sys
import os

def install_requirements():
    """Install required packages"""
    print("📦 Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ All packages installed successfully!")
    except subprocess.CalledProcessError:
        print("❌ Failed to install packages. Please check your Python environment.")
        return False
    return True

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python 3.8+ required. Current version: {version.major}.{version.minor}")
        return False
    print(f"✅ Python version {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def create_directories():
    """Create necessary directories"""
    dirs = ['static/css', 'static/js', 'static/charts']
    for directory in dirs:
        os.makedirs(directory, exist_ok=True)
    print("✅ Directories created successfully!")

def main():
    print("🚀 EnergyRush E-Commerce Platform Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Install requirements
    if not install_requirements():
        sys.exit(1)
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Run: python app.py")
    print("2. Open: http://localhost:5000")
    print("3. Admin panel: http://localhost:5000/admin")
    print("\n💡 Tips:")
    print("- Sample products will be created automatically")
    print("- AI chatbot available in admin panel (bottom-right)")
    print("- ML forecasting activates after 7+ orders")

if __name__ == "__main__":
    main()