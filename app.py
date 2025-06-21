from flask import Flask, request, jsonify, render_template_string, send_from_directory, session
from agents.orchestrator_agent import OrchestratorAgent
import os
import tempfile
import hashlib
import shutil
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
orchestrator = OrchestratorAgent()

# Add processing files tracking to prevent duplicates
processing_files = set()

# UI Language Translations with English as default
UI_TRANSLATIONS = {
    'en-IN': {
        'title': '🏥 Health Partner',
        'subtitle': 'Your companion for understanding medical reports',
        'choose_language': '🌐 Choose Language',
        'choose_audio_language': '🔊 Choose Audio Language',
        'auto_detect': 'Auto Detect',
        'upload_photo': 'Upload Photo',
        'upload_desc': 'Send a picture of your medical report',
        'smart_analysis': 'Smart Analysis',
        'smart_desc': 'AI will analyze your report',
        'multilingual': 'Multilingual Support',
        'multilingual_desc': 'Listen to results in multiple languages',
        'upload_report': 'Upload Medical Report',
        'click_or_drag': 'Click here or drag file here',
        'choose_file': '📁 Choose File',
        'analyze_report': '🔍 Analyze Report',
        'analyzing': 'Your report is being analyzed... Please wait',
        'detected_language': '🔍 Detected Language:',
        'analysis_result': '📊 Analysis Result',
        'selected_file': 'Selected file:',
        'no_file_error': 'Please select a file first.',
        'network_error': 'Network error:',
        'error_prefix': 'Error:',
        'processing_error': 'File is already being processed',
        'invalid_file': 'Please upload only image files (JPG, PNG, etc.)',
        'audio_language_note': 'Audio will be generated in the selected language',
        'file_too_large': 'File is too large. Maximum size is 16MB.',
        'empty_file': 'The uploaded file is empty.'
    },
    'hi-IN': {
        'title': '🏥 स्वास्थ्य साथी',
        'subtitle': 'आपकी मेडिकल रिपोर्ट को समझने में आपका साथी',
        'choose_language': '🌐 भाषा चुनें',
        'choose_audio_language': '🔊 ऑडियो भाषा चुनें',
        'auto_detect': 'स्वचालित पहचान',
        'upload_photo': 'फोटो अपलोड करें',
        'upload_desc': 'अपनी मेडिकल रिपोर्ट की तस्वीर भेजें',
        'smart_analysis': 'स्मार्ट विश्लेषण',
        'smart_desc': 'AI आपकी रिपोर्ट का विश्लेषण करेगा',
        'multilingual': 'बहुभाषी समर्थन',
        'multilingual_desc': 'कई भाषाओं में परिणाम सुनें',
        'upload_report': 'मेडिकल रिपोर्ट अपलोड करें',
        'click_or_drag': 'यहाँ क्लिक करें या फाइल को यहाँ खींचें',
        'choose_file': '📁 फाइल चुनें',
        'analyze_report': '🔍 रिपोर्ट का विश्लेषण करें',
        'analyzing': 'आपकी रिपोर्ट का विश्लेषण हो रहा है... कृपया प्रतीक्षा करें',
        'detected_language': '🔍 पहचानी गई भाषा:',
        'analysis_result': '📊 विश्लेषण परिणाम',
        'selected_file': 'चुनी गई फाइल:',
        'no_file_error': 'कृपया पहले एक फाइल चुनें।',
        'network_error': 'नेटवर्क त्रुटि:',
        'error_prefix': 'त्रुटि:',
        'processing_error': 'फाइल पहले से प्रोसेसिंग में है',
        'invalid_file': 'केवल इमेज फाइलें अपलोड करें (JPG, PNG, etc.)',
        'audio_language_note': 'चुनी गई भाषा में ऑडियो बनाया जाएगा',
        'file_too_large': 'फाइल बहुत बड़ी है। अधिकतम आकार 16MB है।',
        'empty_file': 'अपलोड की गई फाइल खाली है।'
    }
}

# Audio language options
AUDIO_LANGUAGES = {
    'en-IN': {'name': 'English', 'flag': '🇬🇧'},
    'hi-IN': {'name': 'हिंदी', 'flag': '🇮🇳'},
    'ta-IN': {'name': 'தமிழ்', 'flag': '🇮🇳'},
    'te-IN': {'name': 'తెలుగు', 'flag': '🇮🇳'},
    'bn-IN': {'name': 'বাংলা', 'flag': '🇮🇳'},
    'gu-IN': {'name': 'ગુજરાતી', 'flag': '🇮🇳'},
    'kn-IN': {'name': 'ಕನ್ನಡ', 'flag': '🇮🇳'},
    'ml-IN': {'name': 'മലയാളം', 'flag': '🇮🇳'},
    'mr-IN': {'name': 'मराठी', 'flag': '🇮🇳'},
    'pa-IN': {'name': 'ਪੰਜਾਬੀ', 'flag': '🇮🇳'}
}

