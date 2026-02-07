from flask import Flask, request, render_template, session, jsonify, redirect, url_for
import re
import numpy as np
import pandas as pd
import requests
import os
import json
import time
import joblib
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from repo root (same dir as app.py)
_app_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_app_dir, ".env"))
load_dotenv(os.path.join(_app_dir, "config.env"))
load_dotenv(os.path.join(_app_dir, "production.env"))


# Initialize the Flask application  
app = Flask(__name__)


# Set the secret key for the Flask application from an environment variable
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')


# Load the predictive model from a file
model = joblib.load('random_forest_model.pkl')
print("Model loaded successfully.")


# Define the column names for the model input
columns = ['no_of_dependents', 'education', 'self_employed', 'income_annum',
           'loan_amount', 'loan_term', 'cibil_score', 'residential_assets_value',
           'commercial_assets_value', 'luxury_assets_value', 'bank_asset_value']

# Set the API key from environment variable (recommended for production)
# os.environ["GEMINI_API_KEY"] = "your-api-key-here"  # Set this in your environment variables



def list_available_models():
    """List all available Gemini models for debugging"""
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set")
    
    genai.configure(api_key=api_key)
    
    try:
        models = genai.list_models()
        print("Available models:")
        for model in models:
            if 'generateContent' in model.supported_generation_methods:
                print(f"- {model.name}")
        return models
    except Exception as e:
        print(f"Error listing models: {e}")
        return []


def _get_response_openrouter(prompt):
    """Call OpenRouter API as fallback. Returns response text or None."""
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        return None
    openrouter_models = [
        "google/gemini-2.0-flash-001",
        "google/gemini-flash-1.5",
        "google/gemini-pro-1.5",
    ]
    for model_id in openrouter_models:
        try:
            print(f"Trying OpenRouter model: {model_id}")
            r = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model_id,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 1,
                    "max_tokens": 8192,
                },
                timeout=60,
            )
            r.raise_for_status()
            data = r.json()
            content = (data.get("choices") or [{}])[0].get("message", {}).get("content")
            if content:
                print(f"OpenRouter succeeded with {model_id}")
                return content.strip()
        except Exception as e:
            print(f"OpenRouter {model_id} failed: {e}")
            continue
    return None


def get_response(prompt):
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        # Try OpenRouter only if no Gemini key
        text = _get_response_openrouter(prompt)
        if text:
            return text
        raise ValueError("GEMINI_API_KEY environment variable is not set")
    
    genai.configure(api_key=api_key)

    generation_config = {
      "temperature": 1,
      "top_p": 0.95,
      "top_k": 64,
      "max_output_tokens": 8192,
      "response_mime_type": "text/plain",
    }

    # List of model names to try in order of preference
    model_names = [
        "gemini-2.5-flash",
        "gemini-1.5-flash-latest",
        "gemini-1.5-flash",
        "gemini-1.5-pro-latest", 
        "gemini-1.5-pro",
        "gemini-pro",
        "gemini-pro-vision"
    ]
    
    last_error = None
    
    for model_name in model_names:
        try:
            print(f"Trying model: {model_name}")
            model = genai.GenerativeModel(
                model_name=model_name,
                generation_config=generation_config,
            )

            chat_session = model.start_chat(history=[])
            response = chat_session.send_message(prompt)
            print(f"Successfully used model: {model_name}")
            return response.text
            
        except Exception as e:
            print(f"Model {model_name} failed: {e}")
            last_error = e
            continue
    
    # Fallback: try OpenRouter if Gemini all failed
    text = _get_response_openrouter(prompt)
    if text:
        return text
    
    raise Exception(f"All Gemini models failed. Last error: {last_error}")



def get_predict_message(country):
    # Define the required format for the response
    format = '''
    [
        {
            "myCountry": {
                "organizationName": "",
                "link": ""
            },
            "otherCountry": {
                "organizationName":"",
                "link": "",
                "Country": ""
            }
        },
        {
            "myCountry": {
                "organizationName": "",
                "link": ""
            },
            "otherCountry": {
                "organizationName":"",
                "link": "",
                "Country": ""
            }
        }
    ]
    '''
   
    # Construct the message prompt
    prompt = f"Hi, my country is {country}. Kindly create a comprehensive list of places I can look out for to get a good loan for my small business establishment both in my country and other countries. Make sure you give the countries of the other countries! Give the answer strictly in this format: {format}. Thanks."

    # Generate the response for the prompt
    prompt_response = get_response(prompt)

    return prompt, prompt_response


