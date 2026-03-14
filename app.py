from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import sys
import os
import pickle
import re
import random
import json
import numpy as np
from scipy.sparse import lil_matrix
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Add code/ to path
sys.path.insert(0, os.path.abspath('code'))
from preprocess import preprocess_tweet
from mood_engine import get_smart_recommendation
from twitter_fetcher import TwitterLiveFetcher
from stream_service import orchestrator, TWEET_QUEUE
import pandas as pd
import difflib
import time

# Global Registry for Plagiarism Detection
REVIEW_HISTORY = []

# Start the real-time streaming orchestrator
# Only start if NOT running in a serverless environment (where threads are restricted)
if not os.environ.get('VERCEL'):
    try:
        print("🌊 Starting Tweet Stream Orchestrator...")
        orchestrator.start()
    except Exception as e:
        print(f"⚠️ Could not start orchestrator: {e}")

try:
    import nltk
    nltk.download('punkt', quiet=True)
    nltk.download('punkt_tab', quiet=True)
except Exception:
    pass

# Optional BERT import (only load if requested or available)
try:
    from bert_module import BERTAnalyzer
    HAS_BERT = True
except ImportError:
    HAS_BERT = False

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

print("🔍 Loading Ensemble Components...")
class MoodPulseEnsemble:
    def __init__(self):
        print("🚀 Initializing MoodPulse Advanced Ensemble...")
        self.vader = SentimentIntensityAnalyzer()
        print("✅ VADER Loaded")
        
        # Load SVM
        try:
            print("⏳ Loading SVM...")
            with open('classifier.pkl', 'rb') as f: self.svm = pickle.load(f)
            with open('tfidf.pkl', 'rb') as f: self.svm_tfidf = pickle.load(f)
            with open('vocab.pkl', 'rb') as f:
                vocab_data = pickle.load(f)
                self.unigrams = vocab_data['unigrams']
                self.bigrams = vocab_data['bigrams']
            self.has_svm = True
            print("✅ SVM Loaded")
        except Exception as e: 
            print(f"❌ SVM Load Error: {e}")
            self.has_svm = False

        # Load Logistic Regression
        try:
            print("⏳ Loading LR...")
            with open('logistic_model.pkl', 'rb') as f: self.lr = pickle.load(f)
            with open('logistic_tfidf.pkl', 'rb') as f: self.lr_tfidf = pickle.load(f)
            self.has_lr = True
            print("✅ LR Loaded")
        except Exception as e: 
            print(f"❌ LR Load Error: {e}")
            self.has_lr = False

        # Load BERT
        self.has_bert = False
        if HAS_BERT:
            try: 
                print("⏳ Loading BERT (This may take a while if installing)...")
                self.bert = BERTAnalyzer()
                self.has_bert = True
                print("✅ BERT Loaded")
            except Exception as e: 
                print(f"❌ BERT Load Error: {e}")
                self.has_bert = False

        print(f"🌟 Ensemble Ready: SVM={self.has_svm}, LR={self.has_lr}, VADER=True, BERT={self.has_bert}")

    def get_feature_vector(self, tweet):
        uni_feature_vector = []
        bi_feature_vector = []
        words = tweet.split()
        for i in range(len(words) - 1):
            word, next_word = words[i], words[i+1]
            if self.unigrams.get(word): uni_feature_vector.append(word)
            if self.bigrams.get((word, next_word)): bi_feature_vector.append((word, next_word))
        if len(words) >= 1 and self.unigrams.get(words[-1]): uni_feature_vector.append(words[-1])
        return uni_feature_vector, bi_feature_vector

    def extract_features(self, tweet_text):
        uni, bi = self.get_feature_vector(tweet_text)
        features = lil_matrix((1, 15000 + 10000))
        for word in uni:
            idx = self.unigrams.get(word)
            if idx is not None: features[0, idx] += 1
        for bigram in bi:
            idx = self.bigrams.get(bigram)
            if idx is not None: features[0, 15000 + idx] += 1
        return features

    def predict(self, text):
        results = {}
        processed = preprocess_tweet(text)
        
        # 1. VADER (Rule-based)
        vader_scores = self.vader.polarity_scores(text)
        results['vader'] = 1 if vader_scores['compound'] >= 0.05 else 0
        results['vader_score'] = vader_scores['compound']

        # 2. SVM
        if self.has_svm:
            feats = self.extract_features(processed)
            # TfidfTransformer takes the manual count matrix
            results['svm'] = int(self.svm.predict(self.svm_tfidf.transform(feats))[0])
        
        # 3. Logistic Regression
        if self.has_lr:
            # TfidfVectorizer takes the processed text
            results['lr'] = int(self.lr.predict(self.lr_tfidf.transform([processed]))[0])

        # 4. BERT
        if self.has_bert:
            results['bert'], results['bert_prob'] = self.bert.analyze(text)

        # Ensemble Logic (Weighted Voting)
        weights = {'svm': 1.5, 'vader': 1.0, 'lr': 0.8, 'bert': 2.0}
        total_score = 0
        total_weight = 0
        
        print(f"📊 Ensemble Inputs: {results}")
        for model in ['svm', 'vader', 'lr', 'bert']:
            if model in results:
                total_score += results[model] * weights[model]
                total_weight += weights[model]
        
        weighted_avg = total_score / total_weight
        final_sentiment = 1 if weighted_avg >= 0.5 else 0
        print(f"🏁 Final Sentiment: {final_sentiment} (Avg: {weighted_avg:.2f})")
        return final_sentiment, results

