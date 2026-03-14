"""
MoodPulse Smart Recommendation Engine
======================================
Analyzes tweet content + sentiment to deliver:
  - Contextual article / video suggestions based on the tweet's TOPIC
  - Problem tweets  → solutions, guides, alternatives
  - Positive tweets → deeper engagement content, tutorials, related news
  - Fallback        → generic mood-based content
"""

import re
import random

# ─────────────────────────────────────────────────────────────────────────────
# TOPIC CONTENT DATABASE
# Structure: { topic_key: { "positive": [...], "negative": [...] } }
# Each item: { type, title, description, url, icon }
# ─────────────────────────────────────────────────────────────────────────────
TOPIC_CONTENT = {

    # ── AI / Machine Learning ───────────────────────────────────────
    "ai": {
        "positive": [
            {"type":"Tutorial","title":"Build your first AI model in 30 minutes","description":"A beginner-friendly guide to creating a machine learning project from scratch.","url":"https://www.youtube.com/watch?v=7eh4d6sabA0","icon":"🤖"},
            {"type":"Article","title":"Top 10 AI tools transforming 2024","description":"Explore the most powerful AI tools that are changing industries right now.","url":"https://www.technologyreview.com/topic/artificial-intelligence/","icon":"🚀"},
            {"type":"Course","title":"Free Generative AI course by Google","description":"Learn how LLMs work with Google's free certification course.","url":"https://grow.google/certificates/","icon":"🎓"},
        ],
        "negative": [
            {"type":"Solution","title":"AI replacing jobs? Here's how to adapt","description":"Practical guide on future-proofing your career in the age of AI automation.","url":"https://hbr.org/topic/subject/artificial-intelligence","icon":"🛡️"},
            {"type":"Article","title":"AI bias problems and how we fix them","description":"An in-depth look at algorithmic fairness and ethical AI development.","url":"https://www.technologyreview.com/topic/artificial-intelligence/","icon":"⚖️"},
            {"type":"Guide","title":"AI safety explained for everyone","description":"Simple breakdown of AI safety concerns and what researchers are doing about them.","url":"https://80000hours.org/problem-profiles/artificial-intelligence/","icon":"❓"},
        ]
    },

    # ── Technology / Gadgets ─────────────────────────────────────────
    "tech": {
        "positive": [
            {"type":"Review","title":"Best tech gadgets of 2024 reviewed","description":"Hands-on reviews of the most innovative gadgets and devices this year.","url":"https://www.theverge.com/tech","icon":"💻"},
            {"type":"Tutorial","title":"Hidden features in your phone you never knew","description":"Unlock the full potential of your smartphone with these expert tips.","url":"https://www.youtube.com/watch?v=rGk8I6kGU3E","icon":"📱"},
            {"type":"News","title":"Latest tech innovations this week","description":"Stay updated with cutting-edge technology news from around the world.","url":"https://techcrunch.com/","icon":"🔥"},
        ],
        "negative": [
            {"type":"Fix","title":"Common tech problems and instant fixes","description":"Troubleshooting guide for the most frustrating everyday tech issues.","url":"https://www.howtogeek.com/","icon":"🔧"},
            {"type":"Comparison","title":"Best budget alternatives to expensive gadgets","description":"Get the same performance at a fraction of the price. Comparison guide.","url":"https://www.rtings.com/","icon":"💰"},
            {"type":"Guide","title":"How to protect your privacy online","description":"Essential steps to secure your digital life from data breaches and surveillance.","url":"https://www.eff.org/pages/tools","icon":"🔒"},
        ]
    },

    # ── Apple / iPhone ───────────────────────────────────────────────
    "apple": {
        "positive": [
            {"type":"Tips","title":"Top 20 iPhone tips and tricks 2024","description":"Make the most of your iPhone with these incredible hidden features.","url":"https://www.youtube.com/watch?v=fxkBPLCghSQ","icon":"🍎"},
            {"type":"Guide","title":"Best apps for iPhone in 2024","description":"Curated list of must-have apps that work beautifully on iOS.","url":"https://apps.apple.com/us/genre/ios/id36","icon":"📲"},
        ],
        "negative": [
            {"type":"Fix","title":"iPhone problems fixed: battery, speed & storage","description":"Step-by-step solutions for the most common iPhone complaints.","url":"https://support.apple.com/","icon":"🔋"},
            {"type":"Alternative","title":"Best Android phones vs iPhone in 2024","description":"Detailed comparison to help you decide if switching makes sense.","url":"https://www.gsmarena.com/","icon":"📊"},
            {"type":"Save","title":"How to get iPhone cheaper: deals & refurbished","description":"Find genuine iPhone deals, trade-in tips, and certified refurbished options.","url":"https://www.apple.com/shop/refurbished","icon":"💸"},
        ]
    },

    # ── Tesla / Electric Cars ────────────────────────────────────────
    "tesla": {
        "positive": [
            {"type":"Guide","title":"Tesla ownership tips from real owners","description":"Community-sourced tips to get the best out of your Tesla vehicle.","url":"https://www.youtube.com/watch?v=nkFdULBCjTw","icon":"⚡"},
            {"type":"Article","title":"Tesla's latest software update features","description":"Breakdown of every new feature in the latest Tesla OTA update.","url":"https://electrek.co/guides/tesla/","icon":"🚗"},
        ],
        "negative": [
            {"type":"Fix","title":"Tesla charging issues: complete troubleshooting guide","description":"Solve the most common Tesla charging and range problems.","url":"https://www.tesla.com/en_US/support","icon":"🔌"},
            {"type":"Comparison","title":"Best electric cars that aren't Tesla","description":"Explore top-rated EV alternatives from Rivian, Lucid, Hyundai, and more.","url":"https://www.caranddriver.com/features/g15381137/best-electric-cars/","icon":"🔄"},
        ]
    },

    # ── Python / Coding / Programming ───────────────────────────────
    "coding": {
        "positive": [
            {"type":"Project","title":"10 awesome Python projects for beginners","description":"Fun and impressive Python projects you can build this weekend.","url":"https://www.youtube.com/watch?v=SqvVm3QiQVk","icon":"🐍"},
            {"type":"Resource","title":"GitHub's best open-source projects to contribute to","description":"Find meaningful open-source projects that welcome new contributors.","url":"https://github.com/explore","icon":"💻"},
            {"type":"Course","title":"Full Stack Web Development free course","description":"Build real-world web apps from scratch with this comprehensive course.","url":"https://www.freecodecamp.org/","icon":"🎓"},
        ],
        "negative": [
            {"type":"Debug","title":"How to debug Python code like a professional","description":"Master debugging techniques that will save you hours of frustration.","url":"https://realpython.com/python-debugging-pdb/","icon":"🐛"},
            {"type":"Guide","title":"Stack Overflow: get better answers faster","description":"How to ask better questions and find existing solutions efficiently.","url":"https://stackoverflow.com/help/how-to-ask","icon":"❓"},
            {"type":"Docs","title":"Official Python documentation and tutorials","description":"The definitive reference for Python built-in functions, libraries, and more.","url":"https://docs.python.org/3/tutorial/","icon":"📖"},
        ]
    },

    # ── Health / Mental Health ────────────────────────────────────────
    "health": {
        "positive": [
            {"type":"Workout","title":"20-minute full body workout at home","description":"No equipment needed. Stay fit with this highly-rated routine.","url":"https://www.youtube.com/watch?v=UItWltVZZmE","icon":"💪"},
            {"type":"Article","title":"Science-backed habits for a healthier life","description":"Research-proven daily habits that dramatically improve wellbeing.","url":"https://www.healthline.com/","icon":"🌿"},
        ],
        "negative": [
            {"type":"Self-Care","title":"5-minute stress relief techniques that work","description":"Clinically-backed breathing and mindfulness exercises for instant calm.","url":"https://www.youtube.com/watch?v=inpok4MKVLM","icon":"🧘"},
            {"type":"Resource","title":"Free mental health support resources","description":"Access free counseling, hotlines, and mental health tools near you.","url":"https://www.mentalhealth.gov/get-help/immediate-help","icon":"💚"},
            {"type":"Article","title":"How to improve sleep quality naturally","description":"Evidence-based strategies to get better sleep without medication.","url":"https://www.sleepfoundation.org/sleep-hygiene","icon":"😴"},
        ]
    },

    # ── Finance / Money ───────────────────────────────────────────────
    "finance": {
        "positive": [
            {"type":"Investing","title":"How to grow wealth with index funds","description":"Beginner's guide to passive investing and compound interest.","url":"https://www.youtube.com/watch?v=Ci6-KD7hKWg","icon":"📈"},
            {"type":"Article","title":"Best personal finance strategies for 2024","description":"Expert-backed advice on saving, budgeting, and investing wisely.","url":"https://www.nerdwallet.com/","icon":"💰"},
        ],
        "negative": [
            {"type":"Guide","title":"How to recover from financial stress","description":"Practical steps to manage debt, cut costs, and rebuild your finances.","url":"https://www.consumer.gov/articles/1002-making-budget","icon":"🛠️"},
            {"type":"Tool","title":"Free budget calculator and debt tracker","description":"Easy tools to take control of your money and reduce financial anxiety.","url":"https://www.mint.com/","icon":"📊"},
            {"type":"Article","title":"Side hustles that actually make money in 2024","description":"Real side income ideas that are low-cost and beginner friendly.","url":"https://www.bizjournals.com/","icon":"💼"},
        ]
    },

    # ── Gaming ────────────────────────────────────────────────────────
    "gaming": {
        "positive": [
            {"type":"Review","title":"Best games of 2024 you shouldn't miss","description":"Top-rated game releases across PC, PS5, Xbox and Switch this year.","url":"https://www.ign.com/","icon":"🎮"},
            {"type":"Tips","title":"Pro gaming tips to level up your skills","description":"Strategies used by professional gamers to improve quickly.","url":"https://www.youtube.com/results?search_query=pro+gaming+tips+2024","icon":"🏆"},
        ],
        "negative": [
            {"type":"Fix","title":"Fix lag, stuttering and crashes in PC games","description":"Complete guide to optimizing your PC for maximum gaming performance.","url":"https://www.howtogeek.com/tag/gaming/","icon":"⚙️"},
            {"type":"Guide","title":"Best free-to-play games worth your time","description":"High-quality games that are completely free and won't waste your time.","url":"https://store.steampowered.com/genre/Free%20to%20Play/","icon":"🆓"},
        ]
    },

    # ── Music ─────────────────────────────────────────────────────────
    "music": {
        "positive": [
            {"type":"Playlist","title":"Top viral songs playlist 2024","description":"The hottest music trending right now across all genres.","url":"https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M","icon":"🎵"},
            {"type":"Learn","title":"Learn guitar in 10 minutes a day","description":"Super practical beginner guitar lessons that actually work fast.","url":"https://www.youtube.com/watch?v=BBz-Jyr23M4","icon":"🎸"},
        ],
        "negative": [
            {"type":"Therapy","title":"Music proven to reduce stress and anxiety","description":"Scientifically selected tracks and genres for emotional regulation.","url":"https://www.youtube.com/watch?v=1ZYbU82GVz4","icon":"🎧"},
            {"type":"Playlist","title":"Uplifting playlist for tough days","description":"Carefully curated songs proven to elevate mood and restore energy.","url":"https://open.spotify.com/playlist/37i9dQZF1DX3rxVfibe1L0","icon":"☀️"},
        ]
    },

    # ── Science / Space ────────────────────────────────────────────────
    "science": {
        "positive": [
            {"type":"Documentary","title":"Latest space exploration discoveries","description":"Watch NASA's most recent findings and missions explained simply.","url":"https://www.nasa.gov/news-release/","icon":"🚀"},
            {"type":"Article","title":"Biggest science breakthroughs of 2024","description":"The most exciting scientific discoveries happening right now.","url":"https://www.sciencedaily.com/","icon":"🔬"},
        ],
        "negative": [
            {"type":"Explainer","title":"Climate change solutions you can support","description":"Practical actions and proven policies that are making a real difference.","url":"https://www.drawdown.org/solutions","icon":"🌍"},
            {"type":"Article","title":"Fighting misinformation with science","description":"How to identify credible sources and think critically about science news.","url":"https://www.snopes.com/science/","icon":"✅"},
        ]
    },

    # ── Sports ────────────────────────────────────────────────────────
    "sports": {
        "positive": [
            {"type":"Highlights","title":"Best sports moments this week","description":"The most exciting plays and performances from top leagues.","url":"https://www.espn.com/","icon":"⚽"},
            {"type":"Training","title":"Professional athlete training routines","description":"Follow the exact workouts that elite sportspeople use daily.","url":"https://www.youtube.com/results?search_query=athlete+training+routine","icon":"🏋️"},
        ],
        "negative": [
            {"type":"Analysis","title":"Sports analytics: understanding the game deeper","description":"How data and statistics are changing how we watch and understand sports.","url":"https://fivethirtyeight.com/sports/","icon":"📊"},
            {"type":"Article","title":"Injury recovery and comeback stories","description":"How professional athletes overcome setbacks and come back stronger.","url":"https://www.espn.com/nfl/story/_/page/athleterecovery2024","icon":"💪"},
        ]
    },

    # ── Education / Learning ──────────────────────────────────────────
    "education": {
        "positive": [
            {"type":"Course","title":"Free Ivy League courses online","description":"Take free courses from Harvard, MIT, Stanford and more right now.","url":"https://www.edx.org/","icon":"🎓"},
            {"type":"Tool","title":"Best learning tools and apps for students","description":"Productivity and learning apps recommended by top students.","url":"https://www.notion.so/","icon":"📚"},
        ],
        "negative": [
            {"type":"Guide","title":"How to study smarter, not harder","description":"Science-backed study techniques like spaced repetition and active recall.","url":"https://www.youtube.com/watch?v=IlU-zDU6aQ0","icon":"🧠"},
            {"type":"Resource","title":"Free tutoring resources for every subject","description":"Access free tutors, videos, and practice problems for any topic.","url":"https://www.khanacademy.org/","icon":"✏️"},
        ]
    },

    # ── Politics / News ────────────────────────────────────────────────
    "politics": {
        "positive": [
            {"type":"News","title":"Positive political changes happening now","description":"Good news stories about policy improvements and civic progress.","url":"https://www.goodnewsnetwork.org/category/news/world/","icon":"🗳️"},
        ],
        "negative": [
            {"type":"Guide","title":"How to engage with politics productively","description":"Practical ways to make a positive difference without burning out.","url":"https://headspace.com/articles/political-anxiety","icon":"🕊️"},
            {"type":"Resource","title":"Check facts before sharing: fact-checkers","description":"Tools to verify news and political claims before sharing them online.","url":"https://www.politifact.com/","icon":"🔍"},
        ]
    },

    # ── Food / Recipes ────────────────────────────────────────────────
    "food": {
        "positive": [
            {"type":"Recipe","title":"Viral recipes everyone's making this week","description":"The trending food recipes blowing up on social media right now.","url":"https://www.youtube.com/results?search_query=viral+recipes+2024","icon":"🍳"},
            {"type":"Guide","title":"How to cook restaurant-quality food at home","description":"Chef-level techniques simplified for the home kitchen.","url":"https://www.youtube.com/c/JoshuaWeissman","icon":"👨‍🍳"},
        ],
        "negative": [
            {"type":"Article","title":"Healthy eating on a tight budget","description":"Nutritious meals you can make for under $3 per serving.","url":"https://www.budgetbytes.com/","icon":"🥗"},
            {"type":"Guide","title":"Common cooking mistakes and how to fix them","description":"The most common kitchen errors and how to avoid them forever.","url":"https://www.seriouseats.com/","icon":"🔧"},
        ]
    },

    # ── Environment / Climate ──────────────────────────────────────────
    "environment": {
        "positive": [
            {"type":"Story","title":"Environmental wins: good news from 2024","description":"Species recovered, forests regrown, and climate victories happening now.","url":"https://www.goodnewsnetwork.org/category/news/environment/","icon":"🌱"},
            {"type":"Action","title":"Simple ways to reduce your carbon footprint","description":"Practical changes that genuinely make an environmental difference.","url":"https://www.wwf.org.uk/what-can-i-do","icon":"♻️"},
        ],
        "negative": [
            {"type":"Solution","title":"Climate solutions that are actually working","description":"The clean energy and conservation projects showing real results.","url":"https://www.drawdown.org/","icon":"🌍"},
            {"type":"Guide","title":"How to live sustainably without sacrifice","description":"Easy swaps and habits that help the planet without your  lifestyle.","url":"https://sustainableamerica.org/","icon":"🍃"},
        ]
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# TOPIC KEYWORD MAP (keyword → topic key)
# ─────────────────────────────────────────────────────────────────────────────
KEYWORD_MAP = {
    # AI
    "ai": "ai", "artificial intelligence": "ai", "machine learning": "ai",
    "chatgpt": "ai", "gpt": "ai", "gemini": "ai", "llm": "ai",
    "neural": "ai", "robot": "ai", "automation": "ai", "openai": "ai",
    "deepmind": "ai", "claude": "ai", "copilot": "ai",

    # Tech
    "tech": "tech", "technology": "tech", "software": "tech", "hardware": "tech",
    "gadget": "tech", "device": "tech", "update": "tech", "app": "tech",
    "bug": "tech", "feature": "tech", "internet": "tech", "server": "tech",
    "computer": "tech", "laptop": "tech", "pc": "tech",

    # Apple
    "apple": "apple", "iphone": "apple", "ipad": "apple", "macbook": "apple",
    "mac": "apple", "ios": "apple", "macos": "apple", "airpods": "apple",

    # Tesla / EV
    "tesla": "tesla", "elon": "tesla", "ev": "tesla", "electric car": "tesla",
    "electric vehicle": "tesla", "charging": "tesla", "battery": "tesla",
    "rivian": "tesla", "lucid": "tesla",

    # Coding
    "python": "coding", "coding": "coding", "programming": "coding",
    "javascript": "coding", "code": "coding", "developer": "coding",
    "github": "coding", "bug fix": "coding", "debug": "coding",
    "frontend": "coding", "backend": "coding", "api": "coding",
    "data science": "coding", "machine learning": "coding",

    # Health
    "health": "health", "mental health": "health", "anxiety": "health",
    "depression": "health", "stress": "health", "sleep": "health",
    "fitness": "health", "workout": "health", "exercise": "health",
    "diet": "health", "medicine": "health", "therapy": "health",
    "wellness": "health", "doctor": "health",

    # Finance
    "money": "finance", "finance": "finance", "invest": "finance",
    "stock": "finance", "crypto": "finance", "bitcoin": "finance",
    "broke": "finance", "debt": "finance", "salary": "finance",
    "budget": "finance", "savings": "finance", "financial": "finance",
    "economy": "finance", "inflation": "finance",

    # Gaming
    "game": "gaming", "gaming": "gaming", "ps5": "gaming",
    "xbox": "gaming", "nintendo": "gaming", "steam": "gaming",
    "fortnite": "gaming", "minecraft": "gaming", "valorant": "gaming",
    "gamer": "gaming", "esports": "gaming",

    # Music
    "music": "music", "song": "music", "album": "music",
    "artist": "music", "spotify": "music", "concert": "music",
    "playlist": "music", "rap": "music", "pop": "music",
    "band": "music", "guitar": "music", "singing": "music",

    # Science
    "science": "science", "nasa": "science", "space": "science",
    "research": "science", "quantum": "science", "physics": "science",
    "biology": "science", "climate": "science", "discovery": "science",

    # Sports
    "sport": "sports", "football": "sports", "soccer": "sports",
    "cricket": "sports", "basketball": "sports", "tennis": "sports",
    "match": "sports", "team": "sports", "player": "sports",
    "athlete": "sports", "game": "sports", "win": "sports",
    "score": "sports", "fifa": "sports", "nba": "sports",

    # Education
    "study": "education", "education": "education", "school": "education",
    "university": "education", "college": "education", "learn": "education",
    "course": "education", "degree": "education", "exam": "education",
    "knowledge": "education",

    # Politics
    "politics": "politics", "government": "politics", "election": "politics",
    "vote": "politics", "president": "politics", "policy": "politics",
    "congress": "politics", "parliament": "politics", "political": "politics",
    "democracy": "politics", "modi": "politics", "trump": "politics",

    # Food
    "food": "food", "recipe": "food", "cook": "food", "restaurant": "food",
    "eat": "food", "meal": "food", "lunch": "food", "dinner": "food",
    "breakfast": "food", "vegan": "food",

    # Environment
    "environment": "environment", "climate change": "environment",
    "global warming": "environment", "pollution": "environment",
    "renewable": "environment", "solar": "environment",
    "green": "environment", "sustainable": "environment",
    "nature": "environment", "ocean": "environment",
}

# ─────────────────────────────────────────────────────────────────────────────
# GENERIC FALLBACK RECOMMENDATIONS
# ─────────────────────────────────────────────────────────────────────────────
MOOD_MAP = {
    1: {
        "mood": "Happy & Positive",
        "description": "You're radiating positive energy! Let's keep that momentum going.",
        "color": "#10b981",
        "recommendations": [
            {"type":"Music","title":"Pharrell Williams — Happy","description":"The ultimate feel-good anthem to match your vibe.","url":"https://www.youtube.com/watch?v=ZbZSe6N_BXs","icon":"🎵"},
            {"type":"Motivation","title":"The Power of Positive Thinking","description":"How to maintain and grow your positive mindset every day.","url":"https://www.youtube.com/watch?v=7X1V_1Y4e_g","icon":"✨"},
            {"type":"News","title":"Good News Network: Only positive stories","description":"Real uplifting news from around the world to keep your energy high.","url":"https://www.goodnewsnetwork.org/","icon":"🌟"},
        ]
    },
    0: {
        "mood": "Sad or Stressed",
        "description": "It seems like you're going through a tough time. Here's something to lift your spirits.",
        "color": "#3b82f6",
        "recommendations": [
            {"type":"Meditation","title":"10-Minute Mindful Breathing Session","description":"A guided meditation specifically designed to reduce stress quickly.","url":"https://www.youtube.com/watch?v=inpok4MKVLM","icon":"🧘"},
            {"type":"Comedy","title":"Best comedy compilation to make you smile","description":"Guaranteed laughs to shift your mood in under 10 minutes.","url":"https://www.youtube.com/watch?v=n61B0Hw0180","icon":"😂"},
            {"type":"Music","title":"Upbeat Lo-Fi Hip Hop Mix","description":"The most popular study and chill beats playlist on YouTube.","url":"https://www.youtube.com/watch?v=5qap5aO4i9A","icon":"🎧"},
        ]
    }
}

TAMIL_MOOD_MAP = {
    1: {"mood": "மகிழ்ச்சி & நேர்மறை", "description": "நீங்கள் நேர்மறை ஆற்றலை வெளிப்படுத்துகிறீர்கள்!", "color": "#10b981"},
    0: {"mood": "வருத்தம் அல்லது மன அழுத்தம்", "description": "நீங்கள் கடினமான நேரத்தை கடந்து செல்கிறீர்கள்.", "color": "#3b82f6"}
}

TAMIL_RECOMMENDATIONS = {
    1: [
        {"type":"Music","title":"Vaathi Coming — Master","description":"Get pumped with one of Tamil cinema's biggest hits.","url":"https://www.youtube.com/watch?v=fRd_v978q_s","icon":"🎵"},
        {"type":"Comedy","title":"Vadivelu Best Comedy Scenes","description":"Classic Tamil comedy to keep your great mood going!","url":"https://www.youtube.com/watch?v=4Cmsd3pIeb0","icon":"😂"},
    ],
    0: [
        {"type":"Music","title":"Kadhale Kadhale — 96 Movie","description":"Beautiful music to soothe your heart.","url":"https://www.youtube.com/watch?v=pYitB000C8Q","icon":"💙"},
        {"type":"Relaxation","title":"Tamil Meditation & Peace Music","description":"Calm your mind with soothing Tamil meditation audio.","url":"https://www.youtube.com/watch?v=P2kOnW6rA7Y","icon":"🧘"},
    ]
}


# ─────────────────────────────────────────────────────────────────────────────
# CORE FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def detect_topic(text: str) -> str | None:
    """Detect the primary topic of a tweet from its text using word boundaries. Returns topic key or None."""
    text_lower = text.lower()
    topic_scores = {}
    for keyword, topic in KEYWORD_MAP.items():
        # Match keyword as whole word using regex
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, text_lower):
            topic_scores[topic] = topic_scores.get(topic, 0) + 1
            
    if not topic_scores:
        return None
    # Return the topic with the highest match count
    return max(topic_scores, key=topic_scores.get)


def get_smart_recommendation(text: str, sentiment_class: int, language: str = 'en') -> dict:
    """
    Main recommendation function.
    Returns a rich recommendation dict based on tweet TOPIC + SENTIMENT.
    """
    topic = detect_topic(text)
    sentiment_key = "positive" if sentiment_class == 1 else "negative"
    mood_label    = "Happy & Positive" if sentiment_class == 1 else "Sad or Stressed"
    mood_color    = "#10b981" if sentiment_class == 1 else "#ef4444"
    mood_desc     = (
        "Great to hear! Here's something to match your energy 🎉"
        if sentiment_class == 1
        else "Sorry to hear that. Here's something that might help 💙"
    )

    rec = None
    topic_label = topic.capitalize() if topic else None

    # Try topic-specific content first
    if topic and topic in TOPIC_CONTENT:
        pool = TOPIC_CONTENT[topic].get(sentiment_key, [])
        if pool:
            rec = random.choice(pool)

    # Fallback to Tamil-specific
    if rec is None and language == 'ta':
        profile = TAMIL_MOOD_MAP.get(sentiment_class, TAMIL_MOOD_MAP[1])
        pool = TAMIL_RECOMMENDATIONS.get(sentiment_class, TAMIL_RECOMMENDATIONS[1])
        rec = random.choice(pool)
        mood_label = profile["mood"]
        mood_desc  = profile["description"]
        mood_color = profile["color"]
        topic_label = "Tamil"

    # Final fallback
    if rec is None:
        profile = MOOD_MAP.get(sentiment_class, MOOD_MAP[1])
        rec = random.choice(profile["recommendations"])
        mood_label = profile["mood"]
        mood_desc  = profile["description"]
        mood_color = profile["color"]

    return {
        "mood":          mood_label,
        "mood_color":    mood_color,
        "description":   mood_desc,
        "topic":         topic_label,
        "recommendation": rec,       # { type, title, description, url, icon }
        "language":      "Tamil" if language == 'ta' else "English",
        "personalized":  topic is not None,
    }


# Keep backward-compatible wrapper used in app.py
def get_mood_recommendation(sentiment_class: int, language: str = 'en') -> dict:
    """Legacy wrapper — still works; returns basic mood profile."""
    if language == 'ta':
        profile = TAMIL_MOOD_MAP.get(sentiment_class, TAMIL_MOOD_MAP[1])
        pool = TAMIL_RECOMMENDATIONS.get(sentiment_class, TAMIL_RECOMMENDATIONS[1])
        rec = random.choice(pool)
        return {"mood": profile["mood"], "description": profile["description"],
                "color": profile["color"], "recommendation": rec, "language": "Tamil"}
    else:
        profile = MOOD_MAP.get(sentiment_class, MOOD_MAP[1])
        rec = random.choice(profile["recommendations"])
        return {"mood": profile["mood"], "description": profile["description"],
                "color": profile["color"], "recommendation": rec, "language": "English"}


if __name__ == "__main__":
    tests = [
        ("Just tried the new iPhone 16 and it's mind-blowing!", 1),
        ("Tesla's new update broke everything. Very disappointed", 0),
        ("Love learning Python! Just built my first ML model 🚀", 1),
        ("Having serious anxiety attacks and can't sleep", 0),
        ("AI is going to take all our jobs", 0),
        ("The space mission results are incredible!", 1),
    ]
    for text, sent in tests:
        result = get_smart_recommendation(text, sent)
        print(f"\n📝 '{text[:50]}...'")
        print(f"   Mood: {result['mood']} | Topic: {result['topic']} | Personalized: {result['personalized']}")
        rec = result['recommendation']
        print(f"   → {rec.get('icon','')} [{rec['type']}] {rec['title']}")
        print(f"      {rec.get('description','')}")
