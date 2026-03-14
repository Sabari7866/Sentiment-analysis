import re
import sys

from utils import write_status
from nltk.stem.porter import PorterStemmer

use_stemmer = True
porter_stemmer = PorterStemmer()


def preprocess_word(word):
    # Remove punctuation
    word = word.strip('\'"?!,.():;')
    # Convert more than 2 letter repetitions to 2 letter
    # funnnnny --> funny
    word = re.sub(r'(.)\1+', r'\1\1', word)
    # Remove - & '
    word = re.sub(r'(-|\')', '', word)
    return word


stop_words = {'a', 'an', 'the', 'is', 'are', 'was', 'were', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once'}

def is_valid_word(word):
    # Check if word begins with an alphabet (English or Tamil) and is not a common stop word
    # Tamil Unicode range: \u0b80-\u0bff
    return (re.search(r'^[a-zA-Z\u0b80-\u0bff]', word) is not None) and (word not in stop_words)





def handle_emojis(tweet):
    # Smile -- :), : ), :-), (:, ( :, (-:, :')
    tweet = re.sub(r'(:\s?\)|:-\)|\(\s?:|\(-:|:\'\))', ' EMO_POS ', tweet)
    # Laugh -- :D, : D, :-D, xD, x-D, XD, X-D
    tweet = re.sub(r'(:\s?D|:-D|x-?D|X-?D)', ' EMO_POS ', tweet)
    # Love -- <3, :*
    tweet = re.sub(r'(<3|:\*)', ' EMO_POS ', tweet)
    # Wink -- ;-), ;), ;-D, ;D, (;,  (-;
    tweet = re.sub(r'(;-?\)|;-?D|\(-?;)', ' EMO_POS ', tweet)
    # Sad -- :-(, : (, :(, ):, )-:
    tweet = re.sub(r'(:\s?\(|:-\(|\)\s?:|\)-:)', ' EMO_NEG ', tweet)
    # Cry -- :,(, :'(, :"(
    tweet = re.sub(r'(:,\(|:\'\(|:"\()', ' EMO_NEG ', tweet)
    return tweet


def preprocess_tweet(tweet):
    processed_tweet = []
    # Convert to lower case
    tweet = tweet.lower()
    # Replaces URLs with the word URL
    tweet = re.sub(r'((www\.[\S]+)|(https?://[\S]+))', ' URL ', tweet)
    # Replace @handle with the word USER_MENTION
    tweet = re.sub(r'@[\S]+', 'USER_MENTION', tweet)
    # Replaces #hashtag with hashtag
    tweet = re.sub(r'#(\S+)', r' \1 ', tweet)
    # Remove RT (retweet)
    tweet = re.sub(r'\brt\b', '', tweet)
    # Replace 2+ dots with space
    tweet = re.sub(r'\.{2,}', ' ', tweet)
    # Strip space, " and ' from tweet
    tweet = tweet.strip(' "\'')
    # Replace emojis with either EMO_POS or EMO_NEG
    tweet = handle_emojis(tweet)
    # Replace multiple spaces with a single space
    tweet = re.sub(r'\s+', ' ', tweet)
    words = tweet.split()

    for word in words:
        word = preprocess_word(word)
        if is_valid_word(word):
            if use_stemmer:
                word = str(porter_stemmer.stem(word))
            processed_tweet.append(word)

    return ' '.join(processed_tweet)


import csv as csv_lib

def preprocess_csv(csv_file_name, processed_file_name, test_file=False):
    save_to_file = open(processed_file_name, 'w', encoding='utf-8')

    with open(csv_file_name, 'r', encoding='utf-8') as csvfile:
        reader = csv_lib.reader(csvfile)
        rows = list(reader)
        total = len(rows)
        for i, row in enumerate(rows):
            if not row: continue
            tweet_id = row[0]
            if not test_file:
                positive = int(float(row[1])) # Handle potential float strings from pandas
                tweet = row[2]
            else:
                tweet = row[1]
            
            processed_tweet = preprocess_tweet(tweet)
            if not test_file:
                save_to_file.write('%s,%d,%s\n' %
                                   (tweet_id, positive, processed_tweet))
            else:
                save_to_file.write('%s,%s\n' %
                                   (tweet_id, processed_tweet))
            write_status(i + 1, total)
    save_to_file.close()
    print('\nSaved processed tweets to: %s' % processed_file_name)
    return processed_file_name


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python preprocess.py <raw-CSV>')
        exit()
    csv_file_name = sys.argv[1]
    if use_stemmer:
        processed_file_name = sys.argv[1][:-4] + '-processed-stemmed.csv'
    else:
        processed_file_name = sys.argv[1][:-4] + '-processed.csv'
    preprocess_csv(csv_file_name, processed_file_name, test_file=False)
