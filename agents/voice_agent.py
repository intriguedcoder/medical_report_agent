import os
import time
import uuid
import re
import json
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
                # Check for nested analysis
                if 'analysis' in analysis_data:
                    nested_analysis = analysis_data['analysis']
                    print(f"🔍 Nested analysis keys: {list(nested_analysis.keys()) if isinstance(nested_analysis, dict) else 'Not a dict'}")
            
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
            
            # TEST TRANSLATION FIRST - ADDED FOR DEBUGGING
            self.test_translation(language)
            
            # Format speech text based on analysis data - ALWAYS TRANSLATE IF NEEDED
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
    
    # NEW METHOD: Translate analysis data for UI display
    def translate_analysis_for_display(self, analysis_data, target_language):
        """Translate analysis data for UI display"""
        try:
            print(f"🔍 === TRANSLATING ANALYSIS FOR UI DISPLAY ===")
            print(f"🔍 Target language: {target_language}")
            
            if target_language == 'en-IN':
                print(f"🔍 Target is English, returning original data")
                return analysis_data  # No translation needed
            
            # Extract the detailed summary
            english_summary = self._extract_english_summary(analysis_data)
            if not english_summary:
                print(f"🔍 No English summary found, returning original data")
                return analysis_data
            
            print(f"🔍 Found English summary: {len(english_summary)} chars")
            
            # Translate using Sarvam
            translated_summary = self._translate_with_sarvam(english_summary, target_language)
            
            # Create a deep copy of the analysis data
            translated_data = self._deep_copy_dict(analysis_data)
            
            # Update the analysis data with translated content
            self._update_analysis_with_translation(translated_data, translated_summary)
            
            print(f"✅ Analysis data translated for UI display")
            return translated_data
            
        except Exception as e:
            print(f"❌ Error translating analysis for display: {e}")
            import traceback
            traceback.print_exc()
            return analysis_data
    
    def _deep_copy_dict(self, original_dict):
        """Create a deep copy of a dictionary"""
        try:
            import copy
            return copy.deepcopy(original_dict)
        except:
            # Fallback manual copy
            if isinstance(original_dict, dict):
                new_dict = {}
                for key, value in original_dict.items():
                    if isinstance(value, dict):
                        new_dict[key] = self._deep_copy_dict(value)
                    elif isinstance(value, list):
                        new_dict[key] = value.copy()
                    else:
                        new_dict[key] = value
                return new_dict
            return original_dict
    
    def _update_analysis_with_translation(self, analysis_data, translated_text):
        """Update analysis data with translated text"""
        try:
            # Update nested analysis if it exists
            if 'analysis' in analysis_data and isinstance(analysis_data['analysis'], dict):
                if 'summary' in analysis_data['analysis']:
                    analysis_data['analysis']['summary'] = translated_text
                if 'comprehensive_analysis' in analysis_data['analysis']:
                    analysis_data['analysis']['comprehensive_analysis'] = translated_text
                if 'detailed_summary' in analysis_data['analysis']:
                    analysis_data['analysis']['detailed_summary'] = translated_text
            
            # Update top-level fields
            if 'summary' in analysis_data:
                analysis_data['summary'] = translated_text
            if 'comprehensive_analysis' in analysis_data:
                analysis_data['comprehensive_analysis'] = translated_text
            if 'detailed_summary' in analysis_data:
                analysis_data['detailed_summary'] = translated_text
                
        except Exception as e:
            print(f"❌ Error updating analysis with translation: {e}")
    
    def test_translation(self, target_language):
        """Test translation with simple text - ADDED FOR DEBUGGING"""
        if target_language == 'en-IN':
            print(f"🔍 Target is English, skipping translation test")
            return
            
        test_text = "Hello, this is a test message."
        print(f"🔍 Testing translation to {target_language}")
        print(f"🔍 Test input: {test_text}")
        
        try:
            result = self.sarvam_client.translate(
                text=test_text,
                source_language_code='en-IN',
                target_language_code=target_language
            )
            
            print(f"🔍 Test translation result: {result}")
            print(f"🔍 Test result type: {type(result)}")
            print(f"🔍 Test result success: {result.get('success') if result else 'No result'}")
            
            if result and result.get('success'):
                translated = result.get('translated_text', test_text)
                print(f"✅ Test translation successful!")
                print(f"🔍 Original: {test_text}")
                print(f"🔍 Translated: {translated}")
                
                if translated == test_text:
                    print(f"⚠️ WARNING: Test translation returned same text - translation may not be working!")
            else:
                print(f"❌ Test translation failed: {result.get('error') if result else 'No result'}")
                
        except Exception as e:
            print(f"❌ Test translation exception: {e}")
            import traceback
            traceback.print_exc()
    
    def _format_for_speech(self, analysis_data, language):
        """Format analysis data for speech synthesis - ENHANCED WITH DEBUGGING"""
        try:
            print(f"🔍 === _format_for_speech DEBUG START ===")
            print(f"🔍 Target language: {language}")
            
            if not analysis_data.get('success'):
                print(f"🔍 Analysis not successful, returning error speech")
                return self._get_error_speech(language)
            
            # STEP 1: Get the English summary (source content)
            english_summary = self._extract_english_summary(analysis_data)
            
            if not english_summary or len(english_summary.strip()) < 50:
                print(f"🔍 No suitable English summary found, using fallback")
                return self._get_error_speech(language)
            
            print(f"🔍 English summary length: {len(english_summary)}")
            print(f"🔍 English summary preview: {english_summary[:200]}...")
            
            # STEP 2: If target language is English, use directly
            if language == 'en-IN':
                print(f"🔍 Target language is English, using summary directly")
                speech_content = self._make_concise_for_tts(english_summary, language)
                return self._finalize_speech_text(speech_content)
            
            # STEP 3: For other languages, ALWAYS translate using Sarvam-Translate
            print(f"🔍 Translating English summary to {language} using Sarvam-Translate")
            translated_text = self._translate_with_sarvam(english_summary, language)
            speech_content = self._make_concise_for_tts(translated_text, language)
            return self._finalize_speech_text(speech_content)
            
        except Exception as e:
            print(f"❌ Error formatting speech text: {e}")
            import traceback
            traceback.print_exc()
            return self._get_error_speech(language)
    
    def _extract_english_summary(self, analysis_data):
        """Extract English summary from analysis data"""
        try:
            # Check nested analysis first
            nested_analysis = analysis_data.get('analysis', {})
            if nested_analysis:
                summary = nested_analysis.get('summary', '')
                if summary and len(summary.strip()) > 50:
                    return summary
                
                comprehensive = nested_analysis.get('comprehensive_analysis', '')
                if comprehensive and len(comprehensive.strip()) > 50:
                    return comprehensive
                    
                detailed = nested_analysis.get('detailed_summary', '')
                if detailed and len(detailed.strip()) > 50:
                    return detailed
            
            # Check top-level
            summary = analysis_data.get('summary', '')
            if summary and len(summary.strip()) > 50:
                return summary
            
            comprehensive = analysis_data.get('comprehensive_analysis', '')
            if comprehensive and len(comprehensive.strip()) > 50:
                return comprehensive
                
            detailed = analysis_data.get('detailed_summary', '')
            if detailed and len(detailed.strip()) > 50:
                return detailed
            
            return ""
            
        except Exception as e:
            print(f"❌ Error extracting English summary: {e}")
            return ""
    
    def _translate_with_sarvam(self, english_text, target_language):
        """Translate English text to target language using Sarvam-Translate - ENHANCED WITH DEBUGGING"""
        try:
            print(f"🔍 Translating with Sarvam: {len(english_text)} chars to {target_language}")
            print(f"🔍 Input text: {english_text[:100]}...")
            print(f"🔍 Source language: 'en-IN'")
            print(f"🔍 Target language: '{target_language}'")
            print(f"🔍 Supported languages: {list(self.voice_profiles.keys())}")
            
            if target_language == 'en-IN':
                print(f"🔍 Target is English, returning original text")
                return english_text
            
            # Handle long text by chunking
            if len(english_text) > 800:
                return self._translate_long_text(english_text, target_language)
            
            # Test Sarvam connection first
            try:
                connection_test = self.sarvam_client.test_connection()
                print(f"🔍 Sarvam connection test: {connection_test}")
            except:
                print(f"⚠️ Could not test Sarvam connection")
            
            # Use Sarvam client to translate
            result = self.sarvam_client.translate(
                text=english_text,
                source_language_code='en-IN',
                target_language_code=target_language
            )
            
            print(f"🔍 Sarvam translation result: {result}")
            print(f"🔍 Result type: {type(result)}")
            print(f"🔍 Result success: {result.get('success') if result else 'No result'}")
            
            if result and result.get('success'):
                translated_text = result.get('translated_text', english_text)
                print(f"✅ Translation successful!")
                print(f"🔍 Original length: {len(english_text)}")
                print(f"🔍 Translated length: {len(translated_text)}")
                print(f"🔍 Translated preview: {translated_text[:200]}...")
                
                # Verify translation actually happened
                if translated_text != english_text:
                    return translated_text
                else:
                    print(f"⚠️ Translation returned same text - using fallback")
                    return self._get_fallback_translation(english_text, target_language)
            else:
                print(f"❌ Translation failed: {result.get('error') if result else 'No result'}")
                return self._get_fallback_translation(english_text, target_language)
            
        except Exception as e:
            print(f"❌ Translation error: {e}")
            import traceback
            traceback.print_exc()
            return self._get_fallback_translation(english_text, target_language)
    
    def _translate_long_text(self, text, target_language):
        """Translate long text by chunking"""
        try:
            print(f"🔍 Translating long text: {len(text)} chars")
            
            # Split text into sentences
            sentences = re.split(r'[.!?]+', text)
            translated_sentences = []
            
            current_chunk = ""
            for sentence in sentences:
                if len(current_chunk + sentence) < 700:
                    current_chunk += sentence + ". "
                else:
                    if current_chunk:
                        translated_chunk = self._translate_with_sarvam(current_chunk, target_language)
                        translated_sentences.append(translated_chunk)
                    current_chunk = sentence + ". "
            
            # Translate remaining chunk
            if current_chunk:
                translated_chunk = self._translate_with_sarvam(current_chunk, target_language)
                translated_sentences.append(translated_chunk)
            
            return " ".join(translated_sentences)
            
        except Exception as e:
            print(f"❌ Error translating long text: {e}")
            return text
    
    def _get_fallback_translation(self, text, target_language):
        """Provide fallback translations for common phrases"""
        fallback_translations = {
            'hi-IN': {
                'Keep eating healthy foods like you are doing': 'जैसा आप कर रहे हैं वैसे ही स्वस्थ भोजन खाते रहें',
                'Eat more fruits and vegetables every day': 'रोज फल और सब्जियां खाएं',
                'This test shows how your body is working': 'यह जांच दिखाती है कि आपका शरीर कैसे काम कर रहा है',
                'Your health report shows': 'आपकी स्वास्थ्य रिपोर्ट दिखाती है',
                'Hello! I have analyzed your medical report': 'नमस्ते! मैंने आपकी मेडिकल रिपोर्ट का विश्लेषण किया है'
            },
            'ta-IN': {
                'Keep eating healthy foods like you are doing': 'நீங்கள் செய்வது போல் ஆரோக்கியமான உணவுகளை தொடர்ந்து சாப்பிடுங்கள்',
                'Eat more fruits and vegetables every day': 'தினமும் அதிக பழங்கள் மற்றும் காய்கறிகள் சாப்பிடுங்கள்',
                'This test shows how your body is working': 'இந்த பரிசோதனை உங்கள் உடல் எப்படி வேலை செய்கிறது என்பதைக் காட்டுகிறது',
                'Your health report shows': 'உங்கள் சுகாதார அறிக்கை காட்டுகிறது',
                'Hello! I have analyzed your medical report': 'வணக்கம்! நான் உங்கள் மருத்துவ அறிக்கையை பகுப்பாய்வு செய்துள்ளேன்'
            }
        }
        
        lang_dict = fallback_translations.get(target_language, {})
        return lang_dict.get(text, text)
    
    def _make_concise_for_tts(self, text, language):
        """Make text more concise for TTS - limit to key points"""
        try:
            # Remove very long sentences and keep only essential information
            sentences = re.split(r'[.!?]+', text)
            
            # Keep first few sentences and most important ones
            important_sentences = []
            for sentence in sentences[:10]:  # Limit to first 10 sentences
                if len(sentence.strip()) > 10:
                    important_sentences.append(sentence.strip())
            
            concise_text = '. '.join(important_sentences[:8])  # Max 8 sentences
            
            # Ensure it's not too long for TTS
            if len(concise_text) > 1000:
                concise_text = concise_text[:1000]
                # Find last complete sentence
                last_period = concise_text.rfind('.')
                if last_period > 500:
                    concise_text = concise_text[:last_period + 1]
            
            return concise_text
            
        except Exception as e:
            print(f"❌ Error making text concise: {e}")
            return text[:800]  # Fallback to first 800 chars
    
    def _finalize_speech_text(self, text):
        """Finalize speech text with proper formatting"""
        try:
            # Clean up the text
            text = re.sub(r'\s+', ' ', text)  # Remove extra whitespace
            text = text.strip()
            
            # Ensure it ends with proper punctuation
            if not text.endswith(('.', '!', '?')):
                text += '.'
            
            return text
            
        except Exception as e:
            print(f"❌ Error finalizing speech text: {e}")
            return text
    
    def _get_error_speech(self, language):
        """Get error message for speech in specified language"""
        error_messages = {
            'en-IN': "I'm sorry, I couldn't analyze your medical report properly. Please try uploading the image again or consult with your healthcare provider.",
            'hi-IN': "मुझे खुशी है कि मैं आपकी मेडिकल रिपोर्ट का सही विश्लेषण नहीं कर सका। कृपया छवि को फिर से अपलोड करें या अपने डॉक्टर से सलाह लें।",
            'ta-IN': "மன்னிக்கவும், உங்கள் மருத்துவ அறிக்கையை சரியாக பகுப்பாய்வு செய்ய முடியவில்லை। படத்தை மீண்டும் பதிவேற்றவும் அல்லது உங்கள் மருத்துவரை அணுகவும்।"
        }
        return error_messages.get(language, error_messages['en-IN'])
    
    def generate_fallback_audio(self, text, language):
        """Generate fallback audio when main TTS fails"""
        try:
            print(f"🔍 Generating fallback audio for language: {language}")
            
            # Try with different speaker
            fallback_speakers = ['meera', 'arvind', 'diya']
            
            for speaker in fallback_speakers:
                try:
                    print(f"🔍 Trying fallback speaker: {speaker}")
                    audio_data = self.sarvam_client.text_to_speech(
                        text[:500],  # Shorter text
                        language,
                        speaker=speaker
                    )
                    
                    if audio_data:
                        # Save fallback audio
                        timestamp = int(time.time())
                        audio_filename = f"fallback_{timestamp}_{uuid.uuid4().hex[:8]}.wav"
                        
                        try:
                            from flask import current_app
                            static_audio_dir = os.path.join(current_app.root_path, 'static', 'audio')
                        except:
                            project_root = '/Users/nikhilnedungadi/Desktop/NIKHIL/projects/warpspeed/swasthbharat'
                            static_audio_dir = os.path.join(project_root, 'static', 'audio')
                        
                        audio_path = os.path.join(static_audio_dir, audio_filename)
                        
                        with open(audio_path, 'wb') as f:
                            f.write(audio_data)
                        
                        if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
                            print(f"✅ Fallback audio generated: {audio_path}")
                            return audio_path
                            
                except Exception as speaker_error:
                    print(f"❌ Fallback speaker {speaker} failed: {speaker_error}")
                    continue
            
            print(f"❌ All fallback speakers failed")
            return None
            
        except Exception as e:
            print(f"❌ Error generating fallback audio: {e}")
            return None
    
    def get_supported_languages(self):
        """Get list of supported languages"""
        return list(self.voice_profiles.keys())
    
    def get_language_name(self, language_code):
        """Get human-readable language name"""
        language_names = {
            'hi-IN': 'Hindi',
            'en-IN': 'English',
            'ta-IN': 'Tamil',
            'te-IN': 'Telugu',
            'kn-IN': 'Kannada',
            'ml-IN': 'Malayalam',
            'gu-IN': 'Gujarati',
            'mr-IN': 'Marathi',
            'bn-IN': 'Bengali',
            'or-IN': 'Odia',
            'pa-IN': 'Punjabi'
        }
        return language_names.get(language_code, language_code)
    
    def validate_language(self, language_code):
        """Validate if language is supported"""
        return language_code in self.voice_profiles
    
    def debug_translation_status(self, language='hi-IN'):
        """Debug method to check translation status and capabilities"""
        try:
            print(f"🔍 === TRANSLATION DEBUG STATUS ===")
            print(f"🔍 Target language: {language}")
            print(f"🔍 Supported languages: {list(self.voice_profiles.keys())}")
            print(f"🔍 Language validation: {self.validate_language(language)}")
            
            # Test Sarvam client connection
            try:
                if hasattr(self.sarvam_client, 'test_connection'):
                    connection_status = self.sarvam_client.test_connection()
                    print(f"🔍 Sarvam connection: {connection_status}")
                else:
                    print(f"🔍 Sarvam connection: test_connection method not available")
            except Exception as conn_error:
                print(f"❌ Sarvam connection error: {conn_error}")
            
            # Test simple translation
            if language != 'en-IN':
                test_result = self.test_translation(language)
                print(f"🔍 Translation test completed")
            else:
                print(f"🔍 Target is English, skipping translation test")
            
            # Check voice profile
            speaker = self.voice_profiles.get(language, 'meera')
            print(f"🔍 Selected speaker: {speaker}")
            print(f"🔍 Speaker validation: {speaker in self.allowed_speakers}")
            
            return {
                'language': language,
                'supported': self.validate_language(language),
                'speaker': speaker,
                'speaker_valid': speaker in self.allowed_speakers,
                'sarvam_available': hasattr(self, 'sarvam_client') and self.sarvam_client is not None
            }
            
        except Exception as e:
            print(f"❌ Debug translation status error: {e}")
            import traceback
            traceback.print_exc()
            return {
                'error': str(e),
                'language': language,
                'supported': False
            }
    
    def cleanup_old_audio_files(self, max_age_hours=24):
        """Clean up old audio files to save space"""
        try:
            try:
                from flask import current_app
                static_audio_dir = os.path.join(current_app.root_path, 'static', 'audio')
            except:
                project_root = '/Users/nikhilnedungadi/Desktop/NIKHIL/projects/warpspeed/swasthbharat'
                static_audio_dir = os.path.join(project_root, 'static', 'audio')
            
            if not os.path.exists(static_audio_dir):
                return
            
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            for filename in os.listdir(static_audio_dir):
                if filename.endswith('.wav'):
                    file_path = os.path.join(static_audio_dir, filename)
                    file_age = current_time - os.path.getctime(file_path)
                    
                    if file_age > max_age_seconds:
                        try:
                            os.remove(file_path)
                            print(f"🗑️ Cleaned up old audio file: {filename}")
                        except:
                            pass
                            
        except Exception as e:
            print(f"❌ Error cleaning up audio files: {e}")
