#!/usr/bin/env python3
"""
Simple script to run the Flask app with proper error handling
"""

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("Starting Finnec Flask App...")
    print("Loading environment variables...")
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv('config.env')
    
    print("Environment loaded successfully")
    print(f"API Key loaded: {'Yes' if os.getenv('GEMINI_API_KEY') else 'No'}")
    
    # Import and run the app
    print("Importing Flask app...")
    from app import app
    
    print("Flask app imported successfully")
    print("Starting server on http://localhost:5000")
    print("Press Ctrl+C to stop the server")
    
    # Run the app
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
    
except Exception as e:
    print(f"Error starting the application: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
