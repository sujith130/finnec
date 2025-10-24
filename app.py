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

    model = genai.GenerativeModel(
      model_name="gemini-1.5-flash",
      generation_config=generation_config,
    )

    chat_session = model.start_chat(
      history=[
      ]
    )

    response = chat_session.send_message(prompt)

    return response.text



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
        "financial_breakdown": "",
        "link": ""
    }
    '''
   
    try:
        # Construct the message prompt
        if capital_loan == 'capital':
            prompt = f"Hi, I'm from {country}. Kindly help curate a comprehensive financial breakdown with link to read more on it, for how I would manage my business considering that I have a capital of {amount} US Dollars. My domain of business interest is {domain_interest}, the description is: {description} and the country where I want to have my business is {country_interest}. Make your answer strictly in this format: {format}."
        elif capital_loan == 'loan':
            prompt = f"Hi, I'm from {country}. Kindly help curate a comprehensive financial breakdown with link to read more on it, for how I would manage my business considering that I got a loan of {amount} US Dollars and I am meant to pay back in {loan_pay_month} months time. My domain of business interest is {domain_interest}, the description is: {description} and the country where I want to have my business is {country_interest}. Make your answer strictly in this format: {format}."

        # Generate the response for the prompt
        advice_response = get_response(prompt)

        return prompt, advice_response

    except Exception as e:
        print(f"Error occurred while getting financial advice: {e}")
        return None, "Error occurred while getting financial advice."








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
        except json.JSONDecodeError:
            print("Error decoding JSON: Invalid format.")
            bot_predict_response = {"error": "Invalid response format."}

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
        except json.JSONDecodeError:
            print("Error decoding JSON: Invalid format.")
            bot_business_response = {"error": "Invalid response format."}

        session["bot_business_response"] = bot_business_response
        session["bot_business_prompt"] = bot_business_prompt

        return render_template('chat_business.html', name=name, country=country, bot_business_response=bot_business_response)

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

        try:
            bot_finance_response = json.loads(bot_finance_response)
        except json.JSONDecodeError:
            print("Error decoding JSON: Invalid format.")
            bot_finance_response = {"error": "Invalid response format."}

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