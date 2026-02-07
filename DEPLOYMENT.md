# Finnec - AI Financial Advisory App Deployment Guide

## Project Overview

Finnec is an AI-driven financial advisory application designed for Small and Medium Enterprises (SMEs). It provides:

- **Loan Prediction**: ML-based loan approval prediction
- **Business Ideas**: AI-generated business recommendations
- **Financial Advice**: Personalized financial guidance
- **Interactive Chat**: Conversational AI interface

## Technology Stack

- **Backend**: Flask (Python)
- **AI/ML**: Google Generative AI (Gemini), Scikit-learn
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **Model**: Random Forest (joblib)

## Deployment Options

### 1. Heroku (Recommended for beginners)

**Prerequisites:**
- Heroku account
- Git installed
- Heroku CLI

**Steps:**
1. Install Heroku CLI
2. Login to Heroku: `heroku login`
3. Create new app: `heroku create your-app-name`
4. Set environment variables:
   ```bash
   heroku config:set GEMINI_API_KEY=your-api-key
   heroku config:set SECRET_KEY=your-secret-key
   ```
5. Deploy: `git push heroku main`

### 2. Render (Free tier available)

**Steps:**
1. Connect GitHub repository to Render
2. Set environment variables in Render dashboard:
   - `GEMINI_API_KEY`
   - `SECRET_KEY`
3. Deploy automatically

### 3. Railway

**Steps:**
1. Connect GitHub repository
2. Set environment variables
3. Deploy automatically

### 4. DigitalOcean App Platform

**Steps:**
1. Connect GitHub repository
2. Configure environment variables
3. Deploy

## Environment Variables Required

```bash
GEMINI_API_KEY=your-google-gemini-api-key
SECRET_KEY=your-flask-secret-key
FLASK_ENV=production
```

## Local Development Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd finnec-main
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set environment variables:**
   ```bash
   # Create .env file
   cp env.example .env
   # Edit .env with your actual values
   ```

5. **Run the application:**
   ```bash
   python app.py
   ```

## API Key Setup

1. **Get Google Gemini API Key:**
   - Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create a new API key
   - Copy the key

2. **Set the API key:**
   - For local development: Add to `.env` file
   - For production: Set as environment variable in your deployment platform

## File Structure

```
finnec-main/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── Procfile              # Heroku deployment config
├── random_forest_model.pkl # ML model file
├── templates/            # HTML templates
├── static/              # CSS, JS, images
└── env.example          # Environment variables template
```

## Troubleshooting

### Common Issues:

1. **Model loading error:**
   - Ensure `random_forest_model.pkl` is in the root directory
   - Check file permissions

2. **API key not found:**
   - Verify environment variable is set correctly
   - Check variable name spelling

3. **Port binding error:**
   - Ensure port 5000 is available
   - Check if another process is using the port

### Performance Optimization:

1. **Model caching:** The model is loaded once at startup
2. **Session management:** Uses Flask sessions for user data
3. **Error handling:** Comprehensive error handling in all routes

## Security Considerations

1. **API Keys:** Never commit API keys to version control
2. **Secret Key:** Use a strong, random secret key
3. **Environment Variables:** Use environment variables for sensitive data
4. **HTTPS:** Always use HTTPS in production

## Monitoring and Maintenance

1. **Logs:** Check application logs for errors
2. **Performance:** Monitor response times
3. **API Usage:** Monitor Gemini API usage and costs
4. **Updates:** Keep dependencies updated

## Support

For issues or questions:
1. Check the logs for error messages
2. Verify environment variables are set correctly
3. Ensure all dependencies are installed
4. Check API key validity and quota
