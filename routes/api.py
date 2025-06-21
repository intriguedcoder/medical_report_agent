import os
import tempfile
import shutil
from flask import Blueprint, request, jsonify, current_app
from agents.orchestrator_agent import OrchestratorAgent
from utils.helpers import (
    processing_files, validate_file, create_file_hash, 
    save_temp_file, handle_audio_file, get_ui_language
)
from utils.translations import UI_TRANSLATIONS

api_bp = Blueprint('api', __name__)
orchestrator = OrchestratorAgent()

@api_bp.route('/analyze', methods=['POST'])
def analyze_report():
    """Analyze medical report with FIXED audio URL handling"""
    try:
        print("=== ANALYZE REQUEST DEBUG ===")
        print(f"Request method: {request.method}")
        print(f"Content type: {request.content_type}")
        print(f"Request files: {list(request.files.keys())}")
        print(f"Request form: {dict(request.form)}")
        print(f"Request headers: {dict(request.headers)}")
        
        # Check if file is in request
        if 'image' not in request.files:
            print("ERROR: 'image' not found in request.files")
            return jsonify({'success': False, 'error': 'No image uploaded'})
        
        file = request.files['image']
        print(f"File object: {file}")
        print(f"Filename: {file.filename}")
        
        if not file or file.filename == '':
            print("ERROR: Empty filename or no file")
            return jsonify({'success': False, 'error': 'No file selected'})
        
        # Read file content ONCE and store it
        file_content = file.read()
        print(f"File content length: {len(file_content)} bytes")
        
        if len(file_content) == 0:
            return jsonify({'success': False, 'error': 'Empty file uploaded'})
        
        # Check file size
        if len(file_content) > current_app.config['MAX_CONTENT_LENGTH']:
            return jsonify({'success': False, 'error': 'File too large'})
        
        # Validate file type
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_extensions:
            return jsonify({'success': False, 'error': 'Please upload only image files'})
        
        # Create file hash for duplicate prevention
        file_hash = create_file_hash(file_content)
        
        if file_hash in processing_files:
            return jsonify({'success': False, 'error': 'File is already being processed'})
        
        processing_files.add(file_hash)
        
        try:
            selected_language = request.form.get('language', 'en-IN')
            audio_language = request.form.get('audio_language', get_ui_language())
            
            print(f"Processing with UI language: {selected_language}, Audio language: {audio_language}")
            
            # Save file temporarily using the content we already read
            temp_file_path = save_temp_file(file_content, file_ext)
            
            print(f"Temporary file saved: {temp_file_path}")
            
            # Process the report
            result = orchestrator.process_medical_report(temp_file_path, selected_language, audio_language)
            
            # Clean up
            os.unlink(temp_file_path)
            print("Temporary file cleaned up")
            
            print(f"Processing result: {result}")
            
            if result['success']:
                audio_url = handle_audio_file(result.get('audio_file'), current_app.root_path)
                
                print(f"Final audio_url being sent to frontend: {audio_url}")
                
                return jsonify({
                    'success': True,
                    'detected_language': result.get('detected_language'),
                    'language_name': result.get('language_name'),
                    'text_response': result.get('text_response', ''),
                    'audio_url': audio_url,
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

@api_bp.route('/debug_audio')
def debug_audio():
    """Debug route to check audio files"""
    static_audio_dir = os.path.join(current_app.root_path, 'static', 'audio')
    
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

@api_bp.route('/test_upload', methods=['GET', 'POST'])
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
