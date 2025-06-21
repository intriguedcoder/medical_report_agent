import os
import hashlib
import tempfile
import shutil
from flask import session, current_app

# Add processing files tracking to prevent duplicates
processing_files = set()

def get_ui_language():
    """Get UI language from session or default to English"""
    return session.get('ui_language', 'en-IN')

def get_audio_language():
    """Get audio language from session or default to UI language"""
    return session.get('audio_language', get_ui_language())

def validate_file(file, max_size=16*1024*1024):
    """Validate uploaded file"""
    # Check file type
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        return False, 'Invalid file type. Please upload an image file.'
    
    # Check file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > max_size:
        return False, 'File too large. Maximum size is 16MB.'
    
    if file_size == 0:
        return False, 'Empty file uploaded.'
    
    return True, None

def create_file_hash(file_content):
    """Create hash for file content"""
    return hashlib.md5(file_content).hexdigest()

def save_temp_file(file_content, extension):
    """Save file content to temporary file"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=extension)
    temp_file.write(file_content)
    temp_file.close()
    return temp_file.name

def handle_audio_file(audio_file_path, app_root_path=None):
    """Handle audio file and return URL with Flask app context"""
    print(f"🔍 ===== HANDLE AUDIO FILE START =====")
    
    # Use current_app if app_root_path not provided
    if app_root_path is None:
        app_root_path = current_app.root_path
    
    print(f"🔍 App root path: {app_root_path}")
    print(f"🔍 Audio file path provided: {audio_file_path}")
    
    if not audio_file_path:
        print("❌ No audio file path provided")
        return None
    
    # Define the static audio directory using app context
    static_audio_dir = os.path.join(app_root_path, 'static', 'audio')
    print(f"🔍 Static audio directory: {static_audio_dir}")
    
    # Ensure directory exists
    os.makedirs(static_audio_dir, exist_ok=True)
    
    # List existing files for debugging
    if os.path.exists(static_audio_dir):
        files = os.listdir(static_audio_dir)
        print(f"🔍 Files in static/audio: {files}")
    
    # Extract filename
    audio_filename = os.path.basename(audio_file_path)
    static_file_path = os.path.join(static_audio_dir, audio_filename)
    
    print(f"🔍 Target static file path: {static_file_path}")
    
    # Check if source file exists and has content
    if os.path.exists(audio_file_path):
        file_size = os.path.getsize(audio_file_path)
        print(f"✅ Source file exists, size: {file_size} bytes")
        
        if file_size == 0:
            print("❌ Source audio file is empty")
            return None
        
        try:
            # Copy to static directory
            shutil.copy2(audio_file_path, static_file_path)
            
            # Set proper permissions
            if os.name != 'nt':  # Not Windows
                os.chmod(static_file_path, 0o644)
            
            # Verify the copy
            if os.path.exists(static_file_path) and os.path.getsize(static_file_path) > 0:
                audio_url = f'/static/audio/{audio_filename}'
                print(f"✅ File copied successfully, returning URL: {audio_url}")
                return audio_url
            else:
                print("❌ File copy verification failed")
                
        except Exception as e:
            print(f"❌ Error copying file: {e}")
            return None
    
    # Check if file already exists in static directory
    elif os.path.exists(static_file_path) and os.path.getsize(static_file_path) > 0:
        audio_url = f'/static/audio/{audio_filename}'
        print(f"✅ Found existing file, returning URL: {audio_url}")
        return audio_url
    
    print(f"❌ Audio file not found or empty")
    return None
