import datetime
import os
import sys
import time
import webbrowser
import pyautogui
import pyttsx3
import speech_recognition as sr
import json
import pickle
import random
import numpy as np
import psutil
import subprocess
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.sequence import pad_sequences
from pywikihow import search_wikihow  # For WikiHow search
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL
import math

# Initialize TTS engine
def initialize_engine():
    engine = pyttsx3.init("sapi5")
    voices = engine.getProperty("voices")
    engine.setProperty("voice", voices[1].id)
    rate = engine.getProperty("rate")
    engine.setProperty("rate", rate - 50)
    volume = engine.getProperty("volume")
    engine.setProperty("volume", volume + 0.25)
    return engine

def speak(text):
    engine = initialize_engine()
    engine.say(text)
    engine.runAndWait()

# Recognize voice command
def command():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source, duration=0.5)
        print("Listening...", end="", flush=True)
        try:
            audio = r.listen(source, timeout=5)
            print(f"\rRecognizing...", end="", flush=True)
            query = r.recognize_google(audio, language="en-in")
            print(f"\rUser said: {query}\n")
        except Exception:
            print("\rSay that again please")
            return "None"
    return query

# Function to standardize misinterpreted speech-to-text input
def standardize_query(query):
    # Replace common misinterpretations
    query = query.replace("hu r u", "who are you")
    query = query.replace("who r u", "who are you")
    query = query.replace("how r u", "how are you")
    # Add more standardizations as needed
    return query

# Day and time functions
def cal_day():
    day = datetime.datetime.today().weekday() + 1
    day_dict = {1: "Monday", 2: "Tuesday", 3: "Wednesday", 4: "Thursday", 5: "Friday", 6: "Saturday", 7: "Sunday"}
    return day_dict.get(day, "")

def wishMe():
    hour = int(datetime.datetime.now().hour)
    t = time.strftime("%I:%M:%p")
    day = cal_day()

    if hour >= 0 and hour <= 12:
        speak(f"Good morning, it's {day} and the time is {t}")
    elif hour > 12 and hour <= 16:
        speak(f"Good afternoon, it's {day} and the time is {t}")
    else:
        speak(f"Good evening, it's {day} and the time is {t}")

# Function for handling social media commands
def social_media(command):
    platforms = {
        "facebook": "https://www.facebook.com/",
        "whatsapp": "https://web.whatsapp.com/",
        "discord": "https://discord.com/",
        "instagram": "https://www.instagram.com/"
    }
    for platform, url in platforms.items():
        if platform in command:
            speak(f"Opening your {platform}")
            webbrowser.open(url)
            return
    speak("No result found")

# Function for university schedule
def schedule():
    day = cal_day().lower()
    speak("Boss, today's schedule is ")
    week = {
        "monday": "You have Algorithms class from 9:00 to 9:50...",
        "tuesday": "You have Web Development class from 9:00 to 9:50...",
        # Add remaining days here
    }
    speak(week.get(day, "No schedule available"))

# Open and close apps
def openApp(command):
    apps = {"calculator": "calc.exe", "notepad": "notepad.exe", "paint": "mspaint.exe"}
    for app, path in apps.items():
        if app in command:
            speak(f"Opening {app}")
            os.startfile(f"C:\\Windows\\System32\\{path}")
            return

def closeApp(command):
    apps = {"calculator": "calc.exe", "notepad": "notepad.exe", "paint": "mspaint.exe"}
    for app, process in apps.items():
        if app in command:
            speak(f"Closing {app}")
            os.system(f"taskkill /f /im {process}")
            return

# Check system conditions
def condition():
    usage = str(psutil.cpu_percent())
    speak(f"CPU is at {usage} percent")
    battery = psutil.sensors_battery()
    percentage = battery.percent
    speak(f"Battery is at {percentage} percent")

    if percentage >= 80:
        speak("Battery level is sufficient")
    elif 40 <= percentage <= 75:
        speak("Consider charging the battery")
    else:
        speak("Battery is low, please charge")

# Load model, tokenizer, and label encoder
def load_chat_model():
    model = load_model("chat_model.h5")

    with open("tokenizer.pkl", "rb") as f:
        tokenizer = pickle.load(f)

    with open("label_encoder.pkl", "rb") as encoder_file:
        label_encoder = pickle.load(encoder_file)

    return model, tokenizer, label_encoder

# Function to handle WikiHow and GPT fallback
def search_with_fallback(query):
    try:
        max_results = 1
        how_to = search_wikihow(query, max_results)
        if len(how_to) > 0:
            response = how_to[0].summary
            print(f"WikiHow output: {response}")
            speak(response)
            return response
    except Exception as e:
        print("WikiHow search failed. Falling back to GPT.")
        gpt_response = gpt_model(query, max_length=50, num_return_sequences=1)
        response = gpt_response[0]['generated_text']
        print(f"GPT output: {response}")
        speak(response)
        return response
    
    
# Function to get the current system volume
def get_system_volume():
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = interface.QueryInterface(IAudioEndpointVolume)
    current_volume = volume.GetMasterVolumeLevelScalar() * 100  # Convert to percentage
    return current_volume

# Function to set the system volume
def set_system_volume(volume_percentage):
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = interface.QueryInterface(IAudioEndpointVolume)
    volume.SetMasterVolumeLevelScalar(volume_percentage / 100, None)

# Function to adjust the system volume by a percentage
def adjust_volume_by_percentage(change_percentage):
    current_volume = get_system_volume()
    new_volume = max(0, min(100, current_volume + change_percentage))  # Clamp between 0 and 100
    set_system_volume(new_volume)
    return new_volume

if __name__ == "__main__":
    wishMe()
    model, tokenizer, label_encoder = load_chat_model()

    while True:
        query = command().lower()

        # Skip empty query or "None" returned
        if query == "none" or query.strip() == "":
            print("No input detected. Please try again.")
            continue

        # Print user input
        print(f"User input: {query}")

        # Standardize misinterpreted speech input
        query = standardize_query(query)

        # Social media commands
        if "facebook" in query or "discord" in query or "whatsapp" in query or "instagram" in query:
            social_media(query)
        # University schedule
        elif "university time table" in query or "schedule" in query:
            schedule()
        # Volume control
        elif "volume up" in query:
            pyautogui.press("volumeup")
        elif "volume down" in query:
            pyautogui.press("volumedown")
        elif "volume mute" in query:
            pyautogui.press("volumemute")
        # Open and close apps
        elif "open" in query:
            openApp(query)
        elif "close" in query:
            closeApp(query)
        # System condition
        elif "system condition" in query:
            condition()
        # Exit
        elif "exit" in query:
            sys.exit()

        # WikiHow and GPT fallback logic
        elif "what is" in query or "how to" in query:
            search_with_fallback(query)
        else:
            # Default chatbot logic
            padded_sequences = pad_sequences(tokenizer.texts_to_sequences([query]), maxlen=20, truncating='post')
            result = model.predict(padded_sequences)
            confidence = np.max(result)
            tag = label_encoder.inverse_transform([np.argmax(result)])[0]

            if confidence < 0.6:
                response_text = "I'm sorry, I didn't understand that. Let me check that for you."
                print(f"Bot output: {response_text}")
                speak(response_text)
            else:
                for intent in data['intents']:
                    if intent['tag'] == tag:
                        response_text = np.random.choice(intent['responses'])
                        print(f"Bot output: {response_text}")
                        speak(response_text)
