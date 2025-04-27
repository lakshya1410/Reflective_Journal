# Reflective Journal App

A Flask-based journaling application that uses sentiment analysis and AI to provide personalized responses to your journal entries.

## Features

- Web interface for submitting journal entries
- Sentiment analysis of your journal entries using Hugging Face's multilingual sentiment analysis model
- AI-generated personalized responses from Lotus, your empathetic journal companion
- Detailed emotional analysis and personalized activity suggestions

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Hugging Face API key
- Groq API key

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/reflective-journal-app.git
   cd reflective-journal-app
   ```

2. Create a virtual environment (recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root directory with your API keys:
   ```
   HF_API_KEY=your_hugging_face_api_key_here
   GROQ_API_KEY=your_groq_api_key_here
   ```

## Running the Application

1. Start the Flask application:
   ```
   python app.py
   ```

2. Open your web browser and navigate to:
   ```
   http://127.0.0.1:5000/
   ```

3. Start journaling and receive personalized AI responses!

## Deployment

For production deployment, consider using gunicorn:
```
gunicorn app:app
```

## How It Works

1. User submits a journal entry through the web interface
2. The application analyzes the sentiment of the entry using Hugging Face's multilingual model
3. The journal entry and sentiment analysis are sent to the Groq API
4. Lotus (the AI journal companion) generates a personalized response with:
   - Emotional analysis
   - Empathetic acknowledgment
   - Personalized activity suggestions
   - Warm encouragement

## File Structure

- `app.py` - Main Flask application
- `templates/index.html` - Frontend web interface
- `requirements.txt` - Python dependencies
- `.env` - API keys (you need to create this file)

## Troubleshooting

If you encounter issues with the Groq client initialization, the application will attempt different initialization methods automatically. Make sure your API keys are correctly set in the `.env` file.

## License

[Your chosen license]
