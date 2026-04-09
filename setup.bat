@echo off
echo ============================================
echo AI Resume Screener - Setup Script
echo ============================================
echo.

echo [1/3] Installing Python dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies!
    pause
    exit /b 1
)
echo ✓ Dependencies installed
echo.

echo [2/3] Downloading spaCy language model...
python -m spacy download en_core_web_sm
if %errorlevel% neq 0 (
    echo WARNING: spaCy model download failed. Trying alternative method...
    pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl
)
echo ✓ spaCy model ready
echo.

echo [3/3] Verifying installation...
python -c "import spacy; nlp = spacy.load('en_core_web_sm'); print('spaCy model: OK')"
python -c "import sqlalchemy; print('SQLAlchemy: OK')"
python -c "import streamlit; print('Streamlit: OK')"
echo.

echo ============================================
echo Setup Complete! ✅
echo ============================================
echo.
echo Next steps:
echo 1. Copy .env.example to .env and configure
echo 2. Run: streamlit run app.py
echo.
pause
