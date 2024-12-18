import tkinter as tk
from tkinter import scrolledtext
import requests
import webbrowser
from bs4 import BeautifulSoup
import os
import time
import smtplib
import webbrowser
import pyttsx3
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import google.generativeai as genai
import re  # For URL extraction
import speech_recognition as sr  # For voice recognition
import datetime
import platform
import threading  # For threading
from flask import Flask, render_template, request, jsonify

# Initialize components
engine = pyttsx3.init()
scheduler = BackgroundScheduler()
scheduler.start()
recognizer = sr.Recognizer()  # Initialize recognizer

# --- Adjust speech rate here ---
rate = engine.getProperty('rate')
engine.setProperty('rate', 175)

# Authenticate with Google Generative AI
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))  # Replace with your Gemini API key
model = genai.GenerativeModel('gemini-1.5-flash')

sender_email = "e mail "  # add sender email address
sender_password = "password"  # add sender email password

#Global cancelation variable
cancel_flag = False

# Function for text-to-speech
def speak(text):
    global cancel_flag
    cleaned_text = re.sub(r'\*', '', text)  # Remove asterisks from the text
    engine.say(cleaned_text)
    while engine.isBusy():
        if cancel_flag:
           engine.stop()
           break
        time.sleep(0.1)


# Function to send emails
def send_email(recipient, subject, body, sender_email, sender_password):
    global cancel_flag
    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP('smtp.gmail.com', 587) as server:  # Use port 587
            server.starttls()  # Enable TLS encryption
            server.login(sender_email, sender_password)
            server.send_message(msg)
            if cancel_flag:
                return "Email sending cancelled."
        speak("Email sent successfully.")
        if cancel_flag:
                return "Email sending cancelled."
        return  "Email sent successfully."
    except Exception as e:
        speak(f"Failed to send email: {e}")
        print(f"Failed to send email: {e}")  # Print the error for debugging
        return  f"Failed to send email: {e}"


# Function to open websites based on a name search
def open_website(query):
    global cancel_flag
    try:
        # Attempt to treat query as a URL first
        if query.startswith(('http://', 'https://')):
            webbrowser.open(query)
            speak(f"Opening {query} in your browser.")
            if cancel_flag:
                return "Opening website cancelled."
            return f"Opening {query} in your browser."

        # If query is not a URL use a search engine to get the website URL
        search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(search_url, headers=headers)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            first_link = soup.find('a', href=True)

            if first_link:
                first_url = first_link['href']

                # Attempt to open a found url (If the link isn't a direct website link)
                if first_url.startswith(('http://', 'https://')):
                    webbrowser.open(first_url)
                    speak(f"Opening {query} and the website from search results.")
                    if cancel_flag:
                       return "Opening website cancelled."
                    return  f"Opening {query} and the website from search results."
                else:
                    # If no direct link is found, open google search page
                    webbrowser.open(search_url)
                    speak(f"Opening google search results for {query}.")
                    if cancel_flag:
                         return "Opening website cancelled."
                    return  f"Opening google search results for {query}."
            else:
                # if no url is found for the query open a search page
                webbrowser.open(search_url)
                speak(f"Opening search results for {query}.")
                if cancel_flag:
                     return "Opening website cancelled."
                return f"Opening search results for {query}."
        else:
            speak("Failed to search for the website. Please check your internet connection.")
            return  "Failed to search for the website. Please check your internet connection."
    except Exception as e:
        speak(f"Failed to open website: {e}")
        print(f"Failed to open website: {e}")
        return f"Failed to open website: {e}"


# Function to set reminders
def set_reminder(message, delay_minutes):
    global cancel_flag
    def reminder_job():
        speak(f"Reminder: {message}")
        return f"Reminder: {message}"

    delay_seconds = delay_minutes * 60
    scheduler.add_job(reminder_job, 'date', run_date=datetime.now() + timedelta(seconds=delay_seconds))
    speak(f"Reminder set for {delay_minutes} minutes.")
    if cancel_flag:
           return "Setting reminder cancelled."
    return f"Reminder set for {delay_minutes} minutes."


# Function to fetch data using Google Generative AI
def fetch_data(query):
    global cancel_flag
    try:
        answer = model.generate_content(query)
        print(answer.text)
        speak(answer.text)
        if cancel_flag:
              return "Gemini request cancelled."
        return  answer.text
    except Exception as e:
        print(f"Failed to fetch data: {e}")
        speak(f"Failed to fetch data: {e}")
        return  f"Failed to fetch data: {e}"


# --- Add this new function here ---
def get_current_time():
    now = datetime.datetime.now()
    time_str = now.strftime("%H:%M")  # current time
    return time_str


def get_current_date():
    now = datetime.datetime.now()
    date_str = now.strftime("%Y-%m-%d")  # current date
    return date_str


def calculate(expression):
    global cancel_flag
    try:
        result = eval(expression)  # eval function is used for calculations
        if cancel_flag:
            return "Calculation cancelled."
        return str(result)
    except Exception as e:
        return f"Error in calculation: {e}"


