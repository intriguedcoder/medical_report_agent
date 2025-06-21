import os
import time
import uuid
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
            
            # Format speech text based on analysis data
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
    
    def generate_fallback_audio(self, text, language):
        """Generate simple fallback audio for testing"""
        try:
            print(f"🔍 Generating fallback audio for {language}")
            
            # Use Hindi with 'meera' speaker as fallback (most reliable)
            fallback_language = 'hi-IN'
            fallback_speaker = 'meera'
            
            # Limit text length for fallback
            fallback_text = text[:300] if len(text) > 300 else text
            
            print(f"🔍 Fallback: {fallback_language} with {fallback_speaker}")
            print(f"🔍 Fallback text: {fallback_text[:100]}...")
            
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
    
    def _format_for_speech(self, analysis_data, language):
        """Format analysis data for speech synthesis"""
        try:
            if not analysis_data.get('success'):
                return self._get_error_speech(language)
            
            # Extract analysis content
            analysis = analysis_data.get('analysis', {})
            
            if isinstance(analysis, dict):
                summary = analysis.get('summary', '')
                comprehensive = analysis.get('comprehensive_analysis', '')
                
                # Use comprehensive analysis if available, otherwise summary
                speech_text = comprehensive if comprehensive else summary
                
                if not speech_text:
                    speech_text = "Medical report has been analyzed successfully."
                
            else:
                speech_text = "Medical report analysis completed."
            
            # Limit text length for TTS (Sarvam has limits)
            if len(speech_text) > 500:
                speech_text = speech_text[:497] + "..."
            
            return speech_text
            
        except Exception as e:
            print(f"❌ Error formatting speech text: {e}")
            return self._get_error_speech(language)
    
    def _get_error_speech(self, language):
        """Get error message for speech in specified language"""
        error_messages = {
            'hi-IN': 'रिपोर्ट का विश्लेषण पूरा हो गया है। कृपया डॉक्टर से सलाह लें।',
            'en-IN': 'Report analysis completed. Please consult with your doctor.',
            'ta-IN': 'அறிக்கை பகுப்பாய்வு முடிந்தது. தயவுசெய்து உங்கள் மருத்துவரை அணுகவும்.',
            'te-IN': 'రిపోర్ట్ విశ్లేషణ పూర్తయింది. దయచేసి మీ వైద్యుడిని సంప్రదించండి.',
            'kn-IN': 'ವರದಿ ವಿಶ್ಲೇಷಣೆ ಪೂರ್ಣಗೊಂಡಿದೆ. ದಯವಿಟ್ಟು ನಿಮ್ಮ ವೈದ್ಯರನ್ನು ಸಂಪರ್ಕಿಸಿ.',
            'ml-IN': 'റിപ്പോർട്ട് വിശകലനം പൂർത്തിയായി. ദയവായി നിങ്ങളുടെ ഡോക്ടറെ സമീപിക്കുക.',
        }
        
        return error_messages.get(language, error_messages['en-IN'])
    
    def test_sarvam_client(self):
        """Test if Sarvam client is working properly"""
        try:
            print(f"🔍 ===== SARVAM CLIENT TEST START =====")
            
            # Test with simple text and reliable settings
            test_text = "Hello, this is a test message."
            test_language = "hi-IN"  # Use Hindi as most reliable
            test_speaker = "meera"   # Most reliable speaker
            
            print(f"🔍 Testing with:")
            print(f"   Text: {test_text}")
            print(f"   Language: {test_language}")
            print(f"   Speaker: {test_speaker}")
            
            # Call the TTS method
            audio_data = self.sarvam_client.text_to_speech(
                text=test_text,
                language=test_language,
                speaker=test_speaker
            )
            
            print(f"🔍 Audio data received: {type(audio_data)}")
            print(f"🔍 Audio data length: {len(audio_data) if audio_data else 'None'}")
            
            if audio_data:
                print(f"✅ Sarvam client working! Received {len(audio_data)} bytes")
                
                # Test saving the audio
                project_root = '/Users/nikhilnedungadi/Desktop/NIKHIL/projects/warpspeed/swasthbharat'
                test_dir = os.path.join(project_root, 'static', 'audio')
                os.makedirs(test_dir, exist_ok=True)
                
                test_file = os.path.join(test_dir, 'sarvam_test.wav')
                with open(test_file, 'wb') as f:
                    f.write(audio_data)
                
                if os.path.exists(test_file) and os.path.getsize(test_file) > 0:
                    print(f"✅ Test audio file saved: {test_file}")
                    print(f"✅ File size: {os.path.getsize(test_file)} bytes")
                    return True, test_file
                else:
                    print(f"❌ Failed to save test audio file")
                    return False, None
            else:
                print(f"❌ Sarvam client returned no data")
                return False, None
                
        except Exception as e:
            print(f"❌ Sarvam client test failed: {e}")
            import traceback
            traceback.print_exc()
            return False, None
