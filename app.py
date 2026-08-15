# ============================================================
#  FAKE NEWS DETECTOR - PYTHON BACKEND (Flask)
#  Securely proxies Gemini API requests.
#  The API key stays on the server (never exposed to frontend).
# ============================================================

import os
import json
import re
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import requests

# Load environment variables from .env
load_dotenv()

app = Flask(__name__, static_folder='public', static_url_path='')
CORS(app)

PORT = int(os.getenv('PORT', 3000))
API_KEY = os.getenv('GEMINI_API_KEY', '')
AI_PROVIDER = (os.getenv('AI_PROVIDER') or 'gemini').lower()
DEFAULT_MODEL = 'gemini-2.5-flash-preview-05-06'
MODEL_CANDIDATES = [
    'gemini-2.5-flash-preview-05-06',
    'gemini-2.5-flash-lite-preview-05-06',
    'gemini-2.5-pro-preview-05-06',
]
configured_model = (os.getenv('GEMINI_MODEL') or DEFAULT_MODEL).strip() or DEFAULT_MODEL
if configured_model not in MODEL_CANDIDATES:
    configured_model = DEFAULT_MODEL
GEMINI_MODEL = configured_model
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')
OPENROUTER_MODEL = os.getenv('OPENROUTER_MODEL', 'openai/gpt-oss-20b:free')
OPENROUTER_FALLBACK_MODELS = [
    'openai/gpt-oss-20b:free',
    'openai/gpt-oss-20b',
]


def get_model_candidates():
    candidates = []
    configured = (os.getenv('GEMINI_MODEL') or DEFAULT_MODEL).strip() or DEFAULT_MODEL
    for model in [configured, *MODEL_CANDIDATES]:
        if model and model not in candidates:
            candidates.append(model)
    return candidates


def call_gemini(prompt):
    if not API_KEY:
        raise ValueError('Google API key is not configured.')

    last_error = None
    for model_name in get_model_candidates():
        url = f'https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={API_KEY}'
        payload = {
            'contents': [{'parts': [{'text': prompt}]}],
            'generationConfig': {
                'temperature': 0.2,
                'maxOutputTokens': 1024,
            }
        }
        try:
            response = requests.post(url, json=payload, timeout=30)
        except requests.exceptions.RequestException as exc:
            last_error = str(exc)
            continue

        if response.status_code == 200:
            data = response.json()
            try:
                return data['candidates'][0]['content']['parts'][0]['text']
            except (KeyError, IndexError, TypeError):
                raise ValueError('No response content received from the AI.')

        try:
            err_data = response.json()
            msg = err_data.get('error', {}).get('message', f'Gemini API request failed with status {response.status_code}')
        except Exception:
            msg = f'Gemini API request failed with status {response.status_code}'

        last_error = msg
        if response.status_code in (400, 404) and ('not found' in msg.lower() or 'not supported' in msg.lower()):
            continue
        raise RuntimeError(msg)

    raise RuntimeError(last_error or 'Gemini API request failed for the configured models.')


def get_openrouter_candidates():
    configured = (os.getenv('OPENROUTER_MODEL') or OPENROUTER_MODEL).strip()
    candidates = []
    for model in [configured, *OPENROUTER_FALLBACK_MODELS]:
        if model and model not in candidates:
            candidates.append(model)
    return candidates


