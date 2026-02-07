#!/usr/bin/env python3
"""
Finnec App Deployment Status Checker
This script helps verify your app is ready for Render deployment
"""

import os
import sys
import requests
import time

def check_local_app():
    """Check if local app can start"""
    print("=== LOCAL APP CHECK ===")
    print("Checking if app can start locally...")
    
    try:
        # Set environment variables
        os.environ["GEMINI_API_KEY"] = "AIzaSyAJdzZKh83T1CjrgyL7fJQd9ro5rbwckic"
        os.environ["SECRET_KEY"] = "finnec-secret-key-2024"
        
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
        
        # Test API key
        import google.generativeai as genai
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        print("API key configured successfully")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def check_render_url():
    """Check if Render deployment is accessible"""
    print("\n=== RENDER DEPLOYMENT CHECK ===")
    print("Checking https://finnec-app.onrender.com...")
    
    try:
        response = requests.get("https://finnec-app.onrender.com", timeout=10)
        if response.status_code == 200:
            print("App is live and accessible!")
            print(f"Status Code: {response.status_code}")
            return True
        else:
            print(f"App responded with status: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"App not accessible: {e}")
        print("This could mean:")
        print("- App is not deployed yet")
        print("- App is still building")
        print("- App has deployment issues")
        return False

def show_deployment_instructions():
    """Show deployment instructions"""
    print("\n=== RENDER DEPLOYMENT INSTRUCTIONS ===")
    print("To deploy your app to Render:")
    print()
    print("1. Go to: https://render.com")
    print("2. Sign up/Login with GitHub")
    print("3. Click 'New +' -> 'Web Service'")
    print("4. Connect repository: https://github.com/sujith130/finnec")
    print("5. Configure:")
    print("   - Name: finnec-app")
    print("   - Environment: Python 3")
    print("   - Build Command: pip install -r requirements.txt")
    print("   - Start Command: gunicorn app:app")
    print("6. Set environment variables:")
    print("   - GEMINI_API_KEY: AIzaSyAJdzZKh83T1CjrgyL7fJQd9ro5rbwckic")
    print("   - SECRET_KEY: finnec-secret-key-2024")
    print("   - FLASK_ENV: production")
    print("7. Deploy!")
    print()
    print("Your app will be available at: https://finnec-app.onrender.com")

def main():
    """Main function"""
    print("FINNEC APP - DEPLOYMENT STATUS CHECKER")
    print("=" * 60)
    
    # Check local app
    local_ok = check_local_app()
    
    # Check Render deployment
    render_ok = check_render_url()
    
    print("\n" + "=" * 60)
    print("DEPLOYMENT STATUS SUMMARY")
    print("=" * 60)
    
    if local_ok:
        print("Local app: READY")
    else:
        print("Local app: ISSUES")
    
    if render_ok:
        print("Render deployment: LIVE")
        print("Your app is accessible at: https://finnec-app.onrender.com")
    else:
        print("Render deployment: NOT ACCESSIBLE")
        print("Follow deployment instructions below")
        show_deployment_instructions()
    
    print("\nYOUR APP FEATURES:")
    print("- AI Loan Prediction (ML-based)")
    print("- Business Ideas (AI-generated)")
    print("- Financial Advice (Personalized)")
    print("- Interactive Chat (Conversational AI)")

if __name__ == "__main__":
    main()
