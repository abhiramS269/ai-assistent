import os
import json
import pickle
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Embedding, GlobalAveragePooling1D, Input
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from sklearn.preprocessing import LabelEncoder
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.model_selection import train_test_split

# Load intents data
with open("intents.json") as file:
    data = json.load(file)

training_sentences = []
training_labels = []
labels = []
responses = []

# Prepare the data
for intent in data['intents']:
    for pattern in intent['patterns']:
        training_sentences.append(pattern)
        training_labels.append(intent['tag'])
    responses.append(intent['responses'])
    if intent['tag'] not in labels:
        labels.append(intent['tag'])

number_of_classes = len(labels)

# Encode the labels
label_encoder = LabelEncoder()
label_encoder.fit(training_labels)
training_labels = label_encoder.transform(training_labels)

# Tokenization and padding
vocab_size = 1000
max_len = 20
ovv_token = "<OOV>"
embedding_dim = 16

tokenizer = Tokenizer(num_words=vocab_size, oov_token=ovv_token)
tokenizer.fit_on_texts(training_sentences)
word_index = tokenizer.word_index
sequences = tokenizer.texts_to_sequences(training_sentences)
padded_sequences = pad_sequences(sequences, truncating='post', maxlen=max_len)

# Train/test split
X_train, X_val, y_train, y_val = train_test_split(padded_sequences, training_labels, test_size=0.2, random_state=42)

# Build the model
model = Sequential()
model.add(Input(shape=(max_len,)))  # Define input shape explicitly
model.add(Embedding(vocab_size, embedding_dim))
model.add(GlobalAveragePooling1D())
model.add(Dense(16, activation="relu"))
model.add(Dense(16, activation="relu"))
model.add(Dense(number_of_classes, activation="softmax"))

model.compile(loss='sparse_categorical_crossentropy', optimizer="adam", metrics=["accuracy"])

# Early stopping callback with increased patience
early_stopping = EarlyStopping(monitor='val_loss', patience=20, restore_best_weights=True)

# Train the model
model.fit(X_train, np.array(y_train), epochs=1000, validation_data=(X_val, np.array(y_val)), callbacks=[early_stopping])

# Save the model and other artifacts
model.save("chat_model.h5")

with open("tokenizer.pkl", "wb") as f:
    pickle.dump(tokenizer, f, protocol=pickle.HIGHEST_PROTOCOL)

with open("label_encoder.pkl", "wb") as encoder_file:
    pickle.dump(label_encoder, encoder_file, protocol=pickle.HIGHEST_PROTOCOL)
    
def initialize_training_data():
    if not os.path.exists("training_data.pkl"):
        # Initialize with empty data
        training_data = {'patterns': [], 'labels': []}
        with open("training_data.pkl", "wb") as f:
            pickle.dump(training_data, f)

# Call this function before training
initialize_training_data()

print("Model training complete and saved.")
