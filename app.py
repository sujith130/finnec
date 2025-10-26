from flask import Flask, request, render_template, session, jsonify
import numpy as np
import pandas as pd
import requests
import os
import json
import time
import joblib
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


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


def get_response(prompt):
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
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
    
    # If all models fail, raise the last error
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
    Generates a prompt for obtaining financial advice based on the user's financial status and business interests, and gets a response.
    """
    # Define the required format for the response
    format = '''
    {
        "financial_breakdown": "Provide detailed financial advice here including budget allocation, risk management, and growth strategies",
        "link": "https://example.com/financial-resources"
    }
    '''
   
    try:
        # Construct the message prompt with more specific instructions
        if capital_loan == 'capital':
            prompt = f"""You are a financial advisor. I'm from {country} and want to start a business in {country_interest}. 
            I have a capital of {amount} US Dollars. My business domain is {domain_interest}. 
            Business description: {description}
            
            Please provide a comprehensive financial breakdown including:
            1. Budget allocation for different business needs
            2. Risk management strategies
            3. Growth and expansion plans
            4. Cash flow management
            5. Emergency fund recommendations
            
            Respond ONLY in this exact JSON format: {format}
            
            Make the financial_breakdown detailed and actionable. Provide a relevant link for additional resources."""
        elif capital_loan == 'loan':
            prompt = f"""You are a financial advisor. I'm from {country} and want to start a business in {country_interest}. 
            I got a loan of {amount} US Dollars and must repay it in {loan_pay_month} months. My business domain is {domain_interest}. 
            Business description: {description}
            
            Please provide a comprehensive financial breakdown including:
            1. Loan repayment strategy
            2. Budget allocation considering loan payments
            3. Risk management strategies
            4. Cash flow management for loan servicing
            5. Growth plans within loan constraints
            
            Respond ONLY in this exact JSON format: {format}
            
            Make the financial_breakdown detailed and actionable. Provide a relevant link for additional resources."""

        # Generate the response for the prompt
        advice_response = get_response(prompt)

        return prompt, advice_response

    except Exception as e:
        print(f"Error occurred while getting financial advice: {e}")
        # Return a more specific error message based on the error type
        if "404" in str(e) and "models" in str(e):
            return None, "Gemini model not available. Please check your API key and model access."
        elif "API key" in str(e):
            return None, "Invalid or missing API key. Please check your GEMINI_API_KEY."
        else:
            return None, f"Error occurred while getting financial advice: {str(e)}"








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


@app.route('/financial_advice', methods=["GET", "POST"])
def financial_advice():
    try:
        country_interest = request.form['country_interest'].capitalize()
        capital_loan = request.form['capital_loan']
        description = request.form['description']
        amount = request.form['amount']
        domain_interest = request.form['domain_interest']
        loan_pay_month = request.form['loan_pay_month']

        country = session.get("country", None)
        name = session.get("name", None)

        bot_finance_prompt, bot_finance_response = get_financial_advice(country=country, country_interest=country_interest, description=description, capital_loan=capital_loan, amount=amount, domain_interest=domain_interest, loan_pay_month=loan_pay_month)

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
        else:
            try:
                # Try to parse as JSON
                parsed_response = json.loads(bot_finance_response)
                print(f"Successfully parsed JSON: {parsed_response}")
                bot_finance_response = parsed_response
                
                # Ensure required fields exist
                if not bot_finance_response.get('financial_breakdown'):
                    print("Missing financial_breakdown field - adding fallback")
                    bot_finance_response['financial_breakdown'] = "Financial advice is being generated. Please check back in a moment."
                if not bot_finance_response.get('link'):
                    print("Missing link field - adding fallback")
                    bot_finance_response['link'] = "https://www.investopedia.com/financial-advisor-5070221"
                    
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
                print(f"Raw response that failed to parse: {bot_finance_response}")
                
                # If JSON parsing fails, create a fallback response
                # Check if the response looks like it contains useful content
                response_text = str(bot_finance_response).strip()
                if len(response_text) > 50 and not response_text.startswith("Error"):
                    # Use the raw response as financial breakdown
                    bot_finance_response = {
                        "financial_breakdown": response_text,
                        "link": "https://www.investopedia.com/financial-advisor-5070221"
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

        session["bot_finance_response"] = bot_finance_response
        session["bot_finance_prompt"] = bot_finance_prompt

        return render_template('chat_finance.html', name=name, country=country, bot_finance_response=bot_finance_response)

    except Exception as e:
        print(f"Error in financial_advice: {e}")
        return "An error occurred while processing your financial advice."


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

            return jsonify({"response": finance_response})

    except Exception as e:
        print(f"Error in further_finance_chat: {e}")
        return jsonify({"error": "An error occurred during the finance chat."})


if __name__ == '__main__':
    try:
        app.run(debug=True, use_reloader=False, port=5000)
    except Exception as e:
        print(f"Error in starting the application: {e}")