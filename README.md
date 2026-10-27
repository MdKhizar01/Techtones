# Techtones — Text, PDF, and Image to Audio

Original Flask application for converting written content to speech. Includes PDF text extraction, image OCR, generated audio history, and user registration/login endpoints.

## Stack

Python, Flask, gTTS, PyPDF2, Pillow, Tesseract OCR, SQLAlchemy, and bcrypt.

## Local setup

Install Python and the Tesseract OCR executable, then run:

```bash
python -m venv .venv
# Activate the environment using the command for your operating system.
python -m pip install -r requirements.txt
cp .env.example .env
python app.py
```

The example configuration uses a local SQLite database. The app creates database tables and its audio output folder on startup. The default port is 5000; the PORT environment variable can override it.

Speech generation uses an external service and requires internet access. OCR requires Tesseract to be installed and available on PATH.

## API

| Method | Route | Input |
| --- | --- | --- |
| POST | /convert_text | JSON with a text field |
| POST | /convert_pdf | Multipart file field containing a PDF |
| POST | /convert_image | Multipart file field containing an image |
| GET | /audio-history | List generated audio records |
| POST | /register | JSON: username, email, password |
| POST | /login | JSON: email, password |
| GET | /static/audio/<filename> | Generated MP3 |

```bash
curl -X POST http://localhost:5000/convert_text \
  -H 'Content-Type: application/json' \
  -d '{"text":"Hello from Techtones"}'
```

## Project status

Original coursework source is preserved on the default master branch. The earlier standalone conversion API is in [flask-backend](https://github.com/MdKhizar01/flask-backend).

Login validates credentials but does not issue a session or token. The current source enables Flask debug mode when run directly; treat it as a development application. End-to-end OCR and speech conversion were not rerun during this documentation update.

Generated MP3s, Python caches, the runtime database, and local environment configuration were removed from the current tree and added to ignore rules. Existing Git history was retained.
