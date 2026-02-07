# Do this now – get Finnec running on Render

Your **GEMINI_API_KEY** and **SECRET_KEY** are already in `config.env` in this repo. The app loads them on start.

## Option A: Just redeploy (try this first)

1. Go to **https://dashboard.render.com** and sign in.
2. Open your **finnec-app** (or the service connected to **sujith130/finnec**).
3. Click **Manual Deploy** → **Deploy latest commit**.
4. Wait for the deploy to finish, then open **https://your-app.onrender.com/test_api_key**.  
   If it says the API key is set, you’re done. Try **Financial Advice** again.

## Option B: Set env vars in Render (if Option A still fails)

1. Go to **https://dashboard.render.com** and sign in.
2. Open your **finnec-app** service.
3. In the left sidebar, click **Environment**.
4. Click **Add Environment Variable** and add:

   - **Key:** `GEMINI_API_KEY`  
     **Value:** `AIzaSyCl8rMD9MQIwdiRitfrKVbGknDMwlcg_oo`  
     (or your own key from [Google AI Studio](https://aistudio.google.com/apikey))  
     Turn **Secret** on.

   - **Key:** `SECRET_KEY`  
     **Value:** `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`  
     (or any long random string)  
     Turn **Secret** on.

5. Click **Save**. Render will redeploy.
6. When it’s done, open **/test_api_key** and then try **Financial Advice**.

---

**Summary:** Sign in at dashboard.render.com → open your service → try **Manual Deploy** first; if the app still fails, add the two env vars under **Environment** as above.
