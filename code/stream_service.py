"""
MoodPulse AI - Real-Time Tweet Stream Service
==============================================
3-Layer streaming architecture:
  Layer 1: Twitter v2 Filtered Stream API (requires valid Bearer Token in keys.txt)
  Layer 2: Nitter instance scraping  (free, no auth required)
  Layer 3: High-fidelity mock stream  (always available fallback)
"""

import re
import time
import json
import random
import threading
import datetime
import os
import requests
from queue import Queue, Empty


TWEET_QUEUE = Queue(maxsize=500)


def _build_tweet(tweet_id, text, author, lang="en", source="mock"):
    return {
        "tweet_id":   str(tweet_id),
        "tweet_text": text,
        "author_id":  str(author),
        "created_at": datetime.datetime.utcnow().isoformat() + "Z",
        "language":   lang,
        "source":     source,        
        "public_metrics": {
            "like_count":    random.randint(0, 500),
            "retweet_count": random.randint(0, 200),
            "reply_count":   random.randint(0, 80),
        }
    }


# ═══════════════════════════════════════════════════════
# LAYER 1 — Twitter v2 Filtered Stream (real API)
# ═══════════════════════════════════════════════════════
class TwitterV2Stream:
    STREAM_URL   = "https://api.twitter.com/2/tweets/search/stream"
    RULES_URL    = "https://api.twitter.com/2/tweets/search/stream/rules"
    TWEET_FIELDS = "tweet.fields=author_id,created_at,lang,public_metrics,text"

    def __init__(self, bearer_token):
        self.bearer = bearer_token
        self.headers = {"Authorization": f"Bearer {bearer_token}"}
        self.active = False

    def _ensure_rules(self):
        """Set a catch-all rule to sample the global stream."""
        # Delete existing rules
        resp = requests.get(self.RULES_URL, headers=self.headers)
        if resp.ok:
            data = resp.json().get("data", [])
            if data:
                ids = [r["id"] for r in data]
                requests.post(self.RULES_URL, headers=self.headers,
                              json={"delete": {"ids": ids}})
        # Add broad sampling rules (common English terms)
        sample_rules = [
            {"value": "lang:en -is:retweet", "tag": "global_sample"},
        ]
        requests.post(self.RULES_URL, headers=self.headers,
                      json={"add": sample_rules})

    def stream(self):
        self._ensure_rules()
        self.active = True
        url = f"{self.STREAM_URL}?{self.TWEET_FIELDS}"
        while self.active:
            try:
                with requests.get(url, headers=self.headers, stream=True, timeout=90) as r:
                    if r.status_code == 429:
                        print("⚠️ Twitter API rate limit. Waiting 60s...")
                        time.sleep(60)
                        continue
                    for line in r.iter_lines():
                        if not self.active:
                            break
                        if line:
                            try:
                                payload = json.loads(line)
                                t = payload.get("data", {})
                                if t:
                                    tweet = _build_tweet(
                                        tweet_id=t.get("id", ""),
                                        text=t.get("text", ""),
                                        author=t.get("author_id", ""),
                                        lang=t.get("lang", "en"),
                                        source="twitter_api"
                                    )
                                    tweet["public_metrics"] = t.get("public_metrics", tweet["public_metrics"])
                                    tweet["created_at"]     = t.get("created_at", tweet["created_at"])
                                    if not TWEET_QUEUE.full():
                                        TWEET_QUEUE.put(tweet)
                            except json.JSONDecodeError:
                                pass
            except Exception as e:
                print(f"Twitter stream error: {e}. Reconnecting in 5s...")
                time.sleep(5)

    def stop(self):
        self.active = False


# ═══════════════════════════════════════════════════════
# LAYER 2 — Nitter Scraping (free, no auth)
# ═══════════════════════════════════════════════════════
# Popular public topics to cycle through
NITTER_TOPICS = [
    "AI", "technology", "breaking", "news", "gaming",
    "sports", "music", "science", "startup", "coding"
]

NITTER_INSTANCES = [
    "https://nitter.privacydev.net",
    "https://nitter.poast.org",
    "https://nitter.cz",
]

