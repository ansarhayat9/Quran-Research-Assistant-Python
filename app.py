import os
from flask import Flask, request, jsonify, send_from_directory
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()  # Load variables from .env if present

GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
	raise RuntimeError('GOOGLE_API_KEY environment variable not set')

genai.configure(api_key=GOOGLE_API_KEY)

app = Flask(__name__, static_url_path='', static_folder='.')


def build_prompt(question: str, lang: str) -> str:
	q = (question or '').strip()
	lower = q.lower()
	looks_like_count = any(x in lower for x in ['how many', 'count', 'times', 'kitni', 'kitne']) and any(
		y in lower for y in ['word', 'ayat', 'verse', 'verses', 'mentions', 'dafa', 'martaba']
	)
	looks_like_word = any(w in lower for w in [
		'word', 'jhoot', 'lie', 'truth', 'mercy', 'rahmah', 'sabr', 'patience', 'forgive', 'maghfirah', 'shirk', 'tawbah', 'iman', 'kufr',
		'جھوٹ', 'سچ', 'رحمت', 'صبر', 'ایمان'
	])

	guidance = (
		"\n\nPlease ensure the answer is medium length, structured, and includes a short 'References' section with explicit Quran citations like "
		"SurahName Surah:Ayah and quran.com links. If unsure about counts, state uncertainty and provide representative verses and a search link."
	)
	if looks_like_count or looks_like_word:
		guidance += (
			"\nIf the query is about a word frequency, note that counts vary with Arabic morphology and translations. "
			"Provide an approximate count only if confident; otherwise, list 3–6 key verses with brief context and include https://quran.com/search?q={term}."
		)
	guidance += ("\nRespond in Urdu (اردو) with clear, respectful language." if lang == 'ur' else "\nRespond in English with clear, respectful language.")
	return f"{q}{guidance}"


@app.route('/')
def root():
	return send_from_directory('.', 'index.html')


@app.post('/api/ask')
def api_ask():
	try:
		data = request.get_json(silent=True) or {}
		question = data.get('question')
		lang = (data.get('lang') or 'en').lower()
		if not isinstance(question, str) or not question.strip():
			return jsonify({ 'error': 'Question is required' }), 400

		model = genai.GenerativeModel('gemini-1.5-flash')
		result = model.generate_content(build_prompt(question, lang))
		text = getattr(result, 'text', '') or ''
		return jsonify({ 'answer': text })
	except Exception as e:
		return jsonify({ 'error': str(e) }), 500


if __name__ == '__main__':
	# For local testing: flask run would also work, but this keeps parity with node server
	port = int(os.environ.get('PORT', '3000'))
	app.run(host='0.0.0.0', port=port)