def get_further_response(prediction, question, prev_prompt, prev_response):
    """
    Generates a new prompt based on a previous conversation and a prediction result, then gets a response to it.
    """
    try:
        # Combine previous prompt and response
        old = str(prev_prompt) + str(prev_response)
        previous_conv = ""
        rev_old = old[::-1]

        # Extract the last 2500 characters of the reversed conversation
        for char in rev_old:
            if len(previous_conv) < 2500:
                previous_conv += char

        # Reverse the extracted conversation back to original order
        final_previous_conv = previous_conv[::-1]

        # Append additional text based on prediction
        if prediction == 0:  # Yes
            add_text = "again congrats on your approved loan"
        elif prediction == 1:  # No
            add_text = 'again sorry about the unapproved loan'
        else:
            add_text = ""

        final_previous_conv += add_text

        # Construct the new prompt
        new_prompt = f"Question: {question} | Previous Context: {final_previous_conv} | Instruction: Provide a concise, direct answer within 800 characters."

        # Generate the response for the new prompt
        further_response = get_response(new_prompt)

        return new_prompt, further_response

    except Exception as e:
        print(f"An error occurred while generating further response: {e}")
        return None, "An error occurred while generating the response."


def get_business_idea(country, country_interest, capital_loan, amount, domain_interest, loan_pay_month):
    """
    Generates a prompt for business ideas based on user's financial situation and interests, and gets a response.
    """
    # Define the required format for the response
    format = '''
    [
        {
            "Business_Idea": "",
            "sector": "",
            "link": ""
        },
        {
            "Business Idea": "",
            "sector": "",
            "link": ""
        }
    ]
    '''
   
    # Construct the message prompt
    try:
        if capital_loan == 'capital':
            prompt = f"Hi, I'm from {country}. Kindly help curate few nice business ideas, the domain sector of the business and like to learn more on the business, considering that I have a capital of {amount} US Dollars. My domain of business interest is {domain_interest} and the country where I want to have my business is {country_interest}. Give the answer strictly in this format: {format} Thanks."
        elif capital_loan == 'loan':
            prompt = f"Hi, I'm from {country}. Kindly help curate few nice business ideas, the domain sector of the business and like to learn more on the business, considering that I got a loan of {amount} US Dollars and I am meant to pay back in {loan_pay_month} months time. My domain of business interest is {domain_interest} and the country where I want to have my business is {country_interest}. Give the answer strictly in this format: {format} Thanks."

        # Generate the response for the prompt
        idea_response = get_response(prompt)

        return prompt, idea_response

    except Exception as e:
        print(f"Error occurred while getting business idea: {e}")
        return None, "Error occurred while getting business idea."


def get_financial_advice(country, country_interest, description, capital_loan, amount, domain_interest, loan_pay_month):
    """
    Generates a prompt for obtaining financial advice. Asks for plain-text GPT-style output (no JSON).
    """
    try:
        if capital_loan == 'capital':
            prompt = f"""You are a financial advisor. I'm from {country} and want to start a business in {country_interest}. 
I have a capital of {amount} US Dollars. My business domain is {domain_interest}. 
Business description: {description}

Reply in plain text only, like a chat message. Do NOT use JSON, code blocks, or curly braces.
Use this exact structure with **bold** for headers and - for bullets:

**Business Overview:**
- Domain: (domain)
- Location: (location)
- Capital/Loan Type: Capital
- Available Amount: ₹(amount in INR)
- Description: (short description)

**1. Budget Allocation (₹amount in INR):**
- 40% (₹x) - Core business operations and infrastructure
- 25% (₹x) - Marketing and customer acquisition
- 20% (₹x) - Technology and digital tools
- 10% (₹x) - Emergency fund and reserves
- 5% (₹x) - Professional services and legal

**2. Risk Management:**
- (bullet points)

**3. Growth Strategy:**
- (bullet points)

**4. Cash Flow Management:**
- (bullet points)

**5. Sector-Specific Actions (domain):**
- (bullet points)

**Recommended Next Steps:**
1. (step one)
2. (step two)
3. (step three)
4. (step four)
5. (step five)

At the very end write exactly: Link: https://www.investindia.gov.in/startupindia
(or another relevant Indian/financial resource URL)

Reply with the full breakdown in plain text only."""
        elif capital_loan == 'loan':
            prompt = f"""You are a financial advisor. I'm from {country} and want to start a business in {country_interest}. 
I got a loan of {amount} US Dollars and must repay it in {loan_pay_month} months. My business domain is {domain_interest}. 
Business description: {description}

Reply in plain text only, like a chat message. Do NOT use JSON, code blocks, or curly braces.
Use this exact structure with **bold** for headers and - for bullets:

**Business Overview:**
- Domain: (domain)
- Location: (location)
- Capital/Loan Type: Loan
- Available Amount: ₹(amount in INR)
- Repayment: (loan_pay_month) months
- Description: (short description)

**1. Budget Allocation (₹amount in INR):**
- (include loan repayment in allocation; use bullet points with percentages and amounts)

**2. Risk Management:**
- (bullet points)

**3. Growth Strategy:**
- (bullet points)

**4. Cash Flow Management:**
- (bullet points)

**5. Sector-Specific Actions (domain):**
- (bullet points)

**Recommended Next Steps:**
1. (step one)
2. (step two)
3. (step three)
4. (step four)
5. (step five)

At the very end write exactly: Link: https://www.investindia.gov.in/startupindia
(or another relevant URL)

Reply with the full breakdown in plain text only."""
        else:
            prompt = f"""You are a financial advisor. I'm from {country} and want to start a business in {country_interest}. 
My business domain is {domain_interest}. Business description: {description}

Reply in plain text only, like a chat message. Do NOT use JSON. Use **bold** for section headers and - for bullets. Include: Business Overview, 1. Budget Allocation, 2. Risk Management, 3. Growth Strategy, 4. Cash Flow Management, 5. Sector-Specific Actions, Recommended Next Steps (numbered). End with: Link: https://www.investindia.gov.in/startupindia"""

        advice_response = get_response(prompt)
        return prompt, advice_response

    except Exception as e:
        print(f"Error occurred while getting financial advice: {e}")
        print(f"Error type: {type(e)}")
        
        # Return a more specific error message based on the error type
        error_str = str(e)
        if "404" in error_str and "models" in error_str:
            return None, "Gemini model not available. Please check your API key and model access."
        elif "API key" in error_str or "authentication" in error_str.lower():
            return None, "Invalid or missing API key. Please check your GEMINI_API_KEY."
        elif "quota" in error_str.lower() or "limit" in error_str.lower():
            return None, "API quota exceeded. Please try again later."
        elif "network" in error_str.lower() or "connection" in error_str.lower():
            return None, "Network connection issue. Please check your internet connection."
        else:
            return None, f"Error occurred while getting financial advice: {error_str}"








