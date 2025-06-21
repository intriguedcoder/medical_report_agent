import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = 'uploads'
    TEMP_FOLDER = 'temp'
    STATIC_AUDIO_FOLDER = '/Users/nikhilnedungadi/Desktop/NIKHIL/projects/warpspeed/swasthbharat/static/audio'
    
    @staticmethod
    def init_app(app):
        """Initialize application directories and settings"""
        # Define the actual project paths
        project_root = '/Users/nikhilnedungadi/Desktop/NIKHIL/projects/warpspeed/swasthbharat'
        
        directories = [
            os.path.join(project_root, 'static'),
            os.path.join(project_root, 'static', 'audio'),
            os.path.join(project_root, 'uploads'),
            os.path.join(project_root, 'temp')
        ]
        
        for directory in directories:
            try:
                os.makedirs(directory, exist_ok=True)
                print(f"📁 Created/verified directory: {directory}")
                
                # Set proper permissions (Unix/Linux/macOS)
                if os.name != 'nt':  # Not Windows
                    os.chmod(directory, 0o755)
                    
            except Exception as e:
                print(f"❌ Error creating directory {directory}: {e}")
        
        # Verify static audio directory specifically
        static_audio_path = os.path.join(project_root, 'static', 'audio')
        if os.path.exists(static_audio_path):
            print(f"✅ Static audio directory ready: {static_audio_path}")
        else:
            print(f"❌ Failed to create static audio directory: {static_audio_path}")
