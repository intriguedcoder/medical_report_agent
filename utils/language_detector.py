import re
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException


class LanguageDetector:
    def __init__(self):
        self.supported_languages = {
            'hi': 'hi-IN',  # Hindi
            'en': 'en-IN',  # English
            'ta': 'ta-IN',  # Tamil
            'te': 'te-IN',  # Telugu
            'bn': 'bn-IN',  # Bengali
            'gu': 'gu-IN',  # Gujarati
            'kn': 'kn-IN',  # Kannada
            'ml': 'ml-IN',  # Malayalam
            'mr': 'mr-IN',  # Marathi
            'pa': 'pa-IN'   # Punjabi
        }
        
        self.language_names = {
            'hi-IN': 'हिंदी',
            'en-IN': 'English',
            'ta-IN': 'தமிழ்',
            'te-IN': 'తెలుగు',
            'bn-IN': 'বাংলা',
            'gu-IN': 'ગુજરાતી',
            'kn-IN': 'ಕನ್ನಡ',
            'ml-IN': 'മലയാളം',
            'mr-IN': 'मराठी',
            'pa-IN': 'ਪੰਜਾਬੀ'
        }
    
    def detect_language(self, text):
        """Detect language from text"""
        try:
            # Clean text for better detection
            cleaned_text = re.sub(r'[^\w\s]', '', text)
            if len(cleaned_text.strip()) < 3:
                return 'hi-IN'  # Default to Hindi
            
            detected = detect(cleaned_text)
            return self.supported_languages.get(detected, 'hi-IN')
        except LangDetectException:
            return 'hi-IN'  # Default fallback
    
    def get_language_name(self, language_code):
        """Get display name for language"""
        return self.language_names.get(language_code, 'हिंदी')
    
    def get_supported_languages(self):
        """Get list of supported languages"""
        return self.supported_languages.values()


# Global instance for efficiency
_detector_instance = None

def get_language_detector():
    """Get or create language detector instance"""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = LanguageDetector()
    return _detector_instance

def detect_language(text):
    """Standalone function to detect language"""
    return get_language_detector().detect_language(text)