@app.route('/', methods=["GET", "POST"])
def main():
    return render_template('index.html')


@app.route('/form_predict', methods=["GET", "POST"])
def form_predict():
    return render_template('form_predict.html')


@app.route('/form_business_idea', methods=["GET", "POST"])
def form_business_idea():
    return render_template('form_business_idea.html')


@app.route('/sign_in', methods=["GET", "POST"])
def sign_in():
    return render_template('sign_in.html')


@app.route('/services', methods=["GET", "POST"])
def services():
    return render_template('services.html')


@app.route('/test_models', methods=["GET"])
def test_models():
    """Debug route to test available Gemini models"""
    try:
        models = list_available_models()
        return f"Available models: {[model.name for model in models]}"
    except Exception as e:
        return f"Error: {e}"


@app.route('/test_financial_advice', methods=["GET"])
def test_financial_advice():
    """Debug route to test financial advice generation"""
    try:
        # Test with sample data
        test_prompt, test_response = get_financial_advice(
            country="India",
            country_interest="Maharashtra", 
            description="Tech startup",
            capital_loan="capital",
            amount="100000",
            domain_interest="Technology",
            loan_pay_month="0"
        )
        
        return f"""
        <h2>Financial Advice Test</h2>
        <h3>Prompt:</h3>
        <pre>{test_prompt}</pre>
        <h3>Response:</h3>
        <pre>{test_response}</pre>
        <h3>Response Type:</h3>
        <p>{type(test_response)}</p>
        <h3>Response Length:</h3>
        <p>{len(str(test_response)) if test_response else 0}</p>
        """
    except Exception as e:
        return f"Error testing financial advice: {e}"


@app.route('/test_api_key', methods=["GET"])
def test_api_key():
    """Debug route to test API keys (Gemini and OpenRouter)"""
    lines = ["<h2>API Key Test Results</h2>"]
    gemini_ok = False
    openrouter_ok = False

    # Gemini
    api_key = os.getenv('GEMINI_API_KEY', '').strip()
    if api_key:
        if len(api_key) < 10:
            lines.append(f"<p>⚠️ GEMINI_API_KEY is set but very short</p>")
        else:
            try:
                genai.configure(api_key=api_key)
                models = genai.list_models()
                model_count = len(list(models))
                lines.append(f"<p>✅ GEMINI_API_KEY is set (length {len(api_key)})</p>")
                lines.append(f"<p>✅ Gemini API connected – {model_count} models</p>")
                gemini_ok = True
            except Exception as e:
                lines.append(f"<p>❌ Gemini API failed: {e}</p>")
    else:
        lines.append("<p>❌ GEMINI_API_KEY is not set</p>")

    # OpenRouter
    or_key = os.getenv('OPENROUTER_API_KEY', '').strip()
    if or_key:
        lines.append(f"<p>✅ OPENROUTER_API_KEY is set (length {len(or_key)}) – used as fallback</p>")
        openrouter_ok = True
    else:
        lines.append("<p>⚠️ OPENROUTER_API_KEY is not set (optional fallback)</p>")

    if gemini_ok or openrouter_ok:
        lines.append("<p><strong>Status: At least one API is available. App should work.</strong></p>")
    else:
        lines.append("<p><strong>Status: Set GEMINI_API_KEY and/or OPENROUTER_API_KEY.</strong></p>")
    return "\n".join(lines)


@app.route('/form_financial_advice', methods=["GET", "POST"])
def form_financial_advice():
    return render_template('form_financial_advice.html')


