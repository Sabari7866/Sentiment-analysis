# How to Run the MoodPulse AI Project

To run this project perfectly without errors, you need to start **two** separate things: the **Backend API Server** (which handles the machine learning and tweet streaming) and the **Frontend Web Server** (which shows the visual dashboard).

Follow these exact steps:

### Step 1: Start the Backend Machine Learning Server
1. Open a terminal or PowerShell window.
2. Navigate to the project folder (`c:\Users\Ganagasabarinath V N\Downloads\twitter-sentiment-analysis-master\twitter-sentiment-analysis-master`).
3. Run the following command:
   ```bash
   python app.py
   ```
4. **Wait a few moments.** You will see messages like `Initialising MoodPulse Advanced Ensemble...` and `Loading SVM...`. Eventually, it should say `* Running on all addresses (0.0.0.0)` and `* Running on http://127.0.0.1:8888`. 
5. **Leave this terminal open and running.** Do not close it.

### Step 2: Start the Frontend Web Server
1. Open a **SECOND, completely new** terminal or PowerShell window.
2. Navigate to the exact same project folder again.
3. Run the following command:
   ```bash
   python -m http.server 8000 --bind 127.0.0.1
   ```
4. This starts a lightweight web server that serves your `index.html` file on port 8000.
5. **Leave this terminal open too.**

### Step 3: Open the Dashboard
1. Open any modern web browser (Google Chrome, Microsoft Edge, Firefox, etc.).
2. In the address bar at the top, type exactly this URL and press Enter:
   ```
   http://127.0.0.1:8000
   ```
   *(or `http://localhost:8000`)*
3. The sleek MoodPulse AI dashboard should load immediately!

---

### Troubleshooting / How to Restart Without Errors:
- **Port already in use error?** If you try to run `python app.py` or the `http.server` and it crashes with an "Address already in use" error, it means you didn't close a previous terminal properly. 
  - To fix it, you need to force close Python. Open PowerShell and run:
    ```powershell
    Get-NetTCPConnection -LocalPort 8888 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
    ```
    Then try starting it again.
- **Model downloading slowly?** The very first time you run `app.py`, it might take a few minutes to download the massive RoBERTa neural network. Just let it finish. Once it downloads the first time, it will load instantly in the future!
