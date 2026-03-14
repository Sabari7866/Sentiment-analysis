# 🧠 MoodPulse AI (Enterprise Sentiment & Predictive Analytics)

> **Hackathon Submission:** An advanced real-time social intelligence platform capable of ingesting live data, analyzing complex emotional nuances, and dynamically triggering contextual action recommendations.

![Dashboard Preview](https://img.shields.io/badge/Status-Live_Streaming-success) ![Machine Learning](https://img.shields.io/badge/Engine-Ensemble_ML-blue) ![License](https://img.shields.io/badge/License-MIT-green)

---

## 🛑 The Problem
Brands, creators, and individuals are overwhelmed by the sheer volume of chaotic social media data. Traditional sentiment analysis tools only output basic "Positive/Negative" scores, completely ignoring **context, emotional nuance, and actionable next steps.** Furthermore, they are highly susceptible to spam, fake reviews, and bot plagiarism.

## 💡 Our Solution: MoodPulse AI
MoodPulse AI is a distributed, real-time intelligence engine that doesn't just judge text—it understands it. 

By combining high-speed streaming architecture with a weighted **Multi-Model Machine Learning Ensemble**, we capture live data and dissect it for emotion, specific entities (companies/products), vulnerabilities, and plagiarism. More importantly, it features an **Action Recommendation Engine** that maps the user's emotional state and detected topics to instantly suggest hyper-relevant content (e.g., debugging tutorials for frustrated developers, or specific ambient music for anxious users).

---

## 🚀 Key Features

*   **⚡ Real-Time Ingest Pipeline:** A resilient 3-layer architecture capable of handling official API streams, dynamic scraper fallbacks, and high-fidelity simulated streaming to guarantee zero-downtime analytics.
*   **🤖 Advanced Multi-Model Ensemble:** Combines state-of-the-art Deep Learning with lightweight classical models:
    *   **Twitter-RoBERTa (HuggingFace):** Massive transformer neural network for deep contextual understanding.
    *   **SVM & Logistic Regression:** Fast, statistically robust classical models.
    *   **VADER Lexicon:** Specialized rule-based engine tuned specifically for social media slang and emojis.
*   **🎯 Contextual Recommendation Engine:** Dynamically extracts Topics & Named Entities via regex/NLP and pairs them with sentiment scores to suggest actionable next steps (Tutorials, Therapy, Music, Products).
*   **🛡️ Fraud & Plagiarism Security:** Analyzes incoming streams against historical memory buffers using `SequenceMatcher` to instantaneously flag duplicated "bot" reviews and spam patterns.
*   **📊 Reactive Glassmorphism Dashboard:** A sleek, zero-dependency Vanilla JS/CSS frontend powered by Server-Sent Events (SSE) for sub-second visual updates without full-page reloads.

---

## 🛠️ Technology Stack
**Backend / Machine Learning:**
*   Python 3.11
*   Flask (REST API & SSE Streaming)
*   Scikit-Learn (SVM, LR)
*   HuggingFace Transformers (PyTorch / RoBERTa)
*   VADER Sentiment

**Frontend UI:**
*   HTML5 / CSS3 (Custom Glassmorphism Design System)
*   Vanilla JavaScript
*   Chart.js (Dynamic Data Visualization)

---

## ⚙️ How to Run Locally

*See `HOW_TO_RUN_PROJECT.md` for complete step-by-step instructions.*

1. **Start the Backend Machine Learning Engine:**
   ```bash
   python app.py
   ```
   *(Wait until the RoBERTa model loads into memory and the server reports active on port 8888).*

2. **Start the Frontend UI Server:**
   Open a new terminal window and run:
   ```bash
   python -m http.server 8000 --bind 127.0.0.1
   ```

3. **Launch Dashboard:**
   Open a web browser and navigate to `http://127.0.0.1:8000`

---

## 🔮 Future Roadmap
*   **Database Integration:** Connect to PostgreSQL/MongoDB to store historical sentiment trends for long-term pattern analysis.
*   **Webhook Triggers:** Allow enterprise users to trigger automatic customer-support API calls when "Angry" sentiments surrounding their brand spike.
*   **Multi-Lingual Support:** Expand RoBERTa models to support native Tamil, Spanish, and French real-time extraction.