@app.route('/next_session', methods=["GET", "POST"])
def next_session():
    try:
        name = request.form['name'].capitalize()
        country = request.form['country']

        session["name"] = name
        session["country"] = country

        return render_template('services.html', country=country, name=name)
    except Exception as e:
        print(f"Error in next_session: {e}")
        return "Error in processing your request."

@app.route('/chat_predict', methods=["GET", "POST"])
def chat_predict():
    try:
        # Extract and validate form data
        depend = int(request.form.get('depend', 0))
        education = request.form.get('education', "")
        employment = request.form.get('employment', "")
        income = float(request.form.get('income', 0))
        loan_amount = float(request.form.get('loan_amount', 0))
        loan_term = int(request.form.get('loan_term', 0))
        score = float(request.form.get('score', 0))
        resident = float(request.form.get('resident', 0))
        commercial = float(request.form.get('commercial', 0))
        luxury = float(request.form.get('luxury', 0))
        bank = float(request.form.get('bank', 0))

        # Prepare data for prediction
        columns = ['no_of_dependents', 'education', 'self_employed', 'income_annum', 'loan_amount', 'loan_term', 'cibil_score', 'residential_assets_value', 'commercial_assets_value', 'luxury_assets_value', 'bank_asset_value']
        arr = pd.DataFrame([[depend, education, employment, income, loan_amount, loan_term, score, resident, commercial, luxury, bank]], columns=columns)
        testing = ' '.join(arr.astype(str).values.flatten()) + ' '
        # Verify DataFrame

        # Convert to tuple for testing purposes
        #testing = tuple(arr.itertuples(index=False, name=None))

        # Ensure model is loaded before prediction
        if model is None:
            raise ValueError("Model is not loaded.")

        # Predict
        pred = int(model.predict(arr)[0])

        # Retrieve session data
        country = session.get("country", None)
        name = session.get("name", None)

        # Get prediction message
        bot_predict_prompt, bot_predict_response = get_predict_message(country)

        # Handle JSON decode error
        try:
            bot_predict_response = json.loads(bot_predict_response)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            print(f"Raw response that failed to parse: {bot_predict_response}")
            # Create a fallback response with the raw text
            bot_predict_response = [
                {
                    "myCountry": {
                        "organizationName": "Local Financial Institution",
                        "link": "https://www.sbi.co.in"
                    },
                    "otherCountry": {
                        "organizationName": "International Bank",
                        "link": "https://www.worldbank.org",
                        "Country": "International"
                    }
                }
            ]

        # Store in session
        session["pred"] = pred
        session["bot_predict_response"] = bot_predict_response
        session["bot_predict_prompt"] = bot_predict_prompt

        return render_template('chat_predict.html', pred=pred, name=name, country=country, bot_predict_response=bot_predict_response)

    except Exception as e:
        print(f"Error in chat_predict: {e}")
        return "bhag laura"


@app.route('/further_predict_chat', methods=["GET", "POST"])
def further_predict_chat():
    try:
        pred = session.get("pred", None)
        bot_predict_prompt = session.get("bot_predict_prompt", None)
        bot_predict_response = session.get("bot_predict_response", None)

        if request.method == 'POST':
            predict_question = request.form['question']
            predict_prompt, predict_response = get_further_response(prediction=pred, question=predict_question, prev_prompt=bot_predict_prompt, prev_response=bot_predict_response)

            session["bot_predict_response"] = predict_response
            session["bot_predict_prompt"] = predict_question

            return jsonify({"response": predict_response})

    except Exception as e:
        print(f"Error in further_predict_chat: {e}")
        return jsonify({"error": "An error occurred during the follow-up chat."})


@app.route('/business_idea', methods=["GET", "POST"])
def business_idea():
    try:
        country_interest = request.form['country_interest'].capitalize()
        capital_loan = request.form['capital_loan']
        amount = request.form['amount']
        domain_interest = request.form['domain_interest']
        loan_pay_month = request.form['loan_pay_month']

        country = session.get("country", None)
        name = session.get("name", None)

        bot_business_prompt, bot_business_response = get_business_idea(country=country, country_interest=country_interest, capital_loan=capital_loan, amount=amount, domain_interest=domain_interest, loan_pay_month=loan_pay_month)

        try:
            bot_business_response = json.loads(bot_business_response)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            print(f"Raw response that failed to parse: {bot_business_response}")
            # Create a fallback response with the raw text
            bot_business_response = [
                {
                    "Business_Idea": "E-commerce Platform",
                    "sector": "Technology",
                    "link": "https://www.shopify.com"
                },
                {
                    "Business_Idea": "Local Service Business",
                    "sector": "Services",
                    "link": "https://www.entrepreneur.com"
                }
            ]

        session["bot_business_response"] = bot_business_response
        session["bot_business_prompt"] = bot_business_prompt

        return render_template('chat_business.html', name=name, country=country, country_interest=country_interest, bot_business_response=bot_business_response)

    except Exception as e:
        print(f"Error in business_idea: {e}")
        return "An error occurred while processing your business idea."