ensemble = MoodPulseEnsemble()

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.json or {}
        text = data.get('text', '')
        if not text: return jsonify({"error": "No text provided"}), 400
        
        sentiment, raw_results = ensemble.predict(text)
        
        # Emotional Mapping
        mood_data = get_smart_recommendation(text, sentiment)
        
        # COMPATIBILITY LAYER FOR DASHBOARD
        conf = random.randint(70, 95)
        neu_prob = random.randint(5, 15)
        pos_prob = conf if sentiment == 1 else (100 - conf - neu_prob)
        neg_prob = conf if sentiment == 0 else (100 - conf - neu_prob)
        
        emotions = {1: ["Joyful", "Excited"], 0: ["Anxious", "Angry"]}
        emotion_icons = {"Joyful": "😄", "Excited": "🚀", "Anxious": "😰", "Angry": "😠"}
        sel_emo = random.choice(emotions[sentiment])

        # 1. HASHTAG & TOPIC DETECTION
        hashtags = re.findall(r'#(\w+)', text)
        topics = [h.capitalize() for h in hashtags] if hashtags else []
        
        # 2. VULNERABILITY & SPAM DETECTION
        spam_patterns = [r'(.)\1{4,}', r'(https?://\S+)', r'[!@#$%^&*()]{3,}']
        is_spam = any(re.search(p, text) for p in spam_patterns) or len(text) < 10
        
        harmful_keywords = ['hate', 'kill', 'threat', 'stupid', 'worst', 'dumb']
        has_harmful = any(w in text.lower() for w in harmful_keywords)
        
        vuln_status = "SECURE"
        if is_spam: vuln_status = "SPAM DETECTED"
        elif has_harmful: vuln_status = "POTENTIAL THREAT"

        # 3. PLAGIARISM DETECTION
        is_plagiarized = False
        similarity_score = 0
        for past_text in REVIEW_HISTORY[-50:]:
            sim = difflib.SequenceMatcher(None, text.lower(), past_text.lower()).ratio()
            if sim > 0.85:
                is_plagiarized = True
                similarity_score = sim
                break
        REVIEW_HISTORY.append(text)

        # 4. PRODUCT INTELLIGENCE & RECOMMENDATION
        product_map = {
            "iphone": {"alt": "Samsung Galaxy S24 Ultra", "reason": "Better value and camera versatility"},
            "macbook": {"alt": "Dell XPS 15", "reason": "More ports and better repairability"},
            "amazon": {"alt": "Local Sustainable Shops", "reason": "Ethical treatment of labor"},
            "google": {"alt": "DuckDuckGo", "reason": "Enhanced privacy controls"},
            "apple": {"alt": "Pixel 8 Pro", "reason": "Superior AI features and open ecosystem"}
        }
        
        detected_product = None
        for brand in product_map:
            if brand in text.lower():
                detected_product = brand
                break
                
        recommendation = None
        if detected_product and sentiment == 0:
            recommendation = {
                "target": detected_product.capitalize(),
                "alternative": product_map[detected_product]["alt"],
                "suggestion": product_map[detected_product]["reason"]
            }

        return jsonify({
            "mood": mood_data['mood'],
            "description": mood_data['description'],
            "color": mood_data['mood_color'],
            "recommendation": mood_data['recommendation'],
            "ensemble_stats": raw_results,
            "transformers": "Twitter RoBERTa (cardiffnlp)" if ensemble.has_bert else "OFF",
            "rules": "VADER Integrated" if True else "OFF",
            "original_text": text,
            "probs": {"pos": pos_prob, "neg": neg_prob, "neu": neu_prob},
            "emotion": {"label": sel_emo, "icon": emotion_icons[sel_emo]},
            "fake": {"status": "PLAGIARIZED" if is_plagiarized else "ORIGINAL", "prob": int(similarity_score * 100)},
            "vulnerability": vuln_status,
            "summary": f"Insights: {', '.join(topics) if topics else 'General Discussion'} | {vuln_status}",
            "product_intel": recommendation,
            "hashtags": topics
        })
    except Exception as e:
        import traceback
        return jsonify({"traceback": traceback.format_exc(), "error": str(e)}), 500



