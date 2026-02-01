from flask import Blueprint, Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import logging

logger = logging.getLogger(__name__)

# Configure Tesseract path for Windows
try:
    import pytesseract
    # Set Tesseract path for Windows (adjust if needed)
    if os.name == 'nt':  # Windows
        tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        if os.path.exists(tesseract_path):
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
except ImportError:
    pass

# Create Blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# These will be set by app.py
app_config = {}
model = None
collection = None

def init_api(config, gemini_model, chroma_collection):
    """Initialize API with required dependencies"""
    global app_config, model, collection
    app_config = config
    model = gemini_model
    collection = chroma_collection


def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'pdf'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_text_from_pdf(pdf_path):
    """Extract text from PDF file with OCR fallback"""
    import PyPDF2
    try:
        text = ""
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        
        logger.info(f"PyPDF2 extracted {len(text.strip())} characters")
        
        # If no text extracted or very little, try OCR with pymupdf (fitz)
        if len(text.strip()) < 50:
            logger.info(f"PyPDF2 extracted minimal text, attempting OCR with PyMuPDF...")
            try:
                import fitz  # PyMuPDF
                import pytesseract
                from PIL import Image
                import io
                
                # Open PDF with PyMuPDF
                doc = fitz.open(pdf_path)
                ocr_text = ""
                
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    
                    # Convert page to image
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better OCR
                    img_data = pix.tobytes("png")
                    image = Image.open(io.BytesIO(img_data))
                    
                    # Extract text using OCR
                    page_text = pytesseract.image_to_string(image)
                    ocr_text += page_text + "\n"
                    logger.info(f"OCR extracted {len(page_text)} chars from page {page_num+1}")
                
                doc.close()
                
                if len(ocr_text.strip()) > len(text.strip()):
                    text = ocr_text
                    logger.info(f"Using OCR text ({len(text.strip())} chars)")
            except ImportError as ie:
                logger.warning(f"OCR libraries not available: {ie}. Install PyMuPDF and pytesseract for image-based PDFs.")
            except Exception as ocr_error:
                logger.warning(f"OCR failed: {ocr_error}. Using PyPDF2 text.")
        
        return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        raise


def chunk_text(text, chunk_size=1000, overlap=200):
    """Split text into chunks with overlap"""
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap
    
    return chunks


def store_in_chromadb(text, filename):
    """Store text chunks in ChromaDB"""
    import uuid
    
    if not collection:
        raise Exception("ChromaDB collection not initialized")
    
    chunks = chunk_text(text)
    doc_id = str(uuid.uuid4())
    
    # Store each chunk
    ids = []
    documents = []
    metadatas = []
    
    for i, chunk in enumerate(chunks):
        chunk_id = f"{doc_id}_chunk_{i}"
        ids.append(chunk_id)
        documents.append(chunk)
        metadatas.append({
            "filename": filename,
            "doc_id": doc_id,
            "chunk_index": i
        })
    
    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas
    )
    
    return doc_id, len(chunks)


def query_chromadb(query_text, n_results=5):
    """Query ChromaDB for relevant documents"""
    if not collection:
        raise Exception("ChromaDB collection not initialized")
    
    results = collection.query(
        query_texts=[query_text],
        n_results=n_results
    )
    
    return results


def generate_response(question, context):
    """Generate response using Gemini"""
    if not model:
        return "Error: Gemini API is not configured. Please set GEMINI_API_KEY environment variable."
    
    prompt = f"""You are a helpful AI assistant. Answer the user's question based on the provided context.
If the answer cannot be found in the context, say so politely.

Context:
{context}

Question: {question}

Answer:"""
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        return f"Error generating response: {str(e)}"


@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'gemini_configured': model is not None,
        'chromadb_configured': collection is not None
    })