class NitterScraper:
    def __init__(self, interval=8):
        self.interval = interval
        self.active   = False

    def _fetch_topic(self, base, topic):
        """Scrape latest tweets for a topic from a Nitter instance."""
        url = f"{base}/search?q={topic}&f=tweets"
        try:
            resp = requests.get(url, timeout=10, headers={
                "User-Agent": "Mozilla/5.0 (compatible; MoodPulseBot/1.0)"
            })
            if not resp.ok:
                return []
            # Basic regex extraction of tweet text from Nitter HTML
            texts = re.findall(r'<div class="tweet-content[^"]*"[^>]*>(.*?)</div>', resp.text, re.DOTALL)
            tweets = []
            for i, raw in enumerate(texts[:5]):
                clean = re.sub(r'<[^>]+>', '', raw).strip()
                clean = re.sub(r'\s+', ' ', clean)
                if clean and len(clean) > 10:
                    tweets.append(_build_tweet(
                        tweet_id=f"nitter_{int(time.time())}_{i}",
                        text=clean[:280],
                        author=f"nitter_user_{random.randint(1000, 9999)}",
                        source="nitter"
                    ))
            return tweets
        except Exception:
            return []

    def stream(self):
        self.active = True
        topic_idx   = 0
        instance_idx = 0

        while self.active:
            topic    = NITTER_TOPICS[topic_idx % len(NITTER_TOPICS)]
            instance = NITTER_INSTANCES[instance_idx % len(NITTER_INSTANCES)]
            tweets   = self._fetch_topic(instance, topic)

            if tweets:
                print(f"📡 Nitter scraped {len(tweets)} tweets for #{topic}")
            else:
                print(f"⚠️ Nitter {instance} unreachable, trying next...")
                instance_idx += 1

            for t in tweets:
                if not TWEET_QUEUE.full():
                    TWEET_QUEUE.put(t)

            topic_idx    += 1
            instance_idx += 1
            time.sleep(self.interval)

    def stop(self):
        self.active = False


# ═══════════════════════════════════════════════════════
# LAYER 3 — High-Fidelity Mock Stream (always available)
# ═══════════════════════════════════════════════════════
MOCK_TEMPLATES = [
    # Positive tech tweets
    "Just tried out the new {product} feature and it's mind-blowing! 🚀 #tech #AI",
    "{company}'s latest product launch exceeded all expectations. 10/10 would recommend! ⭐",
    "The advancement in {topic} is truly remarkable. The future is now! 🌟",
    "Shoutout to everyone working on {topic}! You're changing the world 🙌 #innovation",
    "Just published my first {topic} project! Feeling proud and excited 😊 #coding",
    # Negative tweets
    "{company}'s new update broke everything. Terrible QA. Very disappointed 😤",
    "Why is {product} getting worse with every update? Used to love it. #disappointed",
    "The {topic} bubble is about to burst. This is getting out of hand 😒",
    "Another {company} failure. When will they learn to listen to users? #feedback",
    "Spent 3 hours on {product} support. Got nowhere. Switching to a competitor. 😡",
    # Neutral informational
    "Article: New {topic} research published by MIT researchers. Link in bio 📰",
    "{company} announces Q4 earnings. Revenue up 12% year-over-year. 📈 #markets",
    "Anyone else noticing changes in {product} today? What do you think? 🤔",
    "Thread 🧵 on how {topic} is reshaping the industry (1/10) 👇",
    "Poll: What's your preferred {topic} tool? Reply below! 👇 #survey",
    # Hashtag-heavy tweets
    "{topic} is trending today! 🔥 #trending #{topic_tag} #viral",
    "Great discussion at the {topic} conference today! 💡 #innovation #future",
    "Learning {topic} changed my career. Here's how: #success #growth 🌱",
]

PRODUCTS  = ["ChatGPT", "iPhone 16", "Tesla Model 3", "Gemini AI", "GitHub Copilot", "YouTube"]
COMPANIES = ["Apple", "Google", "Microsoft", "Tesla", "Meta", "OpenAI", "Amazon"]
TOPICS    = ["AI", "machine learning", "blockchain", "quantum computing", "5G", "robotics", "Python"]
HANDLES   = ["@techguru", "@ai_enthusiast", "@dev_world", "@startup_life", "@coder99", "@sciencenerd"]


