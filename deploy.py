#!/usr/bin/env python3
"""
Deployment script for Finnec Application
This script helps deploy the application to various platforms
"""

import os
import sys
import subprocess
import json

def check_requirements():
    """Check if all requirements are met"""
    print("Checking requirements...")
    
    # Check if required files exist
    required_files = [
        'app.py',
        'requirements.txt',
        'Procfile',
        'random_forest_model.pkl'
    ]
    
    for file in required_files:
        if not os.path.exists(file):
            print(f"Missing required file: {file}")
            return False
        else:
            print(f"Found: {file}")
    
    # Check if model file is not empty
    if os.path.getsize('random_forest_model.pkl') == 0:
        print("❌ Model file is empty")
        return False
    
    print("All requirements met!")
    return True

def check_environment():
    """Check environment variables"""
    print("\nChecking environment variables...")
    
    required_vars = ['GEMINI_API_KEY', 'SECRET_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
            print(f"Missing: {var}")
        else:
            print(f"Found: {var}")
    
    if missing_vars:
        print(f"\nMissing environment variables: {', '.join(missing_vars)}")
        print("Please set these variables before deployment:")
        for var in missing_vars:
            print(f"  export {var}=your-value-here")
        return False
    
    return True

def test_imports():
    """Test if all Python imports work"""
    print("\nTesting Python imports...")
    
    try:
        import flask
        import numpy
        import pandas
        import requests
        import joblib
        import google.generativeai
        from dotenv import load_dotenv
        print("All imports successful")
        return True
    except ImportError as e:
        print(f"Import error: {e}")
        return False

def test_model_loading():
    """Test if the model can be loaded"""
    print("\nTesting model loading...")
    
    try:
        import joblib
        model = joblib.load('random_forest_model.pkl')
        print("Model loaded successfully")
        return True
    except Exception as e:
        print(f"Model loading error: {e}")
        return False

def create_deployment_package():
    """Create a deployment package"""
    print("\nCreating deployment package...")
    
    # Files to include in deployment
    files_to_include = [
        'app.py',
        'requirements.txt',
        'Procfile',
        'random_forest_model.pkl',
        'templates/',
        'static/',
        'env.example'
    ]
    
    print("Files to be deployed:")
    for file in files_to_include:
        if os.path.exists(file):
            print(f"Found: {file}")
        else:
            print(f"Missing: {file}")

def main():
    """Main deployment function"""
    print("Finnec Application Deployment Checker")
    print("=" * 50)
    
    # Check all requirements
    checks = [
        check_requirements,
        test_imports,
        test_model_loading,
        create_deployment_package
    ]
    
    all_passed = True
    for check in checks:
        if not check():
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("Application is ready for deployment!")
        print("\nNext steps:")
        print("1. Set your environment variables")
        print("2. Choose a deployment platform (Heroku, Render, Railway)")
        print("3. Deploy using the platform's instructions")
    else:
        print("Application has issues that need to be fixed before deployment")
        sys.exit(1)

if __name__ == "__main__":
    main()
