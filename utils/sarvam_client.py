import requests
import base64
import os
from dotenv import load_dotenv

load_dotenv()

class SarvamClient:
    def __init__(self):
        self.api_key = os.getenv('SARVAM_API_KEY')
        self.base_url = "https://api.sarvam.ai"
        
    def translate_text(self, text, target_language='hi-IN'):
        """Translate text using Sarvam Translate API"""
        if not self.api_key:
            print("Warning: SARVAM_API_KEY not found")
            return text
            
        url = f"{self.base_url}/translate"
        
        payload = {
            "input": text,
            "source_language_code": "en-IN",
            "target_language_code": target_language,
            "speaker_gender": "Female",
            "mode": "formal",
            "model": "mayura:v1",
            "enable_preprocessing": True
        }
        
        headers = {
            "api-subscription-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                return response.json().get('translated_text', text)
            else:
                print(f"Translation error: {response.status_code} - {response.text}")
                return text
        except Exception as e:
            print(f"Translation exception: {e}")
            return text
    
    def text_to_speech(self, text, language='hi-IN', speaker='meera'):
        """Convert text to speech using Sarvam TTS API"""
        if not self.api_key:
            print("Warning: SARVAM_API_KEY not found")
            return None
            
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
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                audio_base64 = response.json()['audios'][0]
                return base64.b64decode(audio_base64)
            else:
                print(f"TTS error: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"TTS exception: {e}")
            return None