def get_ui_language():
    """Get UI language from session or default to English"""
    return session.get('ui_language', 'en-IN')

def get_audio_language():
    """Get audio language from session or default to UI language"""
    return session.get('audio_language', get_ui_language())

def get_ui_text(key):
    """Get UI text in current language"""
    ui_lang = get_ui_language()
    return UI_TRANSLATIONS.get(ui_lang, UI_TRANSLATIONS['en-IN']).get(key, key)

# Enhanced web interface with better file upload handling
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
            max-width: 800px; 
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
        }
        .language-selector h3 {
            margin-bottom: 15px;
            color: #333;
        }
        .language-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 10px;
        }
        .language-btn {
            background: white;
            border: 2px solid #ddd;
            padding: 10px;
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
        
        .audio-language-selector {
            background: #fff3e0;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
            border-left: 5px solid #ff9800;
        }
        .audio-language-selector h3 {
            margin-bottom: 15px;
            color: #333;
        }
        .audio-language-note {
            font-size: 0.9em;
            color: #666;
            margin-top: 10px;
            font-style: italic;
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
        .audio-debug {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            padding: 10px;
            margin-top: 10px;
            border-radius: 5px;
            font-size: 0.9em;
            color: #856404;
        }
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
                <div class="language-grid">
                    <div class="language-btn {% if current_ui_lang == 'auto' %}selected{% endif %}" data-lang="auto" onclick="changeUILanguage('auto')">
                        <div>🔍 Auto</div>
                        <small>{{ ui_text.auto_detect }}</small>
                    </div>
                    <div class="language-btn {% if current_ui_lang == 'en-IN' %}selected{% endif %}" data-lang="en-IN" onclick="changeUILanguage('en-IN')">
                        <div>🇬🇧 English</div>
                        <small>English</small>
                    </div>
                    <div class="language-btn {% if current_ui_lang == 'hi-IN' %}selected{% endif %}" data-lang="hi-IN" onclick="changeUILanguage('hi-IN')">
                        <div>🇮🇳 हिंदी</div>
                        <small>Hindi</small>
                    </div>
                </div>
            </div>
            
            <div class="audio-language-selector">
                <h3>{{ ui_text.choose_audio_language }}</h3>
                <div class="language-grid">
                    {% for lang_code, lang_info in audio_languages.items() %}
                    <div class="language-btn {% if current_audio_lang == lang_code %}selected{% endif %}" data-audio-lang="{{ lang_code }}" onclick="changeAudioLanguage('{{ lang_code }}')">
                        <div>{{ lang_info.flag }} {{ lang_info.name }}</div>
                        <small>{{ lang_code.split('-')[0].upper() }}</small>
                    </div>
                    {% endfor %}
                </div>
                <div class="audio-language-note">{{ ui_text.audio_language_note }}</div>
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
                <div id="audioDebug" class="audio-debug" style="display:none;"></div>
                <audio id="resultAudio" class="audio-player" controls style="display:none;">
                    Your browser does not support the audio player.
                </audio>
            </div>
            
            <div id="error" class="error" style="display:none;"></div>
            <div id="success" class="success" style="display:none;"></div>
        </div>
    </div>

    <script>
        let selectedLanguage = 'auto';
        let selectedAudioLanguage = '{{ current_audio_lang }}';
        let isSubmitting = false;
        const uiTexts = {{ ui_text_json|safe }};
        
        function changeUILanguage(lang) {
            fetch('/set_ui_language', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({language: lang})
            }).then(() => {
                window.location.reload();
            });
        }
        
        function changeAudioLanguage(lang) {
            selectedAudioLanguage = lang;
            
            // Update visual selection
            document.querySelectorAll('[data-audio-lang]').forEach(btn => {
                btn.classList.remove('selected');
            });
            document.querySelector(`[data-audio-lang="${lang}"]`).classList.add('selected');
            
            // Save to session
            fetch('/set_audio_language', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({language: lang})
            });
        }
        
        document.querySelectorAll('.language-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                if (btn.dataset.lang !== undefined) {
                    selectedLanguage = btn.dataset.lang;
                }
            });
        });
        
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
        const audioDebug = document.getElementById('audioDebug');
        
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
            
            if (selectedLanguage !== 'auto') {
                formData.append('language', selectedLanguage);
            }
            formData.append('audio_language', selectedAudioLanguage);
            
            // Debug FormData contents
            console.log('FormData contents:');
            for (let pair of formData.entries()) {
                console.log(pair[0] + ': ' + (pair[1] instanceof File ? `File: ${pair[1].name}` : pair[1]));
            }
            
            hideMessages();
            loading.style.display = 'block';
            analyzeBtn.disabled = true;
            
            try {
                const response = await fetch('/analyze', {
                    method: 'POST',
                    body: formData
                });
                
                console.log('Response status:', response.status);
                console.log('Response headers:', response.headers);
                
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
                    
                    // Handle audio player with enhanced debugging
                    const audio = document.getElementById('resultAudio');
                    if (data.audio_url) {
                        console.log('Audio URL received:', data.audio_url);
                        
                        // Show debug info
                        audioDebug.innerHTML = `
                            <strong>Audio Debug:</strong><br>
                            URL: ${data.audio_url}<br>
                            Language: ${data.audio_language || 'Not specified'}<br>
                            Status: Loading...
                        `;
                        audioDebug.style.display = 'block';
                        
                        // Test if URL is accessible first
                        try {
                            const testResponse = await fetch(data.audio_url, { method: 'HEAD' });
                            console.log('Audio URL test response:', testResponse.status);
                            
                            if (testResponse.ok) {
                                // Clear previous audio
                                audio.src = '';
                                audio.load();
                                
                                // Set new source
                                audio.src = data.audio_url;
                                
                                audio.onloadeddata = function() {
                                    console.log('Audio loaded successfully');
                                    audio.style.display = 'block';
                                    audioDebug.innerHTML += '<br>Status: ✅ Loaded successfully';
                                };
                                
                                audio.onerror = function(e) {
                                    console.error('Audio failed to load:', e);
                                    console.error('Audio error details:', audio.error);
                                    audio.style.display = 'none';
                                    audioDebug.innerHTML += '<br>Status: ❌ Failed to load';
                                };
                                
                                // Force load
                                audio.load();
                            } else {
                                throw new Error(`Audio URL not accessible: ${testResponse.status}`);
                            }
                        } catch (urlError) {
                            console.error('Audio URL test failed:', urlError);
                            audioDebug.innerHTML += `<br>Status: ❌ URL test failed: ${urlError.message}`;
                            audio.style.display = 'none';
                        }
                    } else {
                        console.log('No audio URL in response');
                        audioDebug.innerHTML = '<strong>Audio Debug:</strong><br>Status: ❌ No audio URL provided';
                        audioDebug.style.display = 'block';
                        audio.style.display = 'none';
                    }
                    
                    result.style.display = 'block';
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
            audioDebug.style.display = 'none';
        }
        
        // Debug: Log when page loads
        console.log('Page loaded, file input element:', fileInput);
        console.log('Upload form element:', document.getElementById('uploadForm'));
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    """Enhanced web interface with audio language selection"""
    ui_lang = get_ui_language()
    audio_lang = get_audio_language()
    ui_text = UI_TRANSLATIONS.get(ui_lang, UI_TRANSLATIONS['en-IN'])
    
    return render_template_string(WEB_INTERFACE, 
                                ui_text=ui_text,
                                current_ui_lang=ui_lang,
                                current_audio_lang=audio_lang,
                                audio_languages=AUDIO_LANGUAGES,
                                ui_text_json=jsonify(ui_text).get_data(as_text=True))

