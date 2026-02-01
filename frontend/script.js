// API Configuration
const API_URL = 'http://localhost:5000/api';

// DOM Elements
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const uploadStatus = document.getElementById('uploadStatus');
const documentsContainer = document.getElementById('documentsContainer');
const chatContainer = document.getElementById('chatContainer');
const questionInput = document.getElementById('questionInput');
const sendButton = document.getElementById('sendButton');

// State
let hasDocuments = false;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    checkHealth();
    loadDocuments();
});

// Setup Event Listeners
function setupEventListeners() {
    // Upload area click
    uploadArea.addEventListener('click', () => {
        fileInput.click();
    });

    // File input change
    fileInput.addEventListener('change', handleFileSelect);

    // Drag and drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('drag-over');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('drag-over');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('drag-over');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    });

    // Send message
    sendButton.addEventListener('click', sendMessage);
    
    questionInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !sendButton.disabled) {
            sendMessage();
        }
    });
}

// Check API Health
async function checkHealth() {
    try {
        const response = await fetch(`${API_URL}/health`);
        const data = await response.json();
        
        if (!data.gemini_configured) {
            showStatus('Warning: Gemini API not configured. Please set GEMINI_API_KEY.', 'error');
        }
    } catch (error) {
        showStatus('Error: Cannot connect to backend server. Make sure it\'s running on port 5000.', 'error');
    }
}

// Handle File Select
function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        handleFile(file);
    }
}

// Handle File Upload
async function handleFile(file) {
    console.log('Handling file:', file.name, file.size);
    
    // Validate file type
    if (!file.name.toLowerCase().endsWith('.pdf')) {
        showStatus('❌ Please upload PDF files only. Other formats are not supported.', 'error');
        return;
    }

    // Validate file size
    if (file.size > 16 * 1024 * 1024) {
        showStatus('❌ File size must be less than 16MB.', 'error');
        return;
    }

    // Show loading
    showStatus('Uploading and processing document...', 'loading');

    // Upload file
    const formData = new FormData();
    formData.append('file', file);

    try {
        console.log('Uploading to:', `${API_URL}/upload`);
        const response = await fetch(`${API_URL}/upload`, {
            method: 'POST',
            body: formData
        });

        console.log('Response status:', response.status);
        const data = await response.json();
        console.log('Response data:', data);

        if (response.ok) {
            console.log('Upload successful - chat messages before loadDocuments:', chatContainer.querySelectorAll('.message').length);
            showStatus(`✓ ${data.message} (${data.chunks} chunks created)`, 'success');
            loadDocuments();
            console.log('After loadDocuments - chat messages:', chatContainer.querySelectorAll('.message').length);
            enableChat();
            console.log('After enableChat - chat messages:', chatContainer.querySelectorAll('.message').length);
            
            // Clear file input
            fileInput.value = '';
        } else {
            showStatus(`Error: ${data.error}`, 'error');
            console.error('Upload error:', data);
        }
    } catch (error) {
        showStatus(`Error: ${error.message}`, 'error');
        console.error('Upload exception:', error);
    }
}

// Load Documents List
async function loadDocuments() {
    console.log('loadDocuments called - chat messages before:', chatContainer.querySelectorAll('.message').length);
    try {
        const response = await fetch(`${API_URL}/documents`);
        const data = await response.json();

        if (data.documents && data.documents.length > 0) {
            hasDocuments = true;
            enableChat();
            
            documentsContainer.innerHTML = data.documents.map(doc => `
                <div class="document-item">
                    <span class="doc-name">📄 ${doc.filename}</span>
                    <button class="delete-btn" data-doc-id="${doc.id}" data-filename="${escapeHtml(doc.filename)}">🗑️</button>
                </div>
            `).join('');
            
            // Add event listeners to delete buttons
            documentsContainer.querySelectorAll('.delete-btn').forEach(btn => {
                btn.addEventListener('click', function() {
                    const docId = this.getAttribute('data-doc-id');
                    const filename = this.getAttribute('data-filename');
                    deleteDocument(docId, filename);
                });
            });
        } else {
            documentsContainer.innerHTML = '<p style="color: #666; font-size: 0.9em;">No documents uploaded yet.</p>';
        }
        
        console.log('loadDocuments finished - chat messages after:', chatContainer.querySelectorAll('.message').length);
    } catch (error) {
        console.error('Error loading documents:', error);
    }
}

// Show Status Message
function showStatus(message, type) {
    uploadStatus.textContent = message;
    uploadStatus.className = `status-message ${type}`;
    
    if (type !== 'loading') {
        setTimeout(() => {
            uploadStatus.style.display = 'none';
        }, 5000);
    }
}