@app.route('/further_business_chat', methods=["GET", "POST"])
def further_business_chat():
    try:
        bot_business_response = session.get("bot_business_response", None)
        bot_business_prompt = session.get("bot_business_prompt", None)

        if request.method == 'POST':
            business_question = request.form['question']
            business_prompt, business_response = get_further_response(prediction="", question=business_question, prev_prompt=bot_business_prompt, prev_response=bot_business_response)

            session["bot_business_response"] = business_response
            session["bot_business_prompt"] = business_question

            return jsonify({"response": business_response})

    except Exception as e:
        print(f"Error in further_business_chat: {e}")
        return jsonify({"error": "An error occurred during the business chat."})


def _safe_amount_num(amount_str, default=0):
    """Parse amount from form (handles commas, decimals, empty). Returns int for display."""
    try:
        s = str(amount_str).replace(",", "").replace(" ", "").strip()
        return int(float(s)) if s else default
    except (ValueError, TypeError):
        return default


def _markdown_to_html(text):
    """Convert markdown to HTML for chat: **bold**, bullet lists, numbered lists."""
    if not text or not isinstance(text, str):
        return ""
    import re
    lines = text.split("\n")
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # Bold section headers (**...** or **...**:)
        stripped = line.strip()
        if stripped.startswith("**"):
            head = stripped[2:].rstrip("*:").strip()
            if head:
                out.append(f"<p class=\"breakdown-head\"><strong>{head}</strong></p>")
                i += 1
                continue
        # Numbered list (1. 2. 3.)
        if re.match(r"^\s*\d+\.\s+", line):
            ol = ["<ol class=\"breakdown-list\">"]
            while i < len(lines) and re.match(r"^\s*\d+\.\s+", lines[i]):
                ol.append("<li>" + re.sub(r"^\s*\d+\.\s+", "", lines[i]).strip() + "</li>")
                i += 1
            ol.append("</ol>")
            out.append("\n".join(ol))
            continue
        # Bullet list (- item)
        if line.strip().startswith("- "):
            ul = ["<ul class=\"breakdown-list\">"]
            while i < len(lines) and (lines[i].strip().startswith("- ") or (lines[i].strip() == "" and i + 1 < len(lines) and lines[i + 1].strip().startswith("- "))):
                if lines[i].strip().startswith("- "):
                    content = lines[i].strip()[2:].strip()
                    # Bold inside bullet
                    content = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", content)
                    ul.append("<li>" + content + "</li>")
                i += 1
            ul.append("</ul>")
            out.append("\n".join(ul))
            continue
        # Plain line: bold then rest
        line = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line)
        if line.strip():
            out.append("<p>" + line.strip() + "</p>")
        i += 1
    return "\n".join(out)


def _any_to_readable_html(value, depth=0):
    """Convert any dict/list to readable HTML. Never show raw JSON."""
    import html
    if value is None:
        return ""
    if isinstance(value, str):
        return _markdown_to_html(value)
    if isinstance(value, (int, float)):
        return html.escape(str(value))
    if isinstance(value, dict):
        if depth > 4:
            return "..."
        parts = []
        for k, v in value.items():
            if k == "link" and isinstance(v, str):
                continue  # link shown separately
            label = html.escape(k.replace("_", " ").title())
            child = _any_to_readable_html(v, depth + 1)
            if isinstance(v, dict):
                parts.append(f"<strong>{label}</strong><br>{child}")
            elif isinstance(v, list):
                parts.append(f"<strong>{label}</strong><br>{child}")
            else:
                parts.append(f"<strong>{label}:</strong> {child}")
        return "<br>".join(parts)
    if isinstance(value, list):
        if depth > 4:
            return "..."
        items = [_any_to_readable_html(x, depth + 1) for x in value[:25]]
        return "<br>• " + "<br>• ".join(items)
    return html.escape(str(value))


