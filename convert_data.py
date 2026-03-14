import pandas as pd
import os

def prepare_data(input_file, output_file):
    print(f"Reading {input_file}...")
    df = pd.read_csv(input_file)
    
    # Map categories: 1.0 -> 1, -1.0 -> 0
    # Drop 0.0 (Neutral) for binary classification
    df = df[df['category'].isin([1.0, -1.0])]
    df['sentiment'] = df['category'].apply(lambda x: 1 if x == 1.0 else 0)
    
    # Ensure clean_text is string
    df['clean_text'] = df['clean_text'].astype(str)
    
    # Create id column
    df['id'] = range(1, len(df) + 1)
    
    # Reorder to: id,sentiment,tweet
    final_df = df[['id', 'sentiment', 'clean_text']]
    
    print(f"Saving {len(final_df)} samples to {output_file}...")
    final_df.to_csv(output_file, index=False, header=False)
    print("Done!")

if __name__ == "__main__":
    input_path = r"C:\Users\Ganagasabarinath V N\Downloads\twitter-sentiment-analysis-master\twitter-sentiment-analysis-master\Twitter_Data.csv"
    output_path = r"C:\Users\Ganagasabarinath V N\Downloads\twitter-sentiment-analysis-master\twitter-sentiment-analysis-master\dataset\train.csv"
    
    # Backup old train.csv if it exists
    if os.path.exists(output_path):
        os.rename(output_path, output_path + ".bak")
        
    prepare_data(input_path, output_path)
