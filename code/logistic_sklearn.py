from sklearn.linear_model import LogisticRegression
import pickle
import utils
import numpy as np
from scipy.sparse import lil_matrix
from sklearn.feature_extraction.text import TfidfTransformer
import sys

# Performs classification using Logistic Regression (Sklearn version for API compatibility).

FREQ_DIST_FILE = 'dataset/train-processed-freqdist.pkl'
BI_FREQ_DIST_FILE = 'dataset/train-processed-freqdist-bi.pkl'
TRAIN_PROCESSED_FILE = 'dataset/train-processed-stemmed.csv'
TRAIN = True
UNIGRAM_SIZE = 15000
BIGRAM_SIZE = 10000
VOCAB_SIZE = UNIGRAM_SIZE + BIGRAM_SIZE
FEAT_TYPE = 'frequency'

def get_feature_vector(tweet):
    uni_feature_vector = []
    bi_feature_vector = []
    words = tweet.split()
    for i in range(len(words) - 1):
        word = words[i]
        next_word = words[i + 1]
        if unigrams.get(word):
            uni_feature_vector.append(word)
        if bigrams.get((word, next_word)):
            bi_feature_vector.append((word, next_word))
    if len(words) >= 1:
        if unigrams.get(words[-1]):
            uni_feature_vector.append(words[-1])
    return uni_feature_vector, bi_feature_vector

def extract_features(tweets, batch_size=1000, test_file=False):
    num_batches = int(np.ceil(len(tweets) / float(batch_size)))
    for i in range(num_batches):
        batch = tweets[i * batch_size: (i + 1) * batch_size]
        features = lil_matrix((len(batch), VOCAB_SIZE))
        labels = np.zeros(len(batch))
        for j, tweet in enumerate(batch):
            tweet_words = tweet[2][0]
            tweet_bigrams = tweet[2][1]
            labels[j] = tweet[1]
            for word in tweet_words:
                idx = unigrams.get(word)
                if idx is not None: features[j, idx] += 1
            for bigram in tweet_bigrams:
                idx = bigrams.get(bigram)
                if idx is not None: features[j, UNIGRAM_SIZE + idx] += 1
        yield features, labels

def process_tweets(csv_file):
    tweets = []
    print('Generating feature vectors')
    import csv
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)
        for i, row in enumerate(rows):
            tweet_id, sentiment, tweet = row
            feature_vector = get_feature_vector(tweet)
            tweets.append((tweet_id, int(sentiment), feature_vector))
            utils.write_status(i + 1, len(rows))
    print('\n')
    return tweets

if __name__ == '__main__':
    np.random.seed(1337)
    unigrams = utils.top_n_words(FREQ_DIST_FILE, UNIGRAM_SIZE)
    bigrams = utils.top_n_bigrams(BI_FREQ_DIST_FILE, BIGRAM_SIZE)
    
    tweets = process_tweets(TRAIN_PROCESSED_FILE)
    train_tweets, val_tweets = utils.split_data(tweets)
    
    print('Extracting features...')
    # Use full data for training in this script
    X_train, y_train = next(extract_features(train_tweets, batch_size=len(train_tweets)))
    X_val, y_val = next(extract_features(val_tweets, batch_size=len(val_tweets)))
    
    tfidf = TfidfTransformer(smooth_idf=True, sublinear_tf=True, use_idf=True)
    X_train = tfidf.fit_transform(X_train)
    X_val = tfidf.transform(X_val)
    
    print('Training Logistic Regression...')
    clf = LogisticRegression(max_iter=1000)
    clf.fit(X_train, y_train)
    
    print('Validation Accuracy:', clf.score(X_val, y_val))
    
    with open('logistic_model.pkl', 'wb') as f:
        pickle.dump(clf, f)
    with open('logistic_tfidf.pkl', 'wb') as f:
        pickle.dump(tfidf, f)
    print('Saved Logistic Regression model.')