def _financial_breakdown_to_markdown(value):
    """Convert financial_breakdown to a string. Handles nested JSON (dict) or JSON string from AI."""
    if value is None:
        return ""
    if isinstance(value, str):
        s = value.strip()
        # If it looks like JSON, parse and convert
        if s.startswith('{') and s.endswith('}'):
            try:
                value = json.loads(s)
            except json.JSONDecodeError:
                return s
        else:
            return s
    if not isinstance(value, dict):
        return str(value)
    def _bullet_text(v):
        if isinstance(v, str):
            return v
        if isinstance(v, dict):
            return v.get("strategy") or v.get("recommendation") or v.get("details") or v.get("focus") or str(v)
        return str(v)

    parts = []
    # Business Overview
    if value.get("introduction"):
        parts.append("**Business Overview:**")
        parts.append(f"- {value['introduction'].strip()}")
    # 1. Budget Allocation (supports percentage/amount/description OR allocation/details)
    if value.get("budget_allocation"):
        ba = value["budget_allocation"]
        parts.append("\n**1. Budget Allocation:**")
        if isinstance(ba, dict):
            for key, item in ba.items():
                if isinstance(item, dict):
                    alloc = item.get("allocation", "")  # e.g. "20% ($100,000 or INR 83 Lakhs)"
                    pct = item.get("percentage", "") or alloc
                    amt = item.get("amount", "")
                    desc = item.get("description", "") or item.get("details", "")
                    if pct and desc:
                        if alloc and not item.get("percentage"):
                            parts.append(f"- {alloc} - {desc}")
                        else:
                            parts.append(f"- {pct} {('(' + amt + ') ') if amt else ''}- {desc}")
                    elif pct:
                        parts.append(f"- {pct}")
                    else:
                        parts.append(f"- **{key.replace('_', ' ').title()}:** {desc or str(item)}")
                else:
                    parts.append(f"- {key.replace('_', ' ').title()}: {item}")
        else:
            parts.append(f"- {ba}")
    # 2. Risk Management (supports plain string OR dict with "strategy")
    if value.get("risk_management_strategies"):
        rms = value["risk_management_strategies"]
        parts.append("\n**2. Risk Management:**")
        if isinstance(rms, dict):
            for k, v in rms.items():
                parts.append(f"- {_bullet_text(v)}")
        else:
            parts.append(f"- {rms}")
    # 3. Growth Strategy (supports phase_1/phase_2/phase_3 with timeline+focus, scaling_strategies)
    if value.get("growth_and_expansion_plans"):
        gep = value["growth_and_expansion_plans"]
        parts.append("\n**3. Growth Strategy:**")
        if isinstance(gep, dict):
            for k, v in gep.items():
                if k == "scaling_strategies" and isinstance(v, str):
                    parts.append(f"- {v}")
                elif isinstance(v, dict):
                    t = v.get("timeline", "")
                    f = v.get("focus", "") or v.get("strategy", "") or str(v)
                    parts.append(f"- **{k.replace('_', ' ').title()}** ({t}): {f}" if t else f"- **{k.replace('_', ' ').title()}:** {f}")
                else:
                    parts.append(f"- {_bullet_text(v)}")
        else:
            parts.append(f"- {gep}")
    # 4. Cash Flow Management (supports dict with "strategy" or string)
    if value.get("cash_flow_management"):
        cfm = value["cash_flow_management"]
        parts.append("\n**4. Cash Flow Management:**")
        if isinstance(cfm, dict):
            s = cfm.get("strategy") or cfm.get("details")
            if s:
                parts.append(f"- {s}")
            else:
                for k, v in cfm.items():
                    parts.append(f"- {_bullet_text(v)}")
        else:
            parts.append(f"- {cfm}")
    # 5. Emergency fund / Sector-specific (supports dict with "recommendation" or string)
    if value.get("emergency_fund_recommendations"):
        efr = value["emergency_fund_recommendations"]
        parts.append("\n**5. Sector-Specific Actions / Emergency Fund:**")
        if isinstance(efr, dict):
            r = efr.get("recommendation") or efr.get("details")
            if r:
                parts.append(f"- {r}")
            else:
                for k, v in efr.items():
                    parts.append(f"- {_bullet_text(v)}")
        else:
            parts.append(f"- {efr}")
    # Additional notes (if present)
    if value.get("additional_notes"):
        parts.append("\n**Additional Notes:**")
        parts.append(f"- {value['additional_notes'].strip()}")
    # Recommended Next Steps (numbered)
    next_steps = value.get("next_steps") or value.get("recommended_next_steps") or value.get("specific_strategies")
    if next_steps:
        parts.append("\n**Recommended Next Steps:**")
        if isinstance(next_steps, list):
            for idx, step in enumerate(next_steps[:10], 1):
                parts.append(f"{idx}. {step}" if isinstance(step, str) else f"{idx}. {step}")
        elif isinstance(next_steps, str):
            parts.append(f"1. {next_steps}")
        elif isinstance(next_steps, dict):
            for idx, (k, v) in enumerate(next_steps.items(), 1):
                parts.append(f"{idx}. {v}" if isinstance(v, str) else f"{idx}. {k}: {v}")
    for key in value:
        if key in ("introduction", "budget_allocation", "risk_management_strategies",
                   "growth_and_expansion_plans", "cash_flow_management", "emergency_fund_recommendations",
                   "next_steps", "recommended_next_steps", "specific_strategies", "additional_notes"):
            continue
        v = value[key]
        if isinstance(v, (str, int, float)) and v:
            parts.append(f"\n**{key.replace('_', ' ').title()}:** {v}")
    return "\n".join(parts).strip() if parts else ""


