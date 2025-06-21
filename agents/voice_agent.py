import os
import time
import uuid
import re
from utils.sarvam_client import SarvamClient

class VoiceAgent:
    def __init__(self):
        self.sarvam_client = SarvamClient()
        
        # Updated voice profiles with correct speakers for each language
        self.voice_profiles = {
            'hi-IN': 'meera',      # Hindi - female
            'en-IN': 'arvind',     # English - male  
            'ta-IN': 'diya',       # Tamil - use 'diya' for Tamil
            'te-IN': 'pavithra',   # Telugu
            'kn-IN': 'maya',       # Kannada
            'ml-IN': 'vidya',      # Malayalam
            'gu-IN': 'manisha',    # Gujarati
            'mr-IN': 'anushka',    # Marathi
            'bn-IN': 'abhilash',   # Bengali
            'or-IN': 'arya',       # Odia
            'pa-IN': 'karun'       # Punjabi
        }
        
        # List of all valid speakers from Sarvam API
        self.allowed_speakers = [
            'meera', 'pavithra', 'maitreyi', 'arvind', 'amol', 
            'amartya', 'diya', 'neel', 'misha', 'vian', 'arjun', 
            'maya', 'anushka', 'abhilash', 'manisha', 'vidya', 
            'arya', 'karun', 'hitesh'
        ]
    
    def generate_speech_response(self, analysis_data, language='hi-IN'):
        """Generate speech from analysis data with enhanced error handling"""
        try:
            print(f"🔍 ===== VOICE AGENT DEBUG START =====")
            print(f"🔍 Generating speech for language: {language}")
            print(f"🔍 Analysis data type: {type(analysis_data)}")
            print(f"🔍 Analysis data success: {analysis_data.get('success') if isinstance(analysis_data, dict) else 'Not a dict'}")
            
            # Debug: Print the full analysis data structure
            if isinstance(analysis_data, dict):
                print(f"🔍 Analysis data keys: {list(analysis_data.keys())}")
            
            # Use Flask app root path if available, otherwise use project path
            try:
                from flask import current_app
                if current_app:
                    app_root = current_app.root_path
                    static_audio_dir = os.path.join(app_root, 'static', 'audio')
                else:
                    raise RuntimeError("No Flask app context")
            except:
                # Fallback to your project path
                project_root = '/Users/nikhilnedungadi/Desktop/NIKHIL/projects/warpspeed/swasthbharat'
                static_audio_dir = os.path.join(project_root, 'static', 'audio')
            
            print(f"🔍 Target audio directory: {static_audio_dir}")
            
            # Ensure static audio directory exists
            os.makedirs(static_audio_dir, exist_ok=True)
            
            # Set proper permissions
            if os.name != 'nt':  # Not Windows
                os.chmod(static_audio_dir, 0o755)
            
            # Format speech text based on analysis data - CONCISE VERSION FOR AUDIO
            if not analysis_data.get('success'):
                speech_text = self._get_error_speech(language)
                print(f"🔍 Using error speech text")
            else:
                speech_text = self._format_for_speech(analysis_data, language)
                print(f"🔍 Using formatted speech text")
            
            print(f"🔍 Speech text length: {len(speech_text)}")
            print(f"🔍 Speech text preview: {speech_text[:200]}...")
            
            # Get the correct speaker for the language
            speaker = self.voice_profiles.get(language, 'meera')
            print(f"🔍 Initial speaker selection: {speaker} for language: {language}")
            
            # Validate speaker is in allowed list
            if speaker not in self.allowed_speakers:
                print(f"❌ Invalid speaker {speaker}, using 'meera' as fallback")
                speaker = 'meera'
            
            print(f"🔍 Final speaker: {speaker}")
            
            # Generate audio using Sarvam TTS
            print(f"🔍 Calling Sarvam TTS...")
            try:
                audio_data = self.sarvam_client.text_to_speech(
                    speech_text,
                    language,
                    speaker=speaker
                )
                print(f"🔍 Audio data received: {type(audio_data)}")
                print(f"🔍 Audio data length: {len(audio_data) if audio_data else 'None'}")
            except Exception as tts_error:
                print(f"❌ Sarvam TTS error: {tts_error}")
                # Try fallback audio generation
                return self.generate_fallback_audio(speech_text, language)
            
            if audio_data:
                # Create unique filename with timestamp
                timestamp = int(time.time())
                audio_filename = f"analysis_{timestamp}_{uuid.uuid4().hex[:8]}.wav"
                audio_path = os.path.join(static_audio_dir, audio_filename)
                
                print(f"🔍 Saving audio to: {audio_path}")
                
                # Write audio data to file with error handling
                try:
                    with open(audio_path, 'wb') as f:
                        f.write(audio_data)
                    
                    print(f"🔍 Audio file written")
                    
                    # Set proper file permissions
                    if os.name != 'nt':  # Not Windows
                        os.chmod(audio_path, 0o644)
                    
                    # Verify file was created successfully
                    if os.path.exists(audio_path):
                        file_size = os.path.getsize(audio_path)
                        print(f"✅ Audio file created successfully: {audio_path}")
                        print(f"✅ File size: {file_size} bytes")
                        
                        if file_size > 0:
                            print(f"🔍 ===== VOICE AGENT DEBUG END - SUCCESS =====")
                            return audio_path
                        else:
                            print("❌ Audio file is empty")
                            return self.generate_fallback_audio(speech_text, language)
                    else:
                        print("❌ Audio file doesn't exist after writing")
                        return self.generate_fallback_audio(speech_text, language)
                        
                except IOError as e:
                    print(f"❌ Error writing audio file: {e}")
                    return self.generate_fallback_audio(speech_text, language)
            else:
                print("❌ No audio data received from TTS service")
                return self.generate_fallback_audio(speech_text, language)
                
        except Exception as e:
            print(f"❌ Error in generate_speech_response: {e}")
            import traceback
            traceback.print_exc()
            return self.generate_fallback_audio(speech_text if 'speech_text' in locals() else "Audio generation failed", language)
    
    def _format_for_speech(self, analysis_data, language):
        """Format analysis data for speech synthesis - CONCISE VERSION FOR SARVAM 500 CHAR LIMIT"""
        try:
            print(f"🔍 === _format_for_speech DEBUG START ===")
            
            if not analysis_data.get('success'):
                print(f"🔍 Analysis not successful, returning error speech")
                return self._get_error_speech(language)
            
            print(f"🔍 Analysis data type: {type(analysis_data)}")
            print(f"🔍 Analysis data keys: {list(analysis_data.keys()) if isinstance(analysis_data, dict) else 'Not a dict'}")
            
            # CREATE CONCISE AUDIO SUMMARY FOR TTS
            speech_content = self._create_concise_audio_summary(analysis_data)
            
            # Clean up the content for speech
            if speech_content:
                speech_text = self._clean_text_for_speech(speech_content)
                print(f"🔍 Cleaned speech text length: {len(speech_text)}")
            else:
                speech_text = "Medical analysis completed. Please consult with your doctor."
                print(f"🔍 Using fallback content")
            
            # ENSURE IT FITS SARVAM 500 CHARACTER LIMIT
            if len(speech_text) > 450:  # Leave buffer for safety
                speech_text = speech_text[:447] + "..."
                print(f"🔍 Truncated speech text to fit 500 character limit")
            
            print(f"🔍 Final speech text length: {len(speech_text)} characters")
            print(f"🔍 Final speech text preview: {speech_text}")
            print(f"🔍 === _format_for_speech DEBUG END ===")
            
            return speech_text
            
        except Exception as e:
            print(f"❌ Error formatting speech text: {e}")
            import traceback
            traceback.print_exc()
            return self._get_error_speech(language)
    
    def _create_concise_audio_summary(self, analysis_data):
        """Create a concise audio summary that fits within 500 characters"""
        try:
            # Get basic data
            structured_data = analysis_data.get('structured_data', {})
            test_results = structured_data.get('test_results', [])
            normal_count = analysis_data.get('normal_count', 0)
            concerning_count = analysis_data.get('concerning_count', 0)
            
            # Build concise summary
            summary_parts = []
            
            # Introduction
            if test_results:
                summary_parts.append(f"Your medical report shows {len(test_results)} test results.")
            
            # Overall health status
            if concerning_count == 0:
                summary_parts.append("All results are in healthy ranges.")
            elif concerning_count == 1:
                summary_parts.append(f"{normal_count} results are healthy, 1 needs attention.")
            else:
                summary_parts.append(f"{normal_count} results are healthy, {concerning_count} need attention.")
            
            # Key recommendations
            recommendations = analysis_data.get('recommendations', [])
            if recommendations:
                # Pick the most important recommendation
                key_rec = recommendations[0] if recommendations[0] != "This test shows how your body is working." else "Maintain healthy lifestyle habits."
                summary_parts.append(f"Key advice: {key_rec}")
            
            # Doctor consultation reminder
            summary_parts.append("Always consult your doctor before making health changes.")
            
            # Join and return
            concise_summary = " ".join(summary_parts)
            
            print(f"🔍 Concise summary created: {len(concise_summary)} characters")
            print(f"🔍 Concise summary: {concise_summary}")
            
            return concise_summary
            
        except Exception as e:
            print(f"❌ Error creating concise summary: {e}")
            return "Medical analysis completed. Please consult with your doctor for detailed information."

    def _clean_text_for_speech(self, text):
        """Clean text to make it more suitable for speech synthesis"""
        if not text:
            return "Medical analysis completed."
        
        # Remove markdown formatting
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Remove bold
        text = re.sub(r'\*(.*?)\*', r'\1', text)      # Remove italic
        text = re.sub(r'#{1,6}\s*', '', text)         # Remove headers
        text = re.sub(r'📋|📊|💡|⚠️|❌|✅|🔍', '', text)  # Remove emojis
        
        # Replace bullet points with spoken equivalents
        text = re.sub(r'•\s*', '', text)  # Remove bullet points for concise version
        text = re.sub(r'-\s*', '', text)
        text = re.sub(r'\d+\.\s*', '', text)
        
        # Clean up extra whitespace and line breaks
        text = re.sub(r'\n+', '. ', text)
        text = re.sub(r'\s+', ' ', text)
        
        # Remove any remaining special characters that might cause TTS issues
        text = re.sub(r'[^\w\s.,!?;:()\'-]', '', text)
        
        return text.strip()
    
    def generate_fallback_audio(self, text, language):
        """Generate simple fallback audio for testing"""
        try:
            print(f"🔍 Generating fallback audio for {language}")
            
            # Use Hindi with 'meera' speaker as fallback (most reliable)
            fallback_language = 'hi-IN'
            fallback_speaker = 'meera'
            
            # Create very short fallback text
            fallback_text = "Medical report analysis completed. Please consult with your doctor."
            
            print(f"🔍 Fallback: {fallback_language} with {fallback_speaker}")
            print(f"🔍 Fallback text: {fallback_text}")
            
            # Try with fallback settings
            audio_data = self.sarvam_client.text_to_speech(
                fallback_text,
                fallback_language,
                speaker=fallback_speaker
            )
            
            if audio_data:
                # Use project path for fallback
                project_root = '/Users/nikhilnedungadi/Desktop/NIKHIL/projects/warpspeed/swasthbharat'
                static_audio_dir = os.path.join(project_root, 'static', 'audio')
                os.makedirs(static_audio_dir, exist_ok=True)
                
                timestamp = int(time.time())
                audio_filename = f"fallback_{timestamp}.wav"
                audio_path = os.path.join(static_audio_dir, audio_filename)
                
                with open(audio_path, 'wb') as f:
                    f.write(audio_data)
                
                if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
                    print(f"✅ Fallback audio generated: {audio_path}")
                    return audio_path
                    
        except Exception as e:
            print(f"❌ Fallback audio generation failed: {e}")
            
        return None
    
    def _get_error_speech(self, language):
        """Get error message for speech in specified language - CONCISE VERSION"""
        error_messages = {
            'hi-IN': 'रिपोर्ट का विश्लेषण पूरा हो गया है। डॉक्टर से सलाह लें।',
            'en-IN': 'Report analysis completed. Please consult your doctor.',
            'ta-IN': 'அறிக்கை பகுப்பாய்வு முடிந்தது. மருத்துவரை அணுகவும்.',
            'te-IN': 'రిపోర్ట్ విశ్లేషణ పూర్తయింది. వైద్యుడిని సంప్రదించండి.',
            'kn-IN': 'ವರದಿ ವಿಶ್ಲೇಷಣೆ ಪೂರ್ಣಗೊಂಡಿದೆ. ವೈದ್ಯರನ್ನು ಸಂಪರ್ಕಿಸಿ.',
            'ml-IN': 'റിപ്പോർട്ട് വിശകലനം പൂർത്തിയായി. ഡോക്ടറെ സമീപിക്കുക.',
        }
        
        return error_messages.get(language, error_messages['en-IN'])