def call_openrouter(prompt):
    if not OPENROUTER_API_KEY:
        raise ValueError('OpenRouter API key is not configured. Add OPENROUTER_API_KEY to the .env file.')

    url = 'https://openrouter.ai/api/v1/chat/completions'
    headers = {
        'Authorization': f'Bearer {OPENROUTER_API_KEY}',
        'Content-Type': 'application/json',
        'HTTP-Referer': 'http://localhost:3000',
        'X-Title': 'Fake News Detector',
    }

    last_error = None
    for model_name in get_openrouter_candidates():
        payload = {
            'model': model_name,
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': 0.2,
            'max_tokens': 1024,
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
        except requests.exceptions.RequestException as exc:
            last_error = str(exc)
            continue

        if response.status_code == 200:
            data = response.json()
            try:
                content = data['choices'][0]['message']['content']
                if isinstance(content, list):
                    return ''.join(part.get('text', '') for part in content if isinstance(part, dict))
                return content
            except (KeyError, IndexError, TypeError):
                raise ValueError('No response content received from OpenRouter.')

        try:
            err_data = response.json()
            msg = err_data.get('error', {}).get('message', f'OpenRouter API request failed with status {response.status_code}')
        except Exception:
            msg = f'OpenRouter API request failed with status {response.status_code}'

        last_error = msg
        if response.status_code in (400, 404) and (
            'not found' in msg.lower() or 'unavailable' in msg.lower() or 'invalid model' in msg.lower()
        ):
            continue
        raise RuntimeError(msg)

    raise RuntimeError(last_error or 'OpenRouter API request failed for the configured models.')


def call_ai(prompt):
    preferred = AI_PROVIDER.lower()
    providers = []
    if preferred == 'openrouter':
        providers = ['openrouter']
    elif preferred == 'gemini':
        providers = ['gemini', 'openrouter']
    else:
        providers = ['gemini', 'openrouter']

    last_error = None
    for provider in providers:
        try:
            if provider == 'gemini':
                return call_gemini(prompt)
            return call_openrouter(prompt)
        except Exception as exc:
            last_error = str(exc)
            if preferred == 'openrouter':
                break

    raise RuntimeError(last_error or 'All configured AI providers failed.')


# ============================================================
#  ROUTES
# ============================================================

@app.route('/')
def index():
    """Serve the frontend."""
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/api/analyze', methods=['POST'])
def analyze():
    """Receive news text, call Gemini API, return structured result."""
    try:
        data = request.get_json()
        text = (data.get('text') or '').strip() if data else ''

        # Validate input
        if not text:
            return jsonify({'error': 'Please provide news text to analyze.'}), 400

        if len(text) > 5000:
            return jsonify({'error': 'Text is too long. Maximum 5000 characters allowed.'}), 400

        # Check the configured provider's API key before sending the request.
        if AI_PROVIDER == 'gemini':
            if not API_KEY or API_KEY == 'YOUR_API_KEY_HERE':
                return jsonify({'error': 'Server is not configured with a Gemini API key. Please check the .env file.'}), 500
        elif AI_PROVIDER == 'openrouter':
            if not OPENROUTER_API_KEY or OPENROUTER_API_KEY == 'YOUR_API_KEY_HERE':
                return jsonify({'error': 'Server is not configured with an OpenRouter API key. Please check the .env file.'}), 500

        # Build the AI prompt
        prompt = build_prompt(text)

        # Call the configured AI provider, with OpenRouter as a free fallback if needed
        try:
            raw_text = call_ai(prompt)
        except RuntimeError as exc:
            return jsonify({'error': str(exc)}), 502
        except ValueError as exc:
            return jsonify({'error': str(exc)}), 500

        # Parse and validate the JSON response
        parsed = parse_ai_response(raw_text)

        # Return clean result to frontend
        return jsonify(parsed)

    except Exception as e:
        print(f'Server error: {e}')
        return jsonify({'error': 'Internal server error. Please try again.'}), 500


# ============================================================
#  AI SYSTEM PROMPT BUILDER
# ============================================================

def build_prompt(news_text):
    return f"""
You are an expert fact-checker and investigative journalist with deep knowledge of media literacy and misinformation.

Analyze the following news article or claim for authenticity:

\"\"\"
{news_text}
\"\"\"

Your task:
1. Evaluate the claim against known facts, logical consistency, and common misinformation patterns.
2. Determine the most accurate verdict.

You MUST respond with ONLY a valid JSON object. Do NOT wrap it in markdown, code fences, or any other text. No explanations outside the JSON.

The JSON must contain EXACTLY these three keys:
{{
  "verdict": "Real" | "Fake" | "Misleading" | "Unverified",
  "confidence_score": <number from 0 to 100>,
  "explanation": "<brief 2-3 sentence explanation of your reasoning>"
}}

Rules:
- "verdict" must be exactly one of: "Real", "Fake", "Misleading", or "Unverified".
- "confidence_score" must be an integer between 0 and 100.
- "explanation" must be 2-3 concise sentences.
"""


# ============================================================
#  PARSE & VALIDATE AI RESPONSE
# ============================================================

def parse_ai_response(raw_text):
    """Extract and validate the JSON object from the AI response."""
    # Strip any markdown code fences if present
    cleaned = raw_text.strip()
    cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'```\s*$', '', cleaned).strip()

    # Find the first { and last } to extract JSON object
    start = cleaned.find('{')
    end = cleaned.rfind('}')
    if start == -1 or end == -1:
        raise ValueError('AI response was not in valid JSON format.')

    json_str = cleaned[start:end + 1]
    parsed = json.loads(json_str)

    # Validate structure
    valid_verdicts = ['Real', 'Fake', 'Misleading', 'Unverified']
    if parsed.get('verdict') not in valid_verdicts:
        raise ValueError(f"AI returned an invalid verdict: {parsed.get('verdict')}")

    try:
        score = int(parsed.get('confidence_score', 0))
    except (ValueError, TypeError):
        score = 0
    score = max(0, min(100, score))

    return {
        'verdict': parsed['verdict'],
        'confidence_score': score,
        'explanation': parsed.get('explanation', 'No explanation provided.')
    }


# ============================================================
#  START SERVER
# ============================================================

if __name__ == '__main__':
    key_status = '✅ Yes' if API_KEY and API_KEY != 'YOUR_API_KEY_HERE' else '❌ No (add to .env)'
    print(f'🚀 Fake News Detector running at http://localhost:{PORT}')
    print(f'   API key configured: {key_status}')
    app.run(host='0.0.0.0', port=PORT, debug=True)