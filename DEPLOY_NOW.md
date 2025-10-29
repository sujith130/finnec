
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
   - GEMINI_API_KEY: AIzaSyAJdzZKh83T1CjrgyL7fJQd9ro5rbwckic
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
3. Run: heroku config:set GEMINI_API_KEY=AIzaSyAJdzZKh83T1CjrgyL7fJQd9ro5rbwckic
4. Run: heroku config:set SECRET_KEY=finnec-secret-key-2024
5. Run: git push heroku main

## Local Testing:
1. Run: python app.py
2. Visit: http://localhost:5000

## Your app is ready to deploy!
