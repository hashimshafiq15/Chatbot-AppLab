# AI Document Chatbot 🤖📄

A Python-based AI chatbot application that allows users to upload PDF documents and ask questions about their content using Google's Gemini AI and ChromaDB vector storage.

## 🎯 Features

- **PDF Document Upload**: Upload and process PDF documents with duplicate detection
- **Advanced Text Extraction**: Extract text using PyPDF2 with automatic OCR fallback (PyMuPDF + Tesseract) for image-based PDFs
- **Vector Storage**: Store document chunks in ChromaDB with persistent storage for efficient retrieval
- **AI-Powered Chat**: Ask questions and get contextually relevant answers using Google Gemini 2.5 Flash Lite
- **Document Management**: List and delete uploaded documents through the API
- **Modern UI**: Clean, responsive interface with drag-and-drop upload built with HTML, CSS, and JavaScript
- **Docker Support**: Full containerization with Docker Compose for easy deployment
- **Health Monitoring**: Built-in health check endpoint

## 🏗️ Architecture

The application consists of two main components:

### Backend (Python/Flask)
- **Framework**: Flask with CORS support and Blueprint architecture
- **AI Model**: Google Gemini 2.5 Flash Lite
- **Vector Database**: ChromaDB with persistent client
- **PDF Processing**: 
  - PyPDF2 for standard text extraction
  - PyMuPDF (fitz) for rendering PDF pages to images
  - Pytesseract for OCR on image-based PDFs
  - Automatic fallback to OCR when PyPDF2 extracts minimal text
- **API Endpoints**:
  - `GET /` - API information and endpoints list
  - `GET /api/health` - Health check with component status
  - `POST /api/upload` - Upload PDF documents (with duplicate detection)
  - `POST /api/chat` - Submit questions and get AI-generated answers
  - `GET /api/documents` - List all uploaded documents
  - `DELETE /api/documents/<doc_id>` - Delete a specific document

### Frontend (HTML/CSS/JavaScript)
- Pure vanilla JavaScript (no frameworks)
- Responsive design with modern CSS
- Drag-and-drop file upload
- Real-time chat interface
- Document management

## 📋 Prerequisites

