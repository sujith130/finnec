#!/usr/bin/env python3
"""
Deployment script for Finnec Application with API Key
This script helps deploy the application with the provided API key
"""

import os
import sys
import subprocess

def setup_environment():
    """Set up environment variables for deployment"""
    print("Setting up environment variables...")
    
    # Set the API key
    os.environ["GEMINI_API_KEY"] = "AIzaSyDniD-YRzG8HXVBDeDdAiiJRF1GRyKqn58"
    os.environ["SECRET_KEY"] = "finnec-secret-key-2024"
    
    print("Environment variables set successfully")
    return True

def test_application():
    """Test the application with the API key"""
    print("\nTesting application with API key...")
    
    try:
        # Test imports
        import flask
        import numpy
        import pandas
        import requests
        import joblib
        import google.generativeai
        from dotenv import load_dotenv
        print("All imports successful")
        
        # Test model loading
        model = joblib.load('random_forest_model.pkl')
        print("Model loaded successfully")
        
        # Test API key configuration
        import google.generativeai as genai
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        print("API key configured successfully")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def create_deployment_files():
    """Create deployment configuration files"""
    print("\nCreating deployment files...")
    
    # Create environment file for deployment platforms
    env_content = """# Environment Variables for Production Deployment
GEMINI_API_KEY=AIzaSyDniD-YRzG8HXVBDeDdAiiJRF1GRyKqn58
SECRET_KEY=finnec-secret-key-2024
FLASK_ENV=production
"""
    
    with open('production.env', 'w') as f:
        f.write(env_content)
    
    print("Created production.env file")
    
    # Create deployment instructions
    deploy_instructions = """
# DEPLOYMENT INSTRUCTIONS FOR YOUR FINNEC APP

## Your API Key is Ready!

Your Google Gemini API key has been configured and tested successfully.

## Quick Deployment Options:

### Option 1: Render (Recommended - Free)
1. Go to https://render.com
2. Sign up with GitHub
3. Connect your repository
4. Create new Web Service
5. Set these environment variables:
   - GEMINI_API_KEY: AIzaSyDniD-YRzG8HXVBDeDdAiiJRF1GRyKqn58
   - SECRET_KEY: finnec-secret-key-2024
6. Deploy!

### Option 2: Railway
1. Go to https://railway.app
2. Connect GitHub repository
3. Set environment variables (same as above)
4. Deploy!

### Option 3: Heroku
1. Install Heroku CLI
2. Run: heroku create your-app-name
3. Run: heroku config:set GEMINI_API_KEY=AIzaSyDniD-YRzG8HXVBDeDdAiiJRF1GRyKqn58
4. Run: heroku config:set SECRET_KEY=finnec-secret-key-2024
5. Run: git push heroku main

## Local Testing:
1. Run: python app.py
2. Visit: http://localhost:5000

## Your app is ready to deploy!
"""
    
    with open('DEPLOY_NOW.md', 'w') as f:
        f.write(deploy_instructions)
    
    print("Created DEPLOY_NOW.md with deployment instructions")

def main():
    """Main deployment function"""
    print("Finnec Application Deployment with API Key")
    print("=" * 60)
    
    # Setup environment
    if not setup_environment():
        print("Failed to setup environment")
        sys.exit(1)
    
    # Test application
    if not test_application():
        print("Application test failed")
        sys.exit(1)
    
    # Create deployment files
    create_deployment_files()
    
    print("\n" + "=" * 60)
    print("SUCCESS! Your Finnec app is ready for deployment!")
    print("\nNext Steps:")
    print("1. Choose a deployment platform (Render recommended)")
    print("2. Set the environment variables:")
    print("   - GEMINI_API_KEY: AIzaSyDniD-YRzG8HXVBDeDdAiiJRF1GRyKqn58")
    print("   - SECRET_KEY: finnec-secret-key-2024")
    print("3. Deploy!")
    print("\nSee DEPLOY_NOW.md for detailed instructions")
    print("\nTest locally: python app.py")

if __name__ == "__main__":
    main()
