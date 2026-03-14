import re
import tweepy
from bs4 import BeautifulSoup
import os

class TwitterLiveFetcher:
    def __init__(self, keys_content=None):
        self.api = None
        self.authenticated = False
        self.keys = {}
        
        if keys_content:
            self._auth_from_string(keys_content)
        elif os.path.exists('keys.txt'):
            self._auth_from_file('keys.txt')

    def _auth_from_file(self, filename):
        try:
            with open(filename, 'r') as f:
                lines = [l.strip() for l in f.readlines() if l.strip()]
                if len(lines) >= 4:
                    self.keys = {
                        'ck': lines[0],
                        'cs': lines[1],
                        'at': lines[2],
                        'as': lines[3]
                    }
                    self._authenticate()
        except Exception as e:
            print(f"Auth File Error: {e}")

    def _auth_from_string(self, content):
        lines = [l.strip() for l in content.split('\n') if l.strip()]
        if len(lines) >= 4:
            self.keys = {
                'ck': lines[0],
                'cs': lines[1],
                'at': lines[2],
                'as': lines[3]
            }
            self._authenticate()

    def _authenticate(self):
        try:
            auth = tweepy.OAuthHandler(self.keys['ck'], self.keys['cs'])
            auth.set_access_token(self.keys['at'], self.keys['as'])
            self.api = tweepy.API(auth, wait_on_rate_limit=True)
            self.authenticated = True
        except Exception as e:
            print(f"Tweepy Auth Error: {e}")
            self.authenticated = False

    def tweet_cleaner(self, text):
        """ Cleans tweet text of URLs, mentions, hashtags, and special characters. """
        try:
            # Remove HTML entities
            soup = BeautifulSoup(text, 'lxml')
            text = soup.get_text()
        except:
            pass
            
        # Remove mentions, URLs, and hashtags
        text = re.sub(r'@[\w_]+', '', text) # Mentions
        text = re.sub(r'https?://[A-Za-z0-9./]+', '', text) # URLs
        text = re.sub(r'\#+[\w_]+[\w\'_\-]*[\w_]+', '', text) # Hashtags
        
        # Remove special characters but keep punctuation for sentiment
        text = re.sub(r"[^a-zA-Z0-9\s.,!?:']", "", text)
        
        return " ".join(text.split()).strip()

    def fetch_by_keyword(self, keyword, count=10):
        if not self.authenticated:
            return self._mock_tweets(keyword, count)
            
        try:
            tweets = []
            results = self.api.search_tweets(q=keyword, count=count, lang='en', tweet_mode='extended')
            for t in results:
                full_text = t.full_text if hasattr(t, 'full_text') else t.text
                if 'RT @' not in full_text:
                    clean = self.tweet_cleaner(full_text)
                    if clean:
                        tweets.append({
                            'id': t.id_str,
                            'text': clean,
                            'original': full_text,
                            'user': t.user.screen_name,
                            'created_at': str(t.created_at)
                        })
            return tweets
        except Exception as e:
            print(f"Fetch Error: {e}")
            return self._mock_tweets(keyword, count)

    def _mock_tweets(self, keyword, count):
        """ Fallback mock tweets if API is not available/configured """
        print(f"⚠️ Using Mock Tweets for '{keyword}' (Twitter API not configured)")
        mocks = [
            f"Wow, I just tried {keyword} and it's absolutely life changing! #amazing",
            f"The new update for {keyword} is incredibly buggy and slow. Very disappointed.",
            f"Does anyone know if {keyword} supports dark mode yet? Asking for a friend.",
            f"I've been using {keyword} for a week now and I can't imagine my life without it.",
            f"Honestly, {keyword} is overrated. There are much better alternatives available.",
            f"Just saw the news about {keyword}. This is going to be huge for the industry!",
            f"Is it just me or is {keyword} getting more expensive every month?",
            f"Shoutout to the {keyword} team for the amazing customer support today!",
            f"Can't believe how many people are still sleeping on {keyword}. Check it out!",
            f"The design of {keyword} is so sleek and modern. I love the minimalist aesthetic."
        ]
        import random
        selected = random.sample(mocks, min(count, len(mocks)))
        return [{'id': str(random.randint(1000, 9999)), 'text': self.tweet_cleaner(m), 'original': m, 'user': 'demo_user', 'created_at': '2024-03-14'} for m in selected]