@api_bp.route('/upload', methods=['POST'])
def upload_document():
    """Upload and process PDF document"""
    try:
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        # Check if file is selected
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Check file extension
        if not allowed_file(file.filename):
            return jsonify({'error': 'Only PDF files are allowed'}), 400
        
        # Check for duplicate filename
        filename = secure_filename(file.filename)
        if collection:
            all_docs = collection.get()
            if all_docs['metadatas']:
                for metadata in all_docs['metadatas']:
                    if metadata.get('filename') == filename:
                        return jsonify({'error': 'File already uploaded. Please delete the existing file first or upload a different file.'}), 400
        
        # Save file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app_config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Extract text
        text = extract_text_from_pdf(filepath)
        
        if not text.strip():
            os.remove(filepath)
            return jsonify({'error': 'No text could be extracted from PDF'}), 400
        
        # Store in ChromaDB
        doc_id, num_chunks = store_in_chromadb(text, filename)
        
        logger.info(f"Successfully processed document: {filename}")
        
        return jsonify({
            'message': 'Document uploaded and processed successfully',
            'filename': filename,
            'doc_id': doc_id,
            'chunks': num_chunks,
            'text_length': len(text)
        }), 200
        
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/chat', methods=['POST'])
def chat():
    """Chat endpoint for asking questions"""
    try:
        data = request.get_json()
        
        if not data or 'question' not in data:
            return jsonify({'error': 'No question provided'}), 400
        
        question = data['question']
        
        # Query ChromaDB for relevant context
        results = query_chromadb(question, n_results=5)
        
        # Combine relevant documents as context
        context = "\n\n".join(results['documents'][0]) if results['documents'][0] else ""
        
        if not context:
            return jsonify({
                'answer': 'I don\'t have any documents to reference. Please upload a PDF document first.',
                'sources': []
            }), 200
        
        # Generate response using Gemini
        answer = generate_response(question, context)
        
        # Extract source information
        sources = []
        if results['metadatas'][0]:
            seen_files = set()
            for metadata in results['metadatas'][0]:
                if metadata['filename'] not in seen_files:
                    sources.append(metadata['filename'])
                    seen_files.add(metadata['filename'])
        
        return jsonify({
            'answer': answer,
            'sources': sources
        }), 200
        
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/documents', methods=['GET'])
def list_documents():
    """List all uploaded documents"""
    try:
        if not collection:
            return jsonify({'documents': []}), 200
        
        # Get all documents from collection
        all_docs = collection.get()
        
        # Extract unique filenames
        unique_docs = {}
        if all_docs['metadatas']:
            for metadata in all_docs['metadatas']:
                filename = metadata.get('filename')
                doc_id = metadata.get('doc_id')
                if filename and doc_id and doc_id not in unique_docs:
                    unique_docs[doc_id] = filename
        
        documents = [{'id': doc_id, 'filename': filename} 
                    for doc_id, filename in unique_docs.items()]
        
        return jsonify({'documents': documents}), 200
        
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/documents/<doc_id>', methods=['DELETE'])
def delete_document(doc_id):
    """Delete a document and its chunks from ChromaDB"""
    try:
        if not collection:
            return jsonify({'error': 'ChromaDB not initialized'}), 500
        
        # Get all documents to find the filename
        all_docs = collection.get()
        filename = None
        
        if all_docs['metadatas']:
            for metadata in all_docs['metadatas']:
                if metadata.get('doc_id') == doc_id:
                    filename = metadata.get('filename')
                    break
        
        if not filename:
            return jsonify({'error': 'Document not found'}), 404
        
        # Delete all chunks with this doc_id
        ids_to_delete = []
        if all_docs['ids']:
            for i, metadata in enumerate(all_docs['metadatas']):
                if metadata.get('doc_id') == doc_id:
                    ids_to_delete.append(all_docs['ids'][i])
        
        if ids_to_delete:
            collection.delete(ids=ids_to_delete)
        
        # Delete the physical file if it exists
        filepath = os.path.join(app_config['UPLOAD_FOLDER'], filename)
        if os.path.exists(filepath):
            os.remove(filepath)
        
        logger.info(f"Deleted document: {filename} ({len(ids_to_delete)} chunks)")
        
        return jsonify({
            'message': 'Document deleted successfully',
            'filename': filename,
            'chunks_deleted': len(ids_to_delete)
        }), 200
        
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        return jsonify({'error': str(e)}), 500

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