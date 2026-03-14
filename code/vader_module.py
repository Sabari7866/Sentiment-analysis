from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

class VADERAnalyzer:
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()
    
    def analyze(self, text):
        scores = self.analyzer.polarity_scores(text)
        # compound score: > 0.05 is positive, < -0.05 is negative
        compound = scores['compound']
        label = 1 if compound >= 0.05 else 0
        return label, compound

if __name__ == "__main__":
    vader = VADERAnalyzer()
    text = "VADER is smart, handsome, and funny!"
    label, score = vader.analyze(text)
    print(f"Text: {text}")
    print(f"Sentiment: {'Positive' if label == 1 else 'Negative'} ({score:.4f})")
