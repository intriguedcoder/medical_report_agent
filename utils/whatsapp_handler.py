import requests
import os
from dotenv import load_dotenv

load_dotenv()

class WhatsAppHandler:
    def __init__(self):
        self.token = os.getenv('WHATSAPP_TOKEN')
        self.base_url = "https://graph.facebook.com/v17.0"
    
    def send_text_message(self, phone_number, message):
        """Send text message via WhatsApp"""
        url = f"{self.base_url}/YOUR_PHONE_NUMBER_ID/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "text",
            "text": {"body": message}
        }
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            return response.status_code == 200
        except Exception as e:
            print(f"WhatsApp send error: {e}")
            return False
    
    def send_audio_message(self, phone_number, audio_file_path):
        """Send audio message via WhatsApp"""
        # Implementation depends on your WhatsApp Business API setup
        # This is a placeholder for audio message sending
        pass
    
    def download_image(self, media_id):
        """Download image from WhatsApp"""
        # Get media URL
        url = f"{self.base_url}/{media_id}"
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                media_url = response.json()['url']
                
                # Download the actual image
                image_response = requests.get(media_url, headers=headers)
                if image_response.status_code == 200:
                    # Save to temporary file
                    import tempfile
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
                    temp_file.write(image_response.content)
                    temp_file.close()
                    return temp_file.name
        except Exception as e:
            print(f"Image download error: {e}")
        
        return None
