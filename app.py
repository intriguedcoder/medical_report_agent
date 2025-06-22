
from flask import Flask, request, jsonify, render_template_string, send_from_directory, session
from agents.orchestrator_agent import OrchestratorAgent
import os
import tempfile
import hashlib
import shutil
from dotenv import load_dotenv
from config import Config
from translations import UI_TRANSLATIONS, AUDIO_LANGUAGES

load_dotenv()

app = Flask(__name__)
Config.init_app(app)  # Initialize directories and settings
app.config.from_object(Config)

orchestrator = OrchestratorAgent()

# Add processing files tracking to prevent duplicates
processing_files = set()

def get_selected_language():
    """Get selected language from session or default to Hindi"""
    return session.get('selected_language', 'hi-IN')

def get_ui_text(key):
    """Get UI text in current language"""
    selected_lang = get_selected_language()
    return UI_TRANSLATIONS.get(selected_lang, UI_TRANSLATIONS['hi-IN']).get(key, key)

# Enhanced web interface with email functionality
WEB_INTERFACE = """
<!DOCTYPE html>
<html>
<head>
    <title>{{ ui_text.title }} - Medical Report Analyzer</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { 
            max-width: 900px; 
            margin: 0 auto; 
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(45deg, #4CAF50, #45a049);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .header p { font-size: 1.2em; opacity: 0.9; }
        .content { padding: 40px; }
        
        .language-selector {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
            border-left: 5px solid #4CAF50;
        }
        .language-selector h3 {
            margin-bottom: 15px;
            color: #333;
        }
        .language-note {
            font-size: 0.9em;
            color: #666;
            margin-bottom: 15px;
            font-style: italic;
        }
        .language-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 10px;
        }
        .language-btn {
            background: white;
            border: 2px solid #ddd;
            padding: 12px;
            border-radius: 8px;
            cursor: pointer;
            text-align: center;
            transition: all 0.3s ease;
            font-size: 0.9em;
        }
        .language-btn:hover {
            border-color: #4CAF50;
            background: #f0f8f0;
        }
        .language-btn.selected {
            border-color: #4CAF50;
            background: #4CAF50;
            color: white;
        }
        
        .email-options {
            background: #e3f2fd;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            border-left: 5px solid #2196F3;
        }
        .email-options h4 {
            margin-bottom: 15px;
            color: #1976D2;
        }
        .patient-info {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
            margin-top: 15px;
        }
        .patient-info input {
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 0.9em;
        }
        
        .upload-area { 
            border: 3px dashed #ddd; 
            padding: 60px 20px; 
            text-align: center; 
            margin: 30px 0;
            border-radius: 15px;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        .upload-area:hover { 
            border-color: #4CAF50; 
            background: #f9f9f9;
        }
        .upload-area.dragover {
            border-color: #4CAF50;
            background: #e8f5e8;
        }
        .file-input { display: none; }
        .upload-btn {
            background: #4CAF50;
            color: white;
            padding: 15px 30px;
            border: none;
            border-radius: 25px;
            font-size: 1.1em;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-top: 20px;
        }
        .upload-btn:hover { 
            background: #45a049; 
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        .analyze-btn {
            background: #2196F3;
            color: white;
            padding: 15px 40px;
            border: none;
            border-radius: 25px;
            font-size: 1.2em;
            cursor: pointer;
            width: 100%;
            margin-top: 20px;
            transition: all 0.3s ease;
        }
        .analyze-btn:hover { 
            background: #1976D2; 
            transform: translateY(-2px);
        }
        .analyze-btn:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }
        .result { 
            margin-top: 30px; 
            padding: 30px; 
            background: #f8f9fa; 
            border-radius: 15px;
            border-left: 5px solid #4CAF50;
        }
        .result h3 { 
            color: #333; 
            margin-bottom: 20px;
            font-size: 1.5em;
        }
        .result-text { 
            line-height: 1.8; 
            color: #555;
            white-space: pre-line;
            font-size: 1.1em;
        }
        .audio-player { 
            width: 100%; 
            margin-top: 20px;
            border-radius: 10px;
            background: #fff;
            padding: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
        }
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #4CAF50;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }
        .feature {
            text-align: center;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
        }
        .feature-icon {
            font-size: 2em;
            margin-bottom: 10px;
        }
        .error {
            background: #ffebee;
            color: #c62828;
            padding: 15px;
            border-radius: 10px;
            margin-top: 20px;
            border-left: 5px solid #f44336;
        }
        .language-info {
            background: #e3f2fd;
            padding: 15px;
            border-radius: 10px;
            margin-top: 20px;
            border-left: 5px solid #2196F3;
        }
        .success {
            background: #e8f5e9;
            color: #2e7d32;
            padding: 15px;
            border-radius: 10px;
            margin-top: 20px;
            border-left: 5px solid #4caf50;
        }
        .file-info {
            background: #f0f0f0;
            padding: 10px;
            border-radius: 5px;
            margin-top: 10px;
            font-size: 0.9em;
            color: #666;
        }
        .email-result {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            padding: 20px;
            margin-top: 20px;
            border-radius: 10px;
        }
        .email-urgency {
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 15px;
            font-weight: bold;
            text-align: center;
        }
        .urgency-high { background: #f44336; color: white; }
        .urgency-medium { background: #ff9800; color: white; }
        .urgency-low { background: #2196f3; color: white; }
        .urgency-routine { background: #4caf50; color: white; }
        .email-field {
            background: white;
            border: 1px solid #ddd;
            padding: 10px;
            margin: 10px 0;
            border-radius: 5px;
            font-family: monospace;
        }
        .email-actions {
            display: flex;
            gap: 10px;
            margin-top: 15px;
        }
        .email-actions button {
            flex: 1;
            padding: 10px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 0.9em;
        }
        .copy-btn { background: #4CAF50; color: white; }
        .download-btn { background: #2196F3; color: white; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{ ui_text.title }}</h1>
            <p>{{ ui_text.subtitle }}</p>
        </div>
        
        <div class="content">
            <div class="language-selector">
                <h3>{{ ui_text.choose_language }}</h3>
                <div class="language-note">
                    📝 Text display and 🔊 audio will both use the selected language
                </div>
                <div class="language-grid">
                    {% for lang_code, lang_info in audio_languages.items() %}
                    <div class="language-btn {% if current_language == lang_code %}selected{% endif %}" 
                         data-lang="{{ lang_code }}" onclick="changeLanguage('{{ lang_code }}')">
                        <div>{{ lang_info.flag }} {{ lang_info.name }}</div>
                        <small>{{ lang_code.split('-')[0].upper() }}</small>
                    </div>
                    {% endfor %}
                </div>
            </div>
            
            <div class="features">
                <div class="feature">
                    <div class="feature-icon">📸</div>
                    <h4>{{ ui_text.upload_photo }}</h4>
                    <p>{{ ui_text.upload_desc }}</p>
                </div>
                <div class="feature">
                    <div class="feature-icon">🔍</div>
                    <h4>{{ ui_text.smart_analysis }}</h4>
                    <p>{{ ui_text.smart_desc }}</p>
                </div>
                <div class="feature">
                    <div class="feature-icon">🎯</div>
                    <h4>{{ ui_text.multilingual }}</h4>
                    <p>{{ ui_text.multilingual_desc }}</p>
                </div>
            </div>
            
            <form id="uploadForm" enctype="multipart/form-data" method="POST">
                <div class="email-options">
                    <h4>📧 Doctor Consultation Email</h4>
                    <label>
                        <input type="checkbox" id="generateEmail" checked> 
                        Generate email draft for doctor consultation
                    </label>
                    
                    <div id="patientInfo" class="patient-info">
                        <input type="text" id="patientName" placeholder="Patient Name (Optional)">
                        <input type="text" id="patientAge" placeholder="Age (Optional)">
                        <input type="email" id="patientEmail" placeholder="Your Email (Optional)">
                        <input type="tel" id="patientPhone" placeholder="Phone Number (Optional)">
                    </div>
                </div>
                
                <div class="upload-area" id="uploadArea">
                    <div class="feature-icon">📋</div>
                    <h3>{{ ui_text.upload_report }}</h3>
                    <p>{{ ui_text.click_or_drag }}</p>
                    <input type="file" id="imageFile" name="image" accept="image/*" class="file-input" required>
                    <button type="button" class="upload-btn" id="chooseFileBtn">
                        {{ ui_text.choose_file }}
                    </button>
                    <div id="fileName" class="file-info" style="display: none;"></div>
                </div>
                <button type="submit" class="analyze-btn" id="analyzeBtn" disabled>
                    {{ ui_text.analyze_report }}
                </button>
            </form>
            
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p>{{ ui_text.analyzing }}</p>
            </div>
            
            <div id="languageInfo" class="language-info" style="display:none;">
                <strong>{{ ui_text.detected_language }}</strong> <span id="detectedLang"></span>
            </div>
            
            <div id="result" class="result" style="display:none;">
                <h3>{{ ui_text.analysis_result }}</h3>
                <div id="resultText" class="result-text"></div>
                <audio id="resultAudio" class="audio-player" controls style="display:none;">
                    Your browser does not support the audio player.
                </audio>
            </div>
            
            <div id="emailResult" class="email-result" style="display:none;">
                <h3>📧 Doctor Consultation Email Draft</h3>
                <div class="email-urgency" id="emailUrgency"></div>
                <div class="email-content">
                    <h4>Subject:</h4>
                    <div id="emailSubject" class="email-field"></div>
                    <h4>Email Body:</h4>
                    <textarea id="emailBody" class="email-field" rows="20"></textarea>
                </div>
                <div class="email-actions">
                    <button onclick="copyEmailToClipboard()" class="copy-btn">📋 Copy Email</button>
                    <button onclick="downloadEmail()" class="download-btn">💾 Download as Text</button>
                </div>
            </div>
            
            <div id="error" class="error" style="display:none;"></div>
            <div id="success" class="success" style="display:none;"></div>
        </div>
    </div>

    <script>
        let selectedLanguage = '{{ current_language }}';
        let isSubmitting = false;
        const uiTexts = {{ ui_text_json|safe }};
        
        function changeLanguage(lang) {
            selectedLanguage = lang;
            
            // Update visual selection
            document.querySelectorAll('[data-lang]').forEach(btn => {
                btn.classList.remove('selected');
            });
            document.querySelector(`[data-lang="${lang}"]`).classList.add('selected');
            
            // Save to session and reload page to update UI
            fetch('/set_language', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({language: lang})
            }).then(() => {
                window.location.reload();
            });
        }
        
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('imageFile');
        const fileName = document.getElementById('fileName');
        const analyzeBtn = document.getElementById('analyzeBtn');
        const chooseFileBtn = document.getElementById('chooseFileBtn');
        const loading = document.getElementById('loading');
        const result = document.getElementById('result');
        const error = document.getElementById('error');
        const success = document.getElementById('success');
        const languageInfo = document.getElementById('languageInfo');
        const emailResult = document.getElementById('emailResult');
        
        // Enhanced drag and drop handling
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.stopPropagation();
            uploadArea.classList.add('dragover');
        });
        
        uploadArea.addEventListener('dragleave', (e) => {
            e.preventDefault();
            e.stopPropagation();
            uploadArea.classList.remove('dragover');
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            e.stopPropagation();
            uploadArea.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                const file = files[0];
                if (validateFile(file)) {
                    fileInput.files = files;
                    updateFileName();
                }
            }
        });
        
        uploadArea.addEventListener('click', (e) => {
            if (!e.target.classList.contains('upload-btn')) {
                fileInput.click();
            }
        });
        
        chooseFileBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            fileInput.click();
        });
        
        fileInput.addEventListener('change', () => {
            if (fileInput.files.length > 0) {
                const file = fileInput.files[0];
                if (validateFile(file)) {
                    updateFileName();
                } else {
                    fileInput.value = '';
                    analyzeBtn.disabled = true;
                }
            }
        });
        
        function validateFile(file) {
            // Check file type
            const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/bmp', 'image/tiff'];
            if (!allowedTypes.includes(file.type)) {
                showError(uiTexts.invalid_file || 'Please upload only image files');
                return false;
            }
            
            // Check file size (16MB limit)
            const maxSize = 16 * 1024 * 1024; // 16MB in bytes
            if (file.size > maxSize) {
                showError(uiTexts.file_too_large || 'File is too large. Maximum size is 16MB.');
                return false;
            }
            
            // Check if file is empty
            if (file.size === 0) {
                showError(uiTexts.empty_file || 'The uploaded file is empty.');
                return false;
            }
            
            return true;
        }
        
        function updateFileName() {
            if (fileInput.files.length > 0) {
                const file = fileInput.files[0];
                const fileSize = (file.size / 1024 / 1024).toFixed(2); // Size in MB
                fileName.innerHTML = `
                    <strong>${uiTexts.selected_file}</strong> ${file.name}<br>
                    <small>Size: ${fileSize} MB | Type: ${file.type}</small>
                `;
                fileName.style.display = 'block';
                analyzeBtn.disabled = false;
                hideMessages();
            }
        }
        
        document.getElementById('uploadForm').onsubmit = async function(e) {
            e.preventDefault();
            
            if (isSubmitting) {
                console.log('Already submitting, ignoring duplicate submission');
                return;
            }
            
            if (!fileInput.files.length) {
                showError(uiTexts.no_file_error);
                return;
            }
            
            const file = fileInput.files[0];
            if (!validateFile(file)) {
                return;
            }
            
            isSubmitting = true;
            console.log('Starting file upload and analysis...');
            
            const formData = new FormData();
            formData.append('image', file);
            formData.append('language', selectedLanguage);
            formData.append('generate_email', document.getElementById('generateEmail').checked);
            formData.append('patient_name', document.getElementById('patientName').value);
            formData.append('patient_age', document.getElementById('patientAge').value);
            formData.append('patient_email', document.getElementById('patientEmail').value);
            formData.append('patient_phone', document.getElementById('patientPhone').value);
            
            hideMessages();
            loading.style.display = 'block';
            analyzeBtn.disabled = true;
            
            try {
                const response = await fetch('/analyze_with_email', {
                    method: 'POST',
                    body: formData
                });
                
                console.log('Response status:', response.status);
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const data = await response.json();
                console.log('Response data:', data);
                
                if (data.success) {
                    if (data.detected_language && data.language_name) {
                        document.getElementById('detectedLang').textContent = data.language_name;
                        languageInfo.style.display = 'block';
                    }
                    
                    // Display the text response
                    document.getElementById('resultText').textContent = data.text_response;
                    
                    // Handle audio player
                    const audio = document.getElementById('resultAudio');
                    if (data.audio_url) {
                        console.log('Audio URL received:', data.audio_url);
                        audio.src = data.audio_url;
                        audio.style.display = 'block';
                        
                        audio.onloadeddata = function() {
                            console.log('Audio loaded successfully');
                        };
                        
                        audio.onerror = function(e) {
                            console.error('Audio failed to load:', e);
                            audio.style.display = 'none';
                        };
                        
                        audio.load();
                    } else {
                        audio.style.display = 'none';
                    }
                    
                    result.style.display = 'block';
                    
                    // Display email draft if generated
                    if (data.email_draft) {
                        displayEmailDraft(data.email_draft, data.urgency_level, data.appointment_timeframe);
                    }
                    
                    showSuccess('Analysis completed successfully!');
                } else {
                    showError(uiTexts.error_prefix + ' ' + data.error);
                }
            } catch (err) {
                console.error('Request error:', err);
                showError(uiTexts.network_error + ' ' + err.message);
            } finally {
                loading.style.display = 'none';
                analyzeBtn.disabled = false;
                isSubmitting = false;
            }
        };
        
        function displayEmailDraft(emailDraft, urgencyLevel, appointmentTimeframe) {
            const emailUrgency = document.getElementById('emailUrgency');
            const emailSubject = document.getElementById('emailSubject');
            const emailBody = document.getElementById('emailBody');
            
            // Set urgency indicator
            const urgencyColors = {
                'high': 'urgency-high',
                'medium': 'urgency-medium',
                'low': 'urgency-low',
                'routine': 'urgency-routine'
            };
            
            emailUrgency.className = `email-urgency ${urgencyColors[urgencyLevel] || 'urgency-low'}`;
            emailUrgency.innerHTML = `
                <strong>Urgency Level: ${urgencyLevel.toUpperCase()}</strong>
                <br>Suggested appointment timeframe: ${appointmentTimeframe || 'As soon as possible'}
            `;
            
            // Set email content
            emailSubject.textContent = emailDraft.subject;
            emailBody.value = emailDraft.body;
            
            emailResult.style.display = 'block';
        }
        
        function copyEmailToClipboard() {
            const subject = document.getElementById('emailSubject').textContent;
            const body = document.getElementById('emailBody').value;
            const fullEmail = `Subject: ${subject}\n\n${body}`;
            
            navigator.clipboard.writeText(fullEmail).then(() => {
                showSuccess('Email copied to clipboard!');
            });
        }
        
        function downloadEmail() {
            const subject = document.getElementById('emailSubject').textContent;
            const body = document.getElementById('emailBody').value;
            const fullEmail = `Subject: ${subject}\n\n${body}`;
            
            const blob = new Blob([fullEmail], { type: 'text/plain' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'doctor_consultation_email.txt';
            a.click();
            window.URL.revokeObjectURL(url);
        }
        
        function showError(message) {
            error.textContent = message;
            error.style.display = 'block';
            success.style.display = 'none';
        }
        
        function showSuccess(message) {
            success.textContent = message;
            success.style.display = 'block';
            error.style.display = 'none';
        }
        
        function hideMessages() {
            error.style.display = 'none';
            success.style.display = 'none';
            result.style.display = 'none';
            languageInfo.style.display = 'none';
            emailResult.style.display = 'none';
        }
        
        // Debug: Log when page loads
        console.log('Page loaded with selected language:', selectedLanguage);
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    """Enhanced web interface with email functionality"""
    selected_lang = get_selected_language()
    ui_text = UI_TRANSLATIONS.get(selected_lang, UI_TRANSLATIONS['hi-IN'])
    
    return render_template_string(WEB_INTERFACE, 
                                ui_text=ui_text,
                                current_language=selected_lang,
                                audio_languages=AUDIO_LANGUAGES,
                                ui_text_json=jsonify(ui_text).get_data(as_text=True))

@app.route('/set_language', methods=['POST'])
def set_language():
    """Set unified language for both UI and audio"""
    data = request.get_json()
    language = data.get('language', 'hi-IN')
    
    session['selected_language'] = language
    print(f"✅ Language set to: {language} (both UI and audio)")
    
    return jsonify({'success': True, 'language': language})

@app.route('/analyze', methods=['POST'])
def analyze_report():
    """Analyze medical report with unified language handling"""
    try:
        print(f"Request method: {request.method}")
        print(f"Content type: {request.content_type}")
        print(f"Request files: {list(request.files.keys())}")
        print(f"Request form: {dict(request.form)}")
        
        # Check if file is in request
        if 'image' not in request.files:
            print("ERROR: 'image' not found in request.files")
            selected_lang = get_selected_language()
            error_msg = UI_TRANSLATIONS[selected_lang].get('no_file_error', 'No image uploaded')
            return jsonify({'success': False, 'error': error_msg})
        
        file = request.files['image']
        print(f"File object: {file}")
        print(f"Filename: {file.filename}")
        
        if file.filename == '':
            print("ERROR: Empty filename")
            selected_lang = get_selected_language()
            error_msg = UI_TRANSLATIONS[selected_lang].get('no_file_error', 'No file selected')
            return jsonify({'success': False, 'error': error_msg})
        
        # Read file content
        file_content = file.read()
        file.seek(0)  # Reset file pointer
        
        print(f"File content length: {len(file_content)} bytes")
        
        if len(file_content) == 0:
            selected_lang = get_selected_language()
            error_msg = UI_TRANSLATIONS[selected_lang].get('empty_file', 'Empty file uploaded')
            return jsonify({'success': False, 'error': error_msg})
        
        # Check file size
        if len(file_content) > app.config['MAX_CONTENT_LENGTH']:
            selected_lang = get_selected_language()
            error_msg = UI_TRANSLATIONS[selected_lang].get('file_too_large', 'File too large')
            return jsonify({'success': False, 'error': error_msg})
        
        # Create file hash for duplicate prevention
        file_hash = hashlib.md5(file_content).hexdigest()
        
        if file_hash in processing_files:
            selected_lang = get_selected_language()
            error_msg = UI_TRANSLATIONS[selected_lang].get('processing_error', 'File is already being processed')
            return jsonify({'success': False, 'error': error_msg})
        
        processing_files.add(file_hash)
        
        try:
            # Use the same language for both UI and audio
            selected_language = request.form.get('language', get_selected_language())
            
            print(f"🔍 Processing with UNIFIED language: {selected_language}")
            print(f"🔍 Both UI text and audio will use: {selected_language}")
            
            # Validate file type
            allowed_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
            file_ext = os.path.splitext(file.filename)[1].lower()
            if file_ext not in allowed_extensions:
                selected_lang = get_selected_language()
                error_msg = UI_TRANSLATIONS[selected_lang].get('invalid_file', 'Please upload only image files')
                return jsonify({'success': False, 'error': error_msg})
            
            # Save file temporarily
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_ext)
            temp_file.write(file_content)
            temp_file.close()
            
            print(f"Temporary file saved: {temp_file.name}")
            
            # Process with the same language for both text and audio
            result = orchestrator.process_medical_report(
                temp_file.name, 
                user_language=selected_language,    # Same language for UI text
                audio_language=selected_language    # Same language for audio
            )
            
            # Clean up
            os.unlink(temp_file.name)
            print("Temporary file cleaned up")
            
            print(f"Processing result: {result}")
            
            if result['success']:
                audio_url = None
                
                # Enhanced audio file handling with proper URL generation
                if result.get('audio_file'):
                    print(f"Audio file path from orchestrator: {result['audio_file']}")
                    print(f"Audio file exists: {os.path.exists(result['audio_file'])}")
                    
                    if os.path.exists(result['audio_file']):
                        file_size = os.path.getsize(result['audio_file'])
                        print(f"Audio file size: {file_size} bytes")
                        
                        if file_size > 0:
                            # Extract just the filename from the full path
                            audio_filename = os.path.basename(result['audio_file'])
                            print(f"Audio filename: {audio_filename}")
                            
                            # Create the URL that the browser can access
                            audio_url = f'/static/audio/{audio_filename}'
                            print(f"Audio URL created: {audio_url}")
                            
                            # Verify the file is actually in the static directory
                            static_audio_path = os.path.join(app.root_path, 'static', 'audio', audio_filename)
                            print(f"Expected static path: {static_audio_path}")
                            print(f"Static file exists: {os.path.exists(static_audio_path)}")
                            
                            # If the file is not in static directory, copy it there
                            if not os.path.exists(static_audio_path):
                                print("Copying audio file to static directory...")
                                os.makedirs(os.path.dirname(static_audio_path), exist_ok=True)
                                shutil.copy2(result['audio_file'], static_audio_path)
                                print(f"Audio file copied to: {static_audio_path}")
                        else:
                            print("Audio file is empty")
                    else:
                        print(f"Audio file does not exist: {result['audio_file']}")
                else:
                    print("No audio_file in result")
                
                print(f"Final audio_url being sent to frontend: {audio_url}")
                
                return jsonify({
                    'success': True,
                    'detected_language': result.get('detected_language'),
                    'language_name': result.get('language_name'),
                    'text_response': result.get('text_response', ''),
                    'audio_url': audio_url,
                    'language': selected_language  # Return the unified language
                })
            else:
                return jsonify({
                    'success': False, 
                    'error': result.get('error', 'Report processing failed')
                })
        
        finally:
            processing_files.discard(file_hash)
            
    except Exception as e:
        print(f"Analysis error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False, 
            'error': f'System error: {str(e)}'
        })

@app.route('/analyze_with_email', methods=['POST'])
def analyze_report_with_email():
    """Analyze medical report and generate doctor consultation email"""
    try:
        # Similar file handling as analyze_report
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No image uploaded'})
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
        
        # Get form data
        selected_language = request.form.get('language', get_selected_language())
        generate_email = request.form.get('generate_email', 'true').lower() == 'true'
        
        # Patient information for email
        patient_info = {
            'name': request.form.get('patient_name', ''),
            'age': request.form.get('patient_age', ''),
            'phone': request.form.get('patient_phone', ''),
            'email': request.form.get('patient_email', '')
        }
        
        # Process file (same as before)
        file_content = file.read()
        file_hash = hashlib.md5(file_content).hexdigest()
        
        if file_hash in processing_files:
            return jsonify({'success': False, 'error': 'File is already being processed'})
        
        processing_files.add(file_hash)
        
        try:
            # Save file temporarily
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
            temp_file.write(file_content)
            temp_file.close()
            
            # Process with email generation
            result = orchestrator.process_medical_report_with_email(
                temp_file.name, 
                user_language=selected_language,
                audio_language=selected_language,
                generate_email=generate_email,
                patient_info=patient_info if any(patient_info.values()) else None
            )
            
            # Clean up
            os.unlink(temp_file.name)
            
            if result['success']:
                # Handle audio file (same as before)
                audio_url = None
                if result.get('audio_file'):
                    audio_filename = os.path.basename(result['audio_file'])
                    audio_url = f'/static/audio/{audio_filename}'
                
                response_data = {
                    'success': True,
                    'detected_language': result.get('detected_language'),
                    'language_name': result.get('language_name'),
                    'text_response': result.get('text_response', ''),
                    'audio_url': audio_url,
                    'language': selected_language
                }
                
                # Add email data if generated
                if 'email_draft' in result:
                    response_data['email_draft'] = result['email_draft']
                    response_data['urgency_level'] = result.get('urgency_level')
                    response_data['appointment_timeframe'] = result.get('appointment_timeframe')
                    
                    if 'email_draft_translated' in result:
                        response_data['email_draft_translated'] = result['email_draft_translated']
                
                return jsonify(response_data)
            else:
                return jsonify({'success': False, 'error': result.get('error', 'Processing failed')})
        
        finally:
            processing_files.discard(file_hash)
            
    except Exception as e:
        print(f"Analysis with email error: {e}")
        return jsonify({'success': False, 'error': f'System error: {str(e)}'})

@app.route('/send_email', methods=['POST'])
def send_email():
    """Send the drafted email to doctor (placeholder for email integration)"""
    try:
        data = request.get_json()
        email_content = data.get('email_content')
        doctor_email = data.get('doctor_email')
        patient_email = data.get('patient_email')
        
        # Here you would integrate with your email service
        # For now, return success with instructions
        
        return jsonify({
            'success': True,
            'message': 'Email draft prepared. Please copy and send to your doctor.',
            'instructions': [
                'Copy the email content below',
                'Paste it into your email client',
                'Add your doctor\'s email address',
                'Review and customize as needed',
                'Send the email'
            ]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/debug_audio')
def debug_audio():
    """Debug route to check audio files"""
    static_audio_dir = os.path.join(app.root_path, 'static', 'audio')
    
    debug_info = {
        'static_audio_dir': static_audio_dir,
        'directory_exists': os.path.exists(static_audio_dir),
        'files': []
    }
    
    if os.path.exists(static_audio_dir):
        files = os.listdir(static_audio_dir)
        for file in files:
            file_path = os.path.join(static_audio_dir, file)
            debug_info['files'].append({
                'name': file,
                'size': os.path.getsize(file_path),
                'url': f'/static/audio/{file}'
            })
    
    return jsonify(debug_info)

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Swasthya Saathi Lite',
        'version': '1.0.0'
    })

if __name__ == '__main__':
    print("Starting Flask application...")
    print(f"Static audio directory: {os.path.abspath('static/audio')}")
    
    # Run the application
    app.run(debug=True, host='0.0.0.0', port=5001)


