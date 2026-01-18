# Student Mental Health Companion (Streamlit + Gemini)

A professional, supportive mental health companion for students, powered by Google Gemini and Streamlit. Includes quick prompts, basic crisis guidance, session-only mood check-ins, and a small statistics visualization.

## Features
- Chatbot guidance for stress, anxiety, academic pressure, sleep, and self-care
- Crisis awareness: highlights resources if risky keywords are detected
- Quick prompts for common student concerns
- Session-only mood check-in and simple trend chart
- Statistics section (WHO and CDC YRBS examples) with an Altair chart

## Important
This app is not a substitute for professional help. If you're in immediate danger or considering harming yourself:
- United States: Call or text 988 (Suicide & Crisis Lifeline)
- International: Visit https://findahelpline.com or contact your local emergency services

## Prerequisites
- Python 3.9+
- A Google API key with access to the Gemini API

## Setup

1. Create and activate a virtual environment (recommended)

   PowerShell (Windows):
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Install dependencies

   ```powershell
   pip install -r requirements.txt
   ```

3. Provide your Google API Key (choose one):
   - Option A: Environment variable (persists across sessions after restart)
     ```powershell
     setx GOOGLE_API_KEY "{{YOUR_GOOGLE_API_KEY}}"
     # Restart the terminal after this
     ```
   - Option B: Streamlit secrets (per project)
     Create a file `.streamlit/secrets.toml` and add:
     ```toml
     GOOGLE_API_KEY = "{{YOUR_GOOGLE_API_KEY}}"
     ```
   - Option C: Paste your key into the sidebar field when the app runs (temporary for the session)

4. Run the app

   ```powershell
   streamlit run app.py
   ```

## Model selection
The sidebar lets you choose between `gemini-1.5-pro` (higher quality) and `gemini-1.5-flash` (faster, cost-efficient). You can change this at runtime.

## Notes on data and privacy
- Conversations are kept only in the current session unless you export or persist them yourself.
- The statistics are examples from reputable sources:
  - WHO (2021): ~1 in 7 adolescents (10–19) experiences a mental disorder.
  - CDC YRBS (2021, published 2023): 42% of US high school students felt persistent sadness; ~22% seriously considered attempting suicide in the past year.
  These figures may vary by region and year; always refer to official sources for the latest data.

## Troubleshooting
- If you see `Failed to configure Gemini` or similar errors, ensure your key is valid and that the `google-generativeai` package is installed.
- If charts do not render, confirm `altair` is installed and your Python version is supported.
- If the terminal cannot find Streamlit, ensure your virtual environment is activated.

## License
For educational purposes. Always seek qualified professional help if you are struggling with your mental health.
