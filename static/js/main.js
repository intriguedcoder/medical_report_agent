console.log('JavaScript file loaded');

// Global variables and functions that need to be accessible from HTML onclick attributes
let selectedLanguage = 'auto';
let selectedAudioLanguage;
let isSubmitting = false;

// These functions need to be global for HTML onclick attributes
function changeUILanguage(lang) {
    console.log('Changing UI language to:', lang);
    selectedLanguage = lang;
    
    fetch('/set_ui_language', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({language: lang})
    })
    .then(response => response.json())
    .then(data => {
        console.log('UI language changed:', data);
        window.location.reload();
    })
    .catch(error => {
        console.error('Error changing UI language:', error);
    });
}

function changeAudioLanguage(lang) {
    console.log('Changing audio language to:', lang);
    selectedAudioLanguage = lang;
    
    // Update visual selection
    document.querySelectorAll('[data-audio-lang]').forEach(btn => {
        btn.classList.remove('selected');
    });
    const selectedBtn = document.querySelector(`[data-audio-lang="${lang}"]`);
    if (selectedBtn) {
        selectedBtn.classList.add('selected');
    }
    
    // Save to session
    fetch('/set_audio_language', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({language: lang})
    })
    .then(response => response.json())
    .then(data => {
        console.log('Audio language changed:', data);
    })
    .catch(error => {
        console.error('Error changing audio language:', error);
    });
}

