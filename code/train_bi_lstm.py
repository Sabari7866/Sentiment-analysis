import numpy as np
import sys
import pickle
from keras.models import Sequential, load_model
from keras.layers import Dense, Dropout, Activation, Embedding, LSTM, Bidirectional
from keras.callbacks import ModelCheckpoint, ReduceLROnPlateau
from keras.preprocessing.sequence import pad_sequences
import os

# Set relative paths to project root
sys.path.insert(0, os.path.abspath('code'))
import utils

# Performs classification using Bi-LSTM network.

TRAIN_PROCESSED_FILE = 'dataset/train-processed-stemmed.csv'
VOCAB_FILE = 'vocab.pkl'
MODEL_PATH = 'bi_lstm_model.h5'
dim = 100 # Reduced for faster training if no GPU
max_length = 40
vocab_size = 20000

def load_vocab():
    with open(VOCAB_FILE, 'rb') as f:
        data = pickle.load(f)
    # Map top unigrams to indices
    unigrams = data['unigrams']
    vocab = {word: i + 1 for i, (word, _) in enumerate(list(unigrams.items())[:vocab_size])}
    return vocab

def get_feature_vector(tweet, vocab):
    words = tweet.split()
    feature_vector = []
    for word in words:
        if vocab.get(word):
            feature_vector.append(vocab.get(word))
    return feature_vector

def process_data(csv_file, vocab):
    import csv
    tweets = []
    labels = []
    print('Generating feature vectors for Bi-LSTM')
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)
        for i, row in enumerate(rows):
            tweet_id, sentiment, tweet = row
            fv = get_feature_vector(tweet, vocab)
            tweets.append(fv)
            labels.append(int(sentiment))
            if i % 1000 == 0: utils.write_status(i, len(rows))
    print('\n')
    return pad_sequences(tweets, maxlen=max_length, padding='post'), np.array(labels)

def build_bilstm_model():
    model = Sequential()
    model.add(Embedding(vocab_size + 1, dim, input_length=max_length))
    model.add(Dropout(0.4))
    model.add(Bidirectional(LSTM(128)))
    model.add(Dense(64, activation='relu'))
    model.add(Dropout(0.5))
    model.add(Dense(1, activation='sigmoid'))
    model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
    return model

if __name__ == '__main__':
    vocab = load_vocab()
    X, y = process_data(TRAIN_PROCESSED_FILE, vocab)
    
    # Shuffle
    indices = np.arange(X.shape[0])
    np.random.shuffle(indices)
    X, y = X[indices], y[indices]
    
    # Train test split (small sample for speed if needed, but here full)
    split = int(0.9 * len(X))
    X_train, X_val = X[:split], X[split:]
    y_train, y_val = y[:split], y[split:]
    
    model = build_bilstm_model()
    print(model.summary())
    
    checkpoint = ModelCheckpoint(MODEL_PATH, monitor='val_accuracy', save_best_only=True, mode='max')
    reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=1)
    
    # limit epochs for demonstration
    model.fit(X_train, y_train, batch_size=256, epochs=3, validation_data=(X_val, y_val), callbacks=[checkpoint, reduce_lr])
    print(f"Bi-LSTM Model saved to {MODEL_PATH}")