// Enable Chat
function enableChat() {
    console.log('enableChat called');
    console.log('Current chat messages:', chatContainer.querySelectorAll('.message').length);
    
    questionInput.disabled = false;
    sendButton.disabled = false;
    
    // Remove welcome message only if it exists and there are no other messages
    const welcomeMessage = chatContainer.querySelector('.welcome-message');
    const otherMessages = chatContainer.querySelectorAll('.message');
    
    console.log('Welcome message exists:', !!welcomeMessage);
    console.log('Other messages count:', otherMessages.length);
    
    // Only remove welcome message if there are no actual chat messages
    if (welcomeMessage && otherMessages.length === 0) {
        console.log('Removing welcome message');
        welcomeMessage.remove();
    } else {
        console.log('Not removing anything - preserving chat history');
    }
}

// Send Message
async function sendMessage() {
    const question = questionInput.value.trim();
    
    if (!question) {
        return;
    }

    // Add user message
    addMessage(question, 'user');
    questionInput.value = '';

    // Disable input while processing
    questionInput.disabled = true;
    sendButton.disabled = true;

    // Add loading message
    const loadingId = addLoadingMessage();

    try {
        const response = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ question })
        });

        const data = await response.json();

        // Remove loading message
        removeLoadingMessage(loadingId);

        if (response.ok) {
            addMessage(data.answer, 'bot', data.sources);
        } else {
            addMessage(`Error: ${data.error}`, 'bot');
        }
    } catch (error) {
        removeLoadingMessage(loadingId);
        addMessage(`Error: ${error.message}`, 'bot');
    }

    // Re-enable input
    questionInput.disabled = false;
    sendButton.disabled = false;
    questionInput.focus();
}

// Add Message to Chat
function addMessage(text, sender, sources = []) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    let messageHTML = `<p>${escapeHtml(text)}</p>`;
    
    // Sources display removed as per user request
    
    messageDiv.innerHTML = messageHTML;
    chatContainer.appendChild(messageDiv);
    
    // Scroll to bottom
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Add Loading Message
function addLoadingMessage() {
    const messageDiv = document.createElement('div');
    const loadingId = 'loading-' + Date.now();
    messageDiv.id = loadingId;
    messageDiv.className = 'message loading';
    messageDiv.innerHTML = `
        <div class="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
        </div>
    `;
    
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    
    return loadingId;
}

// Remove Loading Message
function removeLoadingMessage(loadingId) {
    const loadingMessage = document.getElementById(loadingId);
    if (loadingMessage) {
        loadingMessage.remove();
    }
}

// Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Delete Document
async function deleteDocument(docId, filename) {
    console.log('deleteDocument called - chat messages before:', chatContainer.querySelectorAll('.message').length);
    
    if (!confirm(`Are you sure you want to delete "${filename}"?`)) {
        return;
    }
    
    try {
        showStatus('Deleting document...', 'loading');
        
        const response = await fetch(`${API_URL}/documents/${docId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showStatus(`✓ ${data.message}`, 'success');
            
            // Check if there are no documents left BEFORE reloading
            const docsResponse = await fetch(`${API_URL}/documents`);
            const docsData = await docsResponse.json();
            
            const noDocsLeft = !docsData.documents || docsData.documents.length === 0;
            
            // Reload document list
            console.log('Before loadDocuments in delete - chat messages:', chatContainer.querySelectorAll('.message').length);
            loadDocuments();
            console.log('After loadDocuments in delete - chat messages:', chatContainer.querySelectorAll('.message').length);
            
            if (noDocsLeft) {
                hasDocuments = false;
                questionInput.disabled = true;
                sendButton.disabled = true;
                
                // Only add welcome message back if there are no chat messages
                const existingMessages = chatContainer.querySelectorAll('.message');
                if (existingMessages.length === 0 && !chatContainer.querySelector('.welcome-message')) {
                    const welcomeDiv = document.createElement('div');
                    welcomeDiv.className = 'welcome-message';
                    welcomeDiv.innerHTML = `
                        <p>👋 Welcome! Upload a PDF document to get started.</p>
                        <p>Once uploaded, you can ask questions about the document content.</p>
                    `;
                    chatContainer.appendChild(welcomeDiv);
                }
            }
        } else {
            showStatus(`Error: ${data.error}`, 'error');
        }
    } catch (error) {
        showStatus(`Error: ${error.message}`, 'error');
        console.error('Delete error:', error);
    }
}
