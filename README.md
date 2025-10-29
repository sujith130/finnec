# Finnec – AI SME Advisor

## Live Demo

Visit the deployed app on Render: https://finnec-app.onrender.com

Finnec is an AI-driven financial advisory application that provides personalized guidance for small and medium-sized enterprises (SMEs). It combines a predictive ML model with Google’s Gemini models for conversational insights.

## Features

- **Personalized Business & Financial Advice**: Conversational guidance powered by Gemini.
- **Predictive Analytics**: Random Forest model for outcome prediction.
- **Modern UI**: Responsive frontend served via Flask with static assets.
- **Deploy-ready**: Render/Heroku friendly with Procfile and guides.

## Technology Stack

- **Backend**: Flask (Python)
- **AI**: Google Generative AI (`google-generativeai`)
- **Primary Model**: `gemini-2.5-flash` (with fallbacks)
- **ML**: scikit-learn RandomForest (loaded from `random_forest_model.pkl`)

## Requirements

- Python 3.10+ (3.13 tested)
- Pip

Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

Set required environment variables. You can use `config.env` (loaded automatically by the app) or export variables in your shell.

Required:
- `GEMINI_API_KEY` – your Google AI Studio API key
- `SECRET_KEY` – Flask secret key

Options:
- `FLASK_ENV` – `development` or `production` (defaults to development)

Example (PowerShell on Windows):
```powershell
$env:GEMINI_API_KEY="<your-gemini-api-key>"
$env:SECRET_KEY="finnec-secret-key-2024"
```

Or edit `config.env`:
```env
GEMINI_API_KEY=<your-gemini-api-key>
SECRET_KEY=finnec-secret-key-2024
```

## Running Locally

From the project directory that contains `app.py` (this folder):

Option A – with helper script (recommended):
```bash
python run_app.py
```

Option B – run Flask app directly:
```bash
python app.py
```

Then open: `http://127.0.0.1:5000`

If you see “connection refused”, ensure you’re in the folder that contains `app.py` (e.g. `.../finnec-main/finnec-main`) and that your `GEMINI_API_KEY` is set.

## Gemini Models

The app tries models in this order:
```text
gemini-2.5-flash
gemini-1.5-flash-latest
gemini-1.5-flash
gemini-1.5-pro-latest
gemini-1.5-pro
gemini-pro
gemini-pro-vision
```

You can view available models via the debug route:
```text
GET /test_models
```

## Useful Debug Routes

- `GET /test_api_key` – verifies `GEMINI_API_KEY` presence and length
- `GET /test_models` – lists available Gemini models

## Deployment

This repo includes step-by-step deploy docs for Render/Heroku:
- `FINAL_RENDER_DEPLOYMENT.md`
- `RENDER_DEPLOYMENT_GUIDE.md`
- `FINAL_DEPLOYMENT_SUMMARY.md`
- `DEPLOY_NOW.md`

Ensure you configure environment variables on your platform:
- `GEMINI_API_KEY`
- `SECRET_KEY`

## Security Notes

- Do not commit real API keys to version control. Prefer environment variables and `.env` files excluded by `.gitignore`.
- If a key was exposed, rotate it in Google AI Studio and update `config.env` or platform env vars.



