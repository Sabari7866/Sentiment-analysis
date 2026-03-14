# MoodPulse AI: Twitter Sentiment Analysis Platform

This document breaks down the entire project "from scratch to completion" in an easy-to-understand way. It explains what the project does, the technologies behind it, and how data moves through the whole system.

---

## 1. What Does the Project Do?
**MoodPulse AI** is a real-time intelligence dashboard that analyzes the sentiment (positive, negative, or neutral) of tweets or custom text. 

It tells you:
1. **Mood & Emotion:** Is the user feeling joyful, anxious, excited, or angry?
2. **Contextual Action Recommendations:** Based on the tweet’s topic and mood, what should the user watch or read next? For example, if they are stressed about "coding", it might suggest a debugging tutorial.
3. **Plagiarism & Fraud Detection:** Tells you whether the text might be copied from somewhere else.
4. **Vulnerability / Spam Analysis:** Checks if the tweet contains suspicious links or harmful threats.

---

## 2. Core Components (The Architecture)

The system is divided into three major blocks:
1. **The Frontend (UI/Dashboard)**
2. **The Backend (Flask API Server)**
3. **Data Ingestion (Streams & Integrations)**
4. **The Machine Learning Engine**

### A. The Frontend Dashboard (HTML/CSS/JS)
The dashboard (`index.html`, `style.css`, `script.js`) is what you see in the browser. 
- **Review Navigator:** A scroll-able list separating positive and negative tweets.
- **Donut Charts:** Visual pie charts analyzing current overall live sentiment ratios.
- **Action Recommendation Panel:** Recommends dynamically generated YouTube videos, tutorials, or music based on the sentiment mapped from text.
- **Live Tweet Stream Feed:** The ticker rolling at the bottom showing live streaming tweets in real-time.

All data flows into the frontend dynamically. The `script.js` handles asking the backend API for predictions, reading server-sent events (real-time stream feed), and managing chart animations.

### B. The Backend (Python Flask Server)
The heavy lifting lives in `app.py`, which is the Flask server.
It receives requests from the front end, processes them, and returns JSON data.

**Key Routes:**
* `POST /predict`: You send it a piece of text. It runs it through the machine learning ensemble and sends back probabilities, plagiarism statuses, recommended actions, and specific hashtags dynamically extracted.
* `GET /stream`: An open Server-Sent Events (SSE) channel. The browser connects to this, and whenever the stream ingestion downloads a new tweet, the backend instantly pushes it to the browser.
* `GET /stream/status`: A health-check showing whether the live data sources are active and how many tweets are sitting in the queue.

### C. Live Data Ingestion (`stream_service.py`)
Because official Twitter APIs are heavily restricted or expensive now, the system uses a **Resilient 3-Layer Queue:**
1. **Twitter API:** Checks if you have a Bearer token in `keys.txt` to stream from the true platform (currently skipped unless configured).
2. **Nitter Scraper:** Periodically pulls data from free open-source public Twitter mirrors without requiring developer accounts.
3. **Mock Generator:** An ultra-realistic fallback that auto-generates structured tweets (containing varying sentiments and tech hashtags) locally to keep the dashboard flowing.

Everything gets pushed to an internal worker `TWEET_QUEUE` constantly passing live data to `app.py`.

### D. The Machine Learning Ensemble (`code/ensemble.py` & `code/mood_engine.py`)
To get an accurate feeling of text, it uses multiple "brains" at the same time:
1. **VADER:** A rule-based lexicon. Excellent at detecting quick internet slang and emojis (e.g., "amazing!!! 😍").
2. **Support Vector Machine (SVM) & Logistic Regression (LR):** Classical Machine learning trained on older historical tweet databases. 
3. **HuggingFace Transformers (Twitter RoBERTa):** If connected to the internet, it runs a massive deep neural network trained specifically on millions of tweets to fetch bleeding-edge predictions.

The `ensemble.py` pools the votes of these brains using a weighted average to deliver exactly if it's Positive (1) or Negative (0).

Once the sentiment is decided, `mood_engine.py` is called. It uses regular expressions to hunt for topics (like 'ai', 'tesla', 'coding', 'finance') and cross-references the topic with the negative or positive sentiment to deliver extremely specific contextual advice.

---

## 3. How a Single Tweet is Processed (End-to-End Workflow)

1. A tweet comes in via the **Live Tweet Stream** OR the user types "AI is the future of python coding, but I have a memory error!" into the **Manual Analysis** box.
2. The UI (`script.js`) fires an HTTP POST to `http://127.0.0.1:8888/predict`. 
3. The Backend (`app.py`) parses the text and passes it to the `Ensemble`.
4. The Ensemble tokenizes the text into vector numbers and runs it through its NLP algorithms to get a 0 (Sad/Negative) or 1 (Happy/Positive). *In our test quote, "memory error!" tips it toward Negative/Anxious (0).*
5. `app.py` passes the text and "0" into `mood_engine.py`.
6. `mood_engine.py` identifies the word "\bpython\b" which matches the `coding` category. Because the sentiment is 0, it reaches into its Negative Coding array and pulls out `"How to debug Python code like a professional"`.
7. `app.py` checks for plagiarism by comparing the input against previous recent searches using `SequenceMatcher`.
8. `app.py` packages all this data into a structured JSON string and replies back to the UI.
9. `script.js` natively injects the payload: spinning up the UI's Donut Charts, filling out the Action Recommendation card with the specific debug link, shifting the Emoji face to 😰 (Anxious), and updating the background styling colors to red.

---

## Conclusion

This project evolved from a static script verifying large `.csv` datasets to a **distributed, live-streaming artificial intelligence engine**. It leverages modern Javascript UI reactivity alongside heavy-duty Python networking and Natural Language Processing to serve high-quality insights instantly!
