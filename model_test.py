import json
import pickle
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.sequence import pad_sequences
import numpy as np

# Load required files
with open("intents.json") as file:
    data = json.load(file)

model = load_model("chat_model.h5")

with open("tokenizer.pkl", "rb") as f:
    tokenizer = pickle.load(f)

with open("label_encoder.pkl", "rb") as encoder_file:
    label_encoder = pickle.load(encoder_file)

# Confidence threshold for predictions
CONFIDENCE_THRESHOLD = 0.6

# Chat loop
while True:
    input_text = input("Enter your command-> ").strip().lower()

    if input_text in ["exit", "quit"]:
        print("Exiting... Goodbye!")
        break

    padded_sequences = pad_sequences(tokenizer.texts_to_sequences([input_text]), maxlen=20, truncating='post')
    result = model.predict(padded_sequences)
    confidence = np.max(result)
    tag = label_encoder.inverse_transform([np.argmax(result)])[0]

    if confidence < CONFIDENCE_THRESHOLD:
        print("I'm sorry, I didn't understand that. Could you rephrase?")
    else:
        for intent in data['intents']:
            if intent['tag'] == tag:
                print(np.random.choice(intent['responses']))
