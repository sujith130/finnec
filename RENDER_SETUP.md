# Render setup – Finnec

## 1. Connect the repo

1. Go to [dashboard.render.com](https://dashboard.render.com).
2. **New** → **Web Service**.
3. Connect **GitHub** and select the repo **sujith130/finnec** (or your fork).
4. If Render finds `render.yaml`, it will use it. Otherwise set:
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `gunicorn app:app`

## 2. Set environment variables

1. In the left sidebar, open your **finnec-app** service.
2. Go to **Environment**.
3. Add these variables (use **Add Environment Variable**):

   | Key                   | Value                    | Secret? |
   |-----------------------|--------------------------|--------|
   | `GEMINI_API_KEY`      | Your Google AI API key   | Yes    |
   | `OPENROUTER_API_KEY`  | Your OpenRouter key (sk-or-v1-...) | Yes |
   | `SECRET_KEY`          | Flask session secret (can use same as OpenRouter key) | Yes |

   - **GEMINI_API_KEY:** from [Google AI Studio](https://aistudio.google.com/apikey).
   - **OPENROUTER_API_KEY:** from [OpenRouter](https://openrouter.ai/keys) (the “secret key” / sk-or-v1-... one).
   - **SECRET_KEY:** any long random string for Flask sessions, or the same value as `OPENROUTER_API_KEY`.

4. Save. Render will redeploy automatically.

## 3. Check the deploy

- After the deploy finishes, open: **https://your-service-name.onrender.com**
- Test the API key: **https://your-service-name.onrender.com/test_api_key**  
  You should see “API Key is set” and “Successfully connected to Gemini API”.
- Use **Financial Advice** from the app; it should load without the previous error.

## If the app was already created without Blueprint

- You can still add the env vars: **Service → Environment → Add** `GEMINI_API_KEY` and `SECRET_KEY`.
- Optionally, in the same service use **Settings → Build & Deploy** and set **Build command** to `pip install -r requirements.txt` and **Start command** to `gunicorn app:app` so they match the repo.

## Troubleshooting

- **“GEMINI_API_KEY environment variable is not set”**  
  Add `GEMINI_API_KEY` in **Environment**, then trigger **Manual Deploy**.
- **Financial advice still errors**  
  Open **/test_api_key** and fix the API key if it’s missing or invalid. The error page’s “Technical detail” line shows the exact failure.
