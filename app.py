import os
import uuid
import datetime
import logging
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from gtts import gTTS
import PyPDF2
from PIL import Image
import pytesseract
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import bcrypt
from dotenv import load_dotenv

app = Flask(__name__)
CORS(app)

# Load environment variables
load_dotenv()

# Set up the path for static files
app.config['UPLOAD_FOLDER'] = 'static/audio'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# --- DATABASE SETUP ---
# Configure your database URL from environment variables
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Create a configured "Session" class and a session instance
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for our models
Base = declarative_base()

# Define a model for audio files
class AudioFile(Base):
    __tablename__ = 'audio_files'
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# Define a model for users (expand as needed)
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)  # Add hashed password column
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# Create all tables in the database (this runs only once when the app starts)
Base.metadata.create_all(bind=engine)

# --- ROUTES ---

# Convert Text to Audio
@app.route('/convert_text', methods=['POST'])
def convert_text():
    try:
        text = request.json['text']
        tts = gTTS(text)

        # Generate a unique filename for each audio file
        audio_filename = f"{uuid.uuid4()}.mp3"
        audio_path = os.path.join(app.config['UPLOAD_FOLDER'], audio_filename)
        tts.save(audio_path)

        # Save record to database
        db = SessionLocal()
        audio_file = AudioFile(filename=audio_filename)
        db.add(audio_file)
        db.commit()
        db.close()

        # Return the relative path under the /static folder
        return jsonify({
            "message": "Text converted to audio successfully",
            "audio_path": f"/static/audio/{audio_filename}"
        })
    except Exception as e:
        logging.error(f"Text conversion error: {e}")
        return jsonify({"message": "Text conversion failed"}), 500

# Convert PDF to Audio (extract text from PDF)
@app.route('/convert_pdf', methods=['POST'])
def convert_pdf():
    try:
        file = request.files['file']
        reader = PyPDF2.PdfReader(file)
        text = ''
        for page in reader.pages:
            text += page.extract_text()

        tts = gTTS(text)

        # Generate a unique filename for each audio file
        audio_filename = f"{uuid.uuid4()}.mp3"
        audio_path = os.path.join(app.config['UPLOAD_FOLDER'], audio_filename)
        tts.save(audio_path)

        # Save record to database
        db = SessionLocal()
        audio_file = AudioFile(filename=audio_filename)
        db.add(audio_file)
        db.commit()
        db.close()

        return jsonify({
            "message": "PDF converted to audio successfully",
            "audio_path": f"/static/audio/{audio_filename}"
        })
    except Exception as e:
        logging.error(f"PDF conversion error: {e}")
        return jsonify({"message": "PDF conversion failed"}), 500

# Convert Image to Audio (OCR)
@app.route('/convert_image', methods=['POST'])
def convert_image():
    try:
        file = request.files['file']
        img = Image.open(file)
        text = pytesseract.image_to_string(img)

        tts = gTTS(text)

        # Generate a unique filename for each audio file
        audio_filename = f"{uuid.uuid4()}.mp3"
        audio_path = os.path.join(app.config['UPLOAD_FOLDER'], audio_filename)
        tts.save(audio_path)

        # Save record to database
        db = SessionLocal()
        audio_file = AudioFile(filename=audio_filename)
        db.add(audio_file)
        db.commit()
        db.close()

        return jsonify({
            "message": "Image converted to audio successfully",
            "audio_path": f"/static/audio/{audio_filename}"
        })
    except Exception as e:
        logging.error(f"Image conversion error: {e}")
        return jsonify({"message": "Image conversion failed"}), 500

# Audio History Endpoint
@app.route('/audio-history', methods=['GET'])
def audio_history():
    try:
        db = SessionLocal()
        audios = db.query(AudioFile).all()
        # Create a list of dictionaries with id and filename
        audio_list = [{"id": audio.id, "filename": audio.filename} for audio in audios]
        db.close()
        return jsonify(audio_list)
    except Exception as e:
        logging.error(f"Audio history error: {e}")
        return jsonify({"message": "Error retrieving audio history"}), 500

# User Registration Endpoint
@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.json
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        db = SessionLocal()
        existing_user = db.query(User).filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            db.close()
            return jsonify({"message": "User already exists"}), 400

        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        new_user = User(username=username, email=email, hashed_password=hashed_password)
        db.add(new_user)
        db.commit()
        db.close()
        return jsonify({"message": "Registration successful"})
    except Exception as e:
        logging.error(f"Registration error: {e}")
        return jsonify({"message": "Registration failed"}), 500

# User Login Endpoint
@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')

        db = SessionLocal()
        user = db.query(User).filter(User.email == email).first()
        db.close()

        if user and bcrypt.checkpw(password.encode('utf-8'), user.hashed_password.encode('utf-8')):
            return jsonify({"message": "Login successful"})
        else:
            return jsonify({"message": "Invalid credentials"}), 401
    except Exception as e:
        logging.error(f"Login error: {e}")
        return jsonify({"message": "Login failed"}), 500

# Serve audio files
@app.route('/static/audio/<filename>')
def serve_audio(filename):
    return send_from_directory(os.path.join(app.root_path, 'static', 'audio'), filename)

if __name__ == '__main__':
    # Dynamic port for deployment (e.g., Render)
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