def get_os_info():
    global cancel_flag
    os_name = platform.system()
    if cancel_flag:
        return "Operation cancelled"
    return f"Your operating system is: {os_name}"


def play_music(query):
    global cancel_flag
    search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
    webbrowser.open(search_url)  # opens the music search url in browser
    speak(f"Playing {query} from YouTube.")
    if cancel_flag:
         return "Music playing cancelled."
    return f"Playing {query} from YouTube."


# Function to get voice command
def get_voice_command(phrase_limit=5):
    global cancel_flag
    with sr.Microphone() as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source)
        try:
            audio = recognizer.listen(source, phrase_time_limit=phrase_limit)
            if cancel_flag:
                return ""
        except sr.WaitTimeoutError:  # if no speech is detected in the allocated time
            print("Listening timed out. Please try again.")
            speak("Sorry, I did not hear anything.")
            return ""

    try:
        command = recognizer.recognize_google(audio).lower()
        print(f"You said: {command}")
        if cancel_flag:
           return ""
        return command
    except sr.UnknownValueError:
        speak("Sorry, I could not understand.")
        return ""
    except sr.RequestError as e:
        speak(f"Could not request results from Google Speech Recognition service: {e}")
        print(f"Could not request results from Google Speech Recognition service: {e}")
        return ""


# Main NLP function to decide intent
def process_command(command):
    global cancel_flag
    if cancel_flag:
        cancel_flag = False
        return "Operation cancelled"
    if "reminder" in command or "alarm" in command:
        # unchanged reminder code
        words = command.split()
        if "in" in words:
            try:
                delay_index = words.index("in") + 1
                delay_minutes = int(words[delay_index])
                message = ' '.join(words[delay_index + 1:])
                return set_reminder(message, delay_minutes)
            except ValueError:
                speak("I need to know when to set the reminder. Please provide a numerical value for the delay")
                return "I need to know when to set the reminder. Please provide a numerical value for the delay"
            except Exception as e:
                print(f"Error parsing reminder command: {e}")
                speak(f"Error parsing reminder command: {e}")
                return f"Error parsing reminder command: {e}"
        else:
            speak("I need to know when to set the reminder.")
            return "I need to know when to set the reminder."
    elif "email" in command:
        def email_sequence():
             prompts = ["Who should I send the email to?", "What is the subject?", "What should I say?"]
             keys = ["recipient", "subject", "body"]
             email_data = {}
             global cancel_flag

             for i, prompt in enumerate(prompts):
                 if cancel_flag:
                      return "Operation cancelled"
                 speak(prompt)
                 command = get_voice_command()
                 if command:
                     email_data[keys[i]] = command
                 else:
                     return  "Could not get input for email."

             return send_email(email_data["recipient"], email_data["subject"], email_data["body"], sender_email, sender_password)

        return email_sequence()
    elif "website" in command or "open" in command:
         # unchanged website code
        words = command.split()
        url = None

         # Check for a URL directly in the command
        for word in words:
            if word.startswith(('http://', 'https://')):
               url = word
               break

        if url:
            return open_website(url)
        else:
             # if no url is found just the name of the website try to get the first search result link
            query = command.replace("open", "").replace("website", "").strip()
            if query:
                return open_website(query)
            else:
                print("I need the name of the website to search for.")
                speak("I need the name of the website to search for.")
                return "I need the name of the website to search for."
    elif "time" in command:
        # unchanged time code
        time_str = get_current_time()
        speak(f"The current time is {time_str}")
        return f"The current time is {time_str}"
    elif "date" in command:
        # unchanged date code
        date_str = get_current_date()
        speak(f"The current date is {date_str}")
        return  f"The current date is {date_str}"
    elif "calculate" in command:
         # unchanged calc code
        expression = command.replace("calculate", "").strip()
        result = calculate(expression)
        speak(f"The result is {result}")
        return f"The result is {result}"
    elif "system info" in command or "operating system" in command:
         # unchanged sys info code
        os_info = get_os_info()
        speak(os_info)
        return os_info
    elif "play" in command:
         # unchanged music code
        query = command.replace("play", "").strip()
        return play_music(query)
    else:
         # unchanged gemini response code
        response = fetch_data(command)
        if response:
            return response

app = Flask(__name__)

@app.route('/')
def index():
    global cancel_flag
    cancel_flag = False
    initial_messages = ["Hello! I am ready to assist you."]
    speak("Hello! I am ready to assist you.")
    return render_template('index.html', initial_messages=initial_messages)

@app.route('/process', methods=['POST'])
def process():
    data = request.get_json()
    command = data.get('message')
    if command:
       response =  process_command(command)
       return jsonify({'response': response})
    else:
       return jsonify({'response': "Could not understand the command."})

@app.route('/voice', methods=['POST'])
def voice():
    command = get_voice_command(phrase_limit=5)
    if command:
        response = process_command(command)
        return jsonify({'command': response})
    else:
       return jsonify({'command': "Could not understand the voice command."})

@app.route('/clear', methods=['POST'])
def clear():
   global cancel_flag
   cancel_flag = True
   return jsonify({'status': 'ok'})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')