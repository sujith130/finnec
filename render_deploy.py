#!/usr/bin/env python3
"""
Render Deployment Helper for Finnec Application
This script helps prepare and verify your app for Render deployment
"""

import os
import sys

def check_render_requirements():
    """Check if all requirements for Render deployment are met"""
    print("=== RENDER DEPLOYMENT CHECK ===")
    print()
    
    # Check required files
    required_files = [
        'app.py',
        'requirements.txt', 
        'Procfile',
        'random_forest_model.pkl'
    ]
    
    print("Checking required files:")
    all_files_present = True
    for file in required_files:
        if os.path.exists(file):
            print(f"OK {file}")
        else:
            print(f"MISSING {file} - MISSING!")
            all_files_present = False
    
    # Check directories
    required_dirs = ['templates', 'static']
    print("\nChecking required directories:")
    for dir_name in required_dirs:
        if os.path.exists(dir_name):
            print(f"OK {dir_name}/")
        else:
            print(f"MISSING {dir_name}/ - MISSING!")
            all_files_present = False
    
    return all_files_present

def show_render_instructions():
    """Show step-by-step Render deployment instructions"""
    print("\n" + "="*60)
    print("RENDER DEPLOYMENT INSTRUCTIONS")
    print("="*60)
    print()
    print("1. PREPARE GITHUB REPOSITORY:")
    print("   - Go to GitHub.com")
    print("   - Create new repository (name: finnec-app)")
    print("   - Upload all your files")
    print()
    print("2. DEPLOY ON RENDER:")
    print("   - Go to: https://render.com")
    print("   - Sign up/Login with GitHub")
    print("   - Click 'New +' -> 'Web Service'")
    print("   - Connect your GitHub repository")
    print()
    print("3. CONFIGURE SERVICE:")
    print("   - Name: finnec-app")
    print("   - Environment: Python 3")
    print("   - Build Command: pip install -r requirements.txt")
    print("   - Start Command: gunicorn app:app")
    print()
    print("4. SET ENVIRONMENT VARIABLES:")
    print("   - Click 'Advanced' -> 'Environment Variables'")
    print("   - Add these variables:")
    print("     GEMINI_API_KEY = AIzaSyDniD-YRzG8HXVBDeDdAiiJRF1GRyKqn58")
    print("     SECRET_KEY = finnec-secret-key-2024")
    print("     FLASK_ENV = production")
    print()
    print("5. DEPLOY!")
    print("   - Click 'Create Web Service'")
    print("   - Wait 2-5 minutes")
    print("   - Your app will be live!")
    print()
    print("="*60)
    print("YOUR FINNEC APP IS READY FOR RENDER!")
    print("="*60)

def main():
    """Main function"""
    print("FINNEC APP - RENDER DEPLOYMENT HELPER")
    print()
    
    # Check requirements
    if check_render_requirements():
        print("\nALL REQUIREMENTS MET!")
        print("Your app is ready for Render deployment!")
    else:
        print("\nSOME REQUIREMENTS MISSING!")
        print("Please ensure all files are present before deploying.")
        return
    
    # Show instructions
    show_render_instructions()
    
    print("\nYOUR APP FEATURES:")
    print("- AI Loan Prediction (ML-based)")
    print("- Business Ideas (AI-generated)")
    print("- Financial Advice (Personalized)")
    print("- Interactive Chat (Conversational AI)")
    print()
    print("READY TO DEPLOY ON RENDER!")

if __name__ == "__main__":
    main()
