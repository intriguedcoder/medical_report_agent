import requests
import base64
import os
from dotenv import load_dotenv

load_dotenv()

class SarvamClient:
    def __init__(self):
        self.api_key = os.getenv('SARVAM_API_KEY')
        self.base_url = "https://api.sarvam.ai"
        
        if not self.api_key:
            print("⚠️ WARNING: SARVAM_API_KEY not found in environment variables")
        else:
            print(f"✅ Sarvam API key loaded: {self.api_key[:10]}...")
    
    def translate(self, text, source_language_code="en-IN", target_language_code="hi-IN"):
        """Translate text using Sarvam-Translate (Mayura) API with CORRECTED parameters"""
        if not self.api_key:
            print("❌ SARVAM CLIENT: API key not found")
            return {
                'success': False,
                'error': 'API key not found',
                'translated_text': text
            }
            
        if not text or len(text.strip()) == 0:
            print("⚠️ SARVAM CLIENT: Empty text provided for translation")
            return {
                'success': True,
                'translated_text': text,
                'source_language_code': source_language_code,
                'target_language_code': target_language_code
            }
        
        # Use the correct Sarvam Translate endpoint
        url = f"{self.base_url}/translate"
        
        # CORRECTED payload for Sarvam-Translate (Mayura v1)
        payload = {
            "input": text,
            "source_language_code": source_language_code,
            "target_language_code": target_language_code,
            "speaker_gender": "Female",
            "mode": "formal",
            "model": "mayura:v1",
            "enable_preprocessing": True,
            "output_script": "fully-native",  # FIXED: Changed from "native" to "fully-native"
            "numerals_format": "international"  # FIXED: Changed from "native" to "international"
        }
        
        headers = {
            "api-subscription-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        try:
            print(f"🔍 SARVAM CLIENT: Translating {len(text)} characters from {source_language_code} to {target_language_code}")
            print(f"🔍 SARVAM CLIENT: Text preview: {text[:100]}...")
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            print(f"🔍 SARVAM CLIENT: Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"🔍 SARVAM CLIENT: Response: {result}")
                
                translated_text = result.get('translated_text', text)
                source_detected = result.get('source_language_code', source_language_code)
                
                print(f"✅ SARVAM CLIENT: Translation successful")
                print(f"🔍 SARVAM CLIENT: Original: {text[:100]}...")
                print(f"🔍 SARVAM CLIENT: Translated: {translated_text[:100]}...")
                
                return {
                    'success': True,
                    'translated_text': translated_text,
                    'source_language_code': source_detected,
                    'target_language_code': target_language_code
                }
            else:
                error_text = response.text
                print(f"❌ SARVAM CLIENT: Translation error: {response.status_code}")
                print(f"❌ SARVAM CLIENT: Error response: {error_text}")
                
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {error_text}",
                    'translated_text': text,
                    'source_language_code': source_language_code,
                    'target_language_code': target_language_code
                }
                
        except requests.exceptions.Timeout:
            print(f"❌ SARVAM CLIENT: Translation timeout")
            return {
                'success': False,
                'error': 'Translation request timed out',
                'translated_text': text,
                'source_language_code': source_language_code,
                'target_language_code': target_language_code
            }
        except Exception as e:
            print(f"❌ SARVAM CLIENT: Translation exception: {e}")
            return {
                'success': False,
                'error': str(e),
                'translated_text': text,
                'source_language_code': source_language_code,
                'target_language_code': target_language_code
            }
    
    def translate_text(self, text, target_language='hi-IN'):
        """Legacy method for backward compatibility"""
        result = self.translate(text, "en-IN", target_language)
        if result.get('success'):
            return result.get('translated_text', text)
        else:
            return text
    
    def text_to_speech(self, text, language='hi-IN', speaker='meera'):
        """Convert text to speech using Sarvam TTS API with enhanced debugging"""
        if not self.api_key:
            print("❌ SARVAM CLIENT: API key not found for TTS")
            return None
            
        if not text or len(text.strip()) == 0:
            print("⚠️ SARVAM CLIENT: Empty text provided for TTS")
            return None
        
        # Limit text length for TTS - Sarvam has a 500 character limit
        if len(text) > 500:
            text = text[:497] + "..."
            print(f"⚠️ SARVAM CLIENT: Text truncated to 500 characters for TTS")
            
        url = f"{self.base_url}/text-to-speech"
        
        payload = {
            "inputs": [text],
            "target_language_code": language,
            "speaker": speaker,
            "pitch": 0,
            "pace": 1.0,
            "loudness": 1.0,
            "speech_sample_rate": 8000,
            "enable_preprocessing": True,
            "model": "bulbul:v1"
        }
        
        headers = {
            "api-subscription-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        try:
            print(f"🔍 SARVAM CLIENT: Converting {len(text)} characters to speech")
            print(f"🔍 SARVAM CLIENT: Language: {language}, Speaker: {speaker}")
            print(f"🔍 SARVAM CLIENT: Text preview: {text[:100]}...")
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if 'audios' in result and len(result['audios']) > 0:
                    audio_base64 = result['audios'][0]
                    audio_data = base64.b64decode(audio_base64)
                    print(f"✅ SARVAM CLIENT: TTS successful, audio size: {len(audio_data)} bytes")
                    return audio_data
                else:
                    print(f"❌ SARVAM CLIENT: No audio data in response: {result}")
                    return None
            else:
                print(f"❌ SARVAM CLIENT: TTS error: {response.status_code}")
                print(f"❌ SARVAM CLIENT: Response: {response.text}")
                return None
        except Exception as e:
            print(f"❌ SARVAM CLIENT: TTS exception: {e}")
            import traceback
            traceback.print_exc()
            return None

    def test_connection(self):
        """Test the Sarvam API connection"""
        if not self.api_key:
            return False, "API key not found"
        
        # Test with a simple translation
        test_text = "Hello, this is a test."
        result = self.translate(test_text, 'en-IN', 'hi-IN')
        
        if result.get('success') and result.get('translated_text') != test_text:
            return True, "Connection successful"
        else:
            return False, f"Translation test failed: {result.get('error', 'Unknown error')}"
