from flask import Flask
from flask_cors import CORS
import os
from dotenv import load_dotenv
import google.generativeai as genai
import chromadb
import logging

# Load environment variables from .env file
load_dotenv()

# Import API Blueprint
from API import api_bp, init_api

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Create uploads directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize Gemini
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash-lite')
else:
    logger.warning("GEMINI_API_KEY not set. Please set the environment variable.")
    model = None

# Initialize ChromaDB with new API
chroma_client = chromadb.PersistentClient(path="./chroma_db")

# Get or create collection
try:
    collection = chroma_client.get_or_create_collection(
        name="documents",
        metadata={"hnsw:space": "cosine"}
    )
except Exception as e:
    logger.error(f"Error initializing ChromaDB: {e}")
    collection = None

# Initialize API with dependencies
init_api(app.config, model, collection)

# Register API Blueprint
app.register_blueprint(api_bp)

# Root route for helpful information
@app.route('/')
def index():
    return {
        'message': 'AI Chatbot API Server',
        'status': 'running',
        'endpoints': {
            'health': '/api/health',
            'upload': '/api/upload (POST)',
            'chat': '/api/chat (POST)',
            'documents': '/api/documents (GET)'
        },
        'frontend': 'Open frontend/index.html in your browser'
    }


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