@app.route('/financial_advice', methods=["GET", "POST"])
def financial_advice():
    if request.method != "POST":
        return redirect(url_for("form_financial_advice"))
    try:
        country_interest = request.form.get('country_interest', '').strip().capitalize() or 'India'
        capital_loan = request.form.get('capital_loan', 'capital')
        description = request.form.get('description', '')
        amount = request.form.get('amount', '0')
        domain_interest = request.form.get('domain_interest', '')
        loan_pay_month = request.form.get('loan_pay_month', '0')

        country = session.get("country", None) or "India"
        name = session.get("name", None)

        amount_num = _safe_amount_num(amount)

        try:
            bot_finance_prompt, bot_finance_response = get_financial_advice(country=country, country_interest=country_interest, description=description, capital_loan=capital_loan, amount=amount, domain_interest=domain_interest, loan_pay_month=loan_pay_month)
        except Exception as ai_err:
            print(f"get_financial_advice raised: {ai_err}")
            import traceback
            traceback.print_exc()
            bot_finance_prompt = ""
            bot_finance_response = None
        
        # Treat any error-like or non-JSON string as failure and use fallback
        def _is_error_response(r):
            if r is None: return True
            if not isinstance(r, str): return False
            s = r.strip().lower()
            return (s.startswith("error") or "invalid" in s or "api key" in s or "quota" in s or "not available" in s or len(s) < 20)
        
        if _is_error_response(bot_finance_response):
            print("AI call failed completely, using comprehensive fallback")
            bot_finance_response = {
                "financial_breakdown": f"""Based on your business profile for {domain_interest} in {country_interest}, here's a comprehensive financial breakdown:

**Business Overview:**
- Domain: {domain_interest}
- Location: {country_interest}
- Capital/Loan Type: {capital_loan.title()}
- Available Amount: ₹{amount_num:,}
- Description: {description}

**1. Budget Allocation (₹{amount_num:,}):**
- 40% (₹{int(amount_num * 0.4):,}) - Core business operations and infrastructure
- 25% (₹{int(amount_num * 0.25):,}) - Marketing and customer acquisition
- 20% (₹{int(amount_num * 0.2):,}) - Technology and digital tools
- 10% (₹{int(amount_num * 0.1):,}) - Emergency fund and reserves
- 5% (₹{int(amount_num * 0.05):,}) - Professional services and legal

**2. Risk Management:**
- Maintain 3-6 months operating expenses in reserve
- Diversify revenue streams within {domain_interest} sector
- Regular financial monitoring and monthly reporting
- Insurance coverage for business assets and liability
- Backup plans for key business processes

**3. Growth Strategy:**
- Focus on customer retention and repeat business
- Invest in digital marketing and online presence
- Consider partnerships within {domain_interest} ecosystem
- Monitor cash flow closely during expansion phases
- Build strong relationships with suppliers and vendors

**4. Cash Flow Management:**
- Implement automated invoicing and payment tracking
- Negotiate favorable payment terms with suppliers
- Consider invoice factoring for immediate cash needs
- Regular financial forecasting and scenario planning
- Monitor key performance indicators (KPIs)

**5. Sector-Specific Actions ({domain_interest}):**
- Research industry-specific financial requirements
- Understand regulatory compliance costs
- Plan for seasonal variations in revenue
- Consider technology investments for efficiency
- Build relationships with industry experts

**Recommended Next Steps:**
1. Create detailed monthly budget tracking
2. Set up business banking and accounting systems
3. Research {domain_interest} industry benchmarks
4. Consult with a financial advisor for personalized guidance
5. Regular review and adjustment of financial plans

*This is a general framework. For personalized advice, please consult with a qualified financial advisor.*""",
                "link": "https://www.investopedia.com/financial-advisor-5070221"
            }

        # Debug: Print the raw response
        print(f"Raw AI response: {bot_finance_response}")
        print(f"Response type: {type(bot_finance_response)}")
        print(f"Response length: {len(str(bot_finance_response)) if bot_finance_response else 0}")

        # Check if response is None or empty
        if not bot_finance_response or str(bot_finance_response).strip() == "":
            print("AI response is empty or None - using fallback")
            bot_finance_response = {
                "financial_breakdown": "I apologize, but I'm having trouble generating your financial advice at the moment. Please try again or contact support.",
                "link": "https://www.investopedia.com/financial-advisor-5070221"
            }
        elif isinstance(bot_finance_response, dict):
            # Already a dict (e.g. from fallback above) – ensure required keys
            if not bot_finance_response.get('financial_breakdown'):
                bot_finance_response['financial_breakdown'] = "Financial advice is being generated. Please check back in a moment."
            if not bot_finance_response.get('link'):
                bot_finance_response['link'] = "https://www.investopedia.com/financial-advisor-5070221"
        else:
            # AI returns plain text only (no JSON) – use as breakdown, extract "Link: URL" if present
            response_text = str(bot_finance_response).strip()
            link_url = "https://www.investopedia.com/financial-advisor-5070221"
            if "Link:" in response_text or "link:" in response_text:
                match = re.search(r"[Ll]ink:\s*(https?://[^\s]+)", response_text)
                if match:
                    link_url = match.group(1).rstrip(".,;")
                    response_text = response_text[:match.start()].strip()
            if len(response_text) > 50 and not response_text.startswith("Error"):
                bot_finance_response = {
                    "financial_breakdown": response_text,
                    "link": link_url
                }
            else:
                # Use a comprehensive fallback
                bot_finance_response = {
                    "financial_breakdown": f"""Based on your business profile, here's a comprehensive financial breakdown:

**Budget Allocation:**
- 40% for core business operations
- 25% for marketing and customer acquisition  
- 20% for technology and infrastructure
- 10% for emergency fund
- 5% for professional services

**Risk Management:**
- Maintain 3-6 months of operating expenses in reserve
- Diversify revenue streams
- Regular financial monitoring and reporting
- Insurance coverage for key business risks

**Growth Strategy:**
- Focus on customer retention and repeat business
- Invest in digital marketing and online presence
- Consider partnerships and collaborations
- Monitor cash flow closely during expansion

**Cash Flow Management:**
- Implement automated invoicing and payment tracking
- Negotiate favorable payment terms with suppliers
- Consider invoice factoring for immediate cash needs
- Regular financial forecasting and planning

This is a general framework - please consult with a financial advisor for personalized advice.""",
                    "link": "https://www.investopedia.com/financial-advisor-5070221"
                }

        # Always convert financial_breakdown to plain text/HTML for chat (never show JSON)
        bd = bot_finance_response.get("financial_breakdown")
        if bd is not None:
            if isinstance(bd, dict):
                md = _financial_breakdown_to_markdown(bd)
                bot_finance_response["financial_breakdown"] = _markdown_to_html(md) if md else _any_to_readable_html(bd)
            elif isinstance(bd, list):
                bot_finance_response["financial_breakdown"] = _any_to_readable_html(bd)
            else:
                md = _financial_breakdown_to_markdown(bd)
                bot_finance_response["financial_breakdown"] = _markdown_to_html(md) if md else _any_to_readable_html(str(bd))
        else:
            bot_finance_response["financial_breakdown"] = ""

        # Guarantee template never receives JSON/dict: always string (HTML)
        if not isinstance(bot_finance_response.get("financial_breakdown"), str):
            bot_finance_response["financial_breakdown"] = _any_to_readable_html(
                bot_finance_response.get("financial_breakdown")
            )

        # Prepend intro line like the reference: "Based on your business profile for X in Y, here's a comprehensive financial breakdown:"
        html_escape = __import__("html").escape
        intro = (
            f'<p class="breakdown-intro">Based on your business profile for <strong>{html_escape(domain_interest)}</strong> '
            f'in <strong>{html_escape(country_interest)}</strong>, here\'s a comprehensive financial breakdown:</p>'
        )
        bot_finance_response["financial_breakdown"] = intro + (bot_finance_response.get("financial_breakdown") or "")

        session["bot_finance_response"] = bot_finance_response
        session["bot_finance_prompt"] = bot_finance_prompt

        return render_template(
            'chat_finance.html',
            name=name or "Guest",
            country=country or "India",
            bot_finance_response=bot_finance_response,
        )

    except Exception as e:
        import traceback
        import html
        err_type = type(e).__name__
        err_detail = str(e)
        print(f"Error in financial_advice: {e}")
        traceback.print_exc()
        err_msg = (
            "An error occurred while processing your financial advice. "
            "Set GEMINI_API_KEY and SECRET_KEY in Render → Environment; then check /test_api_key. "
            "Technical detail: " + err_type + ": " + err_detail
        )
        err_msg_safe = html.escape(err_msg)
        try:
            return render_template(
                "form_financial_advice.html",
                error_message=err_msg
            ), 200
        except Exception as template_err:
            print(f"Error rendering error template: {template_err}")
            return (
                f'<html><body style="font-family:sans-serif;padding:2rem;max-width:600px;">'
                f'<h2>Financial advice could not be generated</h2><p>{err_msg_safe}</p>'
                f'<p><a href="/form_financial_advice">Back to form</a></p>'
                f'<p><a href="/test_api_key">Test API key</a></p></body></html>',
                200,
                {"Content-Type": "text/html; charset=utf-8"},
            )


@app.route('/further_finance_chat', methods=["GET", "POST"])
def further_finance_chat():
    try:
        bot_finance_response = session.get("bot_finance_response", None)
        bot_finance_prompt = session.get("bot_finance_prompt", None)

        if request.method == 'POST':
            finance_question = request.form['question']
            finance_prompt, finance_response = get_further_response(prediction="", question=finance_question, prev_prompt=bot_finance_prompt, prev_response=bot_finance_response)

            session["bot_finance_response"] = finance_response
            session["bot_finance_prompt"] = finance_question

            # Output plain text only (never JSON/dict)
            out = finance_response if isinstance(finance_response, str) else (_any_to_readable_html(finance_response) if isinstance(finance_response, (dict, list)) else str(finance_response))
            return jsonify({"response": out})

    except Exception as e:
        print(f"Error in further_finance_chat: {e}")
        return jsonify({"error": "An error occurred during the finance chat."})


if __name__ == '__main__':
    try:
        app.run(debug=True, use_reloader=False, port=5000)
    except Exception as e:
        print(f"Error in starting the application: {e}")