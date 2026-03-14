# MoodPulse AI: System Architecture

Derived from the proposed pipeline, here is the structural breakdown of the current and future state of MoodPulse AI.

## 1. Data Ingestion Layer
- **Source**: Twitter API / Real-time Streams.
- **Messaging**: Kafka (Internal testing via mock streams).

## 2. Preprocessing & Feature Engineering
- **Cleaning**: Removal of URLs, mentions, and PII.
- **Normalization**: Stop-word filtering and Porter Stemming (implemented in `preprocess.py`).
- **Tokenization**: N-gram generation (Unigrams + Bigrams).

## 3. Modeling Layer (Ensemble Approach)
- **Baseline**: TF-IDF + Linear SVM (Current production model).
- **Deep Learning**: BERT-Base for contextual embeddings (Reference Image 2).
- **Hybrid**: VADER for valence-aware dictionary scores combined with BiLSTM for temporal sequences.

## 4. Analytical Intelligence
- **Aspect Extraction**: Identifying specific topics (Company, Product, Service).
- **Emotion Mapping**: Translating sentiment into human emotions (Joy, Anger, Trust).
- **Vulnerability Scoring**: Predicting market or social risks based on negative velocity.

## 5. Dashboard Layer
- **Interface**: Modern Glassmorphism Dashboard (implemented in `index.html`).
- **State Management**: Real-time updates via Fetch API.
- **Visualization**: Chart.js for sentiment distribution and circular metrics.