@app.route('/set_ui_language', methods=['POST'])
def set_ui_language():
    """Set UI language in session"""
    data = request.get_json()
    language = data.get('language', 'en-IN')
    
    if language == 'auto':
        language = 'en-IN'
    
    session['ui_language'] = language
    # If audio language is not set, default to UI language
    if 'audio_language' not in session:
        session['audio_language'] = language
    
    return jsonify({'success': True, 'language': language})

@app.route('/set_audio_language', methods=['POST'])
def set_audio_language():
    """Set audio language in session"""
    data = request.get_json()
    language = data.get('language', get_ui_language())
    
    session['audio_language'] = language
    return jsonify({'success': True, 'audio_language': language})

@app.route('/analyze', methods=['POST'])
def analyze_report():
    """Analyze medical report with FIXED audio URL handling"""
    try:
        print(f"Request method: {request.method}")
        print(f"Content type: {request.content_type}")
        print(f"Request files: {list(request.files.keys())}")
        print(f"Request form: {dict(request.form)}")
        
        # Check if file is in request
        if 'image' not in request.files:
            print("ERROR: 'image' not found in request.files")
            ui_lang = get_ui_language()
            error_msg = UI_TRANSLATIONS[ui_lang].get('no_file_error', 'No image uploaded')
            return jsonify({'success': False, 'error': error_msg})
        
        file = request.files['image']
        print(f"File object: {file}")
        print(f"Filename: {file.filename}")
        
        if file.filename == '':
            print("ERROR: Empty filename")
            ui_lang = get_ui_language()
            error_msg = UI_TRANSLATIONS[ui_lang].get('no_file_error', 'No file selected')
            return jsonify({'success': False, 'error': error_msg})
        
        # Read file content
        file_content = file.read()
        file.seek(0)  # Reset file pointer
        
        print(f"File content length: {len(file_content)} bytes")
        
        if len(file_content) == 0:
            ui_lang = get_ui_language()
            error_msg = UI_TRANSLATIONS[ui_lang].get('empty_file', 'Empty file uploaded')
            return jsonify({'success': False, 'error': error_msg})
        
        # Check file size
        if len(file_content) > app.config['MAX_CONTENT_LENGTH']:
            ui_lang = get_ui_language()
            error_msg = UI_TRANSLATIONS[ui_lang].get('file_too_large', 'File too large')
            return jsonify({'success': False, 'error': error_msg})
        
        # Create file hash for duplicate prevention
        file_hash = hashlib.md5(file_content).hexdigest()
        
        if file_hash in processing_files:
            ui_lang = get_ui_language()
            error_msg = UI_TRANSLATIONS[ui_lang].get('processing_error', 'File is already being processed')
            return jsonify({'success': False, 'error': error_msg})
        
        processing_files.add(file_hash)
        
        try:
            selected_language = request.form.get('language', 'en-IN')
            audio_language = request.form.get('audio_language', get_audio_language())
            
            print(f"Processing with UI language: {selected_language}, Audio language: {audio_language}")
            
            # Validate file type
            allowed_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
            file_ext = os.path.splitext(file.filename)[1].lower()
            if file_ext not in allowed_extensions:
                ui_lang = get_ui_language()
                error_msg = UI_TRANSLATIONS[ui_lang].get('invalid_file', 'Please upload only image files')
                return jsonify({'success': False, 'error': error_msg})
            
            # Save file temporarily
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_ext)
            temp_file.write(file_content)
            temp_file.close()
            
            print(f"Temporary file saved: {temp_file.name}")
            
            # Process the report with audio language
            result = orchestrator.process_medical_report(temp_file.name, selected_language, audio_language)
            
            # Clean up
            os.unlink(temp_file.name)
            print("Temporary file cleaned up")
            
            print(f"Processing result: {result}")
            
            if result['success']:
                audio_url = None
                
                # FIXED: Enhanced audio file handling with proper URL generation
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
                    'audio_url': audio_url,  # This should now have a value if audio file exists
                    'audio_language': audio_language
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