- Python 3.11+
- Google Gemini API Key ([Get one here](https://makersuite.google.com/app/apikey))
- Docker and Docker Compose (for containerized deployment)

## 🚀 Setup Instructions

### Option 1: Local Development

#### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Activate the virtual environment:
- Windows:
  ```bash
  venv\Scripts\activate
  ```
- Linux/Mac:
  ```bash
  source venv/bin/activate
  ```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Set up environment variables:
```bash
# Create a .env file in the root directory
GEMINI_API_KEY=your_actual_api_key_here
```

6. Run the backend server:
```bash
python app.py
```

The backend will be available at `http://localhost:5000`

#### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Serve the files using any web server. For example, using Python's built-in server:
```bash
python -m http.server 8080
```

The frontend will be available at `http://localhost:8080`

### Option 2: Docker Deployment

1. Create a `.env` file in the root directory and add your Gemini API key:
```bash
GEMINI_API_KEY=your_actual_api_key_here
```

2. Build and run the containers:
```bash
docker-compose up --build
```

3. Access the application:
- Frontend: `http://localhost:8080`
- Backend API: `http://localhost:5000`

4. To stop the containers:
```bash
docker-compose down
```

## 📖 Usage

1. **Upload a Document**:
   - Click on the upload area or drag and drop a PDF file
   - Wait for the document to be processed (OCR will be attempted automatically if needed)
   - The document will appear in the "Uploaded Documents" list
   - Duplicate files are automatically detected and rejected

2. **Ask Questions**:
   - Type your question in the chat input
   - Press Enter or click the Send button
   - The AI will respond based on the content of your uploaded documents using RAG (Retrieval Augmented Generation)

3. **View Sources**:
   - Each AI response includes the source documents used to generate the answer

4. **Delete Documents**:
   - Use the DELETE endpoint to remove documents and free up storage

## 🔧 API Documentation

### Upload Document
```http
POST /api/upload
Content-Type: multipart/form-data

Body:
- file: PDF file (max 16MB)

Response:
{
  "message": "Document uploaded and processed successfully",
  "filename": "document.pdf",
  "doc_id": "uuid",
  "chunks": 10,
  "text_length": 5000
}
```

### Chat
```http
POST /api/chat
Content-Type: application/json

Body:
{
  "question": "What is the main topic?"
}

Response:
{
  "answer": "The main topic is...",
  "sources": ["document.pdf"]
}
```

### List Documents
```http
GET /api/documents

Response:
{
  "documents": [
    {
      "id": "uuid",
      "filename": "document.pdf"
    }
  ]
}
```

### Delete Document
```http
DELETE /api/documents/<doc_id>

Response:
{
  "message": "Document deleted successfully",
  "filename": "document.pdf",
  "chunks_deleted": 10
}
```

### Health Check
```http
GET /api/health

Response:
{
  "status": "healthy",
  "gemini_configured": true,
  "chromadb_configured": true
}
```

## 🛠️ Technology Stack

### Backend
- **Flask**: Web framework with Blueprint architecture for modular API design
- **Google Generative AI**: Gemini 2.5 Flash Lite model for AI responses
- **ChromaDB**: Vector database (v0.4.22) for semantic search with persistent storage
- **PyPDF2**: Primary PDF text extraction library
- **PyMuPDF (fitz)**: PDF rendering for OCR fallback
- **Pytesseract**: OCR engine for image-based PDF text extraction
- **Pillow**: Image processing for OCR operations
- **Flask-CORS**: Cross-origin resource sharing
- **python-dotenv**: Environment variable management
- **Werkzeug**: WSGI utility library for secure filename handling

### Frontend
- **HTML5**: Structure
- **CSS3**: Styling with gradients and animations
- **JavaScript (ES6+)**: Functionality and API integration

### DevOps
- **Docker**: Containerization with Python 3.11 slim image for backend
- **Docker Compose**: Multi-container orchestration
- **Nginx**: Frontend web server (alpine image)

## 📁 Project Structure

```
.
├── backend/
│   ├── app.py              # Main Flask application with initialization
│   ├── API.py              # API Blueprint with all endpoints and core functions
│   ├── requirements.txt    # Python dependencies
│   ├── Dockerfile          # Backend container config (Python 3.11 slim)
│   ├── uploads/            # Uploaded PDF files storage
│   ├── chroma_db/          # ChromaDB persistent storage
│   └── __pycache__/        # Python bytecode cache
├── frontend/
│   ├── index.html          # Main HTML file
│   ├── styles.css          # CSS styles
│   └── script.js           # JavaScript functionality
├── chroma_db/              # ChromaDB data (root level)
├── uploads/                # Uploads directory (root level)
├── docker-compose.yml      # Docker composition config
├── .env                    # Environment variables (not in repo)
└── README.md               # This file
```

## 🔒 Security Considerations

- API keys are stored in environment variables and loaded via python-dotenv
- File upload size is limited to 16MB (configurable in app.py)
- Only PDF files are accepted for upload
- Secure filename handling using Werkzeug's secure_filename
- Duplicate file detection prevents overwriting
- CORS is enabled for frontend-backend communication
- Input validation and sanitization is implemented
- Error handling with appropriate HTTP status codes

## 🐛 Troubleshooting

### Backend Issues

**Error: GEMINI_API_KEY not set**
- Make sure you've created a `.env` file with your API key
- Verify the API key is valid

**Error: Cannot connect to ChromaDB**
- Check if the `chroma_db` directory has proper permissions
- Delete the `chroma_db` folder and restart to reinitialize

**Error: PDF text extraction failed**
- Ensure the PDF is not password-protected or corrupted
- For image-based PDFs, OCR will be attempted automatically
- If OCR fails, ensure Tesseract is installed (for local development)
- PyMuPDF and pytesseract are required for OCR functionality
- Check if the PDF contains extractable text or valid images

### Frontend Issues

**Cannot connect to backend**
- Verify the backend is running on port 5000
- Check if CORS is properly configured
- Ensure the API_URL in `script.js` matches your backend URL

**File upload fails**
- Check file size (must be < 16MB)
- Ensure the file is a PDF format
- Check for duplicate filenames (delete existing file first)
- Check browser console for detailed error messages
- Verify backend is accessible at the correct URL

## 🚀 Deployment Considerations

For production deployment:

1. **Environment Variables**: Use secure methods to manage API keys
2. **HTTPS**: Enable SSL/TLS for secure communication
3. **Rate Limiting**: Implement rate limiting on API endpoints
4. **File Storage**: Consider using cloud storage (S3, GCS) for uploaded files
5. **Database**: Use persistent volumes for ChromaDB data
6. **Monitoring**: Add logging and monitoring solutions
7. **Authentication**: Implement user authentication if needed

## 📝 NLP and AI Model Selection

### Why Gemini 2.5 Flash Lite?
- **Advanced Language Understanding**: Excellent contextual comprehension
- **Fast Response Times**: Optimized for low latency in real-time chat
- **Cost-Effective**: Efficient pricing for API usage
- **Large Context Window**: Can process extensive document content
- **Multilingual Support**: Works with various languages
- **google-generativeai v0.3.2**: Stable Python SDK integration

### Why ChromaDB?
- **Efficient Vector Storage**: Optimized for embeddings with cosine similarity
- **Semantic Search**: Find relevant content based on meaning, not just keywords
- **Easy Integration**: Simple Python API with persistent client
- **Local Storage**: No external database required, uses SQLite backend
- **Scalable**: Can handle large document collections
- **Metadata Support**: Track document sources and chunk information

### Text Processing Strategy
- **Chunking**: 1000-character chunks with 200-character overlap for context preservation
- **RAG Pattern**: Retrieval Augmented Generation for accurate, context-based responses
- **OCR Fallback**: Automatic detection and OCR processing for image-based PDFs
- **Source Tracking**: Maintains document provenance for transparency

## 🎥 Presentation Points

1. **Application Design**:
   - Microservices architecture with separate backend and frontend containers
   - RESTful API design with Flask Blueprint pattern for modularity
   - Stateless communication with JSON payloads
   - Persistent storage for documents and vector database
   - Comprehensive error handling and logging
   - Duplicate detection and file management

2. **NLP and AI Approach**:
   - Advanced PDF processing with automatic OCR fallback for image-based PDFs
   - Document chunking (1000 chars) with overlap (200 chars) for better context retrieval
   - ChromaDB for vector embeddings and semantic search using cosine similarity
   - RAG (Retrieval Augmented Generation) pattern for accurate responses
   - Context-aware response generation using Gemini 2.5 Flash Lite
   - Source tracking and metadata management for transparency
   - Query optimization retrieving top 5 most relevant chunks

3. **Deployment**:
   - Fully Dockerized for easy deployment and scalability
   - Environment-based configuration with python-dotenv
   - Docker Compose orchestration with volume persistence
   - Nginx for efficient static file serving
   - Health check endpoints for monitoring
   - Python 3.11 slim base image for optimized container size

## 📄 License

This project is created for educational purposes as part of the AppLab AI/ML Engineer position assignment.

## 👨‍💻 Author

Created for AppLab AI/ML Engineer Position Assignment

## 🙏 Acknowledgments

- Google Generative AI for Gemini API
- ChromaDB for vector storage solution
- Flask community for excellent documentation
