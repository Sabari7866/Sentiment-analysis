from transformers import pipeline
import torch

class BERTAnalyzer:
    def __init__(self):
        print("Loading Twitter-RoBERTa Pipeline (cardiffnlp)...")
        # twitter-roberta-base-sentiment-latest is specifically trained for social media
        self.model_path = "cardiffnlp/twitter-roberta-base-sentiment-latest"
        self.analyzer = pipeline(
            "sentiment-analysis", 
            model=self.model_path,
            device=0 if torch.cuda.is_available() else -1
        )
    
    def analyze(self, text):
        results = self.analyzer(text)
        # twitter-roberta-base-sentiment-latest labels:
        # 'negative' -> 0, 'neutral' -> 1, 'positive' -> 2
        res = results[0]
        label_text = res['label'].lower()
        score = res['score']
        
        if label_text == 'positive':
            return 1, score
        elif label_text == 'negative':
            return 0, score
        else: # neutral - mapping to positive/negative based on score or just positive for simplicity if we must be binary
            return 1 if score > 0.5 else 0, score

if __name__ == "__main__":
    bert = BERTAnalyzer()
    text = "MoodPulse AI is the most amazing sentiment tool ever!"
    label, score = bert.analyze(text)
    print(f"Text: {text}")
    print(f"Sentiment: {'Positive' if label == 1 else 'Negative'} ({score:.4f})")