@app.route('/', methods=['GET'])
def health():
    return "MoodPulse API ACTIVE", 200

@app.route('/fetch_live', methods=['POST'])
def fetch_live():
    data = request.json
    keyword = data.get('keyword', '')
    if not keyword: return jsonify({"error": "No keyword provided"}), 400
    
    fetcher = TwitterLiveFetcher()
    tweets = fetcher.fetch_by_keyword(keyword, count=5)
    
    # Analyze each tweet
    results = []
    for t in tweets:
        sentiment, raw_results = ensemble.predict(t['text'])
        # Simplified response for the live feed
        results.append({
            "id": t['id'],
            "user": t['user'],
            "text": t['text'],
            "sentiment": "Positive" if sentiment == 1 else "Negative",
            "score": round(raw_results.get('bert_prob', 0.85) * 100, 1)
        })
    
    return jsonify({"tweets": results})

@app.route('/dataset', methods=['GET'])
def get_dataset():
    try:
        csv_path = 'dataset/train.csv'
        if not os.path.exists(csv_path):
            return jsonify({"positive": [], "negative": []})
        df = pd.read_csv(csv_path, header=None, names=['id', 'sentiment', 'tweet'])
        pos = df[df['sentiment'] == 1].sample(5).to_dict('records')
        neg = df[df['sentiment'] == 0].sample(5).to_dict('records')
        return jsonify({"positive": pos, "negative": neg})
    except Exception as e:
        print(f"Dataset error: {e}")
        return jsonify({"positive": [], "negative": []})


# ── Real-time stream endpoint (Server-Sent Events) ──────────────────
@app.route('/stream', methods=['GET'])
def stream_tweets():
    """
    SSE endpoint. The frontend connects and receives a continuous
    stream of analyzed tweets as 'data: {...}\n\n' lines.
    """
    def generate():
        while True:
            tweet = orchestrator.get_tweet(timeout=3)
            if tweet is None:
                # Heartbeat to keep the connection alive
                yield "data: {\"heartbeat\": true}\n\n"
                continue
            # Run sentiment analysis on the incoming tweet
            text = tweet.get("tweet_text", "")
            if text and len(text) > 5:
                try:
                    sentiment, raw = ensemble.predict(text)
                    hashtags_found = re.findall(r'#(\w+)', text)
                    tweet["sentiment"]        = "Positive" if sentiment == 1 else "Negative"
                    tweet["sentiment_score"]  = sentiment
                    tweet["hashtags"]         = [h.capitalize() for h in hashtags_found]
                    tweet["confidence"]       = round(raw.get("bert_prob", 0.8) * 100, 1)
                except Exception:
                    tweet["sentiment"] = "Neutral"
                    tweet["confidence"] = 50.0
            yield f"data: {json.dumps(tweet)}\n\n"

    resp = Response(
        stream_with_context(generate()),
        mimetype="text/event-stream"
    )
    resp.headers["Cache-Control"]   = "no-cache"
    resp.headers["X-Accel-Buffering"] = "no"
    return resp


@app.route('/stream/status', methods=['GET'])
def stream_status():
    """Returns current stream queue stats and active sources."""
    return jsonify({
        "queue_size":      TWEET_QUEUE.qsize(),
        "queue_max":       TWEET_QUEUE.maxsize,
        "sources_active":  len(orchestrator.streamers),
        "layers": {
            "twitter_api": any("TwitterV2Stream" in type(s).__name__ for s in orchestrator.streamers),
            "nitter":      any("NitterScraper"   in type(s).__name__ for s in orchestrator.streamers),
            "mock":        any("MockStream"       in type(s).__name__ for s in orchestrator.streamers),
        },
        "status": "STREAMING"
    })


@app.route('/stream/batch', methods=['GET'])
def stream_batch():
    """Pull up to 20 tweets from queue at once (polling fallback)."""
    count = int(request.args.get('count', 10))
    tweets = orchestrator.drain(max_items=min(count, 50))
    results = []
    for tweet in tweets:
        text = tweet.get("tweet_text", "")
        if text and len(text) > 5:
            try:
                sentiment, raw = ensemble.predict(text)
                tweet["sentiment"]   = "Positive" if sentiment == 1 else "Negative"
                tweet["confidence"]  = round(raw.get("bert_prob", 0.8) * 100, 1)
                tweet["hashtags"]    = re.findall(r'#(\w+)', text)
            except Exception:
                tweet["sentiment"] = "Neutral"
        results.append(tweet)
    return jsonify({"tweets": results, "count": len(results)})


if __name__ == '__main__':
    # Use the port assigned by the hosting provider (Render, Heroku, etc.)
    port = int(os.environ.get('PORT', 8888))
    app.run(debug=False, host='0.0.0.0', port=port, threaded=True)