# REMOVED: The conflicting /static/audio/ route - Let Flask handle static files automatically

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

@app.route('/test_upload', methods=['GET', 'POST'])
def test_upload():
    """Simple test route for file upload debugging"""
    if request.method == 'GET':
        return '''
        <!DOCTYPE html>
        <html>
        <head><title>File Upload Test</title></head>
        <body>
            <h2>File Upload Test</h2>
            <form method="POST" enctype="multipart/form-data">
                <input type="file" name="test_file" accept="image/*" required>
                <input type="submit" value="Test Upload">
            </form>
        </body>
        </html>
        '''
    
    if 'test_file' not in request.files:
        return "No file in request"
    
    file = request.files['test_file']
    if file.filename == '':
        return "No file selected"
    
    file_content = file.read()
    return f"File received: {file.filename}, Size: {len(file_content)} bytes, Type: {file.content_type}"

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Swasthya Saathi Lite',
        'version': '1.0.0'
    })

if __name__ == '__main__':
    # Ensure directories exist with proper permissions
    directories = ['static', 'static/audio', 'uploads', 'temp']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Directory ensured: {os.path.abspath(directory)}")
        # Set permissions on Unix systems
        if os.name != 'nt':  # Not Windows
            os.chmod(directory, 0o755)
    
    print("Starting Flask application...")
    print(f"Static audio directory: {os.path.abspath('static/audio')}")
    
    # Run the application
    app.run(debug=True, host='0.0.0.0', port=5001)