class MockStreamGenerator:
    def __init__(self, tps=1.0):
        """tps = tweets per second."""
        self.tps    = tps
        self.active = False
        self._id    = int(time.time() * 1000)

    def _next_tweet(self):
        template = random.choice(MOCK_TEMPLATES)
        product  = random.choice(PRODUCTS)
        company  = random.choice(COMPANIES)
        topic    = random.choice(TOPICS)
        text     = (
            template
            .replace("{product}", product)
            .replace("{company}", company)
            .replace("{topic}", topic)
            .replace("{topic_tag}", topic.replace(" ", ""))
        )
        # Occasionally add a handle mention
        if random.random() < 0.3:
            text = f"{random.choice(HANDLES)} {text}"
        self._id += random.randint(100, 999)
        return _build_tweet(
            tweet_id=self._id,
            text=text,
            author=random.randint(100000, 999999),
            lang=random.choice(["en"] * 8 + ["es", "fr"]),
            source="mock"
        )

    def stream(self):
        self.active = True
        delay = 1.0 / self.tps
        while self.active:
            tweet = self._next_tweet()
            if not TWEET_QUEUE.full():
                TWEET_QUEUE.put(tweet)
            time.sleep(delay + random.uniform(-0.2, 0.5))

    def stop(self):
        self.active = False


# ═══════════════════════════════════════════════════════
# MAIN ORCHESTRATOR
# ═══════════════════════════════════════════════════════
class TweetStreamOrchestrator:
    """
    Starts all available stream layers in background threads.
    Consumers read from TWEET_QUEUE.
    """

    def __init__(self):
        self.threads = []
        self.streamers = []

    def _load_bearer_token(self):
        keys_file = os.path.join(os.path.dirname(__file__), '..', 'keys.txt')
        try:
            with open(keys_file, 'r') as f:
                lines = [l.strip() for l in f if l.strip() and not l.startswith('#')]
            if len(lines) >= 5:          # Line 5 = bearer token (if provided)
                return lines[4]
        except Exception:
            pass
        return None

    def start(self):
        bearer = self._load_bearer_token()

        if bearer and len(bearer) > 20:
            # Layer 1: Real Twitter API
            print("🐦 Starting Twitter v2 Filtered Stream (real API)...")
            tw = TwitterV2Stream(bearer)
            self.streamers.append(tw)
            t = threading.Thread(target=tw.stream, daemon=True)
            t.start()
            self.threads.append(t)
        else:
            print("⚠️  No Bearer Token found — skipping Twitter v2 API stream.")

        # Layer 2: Nitter scraping
        print("🌐 Starting Nitter scraper (free public mirrors)...")
        nitter = NitterScraper(interval=10)
        self.streamers.append(nitter)
        t2 = threading.Thread(target=nitter.stream, daemon=True)
        t2.start()
        self.threads.append(t2)

        # Layer 3: Mock stream (always on)
        print("🎭 Starting mock stream (high-fidelity fallback)...")
        mock = MockStreamGenerator(tps=0.5)   # 1 tweet every ~2s
        self.streamers.append(mock)
        t3 = threading.Thread(target=mock.stream, daemon=True)
        t3.start()
        self.threads.append(t3)

        print(f"✅ Orchestrator running. Queue: {TWEET_QUEUE.qsize()} tweets")

    def stop(self):
        for s in self.streamers:
            s.stop()

    def get_tweet(self, timeout=2):
        """Blocking pop from the shared queue."""
        try:
            return TWEET_QUEUE.get(timeout=timeout)
        except Empty:
            return None

    def drain(self, max_items=20):
        """Non-blocking batch drain."""
        items = []
        while not TWEET_QUEUE.empty() and len(items) < max_items:
            try:
                items.append(TWEET_QUEUE.get_nowait())
            except Empty:
                break
        return items


# Global singleton
orchestrator = TweetStreamOrchestrator()
