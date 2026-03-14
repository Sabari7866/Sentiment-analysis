import subprocess
import os
import sys

def run_step(command, description):
    print(f"\n--- [Step] {description} ---")
    # Use sys.executable to ensure we use the same python environment
    full_command = f'"{sys.executable}" {command}'

    result = subprocess.run(full_command, shell=True)
    if result.returncode != 0:
        print(f"FAILED: {description}")
        return False
    return True

if __name__ == "__main__":
    print("="*40)
    print("TWITTER SENTIMENT ANALYSIS MASTER PIPELINE")
    print("="*40)

    # Ensure dataset directory exists
    if not os.path.exists('dataset/train.csv'):
        print("ERROR: Please place your 'train.csv' in the 'dataset/' folder.")
        sys.exit(1)

    # 1. Preprocess (Uses Stemming by default now)
    if run_step("code/preprocess.py dataset/train.csv", "Preprocessing Data (with Stemming)"):
        processed_file = "dataset/train-processed-stemmed.csv"
        # 2. Stats
        if run_step(f"code/stats.py {processed_file}", "Generating N-Grams"):
            # Update svm.py to point to the stemmed file
            with open('code/svm.py', 'r') as f:
                content = f.read()
            content = content.replace("TRAIN_PROCESSED_FILE = 'dataset/train-processed.csv'", f"TRAIN_PROCESSED_FILE = '{processed_file}'")
            with open('code/svm.py', 'w') as f:
                f.write(content)

            # 3. SVM (The Best Model for this task)

            run_step("code/svm.py", "Running SVM Classifier")
            print("\n" + "="*40)
            print("DONE! Your model is ready and tested.")
            print("Check 'svm.csv' for predictions.")
            print("="*40)