// Wait for DOM to be fully loaded before accessing elements
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing...');
    
    // Initialize audio language with fallback
    selectedAudioLanguage = (typeof currentAudioLang !== 'undefined') ? currentAudioLang : 'en-IN';
    console.log('Selected audio language:', selectedAudioLanguage);
    
    // Get DOM elements
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
    const uploadForm = document.getElementById('uploadForm');
    
    console.log('DOM elements found:', {
        uploadArea: !!uploadArea,
        fileInput: !!fileInput,
        uploadForm: !!uploadForm,
        analyzeBtn: !!analyzeBtn
    });
    
    // Check if required elements exist
    if (!uploadArea || !fileInput || !uploadForm || !analyzeBtn) {
        console.error('Required DOM elements not found!');
        return;
    }
    
    // Language button handlers
    document.querySelectorAll('.language-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            if (btn.dataset.lang !== undefined) {
                selectedLanguage = btn.dataset.lang;
                console.log('Language selected:', selectedLanguage);
            }
        });
    });
    
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
    
    if (chooseFileBtn) {
        chooseFileBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            fileInput.click();
        });
    }
    
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
    
    // Form submission handler
    uploadForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        console.log('Form submitted');
        
        if (isSubmitting) {
            console.log('Already submitting, ignoring duplicate submission');
            return;
        }
        
        if (!fileInput.files.length) {
            const message = (typeof uiTexts !== 'undefined' && uiTexts.no_file_error) ? 
                uiTexts.no_file_error : 'Please select a file first';
            showError(message);
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
        
        console.log('FormData created:', {
            image: file.name,
            language: selectedLanguage,
            audio_language: selectedAudioLanguage
        });
        
        hideMessages();
        if (loading) loading.style.display = 'block';
        analyzeBtn.disabled = true;
        
        try {
            const response = await fetch('/analyze', {
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
                // Show detected language
                if (data.detected_language && data.language_name && languageInfo) {
                    document.getElementById('detectedLang').textContent = data.language_name;
                    languageInfo.style.display = 'block';
                }
                
                // Display the text response
                const resultText = document.getElementById('resultText');
                if (resultText && data.text_response) {
                    resultText.innerHTML = data.text_response.replace(/\n/g, '<br>');
                }
                
                // Handle audio player
                const audio = document.getElementById('resultAudio');
                if (data.audio_url && audio) {
                    console.log('Audio URL received:', data.audio_url);
                    
                    // Show debug info
                    if (audioDebug) {
                        audioDebug.innerHTML = `
                            <strong>Audio Debug:</strong><br>
                            URL: ${data.audio_url}<br>
                            Language: ${data.audio_language || 'Not specified'}<br>
                            Status: Loading...
                        `;
                        audioDebug.style.display = 'block';
                    }
                    
                    try {
                        const testResponse = await fetch(data.audio_url, { method: 'HEAD' });
                        
                        if (testResponse.ok) {
                            audio.src = '';
                            audio.load();
                            audio.src = data.audio_url;
                            
                            audio.onloadeddata = function() {
                                console.log('Audio loaded successfully');
                                audio.style.display = 'block';
                                if (audioDebug) {
                                    audioDebug.innerHTML += '<br>Status: ✅ Loaded successfully';
                                }
                            };
                            
                            audio.onerror = function(e) {
                                console.error('Audio failed to load:', e);
                                audio.style.display = 'none';
                                if (audioDebug) {
                                    audioDebug.innerHTML += '<br>Status: ❌ Failed to load';
                                }
                            };
                            
                            audio.load();
                        } else {
                            throw new Error(`Audio URL not accessible: ${testResponse.status}`);
                        }
                    } catch (urlError) {
                        console.error('Audio URL test failed:', urlError);
                        if (audioDebug) {
                            audioDebug.innerHTML += `<br>Status: ❌ URL test failed: ${urlError.message}`;
                        }
                        audio.style.display = 'none';
                    }
                } else {
                    console.log('No audio URL in response');
                    if (audioDebug) {
                        audioDebug.innerHTML = '<strong>Audio Debug:</strong><br>Status: ❌ No audio URL provided';
                        audioDebug.style.display = 'block';
                    }
                    if (audio) audio.style.display = 'none';
                }
                
                if (result) result.style.display = 'block';
                showSuccess('Analysis completed successfully!');
            } else {
                const errorMessage = data.error || 'Analysis failed';
                const prefix = (typeof uiTexts !== 'undefined' && uiTexts.error_prefix) ? 
                    uiTexts.error_prefix + ' ' : 'Error: ';
                showError(prefix + errorMessage);
            }
        } catch (err) {
            console.error('Request error:', err);
            const networkError = (typeof uiTexts !== 'undefined' && uiTexts.network_error) ? 
                uiTexts.network_error : 'Network error:';
            showError(networkError + ' ' + err.message);
        } finally {
            if (loading) loading.style.display = 'none';
            analyzeBtn.disabled = false;
            isSubmitting = false;
        }
    });
    
    // Helper functions
    function validateFile(file) {
        console.log('Validating file:', file.name, file.type, file.size);
        
        // Check file type
        const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/bmp', 'image/tiff'];
        if (!allowedTypes.includes(file.type)) {
            const message = (typeof uiTexts !== 'undefined' && uiTexts.invalid_file) ? 
                uiTexts.invalid_file : 'Please upload only image files';
            showError(message);
            return false;
        }
        
        // Check file size (16MB limit)
        const maxSize = 16 * 1024 * 1024; // 16MB in bytes
        if (file.size > maxSize) {
            const message = (typeof uiTexts !== 'undefined' && uiTexts.file_too_large) ? 
                uiTexts.file_too_large : 'File is too large. Maximum size is 16MB.';
            showError(message);
            return false;
        }
        
        // Check if file is empty
        if (file.size === 0) {
            const message = (typeof uiTexts !== 'undefined' && uiTexts.empty_file) ? 
                uiTexts.empty_file : 'The uploaded file is empty.';
            showError(message);
            return false;
        }
        
        return true;
    }
    
    function updateFileName() {
        if (fileInput.files.length > 0 && fileName) {
            const file = fileInput.files[0];
            const fileSize = (file.size / 1024 / 1024).toFixed(2); // Size in MB
            const selectedFileText = (typeof uiTexts !== 'undefined' && uiTexts.selected_file) ? 
                uiTexts.selected_file : 'Selected file:';
            
            fileName.innerHTML = `
                <strong>${selectedFileText}</strong> ${file.name}<br>
                <small>Size: ${fileSize} MB | Type: ${file.type}</small>
            `;
            fileName.style.display = 'block';
            analyzeBtn.disabled = false;
            hideMessages();
        }
    }
    
    function showError(message) {
        console.log('Showing error:', message);
        if (error) {
            error.textContent = message;
            error.style.display = 'block';
        }
        if (success) success.style.display = 'none';
    }
    
    function showSuccess(message) {
        console.log('Showing success:', message);
        if (success) {
            success.textContent = message;
            success.style.display = 'block';
        }
        if (error) error.style.display = 'none';
    }
    
    function hideMessages() {
        if (error) error.style.display = 'none';
        if (success) success.style.display = 'none';
        if (result) result.style.display = 'none';
        if (languageInfo) languageInfo.style.display = 'none';
        if (audioDebug) audioDebug.style.display = 'none';
    }
    
    console.log('JavaScript initialization complete');
});
